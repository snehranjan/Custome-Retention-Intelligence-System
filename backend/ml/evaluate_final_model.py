"""
Indian E-Commerce Customer Retention Intelligence System
Module: Phase 5 — Checkpoint 5: Final Model Evaluation on Untouched Test Set
Description: Loads the refitted final production pipeline (models/phase5/final_churn_pipeline.joblib),
             evaluates it on data/modeling/test.csv (N=1,050) using the locked decision threshold (0.46),
             computes full classification metrics, generates confusion matrix and diagnostic plots,
             and exports all test evaluation artifacts.

Author: BCA (AI & ML) Project Team
"""

import os
import sys
import json
import numpy as np
import pandas as pd
import joblib

# Set Matplotlib config directory to avoid permission warnings on Windows
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "..", ".."))
os.environ["MPLCONFIGDIR"] = os.path.join(PROJECT_ROOT, "reports", "figures", ".mplconfig")
os.makedirs(os.environ["MPLCONFIGDIR"], exist_ok=True)

import matplotlib.pyplot as plt
import seaborn as sns

from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    roc_auc_score, average_precision_score, balanced_accuracy_score,
    confusion_matrix, classification_report, roc_curve, precision_recall_curve,
    brier_score_loss
)
from sklearn.calibration import calibration_curve

# Paths
FINAL_PIPELINE_PATH = os.path.join(PROJECT_ROOT, "models", "phase5", "final_churn_pipeline.joblib")
TEST_PATH = os.path.join(PROJECT_ROOT, "data", "modeling", "test.csv")
FEATURE_COLUMNS_PATH = os.path.join(PROJECT_ROOT, "data", "modeling", "feature_columns.json")
MODEL_SELECTION_PATH = os.path.join(PROJECT_ROOT, "reports", "phase5", "model_selection.json")

REPORTS_DIR = os.path.join(PROJECT_ROOT, "reports", "phase5")
FIGURES_DIR = os.path.join(PROJECT_ROOT, "reports", "figures", "phase5")

TEST_METRICS_PATH = os.path.join(REPORTS_DIR, "final_test_metrics.json")
TEST_REPORT_PATH = os.path.join(REPORTS_DIR, "final_test_classification_report.txt")
CONFUSION_CSV_PATH = os.path.join(REPORTS_DIR, "final_confusion_matrix.csv")
TEST_PREDICTIONS_PATH = os.path.join(REPORTS_DIR, "final_test_predictions.csv")

LOCKED_THRESHOLD = 0.46


