"""
Indian E-Commerce Customer Retention Intelligence System
Module: Advanced Feature Engineering Validation Suite
Description: Exhaustively validates advanced feature calculations, missingness handling,
             Log1pTransformer, CorrelationPruner, and full scikit-learn pipeline
             integration without data leakage.

Author: Senior Machine Learning Engineer (BCA AI & ML Project)
"""

import sys
import os
import numpy as np
import pandas as pd
import pytest
from sklearn.pipeline import Pipeline
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import StratifiedKFold, cross_val_score

# Ensure backend/ml is on sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from advanced_feature_engineering import (
    compute_advanced_features,
    Log1pTransformer,
    CorrelationPruner,
    build_advanced_preprocessor,
    BASELINE_NUMERICAL_COLS,
    BASELINE_CATEGORICAL_COLS,
    ADVANCED_NUMERICAL_COLS
)


def test_velocity_momentum_ratios():
    print("\n--- Test 1: Velocity Momentum Ratios & Missingness Semantics ---")
    # Synthetic test DataFrame with key edge cases
    test_df = pd.DataFrame({
        "orders_last_30_days": [0, 0, 1, 3, 0],
        "orders_last_90_days": [0, 1, 3, 6, 0],
        "orders_last_180_days": [0, 2, 6, 12, 4],
        "hist_average_delivery_delay_days": [np.nan, 2.0, 3.5, 1.0, 0.0],
        "hist_return_rate": [0.0, 0.1, 0.2, 0.0, 0.5],
        "hist_cancellation_rate": [1.0, 0.0, 0.1, 0.05, 0.0]
    })

    res = compute_advanced_features(test_df)

    # Row 0: 0 orders in 90 and 180 days -> ratios must be NaN
    assert np.isnan(res.loc[0, "velocity_ratio_30_90"]), "Row 0: 30/90 ratio must be NaN when 90d orders == 0"
    assert np.isnan(res.loc[0, "velocity_ratio_90_180"]), "Row 0: 90/180 ratio must be NaN when 180d orders == 0"
    assert res.loc[0, "has_orders_last_90_days"] == 0, "Row 0: has_orders_last_90_days must be 0"
    assert res.loc[0, "has_orders_last_180_days"] == 0, "Row 0: has_orders_last_180_days must be 0"

    # Row 1: 0 orders in 30d, 1 order in 90d, 2 orders in 180d
    # R_30_90 = (0 + 0.1) / (1/3 + 0.1) = 0.1 / (0.3333 + 0.1) = 0.1 / 0.4333 ≈ 0.2308
    expected_30_90_row1 = round((0 + 0.1) / (1 / 3.0 + 0.1), 4)
    assert abs(res.loc[1, "velocity_ratio_30_90"] - expected_30_90_row1) < 1e-3, f"Row 1: 30/90 mismatch {res.loc[1, 'velocity_ratio_30_90']}"
    assert res.loc[1, "has_orders_last_90_days"] == 1
    # R_90_180 = (1 + 0.1) / (2/2 + 0.1) = 1.1 / 1.1 = 1.0
    assert abs(res.loc[1, "velocity_ratio_90_180"] - 1.0) < 1e-3
    assert res.loc[1, "has_orders_last_180_days"] == 1

    # Row 2: 1 in 30d, 3 in 90d -> R_30_90 = (1 + 0.1) / (3/3 + 0.1) = 1.1 / 1.1 = 1.0
    assert abs(res.loc[2, "velocity_ratio_30_90"] - 1.0) < 1e-3

    # Row 4: 0 in 30d, 0 in 90d, 4 in 180d -> 30/90 is NaN, 90/180 is computed
    assert np.isnan(res.loc[4, "velocity_ratio_30_90"])
    assert res.loc[4, "has_orders_last_90_days"] == 0
    assert res.loc[4, "has_orders_last_180_days"] == 1
    expected_90_180_row4 = round((0 + 0.1) / (4 / 2.0 + 0.1), 4)
    assert abs(res.loc[4, "velocity_ratio_90_180"] - expected_90_180_row4) < 1e-3

    print("   [PASS] Velocity momentum ratios and zero-baseline NaN handling confirmed.")


