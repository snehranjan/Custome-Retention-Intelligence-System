"""
Indian E-Commerce Customer Retention Intelligence System
Module: Phase 5 — Prepare Modeling Dataset
Description: Prepares the curated, leakage-free modeling dataset by joining
             Phase 3 customer features with Phase 4 unsupervised cluster assignments.
             Exports modeling_dataset.csv and feature_columns.json documenting
             Configuration A (36 baseline features) and Configuration B (37 features).

Author: BCA (AI & ML) Project Team
"""

import os
import sys
import json
import pandas as pd
import numpy as np

# Ensure backend/ml is on sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Path configuration
FEATURES_PATH = os.path.join("data", "processed", "customer_features.csv")
SEGMENTS_PATH = os.path.join("data", "processed", "customer_segments.csv")
OUTPUT_DIR = os.path.join("data", "modeling")
MODELING_DATASET_PATH = os.path.join(OUTPUT_DIR, "modeling_dataset.csv")
FEATURE_COLUMNS_PATH = os.path.join(OUTPUT_DIR, "feature_columns.json")

# Approved Feature Definitions from Checkpoint 1
CATEGORICAL_FEATURES_CONFIG_A = [
    "city",
    "state"
]

NUMERICAL_FEATURES = [
    "customer_tenure_days",
    "has_historical_orders",
    "recency_days",
    "recency_delivered_days",
    "has_delivered_order",
    "hist_order_count",
    "hist_delivered_order_count",
    "hist_returned_order_count",
    "hist_cancelled_order_count",
    "hist_total_order_value_inr",
    "hist_delivered_order_value_inr",
    "hist_total_recorded_discount_inr",
    "hist_average_order_value_inr",
    "orders_last_30_days",
    "orders_last_90_days",
    "orders_last_180_days",
    "delivered_orders_last_30_days",
    "delivered_orders_last_90_days",
    "delivered_orders_last_180_days",
    "hist_return_rate",
    "hist_cancellation_rate",
    "hist_average_delivery_delay_days",
    "hist_delivery_delay_missing_count",
    "hist_delivery_delay_missing_rate",
    "hist_average_discount_amount_inr",
    "hist_discounted_order_count",
    "hist_discount_missing_count",
    "hist_discount_missing_rate",
    "hist_payment_missing_count",
    "hist_payment_missing_rate",
    "hist_cod_order_count",
    "hist_cod_usage_rate",
    "hist_upi_order_count",
    "hist_upi_usage_rate"
]

CONFIGURATION_A_FEATURES = CATEGORICAL_FEATURES_CONFIG_A + NUMERICAL_FEATURES
CONFIGURATION_B_FEATURES = CONFIGURATION_A_FEATURES + ["cluster_id"]

CATEGORICAL_FEATURES_CONFIG_B = CATEGORICAL_FEATURES_CONFIG_A + ["cluster_id"]

EXCLUDED_COLUMNS = [
    "customer_name",
    "signup_date",
    "cluster_name"
]


