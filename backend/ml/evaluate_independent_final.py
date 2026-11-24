"""
Indian E-Commerce Customer Retention Intelligence System
Module: Phase 5.1 — Checkpoint 4 Independent Evaluation Script
Description: Conducts the single, one-time independent evaluation of the locked
             Random Forest Configuration D pipeline on the sealed 1,500-customer
             independent test cohort at the pre-locked decision threshold of 0.50.

Author: Senior ML Engineer, Model Validation Auditor and Project Lead
Observation Cutoff: 2025-12-31
Locked Decision Threshold: 0.50 (Strictly enforced)
"""

import os
import sys
import json
import hashlib
import numpy as np
import pandas as pd
import joblib

from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    roc_auc_score, average_precision_score, balanced_accuracy_score,
    confusion_matrix, classification_report, brier_score_loss
)

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, os.path.join(PROJECT_ROOT, "backend", "ml"))

import feature_engineering as fe
import advanced_feature_engineering as afe

# Input paths
CUST_INDEP_PATH = os.path.join(PROJECT_ROOT, "data", "independent_test", "raw", "customers_independent.csv")
ORD_INDEP_PATH = os.path.join(PROJECT_ROOT, "data", "independent_test", "raw", "orders_independent.csv")
MANIFEST_PATH = os.path.join(PROJECT_ROOT, "data", "independent_test", "raw", "independent_cohort_manifest.json")

# Model paths
LOCKED_MODEL_PATH = os.path.join(PROJECT_ROOT, "models", "phase5_1", "checkpoint3", "random_forest_config_d_pipeline.joblib")
PROD_MODEL_PATH = os.path.join(PROJECT_ROOT, "models", "phase5_1", "final_model", "final_churn_rf_pipeline.joblib")
SEGMENTATION_SCALER_PATH = os.path.join(PROJECT_ROOT, "models", "segmentation_scaler.joblib")
KMEANS_MODEL_PATH = os.path.join(PROJECT_ROOT, "models", "kmeans_customer_segmentation.joblib")

# Output paths
EVAL_DIR = os.path.join(PROJECT_ROOT, "reports", "phase5_1", "final_evaluation")
PROCESSED_INDEP_DIR = os.path.join(PROJECT_ROOT, "data", "independent_test", "processed")
os.makedirs(EVAL_DIR, exist_ok=True)
os.makedirs(PROCESSED_INDEP_DIR, exist_ok=True)

EXPECTED_MODEL_SHA = "24F1F0E33C75B5590906369960DB6E5951EC95DF9AE40384DA60082B3438F301"
LOCKED_THRESHOLD = 0.50


def compute_sha256(file_path):
    h = hashlib.sha256()
    with open(file_path, "rb") as f:
        while chunk := f.read(8192):
            h.update(chunk)
    return h.hexdigest().upper()


