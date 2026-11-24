"""
Indian E-Commerce Customer Retention Intelligence System
Module: Phase 5 — Checkpoint 4: Baseline Validation Dataset Evaluation
Description: Evaluates the eight baseline trained pipeline artifacts on the locked
             validation dataset (N=1,050) at the default classification threshold
             of 0.50. Computes full confusion matrices, discrimination metrics,
             and calibration scores. Saves baseline_validation_results.csv.

Author: BCA (AI & ML) Project Team
"""

import os
import sys
import json
import pandas as pd
import numpy as np
import joblib

from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    roc_auc_score, average_precision_score, balanced_accuracy_score,
    confusion_matrix
)

# Ensure backend/ml is on sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Path configuration
VAL_PATH = os.path.join("data", "modeling", "validation.csv")
FEATURE_COLUMNS_PATH = os.path.join("data", "modeling", "feature_columns.json")
SPLIT_MANIFEST_PATH = os.path.join("data", "modeling", "split_manifest.json")
MODELS_DIR = os.path.join("models", "phase5")
REPORTS_DIR = os.path.join("reports", "phase5")
OUTPUT_BASELINE_CSV = os.path.join(REPORTS_DIR, "baseline_validation_results.csv")

BASELINE_MODELS = [
    {
        "model_key": "logistic_regression",
        "model_name": "Logistic Regression",
        "config_key": "config_a",
        "config_name": "Configuration A (Baseline 36 Features)",
        "artifact": "logistic_regression_config_a.joblib"
    },
    {
        "model_key": "logistic_regression",
        "model_name": "Logistic Regression",
        "config_key": "config_b",
        "config_name": "Configuration B (36 Features + RFM cluster_id)",
        "artifact": "logistic_regression_config_b.joblib"
    },
    {
        "model_key": "decision_tree",
        "model_name": "Decision Tree",
        "config_key": "config_a",
        "config_name": "Configuration A (Baseline 36 Features)",
        "artifact": "decision_tree_config_a.joblib"
    },
    {
        "model_key": "decision_tree",
        "model_name": "Decision Tree",
        "config_key": "config_b",
        "config_name": "Configuration B (36 Features + RFM cluster_id)",
        "artifact": "decision_tree_config_b.joblib"
    },
    {
        "model_key": "random_forest",
        "model_name": "Random Forest",
        "config_key": "config_a",
        "config_name": "Configuration A (Baseline 36 Features)",
        "artifact": "random_forest_config_a.joblib"
    },
    {
        "model_key": "random_forest",
        "model_name": "Random Forest",
        "config_key": "config_b",
        "config_name": "Configuration B (36 Features + RFM cluster_id)",
        "artifact": "random_forest_config_b.joblib"
    },
    {
        "model_key": "gradient_boosting",
        "model_name": "Gradient Boosting",
        "config_key": "config_a",
        "config_name": "Configuration A (Baseline 36 Features)",
        "artifact": "gradient_boosting_config_a.joblib"
    },
    {
        "model_key": "gradient_boosting",
        "model_name": "Gradient Boosting",
        "config_key": "config_b",
        "config_name": "Configuration B (36 Features + RFM cluster_id)",
        "artifact": "gradient_boosting_config_b.joblib"
    }
]


