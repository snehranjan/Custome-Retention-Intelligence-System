import os
import sys
sys.path.insert(0, os.path.abspath('.'))

import sqlite3
import pandas as pd
import numpy as np
import uuid
from datetime import datetime, timezone

from backend.app.services.model_loader import ModelLoader
from backend.app.services.churn_service import ChurnPredictionService
from backend.app.services.retention_service import RetentionRecommendationEngine
from backend.app.schemas.ml import ChurnPredictionResponse, RawCustomerFeatures, SegmentationResponse
from backend.ml.advanced_feature_engineering import compute_advanced_features

ModelLoader.setup_python_path()
pipeline = ModelLoader.get_rf_pipeline()

CLUSTER_PERSONAS = {
    0: ("Champions & High-Value Loyalists", "Frequent buyers with high monetary value and high retention propensity."),
    1: ("At-Risk / Lapsed Low-Value Customers", "Customers with long dormancy, low order count, and high churn probability."),
    2: ("Zero Delivered-Purchase Customers", "Accounts with orders cancelled or returned, with zero fulfilled purchases."),
    3: ("Steady Core Repeaters", "Reliable repeat customers with consistent cadence and moderate order value."),
    4: ("Recent Low-Ticket / New Promising Customers", "Recently acquired customers with small cart values and growing interest."),
}

conn = sqlite3.connect('data/local_database.db')
c = conn.cursor()

pred_cnt = c.execute("SELECT COUNT(*) FROM customer_predictions").fetchone()[0]
seg_cnt = c.execute("SELECT COUNT(*) FROM customer_segments").fetchone()[0]
rec_cnt = c.execute("SELECT COUNT(*) FROM retention_recommendations").fetchone()[0]
print(f"Current DB Counts before seed: predictions={pred_cnt}, segments={seg_cnt}, recs={rec_cnt}")