def run_independent_evaluation():
    print("=" * 80)
    print("PHASE 5.1 — CHECKPOINT 4: INDEPENDENT EVALUATION OF LOCKED MODEL")
    print("=" * 80)

    # 1. Verify Model Locks
    print("\n1. Verifying locked model artifacts and SHA-256 integrity...")
    assert os.path.exists(LOCKED_MODEL_PATH), f"Locked model not found: {LOCKED_MODEL_PATH}"
    actual_model_sha = compute_sha256(LOCKED_MODEL_PATH)
    assert actual_model_sha == EXPECTED_MODEL_SHA, f"MODEL TAMPERING DETECTED! Expected {EXPECTED_MODEL_SHA}, got {actual_model_sha}"
    print(f"   [PASS] Locked Model SHA-256 Verified: {actual_model_sha}")

    # Verify production copy
    if os.path.exists(PROD_MODEL_PATH):
        prod_sha = compute_sha256(PROD_MODEL_PATH)
        assert prod_sha == EXPECTED_MODEL_SHA, f"Production copy hash mismatch: {prod_sha}"
        print(f"   [PASS] Production Copy SHA-256 Verified: {prod_sha}")

    # 2. Load Raw Independent Cohort Data
    print("\n2. Loading sealed independent test cohort data...")
    cust_df = pd.read_csv(CUST_INDEP_PATH)
    ord_df = pd.read_csv(ORD_INDEP_PATH)
    assert len(cust_df) == 1500, f"Expected 1,500 independent customers, got {len(cust_df)}"
    print(f"   [PASS] Loaded {len(cust_df)} independent customers and {len(ord_df)} total transactions.")

    # 3. Engineer Base Features (Strictly <= 2025-12-31)
    print("\n3. Engineering base customer features (historical cutoff: 2025-12-31)...")
    base_features = fe.engineer_features(cust_df, ord_df, snapshot_date_str="2025-12-31")
    assert len(base_features) == 1500, "Base features row count mismatch"

    # 4. Assign RFM Clusters using Frozen Phase 4 Models (Do NOT refit!)
    print("\n4. Assigning RFM clusters using frozen Phase 4 K-Means & Scaler...")
    scaler = joblib.load(SEGMENTATION_SCALER_PATH)
    kmeans = joblib.load(KMEANS_MODEL_PATH)

    rfm_recency = base_features["recency_delivered_days"].fillna(1117.0)
    rfm_freq = base_features["hist_delivered_order_count"]
    rfm_monetary = base_features["hist_delivered_order_value_inr"]

    log_rfm = pd.DataFrame({
        "recency_delivered_days": np.log1p(rfm_recency),
        "hist_delivered_order_count": np.log1p(rfm_freq),
        "hist_delivered_order_value_inr": np.log1p(rfm_monetary)
    })

    X_rfm_scaled = scaler.transform(log_rfm)
    clusters = kmeans.predict(X_rfm_scaled)
    base_features["cluster_id"] = clusters
    print("   [PASS] Cluster assignments completed. Distribution:")
    for c_id, count in pd.Series(clusters).value_counts().sort_index().items():
        print(f"      - Cluster {c_id}: {count:4d} customers ({count/1500*100:5.2f}%)")

    # 5. Compute Advanced Features
    print("\n5. Computing advanced behavioral momentum & friction features...")
    adv_features = afe.compute_advanced_features(base_features)
    print(f"   [PASS] Advanced feature dataframe shape: {adv_features.shape}")

    # Save derived independent dataset
    derived_p = os.path.join(PROCESSED_INDEP_DIR, "independent_features.csv")
    adv_features.to_csv(derived_p, index=False)
    print(f"   [PASS] Derived independent features saved to: {derived_p}")

    # 6. Extract Config D Features in Exact Model Order
    with open(os.path.join(EVAL_DIR, "final_model_lock_manifest.json"), "r") as f:
        lock_man = json.load(f)
    req_cols = lock_man["raw_numerical_features"] + lock_man["raw_categorical_features"]
    assert len(req_cols) == 43, f"Expected 43 raw input features, got {len(req_cols)}"

    X_test = adv_features[req_cols].copy()
    y_test = cust_df["churn"].values

    print(f"   [PASS] Test matrix shape: {X_test.shape} (43 raw features)")
    print(f"   [PASS] Ground-truth churn distribution: Retained (0): {(y_test==0).sum()}, Churned (1): {(y_test==1).sum()}")

    # 7. Execute Single Inference on Locked Pipeline
    print(f"\n6. Executing single independent inference with locked threshold {LOCKED_THRESHOLD}...")
    pipeline = joblib.load(LOCKED_MODEL_PATH)

    # Verify fitted sample size of model
    clf = pipeline.named_steps["clf"]
    assert all(t.tree_.weighted_n_node_samples[0] == 5950.0 for t in clf.estimators_), "Model was not fit on 5,950 records!"

    y_prob = pipeline.predict_proba(X_test)[:, 1]
    assert np.isfinite(y_prob).all(), "Non-finite predicted probabilities!"
    assert (y_prob >= 0.0).all() and (y_prob <= 1.0).all(), "Probabilities outside [0, 1]!"

    y_pred = (y_prob >= LOCKED_THRESHOLD).astype(int)

    # 8. Compute Independent Evaluation Metrics
    print("\n7. Computing independent performance metrics...")
    cm = confusion_matrix(y_test, y_pred)
    tn, fp, fn, tp = cm.ravel()

    acc = float(accuracy_score(y_test, y_pred))
    prec = float(precision_score(y_test, y_pred))
    rec = float(recall_score(y_test, y_pred))
    f1 = float(f1_score(y_test, y_pred))
    roc_auc = float(roc_auc_score(y_test, y_prob))
    pr_auc = float(average_precision_score(y_test, y_prob))
    bacc = float(balanced_accuracy_score(y_test, y_pred))
    spec = float(tn / (tn + fp))
    fpr = float(fp / (fp + tn))
    fnr = float(fn / (fn + tp))
    brier = float(brier_score_loss(y_test, y_prob))

    print(f"   Accuracy:            {acc * 100:.2f}%")
    print(f"   Precision:           {prec * 100:.2f}%")
    print(f"   Recall (Sensitivity):{rec * 100:.2f}%")
    print(f"   Specificity:         {spec * 100:.2f}%")
    print(f"   Balanced Accuracy:   {bacc * 100:.2f}%")
    print(f"   F1-Score:            {f1:.4f}")
    print(f"   ROC-AUC:             {roc_auc:.4f}")
    print(f"   Average Precision:   {pr_auc:.4f}")
    print(f"   False Positive Rate: {fpr * 100:.2f}%")
    print(f"   False Negative Rate: {fnr * 100:.2f}%")
    print(f"   Brier Score:         {brier:.4f}")
    print(f"\n   Confusion Matrix: TN={tn}, FP={fp}, FN={fn}, TP={tp}")

    # 9. Save Predictions Table
    pred_df = pd.DataFrame({
        "customer_id": cust_df["customer_id"],
        "actual_churn": y_test,
        "predicted_probability": np.round(y_prob, 5),
        "predicted_churn": y_pred,
        "classification_outcome": np.where(
            (y_test == 1) & (y_pred == 1), "TP",
            np.where((y_test == 0) & (y_pred == 0), "TN",
                     np.where((y_test == 0) & (y_pred == 1), "FP", "FN"))
        )
    })
    pred_p = os.path.join(EVAL_DIR, "independent_test_predictions.csv")
    pred_df.to_csv(pred_p, index=False)
    print(f"\n8. Saved predictions to: {pred_p}")

    # 10. Save Metrics JSON
    metrics_dict = {
        "evaluation_milestone": "Phase 5.1 Checkpoint 4",
        "evaluation_timestamp": pd.Timestamp.now().isoformat(),
        "dataset": "Phase 5.1 Independent Synthetic Test Cohort (customers_independent.csv)",
        "sample_size": len(cust_df),
        "locked_decision_threshold": LOCKED_THRESHOLD,
        "model_id": "random_forest_config_d",
        "model_sha256": actual_model_sha,
        "metrics": {
            "accuracy": acc,
            "precision": prec,
            "recall": rec,
            "specificity": spec,
            "balanced_accuracy": bacc,
            "f1_score": f1,
            "roc_auc": roc_auc,
            "average_precision": pr_auc,
            "false_positive_rate": fpr,
            "false_negative_rate": fnr,
            "brier_score": brier
        },
        "class_distributions": {
            "actual_retained_0": int((y_test == 0).sum()),
            "actual_churned_1": int((y_test == 1).sum()),
            "actual_churn_rate": float(np.mean(y_test)),
            "predicted_retained_0": int((y_pred == 0).sum()),
            "predicted_churned_1": int((y_pred == 1).sum()),
            "predicted_churn_rate": float(np.mean(y_pred))
        },
        "confusion_matrix": {
            "true_negatives": int(tn),
            "false_positives": int(fp),
            "false_negatives": int(fn),
            "true_positives": int(tp)
        },
        "development_cv_comparison": {
            "cv_mean_accuracy": 0.713445,
            "independent_accuracy": acc,
            "accuracy_delta": acc - 0.713445,
            "cv_mean_recall": 0.710203,
            "independent_recall": rec,
            "recall_delta": rec - 0.710203,
            "cv_mean_f1": 0.694398,
            "independent_f1": f1,
            "f1_delta": f1 - 0.694398,
            "cv_mean_roc_auc": 0.779817,
            "independent_roc_auc": roc_auc,
            "roc_auc_delta": roc_auc - 0.779817
        }
    }
    metrics_p = os.path.join(EVAL_DIR, "independent_test_metrics.json")
    with open(metrics_p, "w") as f:
        json.dump(metrics_dict, f, indent=2)
    print(f"9. Saved metrics JSON to: {metrics_p}")

    # 11. Save Confusion Matrix JSON
    cm_dict = {
        "confusion_matrix": {
            "tn": int(tn),
            "fp": int(fp),
            "fn": int(fn),
            "tp": int(tp)
        },
        "rates": {
            "tpr_recall": float(tp / (tp + fn)),
            "tnr_specificity": float(tn / (tn + fp)),
            "fpr": float(fp / (fp + tn)),
            "fnr": float(fn / (fn + tp)),
            "precision_ppv": float(tp / (tp + fp)),
            "npv": float(tn / (tn + fn)) if (tn + fn) > 0 else 0.0
        },
        "totals": {
            "actual_positive": int(tp + fn),
            "actual_negative": int(tn + fp),
            "predicted_positive": int(tp + fp),
            "predicted_negative": int(tn + fn),
            "total_samples": int(len(cust_df))
        }
    }
    cm_p = os.path.join(EVAL_DIR, "confusion_matrix.json")
    with open(cm_p, "w") as f:
        json.dump(cm_dict, f, indent=2)
    print(f"10. Saved confusion matrix JSON to: {cm_p}")

    print("\n" + "=" * 80)
    print("INDEPENDENT EVALUATION COMPLETED SUCCESSFULLY")
    print("=" * 80)
    return metrics_dict


if __name__ == "__main__":
    run_independent_evaluation()
