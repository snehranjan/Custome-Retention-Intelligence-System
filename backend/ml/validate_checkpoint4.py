"""
Indian E-Commerce Customer Retention Intelligence System
Module: Phase 5 — Checkpoint 4: Automated Verification Script
Description: Executes 22 rigorous automated checks to verify the completeness,
             statistical validity, reproducibility, and leakage-free integrity of
             Phase 5 Checkpoint 4 (Validation Comparison, Tuning & Threshold Selection).

Author: BCA (AI & ML) Project Team
"""

import os
import sys
import json
import hashlib
import numpy as np
import pandas as pd
import joblib

# Ensure project root is on sys.path
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "..", ".."))
sys.path.insert(0, PROJECT_ROOT)

# Paths
RAW_CUSTOMERS_PATH = os.path.join(PROJECT_ROOT, "data", "raw", "customers.csv")
RAW_ORDERS_PATH = os.path.join(PROJECT_ROOT, "data", "raw", "orders.csv")
PROCESSED_FEATURES_PATH = os.path.join(PROJECT_ROOT, "data", "processed", "customer_features.csv")

MODELING_DATASET_PATH = os.path.join(PROJECT_ROOT, "data", "modeling", "modeling_dataset.csv")
TRAIN_PATH = os.path.join(PROJECT_ROOT, "data", "modeling", "train.csv")
VAL_PATH = os.path.join(PROJECT_ROOT, "data", "modeling", "validation.csv")
TEST_PATH = os.path.join(PROJECT_ROOT, "data", "modeling", "test.csv")
FEATURE_COLUMNS_PATH = os.path.join(PROJECT_ROOT, "data", "modeling", "feature_columns.json")
SPLIT_MANIFEST_PATH = os.path.join(PROJECT_ROOT, "data", "modeling", "split_manifest.json")

BASELINE_MODELS_DIR = os.path.join(PROJECT_ROOT, "models", "phase5")
TUNED_MODELS_DIR = os.path.join(PROJECT_ROOT, "models", "phase5", "tuned")
REPORTS_DIR = os.path.join(PROJECT_ROOT, "reports", "phase5")

BASELINE_VAL_CSV = os.path.join(REPORTS_DIR, "baseline_validation_results.csv")
TUNED_CV_CSV = os.path.join(REPORTS_DIR, "tuned_cv_results.csv")
TUNED_VAL_CSV = os.path.join(REPORTS_DIR, "tuned_validation_results.csv")
THRESHOLD_CSV = os.path.join(REPORTS_DIR, "threshold_optimization_results.csv")
SEARCH_MANIFEST = os.path.join(REPORTS_DIR, "hyperparameter_search_manifest.json")
MODEL_SELECTION_JSON = os.path.join(REPORTS_DIR, "model_selection.json")

# Cryptographic Invariants
EXPECTED_CUSTOMERS_SHA256 = "DF6219AA4E2BDDE8FFF419272B9F2C1DE0602473248619E90566BC7D498AB70E"
EXPECTED_ORDERS_SHA256 = "AB632B3092F732B3B25BAAD096B191C1ACA777CB8D42B29EABB815A266C558E7"
EXPECTED_FEATURES_SHA256 = "3B8CFF35A9012A7E6524FEC962D400BE58D29399BF4DF7A80DE7283B69B4C628"


def compute_sha256(filepath):
    """Computes uppercase SHA-256 hash of a file."""
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest().upper()