if pred_cnt < 7000 or seg_cnt < 7000:
    print("Seeding 7,000 customer predictions, segments, and retention recommendations...")
    df_feat = pd.read_csv('data/processed/customer_features.csv')
    df_seg = pd.read_csv('data/processed/customer_segments.csv')
    df_seg['segment_name'] = df_seg['cluster_id'].map(lambda cid: CLUSTER_PERSONAS[cid][0])
    df_full = df_feat.merge(df_seg[['customer_id', 'cluster_id', 'segment_name']], on='customer_id')
    df_augmented = compute_advanced_features(df_full)

    features_list = ChurnPredictionService.CONFIG_D_FEATURES
    X = df_augmented[features_list]

    probs = pipeline.predict_proba(X)[:, 1]
    preds = (probs >= 0.50).astype(int)

    now_utc = datetime.now(timezone.utc).isoformat()
    pred_rows = []
    seg_rows = []
    rec_rows = []

    OPTIONAL_COLS = {
        "recency_days", "recency_delivered_days", "hist_return_rate",
        "hist_cancellation_rate", "hist_average_delivery_delay_days",
        "velocity_ratio_30_90", "velocity_ratio_90_180", "delay_friction_score"
    }

    INT_COLS = {
        "has_historical_orders", "has_delivered_order", "hist_order_count",
        "hist_delivered_order_count", "hist_returned_order_count", "hist_cancelled_order_count",
        "orders_last_30_days", "orders_last_90_days", "orders_last_180_days",
        "delivered_orders_last_30_days", "delivered_orders_last_90_days", "delivered_orders_last_180_days",
        "hist_delivery_delay_missing_count", "hist_discounted_order_count", "hist_discount_missing_count",
        "hist_payment_missing_count", "hist_cod_order_count", "hist_upi_order_count",
        "has_orders_last_90_days", "has_orders_last_180_days", "missing_friction_score", "cluster_id"
    }

    for idx, row in df_augmented.iterrows():
        cid = str(row['customer_id'])
        p = float(probs[idx])
        pred_class = int(preds[idx])
        tier = 'LOW' if p < 0.50 else ('MODERATE' if p < 0.70 else 'HIGH')
        pid = str(uuid.uuid4())

        # Prediction row
        pred_rows.append((
            pid, cid, p, round(1.0 - p, 4), pred_class, 0.50, tier,
            "RandomForestClassifier_ConfigD", "1.0.0",
            "24F1F0E33C75B5590906369960DB6E5951EC95DF9AE40384DA60082B3438F301",
            now_utc, now_utc
        ))

        # Segment row
        cluster_id = int(row['cluster_id'])
        persona_name, profile_desc = CLUSTER_PERSONAS[cluster_id]
        recency = float(row['recency_delivered_days']) if pd.notnull(row['recency_delivered_days']) else 1117.0
        orders_count = int(row['hist_delivered_order_count']) if pd.notnull(row['hist_delivered_order_count']) else 0
        order_value = float(row['hist_delivered_order_value_inr']) if pd.notnull(row['hist_delivered_order_value_inr']) else 0.0

        s_id = str(uuid.uuid4())
        seg_rows.append((
            s_id, cid, cluster_id, persona_name,
            recency, orders_count, order_value,
            "KMeans_RFM_K5", 1, now_utc, now_utc
        ))

        # Retention Recommendations
        feat_dict = {}
        for col in features_list:
            val = row[col]
            if pd.isna(val):
                if col in OPTIONAL_COLS:
                    feat_dict[col] = None
                elif col in INT_COLS:
                    feat_dict[col] = 0
                else:
                    feat_dict[col] = 0.0
            else:
                if col in INT_COLS:
                    feat_dict[col] = int(val)
                elif col in ("city", "state"):
                    feat_dict[col] = str(val)
                else:
                    feat_dict[col] = float(val)

        raw_feat = RawCustomerFeatures(**feat_dict)
        churn_resp = ChurnPredictionResponse(
            churn_probability=p,
            retention_probability=round(1.0 - p, 4),
            predicted_class=pred_class,
            decision_threshold=0.50,
            prediction_label="Churn" if pred_class == 1 else "Retained",
            risk_tier=tier,
        )
        seg_resp = SegmentationResponse(
            cluster_id=cluster_id,
            persona_name=persona_name,
            behavioral_profile=profile_desc,
        )

        recs = RetentionRecommendationEngine.generate_recommendations(raw_feat, churn_resp, seg_resp)
        for r in recs.recommendations:
            rec_rows.append((
                str(uuid.uuid4()), cid, pid,
                r.category, r.suggested_action, r.reason, r.evidence,
                r.priority, "PENDING", now_utc, now_utc, now_utc
            ))

    # Atomic insert
    with conn:
        c.executemany("""
            INSERT INTO customer_predictions (
                prediction_id, customer_id, churn_probability, retention_probability,
                predicted_churn, decision_threshold, risk_tier, model_name,
                model_version, model_hash, prediction_timestamp, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, pred_rows)

        c.executemany("""
            INSERT INTO customer_segments (
                segment_record_id, customer_id, cluster_id, segment_name,
                recency_delivered_days, hist_delivered_order_count,
                hist_delivered_order_value_inr, segmentation_model,
                is_current, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, seg_rows)

        c.executemany("""
            INSERT INTO retention_recommendations (
                recommendation_id, customer_id, prediction_id, recommendation_category,
                recommendation_title, recommendation_description, evidence, priority,
                recommendation_status, generated_at, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, rec_rows)

    print(f"Seeding completed successfully! Inserted {len(pred_rows)} predictions, {len(seg_rows)} segments, {len(rec_rows)} recommendations.")

p_count = c.execute("SELECT COUNT(*) FROM customer_predictions").fetchone()[0]
s_count = c.execute("SELECT COUNT(*) FROM customer_segments").fetchone()[0]
r_count = c.execute("SELECT COUNT(*) FROM retention_recommendations").fetchone()[0]
print(f"Verified Final DB Counts: predictions={p_count}, segments={s_count}, recs={r_count}")

conn.close()
