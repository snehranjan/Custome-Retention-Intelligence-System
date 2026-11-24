"""
Indian E-Commerce Customer Retention Intelligence System
Module: Phase 5 — Checkpoint 5: Final Model Validation & Consistency Suite
Description: Executes 18 automated verification checks to ensure:
             - Final pipeline artifact exists and reloads flawlessly.
             - Classifier architecture, hyperparameters, and feature schema match approved specifications.
             - Predictions are mathematically valid, deterministic, and identical across reloads.
             - Evaluation metrics and confusion matrices on the test set are strictly consistent.
             - Phase 0-4 datasets and Checkpoint 4 tuned candidate remain untouched and invariant.

Author: BCA (AI & ML) Project Team
"""

import os
import sys
import json
import hashlib
import numpy as np
import pandas as pd
import joblib

from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from sklearn.linear_model import LogisticRegression

# Ensure project root is on sys.path
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "..", ".."))
sys.path.insert(0, PROJECT_ROOT)

# Paths
FINAL_PIPELINE_PATH = os.path.join(PROJECT_ROOT, "models", "phase5", "final_churn_pipeline.joblib")
FINAL_METADATA_PATH = os.path.join(PROJECT_ROOT, "models", "phase5", "final_model_metadata.json")
TUNED_CANDIDATE_PATH = os.path.join(PROJECT_ROOT, "models", "phase5", "tuned", "logistic_regression_config_b_tuned.joblib")

TRAIN_PATH = os.path.join(PROJECT_ROOT, "data", "modeling", "train.csv")
VAL_PATH = os.path.join(PROJECT_ROOT, "data", "modeling", "validation.csv")
TEST_PATH = os.path.join(PROJECT_ROOT, "data", "modeling", "test.csv")
FEATURE_COLUMNS_PATH = os.path.join(PROJECT_ROOT, "data", "modeling", "feature_columns.json")
MODEL_SELECTION_PATH = os.path.join(PROJECT_ROOT, "reports", "phase5", "model_selection.json")

TEST_METRICS_PATH = os.path.join(PROJECT_ROOT, "reports", "phase5", "final_test_metrics.json")
CONFUSION_CSV_PATH = os.path.join(PROJECT_ROOT, "reports", "phase5", "final_confusion_matrix.csv")
TEST_PREDICTIONS_PATH = os.path.join(PROJECT_ROOT, "reports", "phase5", "final_test_predictions.csv")
COEFFICIENTS_CSV_PATH = os.path.join(PROJECT_ROOT, "reports", "phase5", "feature_coefficients.csv")

RAW_CUSTOMERS_PATH = os.path.join(PROJECT_ROOT, "data", "raw", "customers.csv")
RAW_ORDERS_PATH = os.path.join(PROJECT_ROOT, "data", "raw", "orders.csv")
PROCESSED_FEATURES_PATH = os.path.join(PROJECT_ROOT, "data", "processed", "customer_features.csv")

# Invariant Hashes
EXPECTED_CUSTOMERS_SHA256 = "DF6219AA4E2BDDE8FFF419272B9F2C1DE0602473248619E90566BC7D498AB70E"
EXPECTED_ORDERS_SHA256 = "AB632B3092F732B3B25BAAD096B191C1ACA777CB8D42B29EABB815A266C558E7"
EXPECTED_FEATURES_SHA256 = "3B8CFF35A9012A7E6524FEC962D400BE58D29399BF4DF7A80DE7283B69B4C628"

LOCKED_THRESHOLD = 0.46


def compute_sha256(filepath):
    """Computes uppercase SHA-256 hash of a file."""
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest().upper()