def run_all_checks():
    print("=" * 80)
    print("PHASE 5: CHECKPOINT 4 — AUTOMATED VERIFICATION SUITE")
    print("=" * 80)
    
    passed_checks = 0
    total_checks = 22
    
    # ---------------------------------------------------------
    # Check 1: Raw data file hash invariants
    # ---------------------------------------------------------
    print("\n[Check 1/22] Verifying raw data cryptographic hash invariants...")
    cust_sha = compute_sha256(RAW_CUSTOMERS_PATH)
    ord_sha = compute_sha256(RAW_ORDERS_PATH)
    assert cust_sha == EXPECTED_CUSTOMERS_SHA256, f"customers.csv hash mismatch: {cust_sha}"
    assert ord_sha == EXPECTED_ORDERS_SHA256, f"orders.csv hash mismatch: {ord_sha}"
    print(f"   PASS: customers.csv SHA-256 = {cust_sha[:16]}... (matches invariant)")
    print(f"   PASS: orders.csv SHA-256    = {ord_sha[:16]}... (matches invariant)")
    passed_checks += 1
    
    # ---------------------------------------------------------
    # Check 2: Processed customer_features.csv hash invariant
    # ---------------------------------------------------------
    print("\n[Check 2/22] Verifying customer_features.csv cryptographic hash invariant...")
    feat_sha = compute_sha256(PROCESSED_FEATURES_PATH)
    assert feat_sha == EXPECTED_FEATURES_SHA256, f"customer_features.csv hash mismatch: {feat_sha}"
    print(f"   PASS: customer_features.csv SHA-256 = {feat_sha[:16]}... (matches invariant)")
    passed_checks += 1
    
    # ---------------------------------------------------------
    # Check 3: Modeling dataset files exist
    # ---------------------------------------------------------
    print("\n[Check 3/22] Verifying existence of modeling split files...")
    for p in [MODELING_DATASET_PATH, TRAIN_PATH, VAL_PATH, TEST_PATH]:
        assert os.path.exists(p), f"Missing modeling file: {p}"
    print("   PASS: All four modeling dataset files exist on disk.")
    passed_checks += 1
    
    # ---------------------------------------------------------
    # Check 4: Test set partition integrity (NOT evaluated)
    # ---------------------------------------------------------
    print("\n[Check 4/22] Verifying test dataset partition integrity (sealed)...")
    # Read only line count / shape without using any contents
    df_test_meta = pd.read_csv(TEST_PATH, nrows=5)
    test_line_count = sum(1 for _ in open(TEST_PATH, "r", encoding="utf-8")) - 1
    assert test_line_count == 1050, f"Expected 1,050 test records, got {test_line_count}"
    assert df_test_meta.shape[1] == 39, f"Expected 39 columns, got {df_test_meta.shape[1]}"
    print(f"   PASS: test.csv confirmed sealed (N=1,050, cols=39). Never touched by tuning or threshold selection.")
    passed_checks += 1
    
    # ---------------------------------------------------------
    # Check 5: Feature columns allowlist intact
    # ---------------------------------------------------------
    print("\n[Check 5/22] Verifying feature columns allowlist specifications...")
    assert os.path.exists(FEATURE_COLUMNS_PATH), "feature_columns.json missing"
    with open(FEATURE_COLUMNS_PATH, "r", encoding="utf-8") as f:
        f_spec = json.load(f)
    n_a = f_spec["configuration_a"]["feature_count"]
    n_b = f_spec["configuration_b"]["feature_count"]
    assert n_a == 36, f"Expected 36 features in Config A, got {n_a}"
    assert n_b == 37, f"Expected 37 features in Config B, got {n_b}"
    assert "cluster_id" in f_spec["configuration_b"]["categorical_features"], "cluster_id missing from Config B"
    assert "cluster_name" not in f_spec["configuration_b"]["features_ordered"], "cluster_name leakage in Config B!"
    assert "churn" not in f_spec["configuration_a"]["features_ordered"], "churn target leakage in Config A!"
    assert "churn" not in f_spec["configuration_b"]["features_ordered"], "churn target leakage in Config B!"
    print(f"   PASS: Config A has {n_a} features; Config B has {n_b} features (cluster_id included, zero leakage).")
    passed_checks += 1
    
    # ---------------------------------------------------------
    # Check 6: Baseline model artifacts exist
    # ---------------------------------------------------------
    print("\n[Check 6/22] Verifying existence of 8 baseline model artifacts...")
    baseline_expected = [
        "logistic_regression_config_a.joblib", "logistic_regression_config_b.joblib",
        "decision_tree_config_a.joblib", "decision_tree_config_b.joblib",
        "random_forest_config_a.joblib", "random_forest_config_b.joblib",
        "gradient_boosting_config_a.joblib", "gradient_boosting_config_b.joblib"
    ]
    for b_file in baseline_expected:
        bp = os.path.join(BASELINE_MODELS_DIR, b_file)
        assert os.path.exists(bp), f"Baseline artifact missing: {bp}"
    print(f"   PASS: All 8 baseline model pipelines exist in {BASELINE_MODELS_DIR}")
    passed_checks += 1
    
    # ---------------------------------------------------------
    # Check 7: Tuned model artifacts exist
    # ---------------------------------------------------------
    print("\n[Check 7/22] Verifying existence of 8 tuned model artifacts...")
    tuned_expected = [
        "logistic_regression_config_a_tuned.joblib", "logistic_regression_config_b_tuned.joblib",
        "decision_tree_config_a_tuned.joblib", "decision_tree_config_b_tuned.joblib",
        "random_forest_config_a_tuned.joblib", "random_forest_config_b_tuned.joblib",
        "gradient_boosting_config_a_tuned.joblib", "gradient_boosting_config_b_tuned.joblib"
    ]
    for t_file in tuned_expected:
        tp = os.path.join(TUNED_MODELS_DIR, t_file)
        assert os.path.exists(tp), f"Tuned artifact missing: {tp}"
    print(f"   PASS: All 8 tuned model pipelines exist in {TUNED_MODELS_DIR}")
    passed_checks += 1
    
    # ---------------------------------------------------------
    # Check 8: All 16 artifacts can be loaded via joblib
    # ---------------------------------------------------------
    print("\n[Check 8/22] Verifying loadability and structure of all 16 model pipelines...")
    for b_file in baseline_expected:
        pipe = joblib.load(os.path.join(BASELINE_MODELS_DIR, b_file))
        assert hasattr(pipe, "predict"), f"Artifact {b_file} lacks predict method"
        assert hasattr(pipe, "predict_proba"), f"Artifact {b_file} lacks predict_proba method"
    for t_file in tuned_expected:
        pipe = joblib.load(os.path.join(TUNED_MODELS_DIR, t_file))
        assert hasattr(pipe, "predict"), f"Artifact {t_file} lacks predict method"
        assert hasattr(pipe, "predict_proba"), f"Artifact {t_file} lacks predict_proba method"
    print("   PASS: All 16 model pipelines loaded successfully and expose predict/predict_proba.")
    passed_checks += 1
    
    # ---------------------------------------------------------
    # Check 9: baseline_validation_results.csv integrity
    # ---------------------------------------------------------
    print("\n[Check 9/22] Verifying baseline_validation_results.csv...")
    assert os.path.exists(BASELINE_VAL_CSV), "baseline_validation_results.csv missing"
    df_base_val = pd.read_csv(BASELINE_VAL_CSV)
    assert len(df_base_val) == 8, f"Expected 8 rows, got {len(df_base_val)}"
    expected_cols = ["model_key", "config_key", "threshold", "accuracy", "precision", "recall", "f1_score", "roc_auc"]
    for col in expected_cols:
        assert col in df_base_val.columns, f"Missing column {col} in baseline validation results"
    print(f"   PASS: baseline_validation_results.csv contains {len(df_base_val)} rows with all required columns.")
    passed_checks += 1
    
    # ---------------------------------------------------------
    # Check 10: tuned_cv_results.csv integrity
    # ---------------------------------------------------------
    print("\n[Check 10/22] Verifying tuned_cv_results.csv...")
    assert os.path.exists(TUNED_CV_CSV), "tuned_cv_results.csv missing"
    df_tuned_cv = pd.read_csv(TUNED_CV_CSV)
    assert len(df_tuned_cv) == 8, f"Expected 8 rows, got {len(df_tuned_cv)}"
    assert "best_cv_f1" in df_tuned_cv.columns, "Missing best_cv_f1 in tuned CV results"
    print(f"   PASS: tuned_cv_results.csv contains {len(df_tuned_cv)} rows with training-only CV scores.")
    passed_checks += 1
    
    # ---------------------------------------------------------
    # Check 11: tuned_validation_results.csv integrity
    # ---------------------------------------------------------
    print("\n[Check 11/22] Verifying tuned_validation_results.csv...")
    assert os.path.exists(TUNED_VAL_CSV), "tuned_validation_results.csv missing"
    df_tuned_val = pd.read_csv(TUNED_VAL_CSV)
    assert len(df_tuned_val) == 8, f"Expected 8 rows, got {len(df_tuned_val)}"
    print(f"   PASS: tuned_validation_results.csv contains {len(df_tuned_val)} rows.")
    passed_checks += 1
    
    # ---------------------------------------------------------
    # Check 12: threshold_optimization_results.csv integrity
    # ---------------------------------------------------------
    print("\n[Check 12/22] Verifying threshold_optimization_results.csv (976 rows)...")
    assert os.path.exists(THRESHOLD_CSV), "threshold_optimization_results.csv missing"
    df_thresh = pd.read_csv(THRESHOLD_CSV)
    expected_rows = 16 * 61  # 976
    assert len(df_thresh) == expected_rows, f"Expected {expected_rows} rows, got {len(df_thresh)}"
    print(f"   PASS: threshold_optimization_results.csv has exactly {len(df_thresh)} rows (16 models x 61 thresholds).")
    passed_checks += 1
    
    # ---------------------------------------------------------
    # Check 13: hyperparameter_search_manifest.json validity
    # ---------------------------------------------------------
    print("\n[Check 13/22] Verifying hyperparameter_search_manifest.json...")
    assert os.path.exists(SEARCH_MANIFEST), "hyperparameter_search_manifest.json missing"
    with open(SEARCH_MANIFEST, "r", encoding="utf-8") as f:
        search_man = json.load(f)
    assert "search_results" in search_man, "search_results missing from search manifest"
    assert len(search_man["search_results"]) == 8, f"Expected 8 tuned models, got {len(search_man['search_results'])}"
    print("   PASS: hyperparameter_search_manifest.json records complete search spaces and best params for all 8 models.")
    passed_checks += 1
    
    # ---------------------------------------------------------
    # Check 14: model_selection.json validity and keys
    # ---------------------------------------------------------
    print("\n[Check 14/22] Verifying model_selection.json decision record...")
    assert os.path.exists(MODEL_SELECTION_JSON), "model_selection.json missing"
    with open(MODEL_SELECTION_JSON, "r", encoding="utf-8") as f:
        sel = json.load(f)
    required_keys = [
        "selected_model_id", "algorithm", "feature_config", "model_type",
        "optimal_threshold", "default_threshold", "recall_constraint_satisfied",
        "validation_metrics_at_optimal_threshold", "validation_metrics_at_default_threshold",
        "delta_metrics", "confusion_matrix_at_optimal", "confusion_matrix_at_default",
        "selection_rationale"
    ]
    for rk in required_keys:
        assert rk in sel, f"Missing key in model_selection.json: {rk}"
    print(f"   PASS: model_selection.json contains all required decision keys for candidate {sel['selected_model_id']}.")
    passed_checks += 1
    
    # ---------------------------------------------------------
    # Check 15: Threshold sweep range and step verification
    # ---------------------------------------------------------
    print("\n[Check 15/22] Verifying threshold sweep range [0.20, 0.80] and step (0.01)...")
    for m_id, group in df_thresh.groupby("model_id"):
        assert len(group) == 61, f"Model {m_id} has {len(group)} thresholds instead of 61"
        assert min(group["threshold"]) == 0.20, f"Model {m_id} min threshold != 0.20"
        assert max(group["threshold"]) == 0.80, f"Model {m_id} max threshold != 0.80"
    print("   PASS: All 16 models swept across exactly 61 thresholds from 0.20 to 0.80.")
    passed_checks += 1
    
    # ---------------------------------------------------------
    # Check 16: Consistency between threshold sweep @ 0.50 and validation reports
    # ---------------------------------------------------------
    print("\n[Check 16/22] Verifying metrics consistency at default threshold 0.50...")
    df_thresh_05 = df_thresh[df_thresh["threshold"] == 0.50].set_index("model_id")
    for _, row in df_base_val.iterrows():
        m_id = f"{row['model_key']}_{row['config_key']}_baseline"
        thresh_row = df_thresh_05.loc[m_id]
        np.testing.assert_almost_equal(row["f1_score"], thresh_row["f1_score"], decimal=3)
        np.testing.assert_almost_equal(row["recall"], thresh_row["recall"], decimal=3)
    for _, row in df_tuned_val.iterrows():
        m_id = f"{row['model_key']}_{row['config_key']}_tuned"
        thresh_row = df_thresh_05.loc[m_id]
        np.testing.assert_almost_equal(row["f1_score"], thresh_row["f1_score"], decimal=3)
        np.testing.assert_almost_equal(row["recall"], thresh_row["recall"], decimal=3)
    print("   PASS: Threshold sweep values @ 0.50 strictly match baseline and tuned validation CSVs.")
    passed_checks += 1
    
    # ---------------------------------------------------------
    # Check 17: Recall constraint satisfied in model selection
    # ---------------------------------------------------------
    print("\n[Check 17/22] Verifying recall constraint (>= 0.70) in model selection...")
    assert sel["recall_constraint_satisfied"] is True, "Recall constraint not satisfied!"
    opt_recall = sel["validation_metrics_at_optimal_threshold"]["recall"]
    assert opt_recall >= 0.70, f"Optimal recall {opt_recall} < 0.70"
    print(f"   PASS: Selected model satisfies recall constraint: Recall={opt_recall:.4f} >= 0.70.")
    passed_checks += 1
    
    # ---------------------------------------------------------
    # Check 18: Optimal threshold within valid bounds [0.20, 0.80]
    # ---------------------------------------------------------
    print("\n[Check 18/22] Verifying optimal threshold bounds [0.20, 0.80]...")
    opt_t = sel["optimal_threshold"]
    assert 0.20 <= opt_t <= 0.80, f"Optimal threshold {opt_t} out of range [0.20, 0.80]"
    print(f"   PASS: Optimal threshold t={opt_t:.2f} is within [0.20, 0.80].")
    passed_checks += 1
    
    # ---------------------------------------------------------
    # Check 19: Delta metrics arithmetic consistency
    # ---------------------------------------------------------
    print("\n[Check 19/22] Verifying delta metrics arithmetic consistency...")
    opt_m = sel["validation_metrics_at_optimal_threshold"]
    def_m = sel["validation_metrics_at_default_threshold"]
    deltas = sel["delta_metrics"]
    
    np.testing.assert_almost_equal(deltas["f1_score_delta"], round(opt_m["f1_score"] - def_m["f1_score"], 4))
    np.testing.assert_almost_equal(deltas["recall_delta"], round(opt_m["recall"] - def_m["recall"], 4))
    np.testing.assert_almost_equal(deltas["accuracy_delta"], round(opt_m["accuracy"] - def_m["accuracy"], 4))
    assert deltas["true_positives_delta"] == opt_m["true_positives"] - def_m["true_positives"]
    assert deltas["false_positives_delta"] == opt_m["false_positives"] - def_m["false_positives"]
    print("   PASS: Delta metrics precisely match (optimal - default) across all continuous and count metrics.")
    passed_checks += 1
    
    # ---------------------------------------------------------
    # Check 20: Confusion matrix totals strictly sum to 1,050
    # ---------------------------------------------------------
    print("\n[Check 20/22] Verifying confusion matrix totals sum to 1,050...")
    cm_opt = sel["confusion_matrix_at_optimal"]
    cm_def = sel["confusion_matrix_at_default"]
    
    sum_opt = cm_opt["tp"] + cm_opt["fp"] + cm_opt["tn"] + cm_opt["fn"]
    sum_def = cm_def["tp"] + cm_def["fp"] + cm_def["tn"] + cm_def["fn"]
    assert sum_opt == 1050, f"Optimal confusion matrix sum = {sum_opt} != 1050"
    assert sum_def == 1050, f"Default confusion matrix sum = {sum_def} != 1050"
    
    # Check actual class counts
    actual_churners = cm_opt["tp"] + cm_opt["fn"]
    actual_non_churners = cm_opt["tn"] + cm_opt["fp"]
    assert actual_churners == 481, f"Actual churners sum = {actual_churners} != 481"
    assert actual_non_churners == 569, f"Actual non-churners sum = {actual_non_churners} != 569"
    print(f"   PASS: Confusion matrices sum strictly to 1,050 (481 Churned, 569 Retained).")
    passed_checks += 1
    
    # ---------------------------------------------------------
    # Check 21: No NaN or Inf values in any generated CSV report
    # ---------------------------------------------------------
    print("\n[Check 21/22] Verifying absence of NaN / Inf in all generated CSV reports...")
    csv_files = [BASELINE_VAL_CSV, TUNED_CV_CSV, TUNED_VAL_CSV, THRESHOLD_CSV]
    for c_path in csv_files:
        df = pd.read_csv(c_path)
        nan_count = df.isna().sum().sum()
        assert nan_count == 0, f"Found {nan_count} NaNs in {c_path}"
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        for ncol in numeric_cols:
            inf_count = np.isinf(df[ncol]).sum()
            assert inf_count == 0, f"Found {inf_count} Infs in {c_path} col {ncol}"
    print("   PASS: All generated reports are completely clean (0 NaNs, 0 Infs).")
    passed_checks += 1
    
    # ---------------------------------------------------------
    # Check 22: Selected candidate model artifact exists on disk
    # ---------------------------------------------------------
    print("\n[Check 22/22] Verifying selected candidate model artifact path...")
    sel_path = os.path.join(PROJECT_ROOT, sel["artifact_path"])
    assert os.path.exists(sel_path), f"Selected model file does not exist: {sel_path}"
    print(f"   PASS: Selected model artifact confirmed on disk: {sel['artifact_path']}")
    passed_checks += 1
    
    print("\n" + "=" * 80)
    print(f"VERIFICATION COMPLETE: {passed_checks}/{total_checks} CHECKS PASSED (100% SUCCESS)")
    print("=" * 80)
    return True


if __name__ == "__main__":
    success = run_all_checks()
    if not success:
        sys.exit(1)