def evaluate_final_model():
    print("=" * 80)
    print("PHASE 5: CHECKPOINT 5 — FINAL MODEL EVALUATION ON UNTOUCHED TEST DATASET")
    print("=" * 80)

    os.makedirs(REPORTS_DIR, exist_ok=True)
    os.makedirs(FIGURES_DIR, exist_ok=True)

    # 1. Load Final Pipeline
    print(f"\n1. Loading final refitted pipeline from: {FINAL_PIPELINE_PATH}")
    assert os.path.exists(FINAL_PIPELINE_PATH), f"Missing final pipeline: {FINAL_PIPELINE_PATH}"
    pipeline = joblib.load(FINAL_PIPELINE_PATH)

    # 2. Inspect classes and positive class index
    classes = pipeline.classes_
    print(f"   Model classes: {classes}")
    assert 1 in classes, "Class 1 (churn) not found in model classes!"
    pos_idx = int(np.where(classes == 1)[0][0])
    print(f"   Positive class index for Churn (1): {pos_idx}")

    # 3. Load Feature Specification
    print(f"\n2. Loading Configuration B features from: {FEATURE_COLUMNS_PATH}")
    with open(FEATURE_COLUMNS_PATH, "r", encoding="utf-8") as f:
        f_spec = json.load(f)
    ordered_features = f_spec["configuration_b"]["features_ordered"]
    assert len(ordered_features) == 37, f"Expected 37 features, got {len(ordered_features)}"
    print(f"   Verified {len(ordered_features)} Configuration B predictive features.")

    # 4. Load Untouched Test Dataset
    print(f"\n3. Loading untouched test dataset from: {TEST_PATH}")
    assert os.path.exists(TEST_PATH), f"Missing test.csv: {TEST_PATH}"
    df_test = pd.read_csv(TEST_PATH)
    n_test = len(df_test)
    print(f"   Test records loaded: {n_test} (expected 1,050)")
    assert n_test == 1050, f"Expected 1,050 test records, got {n_test}"

    # Extract X, y, and identifier
    customer_ids = df_test["customer_id"].values
    y_test = df_test["churn"].values
    X_test = df_test[ordered_features]

    test_churners = int(np.sum(y_test == 1))
    test_retained = int(np.sum(y_test == 0))
    print(f"   Test class distribution: {test_churners} Churned ({test_churners/n_test*100:.2f}%), "
          f"{test_retained} Retained ({test_retained/n_test*100:.2f}%)")

    # 5. Predict Probabilities & Apply Fixed Decision Threshold (0.46)
    print(f"\n4. Generating test predictions using locked decision threshold: t = {LOCKED_THRESHOLD}")
    y_prob = pipeline.predict_proba(X_test)[:, pos_idx]
    y_pred = (y_prob >= LOCKED_THRESHOLD).astype(int)

    # 6. Compute Comprehensive Classification Metrics
    acc = accuracy_score(y_test, y_pred)
    prec = precision_score(y_test, y_pred, zero_division=0)
    rec = recall_score(y_test, y_pred, zero_division=0)
    f1 = f1_score(y_test, y_pred, zero_division=0)
    roc_auc = roc_auc_score(y_test, y_prob)
    avg_prec = average_precision_score(y_test, y_prob)
    bal_acc = balanced_accuracy_score(y_test, y_pred)
    brier = brier_score_loss(y_test, y_prob)

    # Confusion matrix
    cm = confusion_matrix(y_test, y_pred, labels=[0, 1])
    tn, fp, fn, tp = cm.ravel()
    assert (tn + fp + fn + tp) == n_test, f"Confusion matrix does not sum to {n_test}"

    spec = tn / (tn + fp) if (tn + fp) > 0 else 0.0
    fpr = fp / (tn + fp) if (tn + fp) > 0 else 0.0
    fnr = fn / (tp + fn) if (tp + fn) > 0 else 0.0

    print(f"\n   TEST RESULTS SUMMARY (@ t={LOCKED_THRESHOLD}):")
    print(f"   Accuracy            : {acc:.4f} ({acc*100:.2f}%)")
    print(f"   Precision           : {prec:.4f} ({prec*100:.2f}%)")
    print(f"   Recall (Sensitivity): {rec:.4f} ({rec*100:.2f}%)  [Target: >= 0.70]")
    print(f"   F1-Score            : {f1:.4f}")
    print(f"   ROC-AUC             : {roc_auc:.4f}")
    print(f"   Average Precision   : {avg_prec:.4f}")
    print(f"   Specificity         : {spec:.4f} ({spec*100:.2f}%)")
    print(f"   Balanced Accuracy   : {bal_acc:.4f} ({bal_acc*100:.2f}%)")
    print(f"   False Positive Rate : {fpr:.4f} ({fpr*100:.2f}%)")
    print(f"   False Negative Rate : {fnr:.4f} ({fnr*100:.2f}%)")
    print(f"   Diagnostic Brier Loss: {brier:.4f}")

    print(f"\n   CONFUSION MATRIX (N=1,050):")
    print(f"   True Positives  (TP) : {tp}  (Actual churners correctly identified)")
    print(f"   False Negatives (FN) : {fn}  (Actual churners missed)")
    print(f"   True Negatives  (TN) : {tn}  (Actual retained correctly identified)")
    print(f"   False Positives (FP) : {fp}  (Actual retained flagged as churn)")

    # 7. Classification Report
    clf_report = classification_report(
        y_test, y_pred,
        target_names=["Retained (Class 0)", "Churned (Class 1)"],
        digits=4
    )
    print("\n   CLASSIFICATION REPORT:")
    print(clf_report)

    with open(TEST_REPORT_PATH, "w", encoding="utf-8") as f:
        f.write("Indian E-Commerce Customer Retention Intelligence System\n")
        f.write("Phase 5: Checkpoint 5 — Final Test Set Classification Report\n")
        f.write(f"Model: Logistic Regression Configuration B (Tuned & Refitted)\n")
        f.write(f"Decision Threshold: {LOCKED_THRESHOLD}\n")
        f.write(f"Test Records: {n_test}\n")
        f.write("=" * 60 + "\n\n")
        f.write(clf_report)
        f.write("\n\nConfusion Matrix:\n")
        f.write(f"  TN={tn}, FP={fp}, FN={fn}, TP={tp}\n")
        f.write(f"  Specificity = {spec:.4f}, FPR = {fpr:.4f}, FNR = {fnr:.4f}\n")
        f.write(f"  ROC-AUC = {roc_auc:.4f}, Average Precision = {avg_prec:.4f}\n")
        f.write(f"  Diagnostic Brier Score = {brier:.4f}\n")
    print(f"   Saved classification report to: {TEST_REPORT_PATH}")

    # 8. Save Final Test Metrics JSON
    metrics_dict = {
        "metadata": {
            "title": "Phase 5 Checkpoint 5 Final Test Set Evaluation Metrics",
            "model_id": "logistic_regression_config_b_tuned_refitted",
            "algorithm": "Logistic Regression",
            "feature_configuration": "B",
            "feature_count": len(ordered_features),
            "refit_training_records": 5950,
            "test_records": n_test,
            "decision_threshold": LOCKED_THRESHOLD
        },
        "test_metrics": {
            "accuracy": round(float(acc), 4),
            "precision": round(float(prec), 4),
            "recall": round(float(rec), 4),
            "f1_score": round(float(f1), 4),
            "roc_auc": round(float(roc_auc), 4),
            "average_precision": round(float(avg_prec), 4),
            "specificity": round(float(spec), 4),
            "balanced_accuracy": round(float(bal_acc), 4),
            "false_positive_rate": round(float(fpr), 4),
            "false_negative_rate": round(float(fnr), 4),
            "brier_score_loss": round(float(brier), 4)
        },
        "confusion_matrix": {
            "true_positives": int(tp),
            "false_positives": int(fp),
            "true_negatives": int(tn),
            "false_negatives": int(fn),
            "total": int(n_test)
        },
        "recall_constraint_satisfied": bool(rec >= 0.70)
    }

    with open(TEST_METRICS_PATH, "w", encoding="utf-8") as f:
        json.dump(metrics_dict, f, indent=2)
    print(f"   Saved test metrics JSON to: {TEST_METRICS_PATH}")

    # 9. Save Confusion Matrix CSV
    df_cm = pd.DataFrame({
        "actual_class": ["Retained (0)", "Retained (0)", "Churned (1)", "Churned (1)"],
        "predicted_class": ["Retained (0)", "Churned (1)", "Retained (0)", "Churned (1)"],
        "metric_label": ["True Negative (TN)", "False Positive (FP)", "False Negative (FN)", "True Positive (TP)"],
        "count": [tn, fp, fn, tp],
        "percentage_of_total": [
            round(tn / n_test * 100, 2),
            round(fp / n_test * 100, 2),
            round(fn / n_test * 100, 2),
            round(tp / n_test * 100, 2)
        ]
    })
    df_cm.to_csv(CONFUSION_CSV_PATH, index=False)
    print(f"   Saved confusion matrix CSV to: {CONFUSION_CSV_PATH}")

    # 10. Save Test Predictions CSV
    df_preds = pd.DataFrame({
        "customer_id": customer_ids,
        "actual_churn": y_test,
        "predicted_probability": np.round(y_prob, 4),
        "predicted_churn": y_pred,
        "decision_threshold": LOCKED_THRESHOLD
    })
    df_preds.to_csv(TEST_PREDICTIONS_PATH, index=False)
    print(f"   Saved test predictions CSV ({len(df_preds)} rows) to: {TEST_PREDICTIONS_PATH}")

    # 11. Generate Visualizations
    print("\n5. Generating test performance visualizations...")

    # A. Confusion Matrix Plot
    plt.figure(figsize=(7, 6))
    cm_display = np.array([[tn, fp], [fn, tp]])
    sns.heatmap(
        cm_display, annot=True, fmt="d", cmap="Blues", cbar=False,
        xticklabels=["Predicted Retained (0)", "Predicted Churned (1)"],
        yticklabels=["Actual Retained (0)", "Actual Churned (1)"],
        annot_kws={"size": 14, "weight": "bold"}
    )
    plt.title(f"Final Model Confusion Matrix on Test Set (N=1,050)\nDecision Threshold t = {LOCKED_THRESHOLD}", fontsize=13, pad=15)
    plt.xlabel("Predicted Label", fontsize=11, labelpad=10)
    plt.ylabel("Actual True Label", fontsize=11, labelpad=10)
    plt.tight_layout()
    cm_fig_path = os.path.join(FIGURES_DIR, "final_confusion_matrix.png")
    plt.savefig(cm_fig_path, dpi=300)
    plt.close()
    print(f"   [Plot 1/4] Saved Confusion Matrix heatmap to: {cm_fig_path}")

    # B. ROC Curve
    fpr_curve, tpr_curve, _ = roc_curve(y_test, y_prob)
    plt.figure(figsize=(7, 6))
    plt.plot(fpr_curve, tpr_curve, color="#1f77b4", lw=2.5, label=f"ROC Curve (AUC = {roc_auc:.4f})")
    plt.plot([0, 1], [0, 1], color="gray", lw=1.5, linestyle="--", label="Random Chance (AUC = 0.5000)")
    # Plot operational point at threshold 0.46
    plt.plot(fpr, rec, marker="o", markersize=8, color="#d62728", label=f"Operating Point (t={LOCKED_THRESHOLD}: FPR={fpr:.3f}, Rec={rec:.3f})")
    plt.xlim([0.0, 1.0])
    plt.ylim([0.0, 1.05])
    plt.xlabel("False Positive Rate (1 - Specificity)", fontsize=11)
    plt.ylabel("True Positive Rate (Recall / Sensitivity)", fontsize=11)
    plt.title("Receiver Operating Characteristic (ROC) Curve\nFinal Model on Untouched Test Set", fontsize=13, pad=15)
    plt.legend(loc="lower right", fontsize=10)
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    roc_fig_path = os.path.join(FIGURES_DIR, "final_roc_curve.png")
    plt.savefig(roc_fig_path, dpi=300)
    plt.close()
    print(f"   [Plot 2/4] Saved ROC curve to: {roc_fig_path}")

    # C. Precision-Recall Curve
    pr_curve_precision, pr_curve_recall, _ = precision_recall_curve(y_test, y_prob)
    no_skill = test_churners / n_test
    plt.figure(figsize=(7, 6))
    plt.plot(pr_curve_recall, pr_curve_precision, color="#2ca02c", lw=2.5, label=f"PR Curve (Average Precision = {avg_prec:.4f})")
    plt.plot([0, 1], [no_skill, no_skill], color="gray", lw=1.5, linestyle="--", label=f"No Skill Baseline ({no_skill:.4f})")
    plt.plot(rec, prec, marker="o", markersize=8, color="#d62728", label=f"Operating Point (t={LOCKED_THRESHOLD}: Rec={rec:.3f}, Prec={prec:.3f})")
    plt.xlim([0.0, 1.0])
    plt.ylim([0.0, 1.05])
    plt.xlabel("Recall (Sensitivity)", fontsize=11)
    plt.ylabel("Precision (Positive Predictive Value)", fontsize=11)
    plt.title("Precision-Recall Curve\nFinal Model on Untouched Test Set", fontsize=13, pad=15)
    plt.legend(loc="upper right", fontsize=10)
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    pr_fig_path = os.path.join(FIGURES_DIR, "final_precision_recall_curve.png")
    plt.savefig(pr_fig_path, dpi=300)
    plt.close()
    print(f"   [Plot 3/4] Saved Precision-Recall curve to: {pr_fig_path}")

    # D. Metric Comparison Bar Chart
    metric_names = ["Accuracy", "Precision", "Recall", "F1-Score", "ROC-AUC", "Avg Precision", "Specificity", "Balanced Acc"]
    metric_values = [acc, prec, rec, f1, roc_auc, avg_prec, spec, bal_acc]
    colors = ["#4C72B0", "#55A868", "#C44E52", "#8172B2", "#CCB974", "#64B5CD", "#8C8C8C", "#E377C2"]

    plt.figure(figsize=(9, 5))
    bars = plt.bar(metric_names, metric_values, color=colors, width=0.6, edgecolor="black", linewidth=0.8)
    plt.ylim([0.0, 1.05])
    plt.axhline(0.70, color="red", linestyle="--", lw=1.2, label="Recall Constraint Target (0.70)")
    plt.ylabel("Score", fontsize=11)
    plt.title(f"Final Model Test Performance Metrics Summary (Threshold t = {LOCKED_THRESHOLD})", fontsize=13, pad=15)
    plt.xticks(rotation=20, ha="right", fontsize=10)

    for bar, val in zip(bars, metric_values):
        plt.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.02, f"{val:.4f}", ha="center", va="bottom", fontsize=9, weight="bold")

    plt.legend(loc="upper right", fontsize=10)
    plt.grid(axis="y", alpha=0.3)
    plt.tight_layout()
    metric_fig_path = os.path.join(FIGURES_DIR, "final_metric_comparison.png")
    plt.savefig(metric_fig_path, dpi=300)
    plt.close()
    print(f"   [Plot 4/4] Saved Metric Comparison bar chart to: {metric_fig_path}")

    print("\n" + "=" * 80)
    print("FINAL TEST EVALUATION COMPLETED SUCCESSFULLY!")
    print("=" * 80)
    return metrics_dict


if __name__ == "__main__":
    evaluate_final_model()