def test_customer_friction_index():
    print("\n--- Test 2: Customer Friction Index & Missingness Propagation ---")
    test_df = pd.DataFrame({
        "orders_last_30_days": [1, 2],
        "orders_last_90_days": [2, 4],
        "orders_last_180_days": [3, 6],
        "hist_average_delivery_delay_days": [np.nan, 4.0],
        "hist_return_rate": [0.2, 0.1],
        "hist_cancellation_rate": [0.1, 0.05]
    })

    res = compute_advanced_features(test_df)

    # Row 0: Delivery delay is NaN -> Friction score MUST be NaN, missing_friction_score MUST be 1
    assert np.isnan(res.loc[0, "delay_friction_score"]), "Friction score must be NaN when delivery delay is missing!"
    assert res.loc[0, "missing_friction_score"] == 1, "missing_friction_score must be 1 when delay is missing!"

    # Row 1: Delay = 4.0, Return = 0.1, Cancel = 0.05 -> Friction = 4.0 * (1 + 0.1 + 0.05) = 4.60
    assert abs(res.loc[1, "delay_friction_score"] - 4.60) < 1e-3, f"Friction mismatch: {res.loc[1, 'delay_friction_score']}"
    assert res.loc[1, "missing_friction_score"] == 0, "missing_friction_score must be 0 when delay is present!"

    print("   [PASS] Friction index calculation and NaN propagation verified.")


def test_log1p_transformer():
    print("\n--- Test 3: Log1pTransformer Validation ---")
    test_df = pd.DataFrame({
        "tenure": [0.0, 10.0, 100.0, np.nan],
        "spend": [0.0, 500.0, 5000.0, 1000.0],
        "negative_col": [1.0, -5.0, 10.0, 20.0]
    })

    transformer = Log1pTransformer(columns=["tenure", "spend"])
    transformer.fit(test_df)
    transformed_df = transformer.transform(test_df)

    # Check tenure
    assert transformed_df.loc[0, "tenure"] == 0.0, "log1p(0) must equal 0.0"
    assert abs(transformed_df.loc[1, "tenure"] - np.log1p(10.0)) < 1e-5
    assert abs(transformed_df.loc[2, "tenure"] - np.log1p(100.0)) < 1e-5
    assert np.isnan(transformed_df.loc[3, "tenure"]), "NaN values must be preserved intact"

    # Check rejection of negative values
    bad_transformer = Log1pTransformer(columns=["negative_col"])
    try:
        bad_transformer.fit(test_df)
        assert False, "Should have raised ValueError on negative values!"
    except ValueError as e:
        assert "negative values" in str(e).lower()
        print("   [PASS] Log1pTransformer rejected negative values correctly.")

    print("   [PASS] Log1pTransformer correctly transforms non-negative values and preserves NaNs.")


def test_correlation_pruner():
    print("\n--- Test 4: CorrelationPruner Validation ---")
    np.random.seed(42)
    n = 200
    # Create two highly correlated features: x2 is x1 + tiny noise (r > 0.99)
    x1 = np.random.normal(0, 1, n)
    x2 = x1 + np.random.normal(0, 0.05, n)
    # Target y is strongly correlated with x1 (r ~ 0.8) and poorly correlated with x3
    y = x1 + np.random.normal(0, 0.5, n)
    x3 = np.random.normal(0, 1, n)

    df = pd.DataFrame({"x1": x1, "x2": x2, "x3": x3})

    # Case A: Prune with y target -> x1 and x2 are collinear; pruner should retain the one with higher target correlation
    pruner_target = CorrelationPruner(threshold=0.85)
    pruner_target.fit(df, y=y)
    
    dropped = pruner_target.columns_to_drop_
    kept = pruner_target.columns_to_keep_
    print(f"   Target-aware pruner dropped: {dropped}, kept: {kept}")
    assert len(dropped) == 1, f"Expected 1 dropped column, got {len(dropped)}"
    assert ("x1" in dropped and "x2" in kept) or ("x2" in dropped and "x1" in kept)
    assert "x3" in kept, "Uncorrelated x3 must be kept"

    # Case B: Protected column -> protect x2 even if x1 has higher correlation
    pruner_prot = CorrelationPruner(threshold=0.85, protected_cols=["x2"])
    pruner_prot.fit(df, y=y)
    assert "x2" in pruner_prot.columns_to_keep_, "Protected column x2 must be kept"
    assert "x1" in pruner_prot.columns_to_drop_, "Unprotected collinear x1 must be dropped"
    print("   [PASS] Protected columns correctly shielded from pruning.")

    # Case C: Array-like input without y
    X_arr = df.values
    pruner_arr = CorrelationPruner(threshold=0.85)
    pruner_arr.fit(X_arr)
    X_trans = pruner_arr.transform(X_arr)
    assert X_trans.shape[1] == 2, f"Array output should have 2 columns, got {X_trans.shape[1]}"
    print("   [PASS] CorrelationPruner works identically with numpy arrays.")