def prepare_modeling_data():
    print("=" * 75)
    print("PHASE 5: PREPARING MODELING DATASET & FEATURE DEFINITIONS")
    print("=" * 75)

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # 1. Load source datasets
    print(f"Loading Phase 3 features from: {FEATURES_PATH}")
    df_feat = pd.read_csv(FEATURES_PATH)
    print(f"  -> Features shape: {df_feat.shape}")

    print(f"Loading Phase 4 segments from: {SEGMENTS_PATH}")
    df_seg = pd.read_csv(SEGMENTS_PATH)
    print(f"  -> Segments shape: {df_seg.shape}")

    # 2. Validate row counts and keys
    assert len(df_feat) == 7000, f"Expected 7,000 features rows, found {len(df_feat)}"
    assert len(df_seg) == 7000, f"Expected 7,000 segments rows, found {len(df_seg)}"
    assert df_feat["customer_id"].nunique() == 7000, "Features customer_id not unique"
    assert df_seg["customer_id"].nunique() == 7000, "Segments customer_id not unique"
    assert set(df_feat["customer_id"]) == set(df_seg["customer_id"]), "Customer ID mismatch between features and segments"

    # 3. Perform validated 1-to-1 join
    print("Executing validated 1-to-1 join on customer_id...")
    df_merged = pd.merge(
        df_feat,
        df_seg[["customer_id", "cluster_id"]],
        on="customer_id",
        how="left",
        validate="1:1"
    )

    assert len(df_merged) == 7000, f"Merged row count changed to {len(df_merged)}"
    assert df_merged["cluster_id"].isnull().sum() == 0, "Missing cluster_id found after merge"
    assert set(df_merged["cluster_id"].unique()) == {0, 1, 2, 3, 4}, "Unexpected cluster_id values"

    # 4. Construct final column order
    # customer_id + 36 Config A features + cluster_id + churn = 39 columns
    final_columns = ["customer_id"] + CONFIGURATION_A_FEATURES + ["cluster_id", "churn"]
    df_modeling = df_merged[final_columns].copy()

    # Ensure cluster_id is int64 (will be treated as categorical in pipelines)
    df_modeling["cluster_id"] = df_modeling["cluster_id"].astype(int)

    # Validate target
    assert set(df_modeling["churn"].unique()) == {0, 1}, "Target churn contains values other than 0 and 1"
    assert df_modeling["churn"].isnull().sum() == 0, "Missing values found in target churn"

    # Verify column counts
    print(f"\nValidating schema:")
    print(f"  - Total modeling columns: {len(df_modeling.columns)} (Expected 39)")
    print(f"  - Configuration A feature count: {len(CONFIGURATION_A_FEATURES)} (Expected 36)")
    print(f"  - Configuration B feature count: {len(CONFIGURATION_B_FEATURES)} (Expected 37)")
    print(f"  - Target column: churn")
    print(f"  - Identifier column: customer_id (tracing only)")

    assert len(df_modeling.columns) == 39, f"Expected 39 columns, got {len(df_modeling.columns)}"
    assert len(CONFIGURATION_A_FEATURES) == 36, f"Expected 36 Config A features, got {len(CONFIGURATION_A_FEATURES)}"
    assert len(CONFIGURATION_B_FEATURES) == 37, f"Expected 37 Config B features, got {len(CONFIGURATION_B_FEATURES)}"

    # 5. Export modeling_dataset.csv
    df_modeling.to_csv(MODELING_DATASET_PATH, index=False)
    print(f"\nSaved modeling dataset to: {MODELING_DATASET_PATH}")
    print(f"  -> File size: {os.path.getsize(MODELING_DATASET_PATH) / 1024:.1f} KB")
    print(f"  -> Class distribution: 0={int((df_modeling['churn'] == 0).sum())} ({((df_modeling['churn'] == 0).mean()*100):.2f}%), "
          f"1={int((df_modeling['churn'] == 1).sum())} ({((df_modeling['churn'] == 1).mean()*100):.2f}%)")

    # 6. Export feature_columns.json
    feature_metadata = {
        "metadata": {
            "title": "Phase 5 Modeling Feature Specifications & Allowlist",
            "snapshot_cutoff_date": "2025-12-31",
            "target_label_window": "2026-01-01 through 2026-03-31, inclusive",
            "total_customers": 7000,
            "modeling_dataset_file": "data/modeling/modeling_dataset.csv"
        },
        "target_column": "churn",
        "identifier_column": "customer_id",
        "configuration_a": {
            "name": "Baseline Behavioral Features (Phase 3)",
            "feature_count": len(CONFIGURATION_A_FEATURES),
            "categorical_features": CATEGORICAL_FEATURES_CONFIG_A,
            "numerical_features": NUMERICAL_FEATURES,
            "features_ordered": CONFIGURATION_A_FEATURES
        },
        "configuration_b": {
            "name": "Behavioral Features + Unsupervised RFM Cluster Persona",
            "feature_count": len(CONFIGURATION_B_FEATURES),
            "categorical_features": CATEGORICAL_FEATURES_CONFIG_B,
            "numerical_features": NUMERICAL_FEATURES,
            "features_ordered": CONFIGURATION_B_FEATURES
        },
        "excluded_columns": EXCLUDED_COLUMNS,
        "imputation_strategy": {
            "numerical": "median imputation with missingness indicators for partially recorded metrics",
            "categorical": "most-frequent imputation or 'Unknown' category encoding"
        }
    }

    with open(FEATURE_COLUMNS_PATH, "w", encoding="utf-8") as f:
        json.dump(feature_metadata, f, indent=2)

    print(f"Saved feature column specifications to: {FEATURE_COLUMNS_PATH}")
    print("=" * 75)
    print("MODELING DATASET PREPARATION COMPLETED SUCCESSFULLY!")
    print("=" * 75)


if __name__ == "__main__":
    prepare_modeling_data()