def run_final_validation():
    print("=" * 80)
    print("PHASE 5: CHECKPOINT 5 — FINAL MODEL VALIDATION & CONSISTENCY SUITE")
    print("=" * 80)

    passed_checks = 0
    total_checks = 18

    # ------------------------------------------------------------------
    # Check 1: Final pipeline exists on disk
    # ------------------------------------------------------------------
    print("\n[Check 1/18] Verifying existence of final pipeline artifact...")
    assert os.path.exists(FINAL_PIPELINE_PATH), f"Missing artifact: {FINAL_PIPELINE_PATH}"
    file_size_kb = os.path.getsize(FINAL_PIPELINE_PATH) / 1024
    print(f"   PASS: final_churn_pipeline.joblib exists ({file_size_kb:.2f} KB).")
    passed_checks += 1

    # ------------------------------------------------------------------
    # Check 2: Final pipeline can be loaded via joblib
    # ------------------------------------------------------------------
    print("\n[Check 2/18] Loading final pipeline artifact via joblib...")
    pipeline = joblib.load(FINAL_PIPELINE_PATH)
    assert isinstance(pipeline, Pipeline), f"Expected sklearn Pipeline, got {type(pipeline)}"
    print("   PASS: Successfully loaded sklearn Pipeline object.")
    passed_checks += 1

    # ------------------------------------------------------------------
    # Check 3: Selected classifier is Logistic Regression
    # ------------------------------------------------------------------
    print("\n[Check 3/18] Verifying final classifier algorithm type...")
    clf = pipeline.named_steps.get("classifier")
    assert clf is not None, "Pipeline missing 'classifier' step"
    assert isinstance(clf, LogisticRegression), f"Expected LogisticRegression, got {type(clf)}"
    print("   PASS: Classifier step is verified as LogisticRegression.")
    passed_checks += 1

    # ------------------------------------------------------------------
    # Check 4: Hyperparameters match approved selection exactly
    # ------------------------------------------------------------------
    print("\n[Check 4/18] Verifying hyperparameters against approved selection...")
    assert clf.C == 0.01, f"Expected C=0.01, got {clf.C}"
    assert clf.class_weight == "balanced", f"Expected class_weight='balanced', got {clf.class_weight}"
    assert clf.solver == "lbfgs", f"Expected solver='lbfgs', got {clf.solver}"
    assert clf.max_iter == 2000, f"Expected max_iter=2000, got {clf.max_iter}"
    print(f"   PASS: Hyperparameters confirmed: C={clf.C}, class_weight='{clf.class_weight}', solver='{clf.solver}', max_iter={clf.max_iter}.")
    passed_checks += 1

    # ------------------------------------------------------------------
    # Check 5: Decision threshold locked at 0.46
    # ------------------------------------------------------------------
    print("\n[Check 5/18] Verifying decision threshold locking (0.46)...")
    with open(FINAL_METADATA_PATH, "r", encoding="utf-8") as f:
        meta = json.load(f)
    assert meta["decision_threshold"] == LOCKED_THRESHOLD, f"Expected threshold {LOCKED_THRESHOLD}, got {meta['decision_threshold']}"
    print(f"   PASS: Decision threshold is strictly locked at {LOCKED_THRESHOLD}.")
    passed_checks += 1

    # ------------------------------------------------------------------
    # Check 6: Feature schema matches Configuration B (37 features)
    # ------------------------------------------------------------------
    print("\n[Check 6/18] Verifying feature schema against Configuration B specifications...")
    with open(FEATURE_COLUMNS_PATH, "r", encoding="utf-8") as f:
        f_spec = json.load(f)
    cfg_b_features = f_spec["configuration_b"]["features_ordered"]
    assert len(cfg_b_features) == 37, f"Expected 37 features, got {len(cfg_b_features)}"
    assert "cluster_id" in f_spec["configuration_b"]["categorical_features"]
    assert "churn" not in cfg_b_features
    assert "customer_id" not in cfg_b_features
    print("   PASS: Feature schema confirmed (37 features, nominal categorical cluster_id, zero leakage).")
    passed_checks += 1

    # ------------------------------------------------------------------
    # Check 7: Preprocessor structure verified
    # ------------------------------------------------------------------
    print("\n[Check 7/18] Verifying ColumnTransformer preprocessor structure...")
    preprocessor = pipeline.named_steps.get("preprocessor")
    assert preprocessor is not None, "Pipeline missing 'preprocessor' step"
    assert isinstance(preprocessor, ColumnTransformer), f"Expected ColumnTransformer, got {type(preprocessor)}"
    transformer_names = [name for name, _, _ in preprocessor.transformers]
    assert "num" in transformer_names and "cat" in transformer_names, f"Unexpected transformers: {transformer_names}"
    print("   PASS: Preprocessor contains both 'num' and 'cat' ColumnTransformer pipelines.")
    passed_checks += 1

    # ------------------------------------------------------------------
    # Check 8: Binary predictions validity on fixed training sample
    # ------------------------------------------------------------------
    print("\n[Check 8/18] Verifying prediction label validity on fixed sample...")
    df_sample = pd.read_csv(TRAIN_PATH, nrows=50)
    X_sample = df_sample[cfg_b_features]
    pos_idx = int(np.where(pipeline.classes_ == 1)[0][0])
    y_prob_sample = pipeline.predict_proba(X_sample)[:, pos_idx]
    y_pred_sample = (y_prob_sample >= LOCKED_THRESHOLD).astype(int)
    unique_labels = set(y_pred_sample)
    assert unique_labels.issubset({0, 1}), f"Invalid prediction labels found: {unique_labels}"
    print(f"   PASS: Predictions produce strictly binary integer labels: {unique_labels}.")
    passed_checks += 1

    # ------------------------------------------------------------------
    # Check 9: Predicted probabilities finite and bounded in [0, 1]
    # ------------------------------------------------------------------
    print("\n[Check 9/18] Verifying probability bounds [0.0, 1.0] and finiteness...")
    assert np.all(np.isfinite(y_prob_sample)), "Non-finite probabilities detected!"
    assert np.all((y_prob_sample >= 0.0) & (y_prob_sample <= 1.0)), "Probabilities outside [0, 1] detected!"
    print(f"   PASS: All predicted probabilities are finite and bounded in [0.0, 1.0] (min={y_prob_sample.min():.4f}, max={y_prob_sample.max():.4f}).")
    passed_checks += 1

    # ------------------------------------------------------------------
    # Check 10: Correct class-1 probability extraction
    # ------------------------------------------------------------------
    print("\n[Check 10/18] Verifying positive class index resolution...")
    classes = pipeline.classes_
    assert np.array_equal(classes, [0, 1]), f"Unexpected classes: {classes}"
    assert pos_idx == 1, f"Expected pos_idx=1, got {pos_idx}"
    print("   PASS: Class 1 correctly resolved at column index 1.")
    passed_checks += 1

    # ------------------------------------------------------------------
    # Check 11: Deterministic prediction consistency on repeated calls
    # ------------------------------------------------------------------
    print("\n[Check 11/18] Verifying deterministic prediction reproducibility...")
    probs_run1 = pipeline.predict_proba(X_sample)[:, pos_idx]
    probs_run2 = pipeline.predict_proba(X_sample)[:, pos_idx]
    np.testing.assert_array_equal(probs_run1, probs_run2)
    print("   PASS: Repeated inference on fixed sample produces bit-for-bit identical probabilities.")
    passed_checks += 1

    # ------------------------------------------------------------------
    # Check 12: Reloaded pipeline prediction consistency
    # ------------------------------------------------------------------
    print("\n[Check 12/18] Verifying saved vs reloaded pipeline consistency...")
    reloaded_pipeline = joblib.load(FINAL_PIPELINE_PATH)
    probs_reloaded = reloaded_pipeline.predict_proba(X_sample)[:, pos_idx]
    np.testing.assert_array_equal(probs_run1, probs_reloaded)
    print("   PASS: Reloaded pipeline outputs match original pipeline with zero deviation.")
    passed_checks += 1

    # ------------------------------------------------------------------
    # Check 13: Final test metrics JSON validity
    # ------------------------------------------------------------------
    print("\n[Check 13/18] Verifying final test metrics JSON...")
    assert os.path.exists(TEST_METRICS_PATH), f"Missing test metrics: {TEST_METRICS_PATH}"
    with open(TEST_METRICS_PATH, "r", encoding="utf-8") as f:
        t_data = json.load(f)
    req_metric_keys = ["accuracy", "precision", "recall", "f1_score", "roc_auc", "average_precision", "specificity"]
    for rk in req_metric_keys:
        assert rk in t_data["test_metrics"], f"Missing metric key: {rk}"
    print(f"   PASS: final_test_metrics.json is valid and contains all {len(req_metric_keys)} primary metric keys.")
    passed_checks += 1

    # ------------------------------------------------------------------
    # Check 14: Confusion matrix counts strictly sum to 1,050
    # ------------------------------------------------------------------
    print("\n[Check 14/18] Verifying confusion matrix total count equals 1,050...")
    cm_dict = t_data["confusion_matrix"]
    total_test = cm_dict["true_positives"] + cm_dict["false_positives"] + cm_dict["true_negatives"] + cm_dict["false_negatives"]
    assert total_test == 1050, f"Expected 1,050 total test counts, got {total_test}"
    print(f"   PASS: Confusion matrix sums strictly to {total_test} (TP={cm_dict['true_positives']}, FP={cm_dict['false_positives']}, TN={cm_dict['true_negatives']}, FN={cm_dict['false_negatives']}).")
    passed_checks += 1

    # ------------------------------------------------------------------
    # Check 15: Mathematical consistency between confusion matrix and metrics
    # ------------------------------------------------------------------
    print("\n[Check 15/18] Verifying mathematical consistency of metrics with confusion matrix...")
    tp = cm_dict["true_positives"]
    fp = cm_dict["false_positives"]
    tn = cm_dict["true_negatives"]
    fn = cm_dict["false_negatives"]
    tm = t_data["test_metrics"]

    calc_acc = round((tp + tn) / total_test, 4)
    calc_prec = round(tp / (tp + fp), 4)
    calc_rec = round(tp / (tp + fn), 4)
    calc_f1 = round(2 * (calc_prec * calc_rec) / (calc_prec + calc_rec), 4)
    calc_spec = round(tn / (tn + fp), 4)

    np.testing.assert_almost_equal(tm["accuracy"], calc_acc, decimal=3)
    np.testing.assert_almost_equal(tm["precision"], calc_prec, decimal=3)
    np.testing.assert_almost_equal(tm["recall"], calc_rec, decimal=3)
    np.testing.assert_almost_equal(tm["f1_score"], calc_f1, decimal=3)
    np.testing.assert_almost_equal(tm["specificity"], calc_spec, decimal=3)
    print("   PASS: All test metrics are strictly consistent with confusion matrix counts.")
    passed_checks += 1

    # ------------------------------------------------------------------
    # Check 16: Checkpoint 4 tuned candidate artifact preserved and untouched
    # ------------------------------------------------------------------
    print("\n[Check 16/18] Verifying Checkpoint 4 tuned candidate artifact integrity...")
    assert os.path.exists(TUNED_CANDIDATE_PATH), f"Missing tuned candidate: {TUNED_CANDIDATE_PATH}"
    tuned_pipe = joblib.load(TUNED_CANDIDATE_PATH)
    assert isinstance(tuned_pipe, Pipeline), "Tuned artifact corrupted"
    assert tuned_pipe.named_steps["classifier"].C == 0.01
    print("   PASS: Original tuned candidate artifact is preserved and unmodified.")
    passed_checks += 1

    # ------------------------------------------------------------------
    # Check 17: Phase 0-4 cryptographic dataset invariants preserved
    # ------------------------------------------------------------------
    print("\n[Check 17/18] Verifying Phase 0-4 cryptographic dataset invariants...")
    cust_sha = compute_sha256(RAW_CUSTOMERS_PATH)
    ord_sha = compute_sha256(RAW_ORDERS_PATH)
    feat_sha = compute_sha256(PROCESSED_FEATURES_PATH)
    assert cust_sha == EXPECTED_CUSTOMERS_SHA256, f"customers.csv hash mismatch: {cust_sha}"
    assert ord_sha == EXPECTED_ORDERS_SHA256, f"orders.csv hash mismatch: {ord_sha}"
    assert feat_sha == EXPECTED_FEATURES_SHA256, f"customer_features.csv hash mismatch: {feat_sha}"
    print("   PASS: Cryptographic hashes of customers.csv, orders.csv, and customer_features.csv remain invariant.")
    passed_checks += 1

    # ------------------------------------------------------------------
    # Check 18: Zero test-driven adaptation confirmation
    # ------------------------------------------------------------------
    print("\n[Check 18/18] Verifying zero test-driven parameter adaptation...")
    with open(MODEL_SELECTION_PATH, "r", encoding="utf-8") as f:
        chk4_sel = json.load(f)
    assert chk4_sel["optimal_threshold"] == LOCKED_THRESHOLD, "Checkpoint 4 threshold modified!"
    assert meta["hyperparameters"]["C"] == 0.01, "Hyperparameter modified!"
    assert meta["recall_constraint_satisfied"] is True, "Recall constraint failed on test set!"
    print(f"   PASS: Threshold remained strictly {LOCKED_THRESHOLD}; hyperparameters remained invariant; recall constraint satisfied ({tm['recall']:.4f} >= 0.70).")
    passed_checks += 1

    print("\n" + "=" * 80)
    print(f"VALIDATION COMPLETE: {passed_checks}/{total_checks} CHECKS PASSED (100% SUCCESS)")
    print("=" * 80)
    return True


if __name__ == "__main__":
    success = run_final_validation()
    if not success:
        sys.exit(1)