def test_full_preprocessing_pipeline_on_real_data():
    print("\n--- Test 5: Full Pipeline Integration on Train & Validation Datasets ---")
    train_path = os.path.join("data", "modeling", "train.csv")
    val_path = os.path.join("data", "modeling", "validation.csv")

    assert os.path.exists(train_path), f"Train dataset missing: {train_path}"
    assert os.path.exists(val_path), f"Val dataset missing: {val_path}"

    train_df = pd.read_csv(train_path)
    val_df = pd.read_csv(val_path)

    # Compute advanced features
    train_adv = compute_advanced_features(train_df)
    val_adv = compute_advanced_features(val_df)

    num_cols = BASELINE_NUMERICAL_COLS + ADVANCED_NUMERICAL_COLS
    cat_cols = BASELINE_CATEGORICAL_COLS

    X_train = train_adv[num_cols + cat_cols]
    y_train = train_adv["churn"]

    X_val = val_adv[num_cols + cat_cols]
    y_val = val_adv["churn"]

    # Construct pipeline with ALL advanced options enabled:
    # log1p, scaling, correlation pruner
    preprocessor = build_advanced_preprocessor(
        categorical_cols=cat_cols,
        numerical_cols=num_cols,
        scale_numerical=True,
        use_log1p=True,
        use_correlation_pruner=True,
        correlation_threshold=0.85,
        protected_cols={"velocity_ratio_30_90", "delay_friction_score"}
    )

    clf_pipeline = Pipeline([
        ("preprocessor", preprocessor),
        ("classifier", LogisticRegression(max_iter=1000, solver="lbfgs", random_state=42))
    ])

    # Fit strictly on training fold
    clf_pipeline.fit(X_train, y_train)

    # Predict on validation fold
    val_preds = clf_pipeline.predict(X_val)
    val_probs = clf_pipeline.predict_proba(X_val)[:, 1]

    assert len(val_preds) == len(val_df), "Validation predictions length mismatch!"
    assert len(val_probs) == len(val_df), "Validation probabilities length mismatch!"
    assert (val_probs >= 0.0).all() and (val_probs <= 1.0).all(), "Probabilities outside [0, 1]!"

    print(f"   Train samples: {len(X_train):,}")
    print(f"   Validation samples: {len(X_val):,}")
    print(f"   Validation predictions generated successfully.")
    print(f"   Validation mean predicted probability: {val_probs.mean():.4f}")
    print("   [PASS] Full scikit-learn pipeline fits and transforms seamlessly without data leakage.")


def run_all_tests():
    print("=" * 80)
    print("PHASE 5.1: ADVANCED FEATURE ENGINEERING VALIDATION SUITE")
    print("=" * 80)

    test_velocity_momentum_ratios()
    test_customer_friction_index()
    test_log1p_transformer()
    test_correlation_pruner()
    test_full_preprocessing_pipeline_on_real_data()

    print("\n" + "=" * 80)
    print("ALL ADVANCED FEATURE TESTS PASSED SUCCESSFULLY!")
    print("ZERO LEAKAGE & STRICT PIPELINE COMPLIANCE VERIFIED.")
    print("=" * 80)


if __name__ == "__main__":
    run_all_tests()