def evaluate_baseline_validation():
    print("=" * 80)
    print("PHASE 5: CHECKPOINT 4 — BASELINE VALIDATION DATASET EVALUATION (Threshold = 0.50)")
    print("=" * 80)

    # 1. Load validation dataset
    print(f"\n1. Loading validation dataset from: {VAL_PATH}")
    df_val = pd.read_csv(VAL_PATH)
    n_val = len(df_val)
    assert n_val == 1050, f"Expected 1,050 validation records, got {n_val}"
    print(f"   -> Validation records: {n_val:,} rows, {len(df_val.columns)} columns")

    y_val = df_val["churn"].values
    n_retained = int((y_val == 0).sum())
    n_churned = int((y_val == 1).sum())
    print(f"   -> Class 0 (Retained): {n_retained:,} ({n_retained/n_val*100:.2f}%)")
    print(f"   -> Class 1 (Churned):  {n_churned:,} ({n_churned/n_val*100:.2f}%)")

    # 2. Load feature specifications
    print(f"\n2. Loading feature allowlist specifications from: {FEATURE_COLUMNS_PATH}")
    with open(FEATURE_COLUMNS_PATH, "r", encoding="utf-8") as f:
        fmeta = json.load(f)

    cfg_a_cols = fmeta["configuration_a"]["features_ordered"]
    cfg_b_cols = fmeta["configuration_b"]["features_ordered"]

    results = []

    print(f"\n3. Evaluating all 8 baseline pipelines on validation.csv...")
    print("-" * 80)

    for item in BASELINE_MODELS:
        artifact_path = os.path.join(MODELS_DIR, item["artifact"])
        assert os.path.exists(artifact_path), f"Artifact missing: {artifact_path}"

        pipeline = joblib.load(artifact_path)
        clf = pipeline.named_steps["classifier"]
        classes = list(clf.classes_)
        assert 1 in classes, "Positive class 1 not in estimator classes_"
        pos_idx = classes.index(1)

        # Select appropriate features
        feature_cols = cfg_b_cols if item["config_key"] == "config_b" else cfg_a_cols
        X_val = df_val[feature_cols]

        # Generate positive class probability scores
        y_proba = pipeline.predict_proba(X_val)
        y_scores = y_proba[:, pos_idx]

        # Default classification at threshold = 0.50
        threshold = 0.50
        y_pred = (y_scores >= threshold).astype(int)

        # Calculate metrics
        acc = accuracy_score(y_val, y_pred)
        prec = precision_score(y_val, y_pred, zero_division=0)
        rec = recall_score(y_val, y_pred, zero_division=0)
        f1 = f1_score(y_val, y_pred, zero_division=0)
        roc_auc = roc_auc_score(y_val, y_scores)
        pr_auc = average_precision_score(y_val, y_scores)
        bal_acc = balanced_accuracy_score(y_val, y_pred)

        # Confusion matrix: TN, FP, FN, TP
        tn, fp, fn, tp = confusion_matrix(y_val, y_pred).ravel()
        specificity = tn / (tn + fp) if (tn + fp) > 0 else 0.0

        print(f"[{item['model_name']} - {item['config_key'].upper()}]")
        print(f"   Accuracy: {acc:.4f} | Prec: {prec:.4f} | Rec: {rec:.4f} | F1: {f1:.4f} | ROC-AUC: {roc_auc:.4f} | PR-AUC: {pr_auc:.4f}")
        print(f"   Confusion Matrix: TP={tp}, FP={fp}, TN={tn}, FN={fn} | Specificity: {specificity:.4f}")

        results.append({
            "model_key": item["model_key"],
            "model_name": item["model_name"],
            "config_key": item["config_key"],
            "config_name": item["config_name"],
            "feature_count": len(feature_cols),
            "threshold": threshold,
            "accuracy": round(acc, 4),
            "precision": round(prec, 4),
            "recall": round(rec, 4),
            "f1_score": round(f1, 4),
            "roc_auc": round(roc_auc, 4),
            "average_precision": round(pr_auc, 4),
            "balanced_accuracy": round(bal_acc, 4),
            "specificity": round(specificity, 4),
            "true_positives": int(tp),
            "false_positives": int(fp),
            "true_negatives": int(tn),
            "false_negatives": int(fn)
        })

    # Save to CSV
    os.makedirs(REPORTS_DIR, exist_ok=True)
    df_results = pd.DataFrame(results)
    df_results.to_csv(OUTPUT_BASELINE_CSV, index=False)
    print(f"\n4. Saved baseline validation results to: {OUTPUT_BASELINE_CSV}")
    print("=" * 80)
    print("BASELINE VALIDATION EVALUATION COMPLETED SUCCESSFULLY!")
    print("=" * 80)
    return df_results


if __name__ == "__main__":
    evaluate_baseline_validation()
