"""
Indian E-Commerce Customer Retention Intelligence System
Module: Phase 5 — Checkpoint 5: Final Model Refitting
Description: Combines train.csv (N=4,900) and validation.csv (N=1,050) to create
             the final combined training dataset (N=5,950).
             Reconstructs and refits the selected Logistic Regression Configuration B
             pipeline (C=0.01, class_weight='balanced', solver='lbfgs', max_iter=2000).
             Saves the final production-ready artifact to models/phase5/final_churn_pipeline.joblib.

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
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.linear_model import LogisticRegression

# Ensure project root and backend/ml are on sys.path
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "..", ".."))
sys.path.insert(0, SCRIPT_DIR)
sys.path.insert(0, PROJECT_ROOT)

# Paths
TRAIN_PATH = os.path.join(PROJECT_ROOT, "data", "modeling", "train.csv")
VAL_PATH = os.path.join(PROJECT_ROOT, "data", "modeling", "validation.csv")
FEATURE_COLUMNS_PATH = os.path.join(PROJECT_ROOT, "data", "modeling", "feature_columns.json")
MODEL_SELECTION_PATH = os.path.join(PROJECT_ROOT, "reports", "phase5", "model_selection.json")
FINAL_MODEL_DIR = os.path.join(PROJECT_ROOT, "models", "phase5")
FINAL_PIPELINE_PATH = os.path.join(FINAL_MODEL_DIR, "final_churn_pipeline.joblib")

RANDOM_STATE = 42


def compute_sha256(filepath):
    """Computes uppercase SHA-256 hash of a file."""
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest().upper()


def build_preprocessor(categorical_cols, numerical_cols, scale_numerical=True):
    """
    Constructs the approved leakage-free ColumnTransformer preprocessor.
    - Numerical: SimpleImputer(strategy='median', add_indicator=True) + StandardScaler().
    - Categorical: SimpleImputer(strategy='most_frequent') + OneHotEncoder(handle_unknown='ignore', sparse_output=False).
    """
    num_pipeline = Pipeline([
        ("imputer", SimpleImputer(strategy="median", add_indicator=True)),
        ("scaler", StandardScaler())
    ])

    cat_pipeline = Pipeline([
        ("imputer", SimpleImputer(strategy="most_frequent")),
        ("encoder", OneHotEncoder(handle_unknown="ignore", sparse_output=False))
    ])

    preprocessor = ColumnTransformer(
        transformers=[
            ("num", num_pipeline, numerical_cols),
            ("cat", cat_pipeline, categorical_cols)
        ],
        remainder="drop"
    )
    return preprocessor


def refit_final_model():
    print("=" * 80)
    print("PHASE 5: CHECKPOINT 5 — FINAL MODEL REFITTING (TRAIN + VALIDATION)")
    print("=" * 80)

    # 1. Audit Checkpoint 4 Selection Record
    print(f"\n1. Verifying model selection record from: {MODEL_SELECTION_PATH}")
    assert os.path.exists(MODEL_SELECTION_PATH), f"Missing model_selection.json: {MODEL_SELECTION_PATH}"
    with open(MODEL_SELECTION_PATH, "r", encoding="utf-8") as f:
        selection_record = json.load(f)

    selected_model_id = selection_record["selected_model_id"]
    algorithm = selection_record["algorithm"]
    config = selection_record["feature_config"]
    optimal_threshold = selection_record["optimal_threshold"]

    print(f"   Selected Model ID : {selected_model_id}")
    print(f"   Algorithm         : {algorithm} (Logistic Regression)")
    print(f"   Feature Config    : {config} (Configuration B: 37 features)")
    print(f"   Locked Threshold  : {optimal_threshold}")

    assert selected_model_id == "logistic_regression_config_b_tuned", f"Unexpected model ID: {selected_model_id}"
    assert config == "B", f"Expected Config B, got {config}"
    assert optimal_threshold == 0.46, f"Expected threshold 0.46, got {optimal_threshold}"

    # 2. Load Feature Allowlist
    print(f"\n2. Loading feature allowlist specifications from: {FEATURE_COLUMNS_PATH}")
    with open(FEATURE_COLUMNS_PATH, "r", encoding="utf-8") as f:
        feature_spec = json.load(f)

    cfg_b = feature_spec["configuration_b"]
    cat_cols = cfg_b["categorical_features"]
    num_cols = cfg_b["numerical_features"]
    ordered_features = cfg_b["features_ordered"]

    assert len(cat_cols) == 3, f"Expected 3 categorical features, got {len(cat_cols)}"
    assert "cluster_id" in cat_cols, "cluster_id missing from categorical list"
    assert len(num_cols) == 34, f"Expected 34 numerical features, got {len(num_cols)}"
    assert len(ordered_features) == 37, f"Expected 37 ordered features, got {len(ordered_features)}"
    assert "churn" not in ordered_features, "Target 'churn' leaked into predictive features!"
    assert "customer_id" not in ordered_features, "'customer_id' leaked into predictive features!"
    assert "customer_name" not in ordered_features, "'customer_name' leaked into predictive features!"
    assert "cluster_name" not in ordered_features, "'cluster_name' leaked into predictive features!"

    print(f"   Categorical features ({len(cat_cols)}): {cat_cols}")
    print(f"   Numerical features   ({len(num_cols)}): {len(num_cols)} features verified")
    print(f"   Total predictive features: {len(ordered_features)}")

    # 3. Load & Combine Train and Validation Partitions
    print(f"\n3. Loading train and validation datasets...")
    assert os.path.exists(TRAIN_PATH), f"Missing train.csv: {TRAIN_PATH}"
    assert os.path.exists(VAL_PATH), f"Missing validation.csv: {VAL_PATH}"

    df_train = pd.read_csv(TRAIN_PATH)
    df_val = pd.read_csv(VAL_PATH)

    n_train = len(df_train)
    n_val = len(df_val)
    print(f"   Training records   : {n_train} (expected 4,900)")
    print(f"   Validation records : {n_val} (expected 1,050)")
    assert n_train == 4900, f"Expected 4,900 train rows, got {n_train}"
    assert n_val == 1050, f"Expected 1,050 val rows, got {n_val}"

    df_combined = pd.concat([df_train, df_val], ignore_index=True)
    n_combined = len(df_combined)
    print(f"   Combined records   : {n_combined} (expected 5,950)")
    assert n_combined == 5950, f"Expected 5,950 combined rows, got {n_combined}"

    # Verify disjointness
    train_ids = set(df_train["customer_id"])
    val_ids = set(df_val["customer_id"])
    assert len(train_ids.intersection(val_ids)) == 0, "Train and Validation customer overlap detected!"

    # Class balance in combined dataset
    combined_churn = int(df_combined["churn"].sum())
    combined_retained = n_combined - combined_churn
    print(f"   Combined Class Balance: {combined_churn} Churned ({combined_churn/n_combined*100:.2f}%), "
          f"{combined_retained} Retained ({combined_retained/n_combined*100:.2f}%)")

    # 4. Extract Feature Matrix and Target Vector
    X_combined = df_combined[ordered_features]
    y_combined = df_combined["churn"].values

    assert X_combined.shape == (5950, 37), f"Unexpected X shape: {X_combined.shape}"
    assert len(y_combined) == 5950, f"Unexpected y length: {len(y_combined)}"

    # 5. Build and Fit the Final Pipeline
    print("\n4. Reconstructing and fitting the final Logistic Regression pipeline...")
    preprocessor = build_preprocessor(cat_cols, num_cols, scale_numerical=True)

    classifier = LogisticRegression(
        C=0.01,
        class_weight="balanced",
        solver="lbfgs",
        max_iter=2000,
        random_state=RANDOM_STATE
    )

    final_pipeline = Pipeline([
        ("preprocessor", preprocessor),
        ("classifier", classifier)
    ])

    print("   Pipeline architecture:")
    print("     [Step 1] preprocessor: ColumnTransformer (median impute + standard scale num; frequent impute + OHE cat)")
    print("     [Step 2] classifier  : LogisticRegression(C=0.01, class_weight='balanced', solver='lbfgs', max_iter=2000, random_state=42)")

    # Fit exclusively on combined training + validation data
    print("   Fitting on N=5,950 combined records...")
    final_pipeline.fit(X_combined, y_combined)

    # 6. Verify Fitted Pipeline
    classes = final_pipeline.classes_
    print(f"\n5. Verifying fitted pipeline:")
    print(f"   Classes discovered: {classes} (class index 1 corresponds to Churn=1: {classes[1] == 1})")
    assert np.array_equal(classes, [0, 1]), f"Unexpected classes: {classes}"

    fitted_clf = final_pipeline.named_steps["classifier"]
    assert fitted_clf.C == 0.01, f"Unexpected C: {fitted_clf.C}"
    assert fitted_clf.class_weight == "balanced", f"Unexpected class_weight: {fitted_clf.class_weight}"
    assert fitted_clf.solver == "lbfgs", f"Unexpected solver: {fitted_clf.solver}"
    assert fitted_clf.max_iter == 2000, f"Unexpected max_iter: {fitted_clf.max_iter}"
    assert fitted_clf.coef_.shape[0] == 1, "Expected binary classification coefficient vector"
    n_features_transformed = fitted_clf.coef_.shape[1]
    print(f"   Transformed feature count in classifier: {n_features_transformed}")
    print(f"   Intercept: {fitted_clf.intercept_[0]:.4f}")

    # 7. Save Final Pipeline Artifact
    os.makedirs(FINAL_MODEL_DIR, exist_ok=True)
    joblib.dump(final_pipeline, FINAL_PIPELINE_PATH)
    file_size_kb = os.path.getsize(FINAL_PIPELINE_PATH) / 1024
    sha256_hash = compute_sha256(FINAL_PIPELINE_PATH)

    print(f"\n6. Successfully saved final model artifact:")
    print(f"   Path     : {FINAL_PIPELINE_PATH}")
    print(f"   Size     : {file_size_kb:.2f} KB")
    print(f"   SHA-256  : {sha256_hash}")

    print("\n" + "=" * 80)
    print("FINAL MODEL REFITTING COMPLETED SUCCESSFULLY!")
    print("=" * 80)
    return final_pipeline, sha256_hash


if __name__ == "__main__":
    refit_final_model()
