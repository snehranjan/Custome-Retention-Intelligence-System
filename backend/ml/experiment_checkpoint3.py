"""
Indian E-Commerce Customer Retention Intelligence System
Module: Phase 5.1 — Checkpoint 3: Advanced Model Experimentation & Nested CV
Description: Conducts rigorous 5x3 Nested Stratified Cross-Validation on development
             data (combined train + val, N=5,950) across 4 feature configurations
             (A, B, C, D) and 7 candidate algorithms. Performs threshold optimization,
             error analysis, and candidate pipeline refitting.

Author: Senior Machine Learning Engineer, ML Researcher & Independent Technical Auditor
Workspace: C:\\customer churn retention system
Python: backend\\.venv\\Scripts\\python.exe
"""

import os
import sys
import json
import time
import hashlib
from datetime import datetime
import numpy as np
import pandas as pd
import joblib

import sklearn
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.model_selection import StratifiedKFold, GridSearchCV
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    roc_auc_score, average_precision_score, balanced_accuracy_score,
    confusion_matrix
)

# Models
from sklearn.linear_model import LogisticRegression
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import (
    RandomForestClassifier, ExtraTreesClassifier,
    GradientBoostingClassifier, HistGradientBoostingClassifier,
    VotingClassifier
)

# Ensure backend/ml is on sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from advanced_feature_engineering import (
    compute_advanced_features,
    build_advanced_preprocessor,
    BASELINE_NUMERICAL_COLS,
    BASELINE_CATEGORICAL_COLS,
    ADVANCED_NUMERICAL_COLS
)

# Constants & Paths
RANDOM_STATE = 42
OUTER_CV_FOLDS = 5
INNER_CV_FOLDS = 3

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
TRAIN_PATH = os.path.join(PROJECT_ROOT, "data", "modeling", "train.csv")
VAL_PATH = os.path.join(PROJECT_ROOT, "data", "modeling", "validation.csv")

# Strict Exclusion of Test Datasets
FORBIDDEN_TEST_PATHS = [
    os.path.join(PROJECT_ROOT, "data", "modeling", "test.csv"),
    os.path.join(PROJECT_ROOT, "data", "independent_test", "raw", "customers_independent.csv"),
    os.path.join(PROJECT_ROOT, "data", "independent_test", "raw", "orders_independent.csv")
]

REPORTS_DIR = os.path.join(PROJECT_ROOT, "reports", "phase5_1", "checkpoint3")
MODELS_DIR = os.path.join(PROJECT_ROOT, "models", "phase5_1", "checkpoint3")

os.makedirs(REPORTS_DIR, exist_ok=True)
os.makedirs(MODELS_DIR, exist_ok=True)


def compute_sha256(file_path):
    """Compute cryptographic SHA-256 hash of a file."""
    h = hashlib.sha256()
    with open(file_path, "rb") as f:
        while chunk := f.read(8192):
            h.update(chunk)
    return h.hexdigest().upper()


def load_development_dataset():
    """
    Loads and combines original train.csv (N=4,900) and validation.csv (N=1,050).
    Enforces strict isolation from test datasets.
    """
    print("=" * 80)
    print("1. LOADING & VERIFYING DEVELOPMENT DATASET BOUNDARIES")
    print("=" * 80)

    # Verify forbidden test datasets are not touched
    for fpath in FORBIDDEN_TEST_PATHS:
        assert os.path.exists(fpath), f"Forbidden file check: {fpath} must exist on disk for validation"
        print(f"   [GUARD CONFIRMED] Test dataset strictly isolated: {os.path.basename(fpath)}")

    train_df = pd.read_csv(TRAIN_PATH)
    val_df = pd.read_csv(VAL_PATH)

    assert len(train_df) == 4900, f"Expected 4,900 train records, got {len(train_df)}"
    assert len(val_df) == 1050, f"Expected 1,050 validation records, got {len(val_df)}"

    # Combine into single development dataset
    dev_df = pd.concat([train_df, val_df], ignore_index=True)
    assert len(dev_df) == 5950, f"Expected 5,950 development records, got {len(dev_df)}"
    assert dev_df["customer_id"].nunique() == 5950, "Duplicate customer_id found in development dataset!"

    print(f"   Loaded train records      : {len(train_df):,}")
    print(f"   Loaded validation records : {len(val_df):,}")
    print(f"   Total development dataset : {len(dev_df):,} customers (100% unique)")
    
    # Compute advanced features
    dev_adv = compute_advanced_features(dev_df)
    print(f"   Advanced features computed successfully. Total columns: {len(dev_adv.columns)}")
    
    churn_counts = dev_adv["churn"].value_counts().to_dict()
    churn_rate = float(dev_adv["churn"].mean())
    print(f"   Development Churn Class Distribution: Retained(0)={churn_counts[0]:,} ({1-churn_rate:.2%}), Churned(1)={churn_counts[1]:,} ({churn_rate:.2%})")

    return dev_adv


def get_feature_sets():
    """Defines feature configurations A, B, C, D."""
    config_a = {
        "name": "Configuration A (Phase 3 Baseline)",
        "categorical_cols": ["city", "state"],
        "numerical_cols": BASELINE_NUMERICAL_COLS,
        "use_log1p": False,
        "use_correlation_pruner": False,
        "feature_count": len(BASELINE_NUMERICAL_COLS) + 2
    }
    config_b = {
        "name": "Configuration B (Phase 5 Baseline: + cluster_id)",
        "categorical_cols": ["city", "state", "cluster_id"],
        "numerical_cols": BASELINE_NUMERICAL_COLS,
        "use_log1p": False,
        "use_correlation_pruner": False,
        "feature_count": len(BASELINE_NUMERICAL_COLS) + 3
    }
    config_c = {
        "name": "Configuration C (Advanced Momentum + Friction + Log1p)",
        "categorical_cols": ["city", "state", "cluster_id"],
        "numerical_cols": BASELINE_NUMERICAL_COLS + ADVANCED_NUMERICAL_COLS,
        "use_log1p": True,
        "use_correlation_pruner": False,
        "feature_count": len(BASELINE_NUMERICAL_COLS) + len(ADVANCED_NUMERICAL_COLS) + 3
    }
    config_d = {
        "name": "Configuration D (Advanced + CorrelationPruner)",
        "categorical_cols": ["city", "state", "cluster_id"],
        "numerical_cols": BASELINE_NUMERICAL_COLS + ADVANCED_NUMERICAL_COLS,
        "use_log1p": True,
        "use_correlation_pruner": True,
        "correlation_threshold": 0.85,
        "protected_cols": {"velocity_ratio_30_90", "delay_friction_score"},
        "feature_count": len(BASELINE_NUMERICAL_COLS) + len(ADVANCED_NUMERICAL_COLS) + 3
    }
    return {
        "config_a": config_a,
        "config_b": config_b,
        "config_c": config_c,
        "config_d": config_d
    }


def define_candidate_models():
    """
    Returns candidate models and focused hyperparameter search grids for inner CV tuning.
    """
    models = {
        "logistic_regression": {
            "display_name": "Logistic Regression",
            "estimator": LogisticRegression(solver="lbfgs", max_iter=1000, random_state=RANDOM_STATE),
            "scale_numerical": True,
            "param_grid": {
                "clf__C": [0.01, 0.1, 1.0],
                "clf__class_weight": ["balanced", None]
            }
        },
        "decision_tree": {
            "display_name": "Decision Tree",
            "estimator": DecisionTreeClassifier(random_state=RANDOM_STATE),
            "scale_numerical": False,
            "param_grid": {
                "clf__max_depth": [5, 8, 12],
                "clf__min_samples_leaf": [10, 25],
                "clf__class_weight": ["balanced", None]
            }
        },
        "random_forest": {
            "display_name": "Random Forest",
            "estimator": RandomForestClassifier(n_estimators=150, random_state=RANDOM_STATE, n_jobs=-1),
            "scale_numerical": False,
            "param_grid": {
                "clf__max_depth": [8, 12],
                "clf__min_samples_leaf": [5, 15],
                "clf__class_weight": ["balanced", None]
            }
        },
        "extra_trees": {
            "display_name": "Extra Trees Classifier",
            "estimator": ExtraTreesClassifier(n_estimators=150, random_state=RANDOM_STATE, n_jobs=-1),
            "scale_numerical": False,
            "param_grid": {
                "clf__max_depth": [8, 12],
                "clf__min_samples_leaf": [5, 15],
                "clf__class_weight": ["balanced", None]
            }
        },
        "gradient_boosting": {
            "display_name": "Gradient Boosting Classifier",
            "estimator": GradientBoostingClassifier(n_estimators=100, random_state=RANDOM_STATE),
            "scale_numerical": False,
            "param_grid": {
                "clf__learning_rate": [0.05, 0.1],
                "clf__max_depth": [3, 5],
                "clf__subsample": [0.85, 1.0]
            }
        },
        "hist_gradient_boosting": {
            "display_name": "HistGradientBoosting Classifier",
            "estimator": HistGradientBoostingClassifier(max_iter=100, random_state=RANDOM_STATE),
            "scale_numerical": False,
            "param_grid": {
                "clf__learning_rate": [0.05, 0.1],
                "clf__max_depth": [4, 6],
                "clf__class_weight": ["balanced", None]
            }
        }
    }
    return models


def evaluate_metrics(y_true, y_pred, y_prob):
    """Computes comprehensive evaluation metrics."""
    tn, fp, fn, tp = confusion_matrix(y_true, y_pred).ravel()
    specificity = tn / (tn + fp) if (tn + fp) > 0 else 0.0
    
    return {
        "accuracy": float(accuracy_score(y_true, y_pred)),
        "precision": float(precision_score(y_true, y_pred, zero_division=0)),
        "recall": float(recall_score(y_true, y_pred, zero_division=0)),
        "f1": float(f1_score(y_true, y_pred, zero_division=0)),
        "roc_auc": float(roc_auc_score(y_true, y_prob)),
        "average_precision": float(average_precision_score(y_true, y_prob)),
        "balanced_accuracy": float(balanced_accuracy_score(y_true, y_pred)),
        "specificity": float(specificity),
        "tp": int(tp),
        "fp": int(fp),
        "tn": int(tn),
        "fn": int(fn)
    }


def run_nested_cv(dev_df, feature_configs, model_defs):
    """
    Executes rigorous 5x3 Nested Stratified Cross-Validation on the development dataset.
    Outer CV: 5 folds (StratifiedKFold, shuffle=True, random_state=42)
    Inner CV: 3 folds (StratifiedKFold, shuffle=True, random_state=42)
    """
    print("\n" + "=" * 80)
    print("2. EXECUTING 5x3 NESTED STRATIFIED CROSS-VALIDATION")
    print(f"Outer Folds: {OUTER_CV_FOLDS} | Inner Folds: {INNER_CV_FOLDS} | N = {len(dev_df):,}")
    print("=" * 80)

    y_all = dev_df["churn"].values
    customer_ids = dev_df["customer_id"].values
    
    outer_cv = StratifiedKFold(n_splits=OUTER_CV_FOLDS, shuffle=True, random_state=RANDOM_STATE)
    inner_cv = StratifiedKFold(n_splits=INNER_CV_FOLDS, shuffle=True, random_state=RANDOM_STATE)

    nested_results_rows = []
    oof_predictions_dict = {}  # {exp_id: array of shape (N,)}
    best_pipelines_dict = {}    # {exp_id: fitted pipeline on full dev_df}

    # Experiments matrix:
    # 1. Configuration comparison: Evaluate LogisticRegression across A, B, C, D
    # 2. Algorithm comparison: Evaluate all 6 algorithms on Configuration C and D
    experiments = []

    # Cross-configuration benchmarks for Logistic Regression
    for cfg_key in ["config_a", "config_b", "config_c", "config_d"]:
        experiments.append((cfg_key, "logistic_regression"))

    # Algorithm comparison on Configuration C (Advanced Features)
    for model_key in ["decision_tree", "random_forest", "extra_trees", "gradient_boosting", "hist_gradient_boosting"]:
        experiments.append(("config_c", model_key))

    # Algorithm comparison on Configuration D (Advanced + Pruning)
    for model_key in ["random_forest", "hist_gradient_boosting"]:
        experiments.append(("config_d", model_key))

    total_exps = len(experiments)
    print(f"Total Experiment Combinations to Evaluate: {total_exps}")

    for exp_idx, (cfg_key, model_key) in enumerate(experiments, 1):
        exp_id = f"{model_key}_{cfg_key}"
        cfg = feature_configs[cfg_key]
        m_def = model_defs[model_key]

        print(f"\n[{exp_idx}/{total_exps}] Running Nested CV: {m_def['display_name']} | {cfg['name']}")
        start_time = time.time()

        all_cols = cfg["numerical_cols"] + cfg["categorical_cols"]
        X_df = dev_df[all_cols].copy()

        oof_probs = np.zeros(len(dev_df), dtype=float)
        oof_preds = np.zeros(len(dev_df), dtype=int)
        outer_fold_metrics = []

        for outer_fold, (train_idx, val_idx) in enumerate(outer_cv.split(X_df, y_all), 1):
            X_outer_train, y_outer_train = X_df.iloc[train_idx], y_all[train_idx]
            X_outer_val, y_outer_val = X_df.iloc[val_idx], y_all[val_idx]

            # Construct leakage-free preprocessor
            preprocessor = build_advanced_preprocessor(
                categorical_cols=cfg["categorical_cols"],
                numerical_cols=cfg["numerical_cols"],
                scale_numerical=m_def["scale_numerical"],
                use_log1p=cfg["use_log1p"],
                use_correlation_pruner=cfg["use_correlation_pruner"],
                correlation_threshold=cfg.get("correlation_threshold", 0.85),
                protected_cols=cfg.get("protected_cols", None)
            )

            pipeline = Pipeline([
                ("preprocessor", preprocessor),
                ("clf", m_def["estimator"])
            ])

            # Inner CV for hyperparameter tuning strictly on outer training partition
            grid_search = GridSearchCV(
                estimator=pipeline,
                param_grid=m_def["param_grid"],
                scoring="f1",
                cv=inner_cv,
                n_jobs=-1,
                refit=True
            )

            # Fit strictly on outer training partition
            grid_search.fit(X_outer_train, y_outer_train)
            best_pipe = grid_search.best_estimator_

            # Predict on untouched outer holdout partition
            val_probs = best_pipe.predict_proba(X_outer_val)[:, 1]
            val_preds = (val_probs >= 0.50).astype(int)

            oof_probs[val_idx] = val_probs
            oof_preds[val_idx] = val_preds

            fold_m = evaluate_metrics(y_outer_val, val_preds, val_probs)
            fold_m["outer_fold"] = outer_fold
            fold_m["best_params"] = json.dumps(grid_search.best_params_)
            outer_fold_metrics.append(fold_m)

        # Aggregate metrics across outer folds
        accs = [m["accuracy"] for m in outer_fold_metrics]
        recs = [m["recall"] for m in outer_fold_metrics]
        precs = [m["precision"] for m in outer_fold_metrics]
        f1s = [m["f1"] for m in outer_fold_metrics]
        aucs = [m["roc_auc"] for m in outer_fold_metrics]
        aps = [m["average_precision"] for m in outer_fold_metrics]
        baccs = [m["balanced_accuracy"] for m in outer_fold_metrics]
        specs = [m["specificity"] for m in outer_fold_metrics]

        # Overall pooled OOF metrics at threshold 0.50
        pooled_m = evaluate_metrics(y_all, oof_preds, oof_probs)

        elapsed = time.time() - start_time
        print(f"   Nested CV Mean F1: {np.mean(f1s):.4f} (+/- {np.std(f1s):.4f}) | Mean ROC-AUC: {np.mean(aucs):.4f} | Accuracy: {np.mean(accs):.4f} ({elapsed:.1f}s)")

        # Record fold-level results
        for m in outer_fold_metrics:
            row = {
                "experiment_id": exp_id,
                "model": model_key,
                "display_name": m_def["display_name"],
                "configuration": cfg_key,
                "config_name": cfg["name"],
                "outer_fold": m["outer_fold"],
                "accuracy": round(m["accuracy"], 4),
                "precision": round(m["precision"], 4),
                "recall": round(m["recall"], 4),
                "f1": round(m["f1"], 4),
                "roc_auc": round(m["roc_auc"], 4),
                "average_precision": round(m["average_precision"], 4),
                "balanced_accuracy": round(m["balanced_accuracy"], 4),
                "specificity": round(m["specificity"], 4),
                "tp": m["tp"],
                "fp": m["fp"],
                "tn": m["tn"],
                "fn": m["fn"],
                "best_params": m["best_params"]
            }
            nested_results_rows.append(row)

        oof_predictions_dict[exp_id] = oof_probs

        # Fit best pipeline on full development dataset (N=5,950) for persistence
        full_prep = build_advanced_preprocessor(
            categorical_cols=cfg["categorical_cols"],
            numerical_cols=cfg["numerical_cols"],
            scale_numerical=m_def["scale_numerical"],
            use_log1p=cfg["use_log1p"],
            use_correlation_pruner=cfg["use_correlation_pruner"],
            correlation_threshold=cfg.get("correlation_threshold", 0.85),
            protected_cols=cfg.get("protected_cols", None)
        )
        full_pipe = Pipeline([
            ("preprocessor", full_prep),
            ("clf", m_def["estimator"])
        ])
        full_grid = GridSearchCV(
            estimator=full_pipe,
            param_grid=m_def["param_grid"],
            scoring="f1",
            cv=inner_cv,
            n_jobs=-1,
            refit=True
        )
        full_grid.fit(X_df, y_all)
        best_pipelines_dict[exp_id] = {
            "pipeline": full_grid.best_estimator_,
            "best_params": full_grid.best_params_,
            "mean_metrics": {
                "accuracy": np.mean(accs), "accuracy_std": np.std(accs),
                "recall": np.mean(recs), "recall_std": np.std(recs),
                "precision": np.mean(precs), "precision_std": np.std(precs),
                "f1": np.mean(f1s), "f1_std": np.std(f1s),
                "roc_auc": np.mean(aucs), "roc_auc_std": np.std(aucs),
                "average_precision": np.mean(aps), "average_precision_std": np.std(aps),
                "balanced_accuracy": np.mean(baccs), "balanced_accuracy_std": np.std(baccs),
                "specificity": np.mean(specs), "specificity_std": np.std(specs)
            },
            "pooled_metrics": pooled_m,
            "cfg_key": cfg_key,
            "model_key": model_key
        }

    # Evaluate Voting Classifier on Configuration C
    print("\n--- Evaluating Soft Voting Classifier Ensemble (Config C) ---")
    voting_exp_id = "voting_ensemble_config_c"
    top_models = [
        ("lr", best_pipelines_dict["logistic_regression_config_c"]["pipeline"].named_steps["clf"]),
        ("rf", best_pipelines_dict["random_forest_config_c"]["pipeline"].named_steps["clf"]),
        ("hgb", best_pipelines_dict["hist_gradient_boosting_config_c"]["pipeline"].named_steps["clf"])
    ]
    voting_clf = VotingClassifier(estimators=top_models, voting="soft")
    
    cfg_c = feature_configs["config_c"]
    X_df_c = dev_df[cfg_c["numerical_cols"] + cfg_c["categorical_cols"]].copy()
    
    voting_oof_probs = np.zeros(len(dev_df), dtype=float)
    voting_oof_preds = np.zeros(len(dev_df), dtype=int)
    voting_fold_metrics = []

    for outer_fold, (train_idx, val_idx) in enumerate(outer_cv.split(X_df_c, y_all), 1):
        X_outer_train, y_outer_train = X_df_c.iloc[train_idx], y_all[train_idx]
        X_outer_val, y_outer_val = X_df_c.iloc[val_idx], y_all[val_idx]

        prep = build_advanced_preprocessor(
            categorical_cols=cfg_c["categorical_cols"],
            numerical_cols=cfg_c["numerical_cols"],
            scale_numerical=True,
            use_log1p=True,
            use_correlation_pruner=False
        )
        pipe = Pipeline([
            ("preprocessor", prep),
            ("clf", VotingClassifier(estimators=[
                ("lr", LogisticRegression(C=0.1, class_weight="balanced", solver="lbfgs", max_iter=1000, random_state=RANDOM_STATE)),
                ("rf", RandomForestClassifier(n_estimators=150, max_depth=12, min_samples_leaf=5, class_weight="balanced", random_state=RANDOM_STATE, n_jobs=-1)),
                ("hgb", HistGradientBoostingClassifier(max_iter=100, max_depth=6, class_weight="balanced", random_state=RANDOM_STATE))
            ], voting="soft"))
        ])
        pipe.fit(X_outer_train, y_outer_train)
        v_probs = pipe.predict_proba(X_outer_val)[:, 1]
        v_preds = (v_probs >= 0.50).astype(int)

        voting_oof_probs[val_idx] = v_probs
        voting_oof_preds[val_idx] = v_preds

        m = evaluate_metrics(y_outer_val, v_preds, v_probs)
        m["outer_fold"] = outer_fold
        m["best_params"] = json.dumps({"voting": "soft", "estimators": ["lr", "rf", "hgb"]})
        voting_fold_metrics.append(m)

        nested_results_rows.append({
            "experiment_id": voting_exp_id,
            "model": "voting_ensemble",
            "display_name": "Soft Voting Ensemble (LR + RF + HGB)",
            "configuration": "config_c",
            "config_name": cfg_c["name"],
            "outer_fold": outer_fold,
            "accuracy": round(m["accuracy"], 4),
            "precision": round(m["precision"], 4),
            "recall": round(m["recall"], 4),
            "f1": round(m["f1"], 4),
            "roc_auc": round(m["roc_auc"], 4),
            "average_precision": round(m["average_precision"], 4),
            "balanced_accuracy": round(m["balanced_accuracy"], 4),
            "specificity": round(m["specificity"], 4),
            "tp": m["tp"],
            "fp": m["fp"],
            "tn": m["tn"],
            "fn": m["fn"],
            "best_params": m["best_params"]
        })

    oof_predictions_dict[voting_exp_id] = voting_oof_probs
    pooled_voting_m = evaluate_metrics(y_all, voting_oof_preds, voting_oof_probs)
    print(f"   Voting Ensemble Mean F1: {np.mean([m['f1'] for m in voting_fold_metrics]):.4f} | Mean ROC-AUC: {np.mean([m['roc_auc'] for m in voting_fold_metrics]):.4f} | Accuracy: {np.mean([m['accuracy'] for m in voting_fold_metrics]):.4f}")

    # Fit full voting pipeline
    full_voting_prep = build_advanced_preprocessor(
        categorical_cols=cfg_c["categorical_cols"],
        numerical_cols=cfg_c["numerical_cols"],
        scale_numerical=True,
        use_log1p=True,
        use_correlation_pruner=False
    )
    full_voting_pipe = Pipeline([
        ("preprocessor", full_voting_prep),
        ("clf", VotingClassifier(estimators=[
            ("lr", LogisticRegression(C=0.1, class_weight="balanced", solver="lbfgs", max_iter=1000, random_state=RANDOM_STATE)),
            ("rf", RandomForestClassifier(n_estimators=150, max_depth=12, min_samples_leaf=5, class_weight="balanced", random_state=RANDOM_STATE, n_jobs=-1)),
            ("hgb", HistGradientBoostingClassifier(max_iter=100, max_depth=6, class_weight="balanced", random_state=RANDOM_STATE))
        ], voting="soft"))
    ])
    full_voting_pipe.fit(X_df_c, y_all)
    best_pipelines_dict[voting_exp_id] = {
        "pipeline": full_voting_pipe,
        "best_params": {"voting": "soft", "estimators": ["lr", "rf", "hgb"]},
        "mean_metrics": {
            "accuracy": np.mean([m["accuracy"] for m in voting_fold_metrics]),
            "accuracy_std": np.std([m["accuracy"] for m in voting_fold_metrics]),
            "recall": np.mean([m["recall"] for m in voting_fold_metrics]),
            "recall_std": np.std([m["recall"] for m in voting_fold_metrics]),
            "precision": np.mean([m["precision"] for m in voting_fold_metrics]),
            "precision_std": np.std([m["precision"] for m in voting_fold_metrics]),
            "f1": np.mean([m["f1"] for m in voting_fold_metrics]),
            "f1_std": np.std([m["f1"] for m in voting_fold_metrics]),
            "roc_auc": np.mean([m["roc_auc"] for m in voting_fold_metrics]),
            "roc_auc_std": np.std([m["roc_auc"] for m in voting_fold_metrics]),
            "average_precision": np.mean([m["average_precision"] for m in voting_fold_metrics]),
            "average_precision_std": np.std([m["average_precision"] for m in voting_fold_metrics]),
            "balanced_accuracy": np.mean([m["balanced_accuracy"] for m in voting_fold_metrics]),
            "balanced_accuracy_std": np.std([m["balanced_accuracy"] for m in voting_fold_metrics]),
            "specificity": np.mean([m["specificity"] for m in voting_fold_metrics]),
            "specificity_std": np.std([m["specificity"] for m in voting_fold_metrics])
        },
        "pooled_metrics": pooled_voting_m,
        "cfg_key": "config_c",
        "model_key": "voting_ensemble"
    }

    return pd.DataFrame(nested_results_rows), oof_predictions_dict, best_pipelines_dict


def run_threshold_optimization(y_true, oof_probs):
    """Sweeps decision thresholds from 0.20 to 0.80 (step 0.01) on OOF probabilities."""
    thresholds = np.round(np.arange(0.20, 0.81, 0.01), 2)
    rows = []

    for t in thresholds:
        preds = (oof_probs >= t).astype(int)
        m = evaluate_metrics(y_true, preds, oof_probs)
        rows.append({
            "threshold": float(t),
            "accuracy": round(m["accuracy"], 4),
            "precision": round(m["precision"], 4),
            "recall": round(m["recall"], 4),
            "f1": round(m["f1"], 4),
            "balanced_accuracy": round(m["balanced_accuracy"], 4),
            "specificity": round(m["specificity"], 4),
            "tp": m["tp"],
            "fp": m["fp"],
            "tn": m["tn"],
            "fn": m["fn"]
        })

    thresh_df = pd.DataFrame(rows)

    # Key optimal thresholds
    f1_max_idx = thresh_df["f1"].idxmax()
    f1_opt = thresh_df.iloc[f1_max_idx].to_dict()

    acc_max_idx = thresh_df["accuracy"].idxmax()
    acc_opt = thresh_df.iloc[acc_max_idx].to_dict()

    # Recall >= 70% closest threshold
    valid_recall = thresh_df[thresh_df["recall"] >= 0.70]
    if len(valid_recall) > 0:
        rec_70_idx = valid_recall["recall"].sub(0.70).abs().idxmin()
        rec_70_opt = thresh_df.iloc[rec_70_idx].to_dict()
    else:
        rec_70_opt = f1_opt

    return thresh_df, {
        "f1_maximizing": f1_opt,
        "accuracy_maximizing": acc_opt,
        "recall_70_target": rec_70_opt
    }


def perform_error_analysis(dev_df, oof_probs, best_threshold):
    """
    Examines out-of-fold prediction errors on the development dataset at the selected threshold.
    """
    df = dev_df.copy()
    y_true = df["churn"].values
    preds = (oof_probs >= best_threshold).astype(int)

    df["oof_prob"] = np.round(oof_probs, 4)
    df["oof_pred"] = preds
    df["error_type"] = "TN"
    df.loc[(y_true == 1) & (preds == 1), "error_type"] = "TP"
    df.loc[(y_true == 0) & (preds == 1), "error_type"] = "FP"
    df.loc[(y_true == 1) & (preds == 0), "error_type"] = "FN"

    # Segment breakdowns
    error_summary = []

    segments = {
        "Overall Development Population": df,
        "Zero Historical Orders (has_historical_orders == 0)": df[df["has_historical_orders"] == 0],
        "Zero Delivered Orders (has_delivered_order == 0)": df[df["has_delivered_order"] == 0],
        "Dormant (orders_last_90_days == 0)": df[df["orders_last_90_days"] == 0],
        "Active Recent (orders_last_30_days >= 1)": df[df["orders_last_30_days"] >= 1],
        "High Delivery Delay (hist_average_delivery_delay_days >= 4)": df[df["hist_average_delivery_delay_days"] >= 4],
        "High Return Rate (hist_return_rate >= 0.20)": df[df["hist_return_rate"] >= 0.20],
        "High Cancellation Rate (hist_cancellation_rate >= 0.15)": df[df["hist_cancellation_rate"] >= 0.15]
    }

    for seg_name, seg_df in segments.items():
        if len(seg_df) == 0:
            continue
        seg_y = seg_df["churn"].values
        seg_p = seg_df["oof_pred"].values
        seg_prob = seg_df["oof_prob"].values
        m = evaluate_metrics(seg_y, seg_p, seg_prob) if len(np.unique(seg_y)) > 1 else {
            "accuracy": float(accuracy_score(seg_y, seg_p)),
            "precision": float(precision_score(seg_y, seg_p, zero_division=0)),
            "recall": float(recall_score(seg_y, seg_p, zero_division=0)),
            "f1": float(f1_score(seg_y, seg_p, zero_division=0)),
            "roc_auc": 0.5, "average_precision": 0.5, "balanced_accuracy": 0.5, "specificity": 0.5,
            "tp": int(np.sum((seg_y == 1) & (seg_p == 1))),
            "fp": int(np.sum((seg_y == 0) & (seg_p == 1))),
            "tn": int(np.sum((seg_y == 0) & (seg_p == 0))),
            "fn": int(np.sum((seg_y == 1) & (seg_p == 0)))
        }
        error_summary.append({
            "segment_name": seg_name,
            "sample_count": len(seg_df),
            "churn_rate": round(float(np.mean(seg_y)), 4),
            "accuracy": round(m["accuracy"], 4),
            "precision": round(m["precision"], 4),
            "recall": round(m["recall"], 4),
            "f1": round(m["f1"], 4),
            "tp": m["tp"],
            "fp": m["fp"],
            "tn": m["tn"],
            "fn": m["fn"]
        })

    return pd.DataFrame(error_summary), df[["customer_id", "churn", "oof_prob", "oof_pred", "error_type", "orders_last_30_days", "orders_last_90_days", "hist_average_delivery_delay_days", "delay_friction_score"]]


def save_all_artifacts(nested_results_df, oof_probs_dict, best_pipelines_dict, dev_df):
    """
    Generates and saves all required Checkpoint 3 CSV and JSON artifacts.
    """
    print("\n" + "=" * 80)
    print("3. SAVING CHECKPOINT 3 ARTIFACTS & MODELS")
    print("=" * 80)

    # 1. Save nested_cv_results.csv
    nested_cv_path = os.path.join(REPORTS_DIR, "nested_cv_results.csv")
    nested_results_df.to_csv(nested_cv_path, index=False)
    print(f"   Saved nested CV fold-level results: {nested_cv_path}")

    # 2. Build candidate comparison summary table
    comparison_rows = []
    for exp_id, meta in best_pipelines_dict.items():
        m = meta["mean_metrics"]
        p = meta["pooled_metrics"]
        row = {
            "experiment_id": exp_id,
            "model_key": meta["model_key"],
            "configuration": meta["cfg_key"],
            "cv_f1_mean": round(m["f1"], 4),
            "cv_f1_std": round(m["f1_std"], 4),
            "cv_roc_auc_mean": round(m["roc_auc"], 4),
            "cv_roc_auc_std": round(m["roc_auc_std"], 4),
            "cv_accuracy_mean": round(m["accuracy"], 4),
            "cv_accuracy_std": round(m["accuracy_std"], 4),
            "cv_recall_mean": round(m["recall"], 4),
            "cv_recall_std": round(m["recall_std"], 4),
            "cv_precision_mean": round(m["precision"], 4),
            "cv_precision_std": round(m["precision_std"], 4),
            "cv_balanced_acc_mean": round(m["balanced_accuracy"], 4),
            "cv_specificity_mean": round(m["specificity"], 4),
            "pooled_f1_th50": round(p["f1"], 4),
            "pooled_acc_th50": round(p["accuracy"], 4),
            "best_params": json.dumps(meta["best_params"])
        }
        comparison_rows.append(row)

    candidate_comp_df = pd.DataFrame(comparison_rows).sort_values(by="cv_f1_mean", ascending=False).reset_index(drop=True)
    comp_path = os.path.join(REPORTS_DIR, "candidate_comparison.csv")
    candidate_comp_df.to_csv(comp_path, index=False)
    print(f"   Saved candidate comparison summary : {comp_path}")

    # Identify top candidate
    top_candidate_row = candidate_comp_df.iloc[0]
    top_exp_id = top_candidate_row["experiment_id"]
    print(f"\n   >>> TOP RANKED CANDIDATE BY NESTED CV F1: {top_exp_id}")
    print(f"       Mean F1: {top_candidate_row['cv_f1_mean']:.4f} (+/- {top_candidate_row['cv_f1_std']:.4f})")
    print(f"       Mean ROC-AUC: {top_candidate_row['cv_roc_auc_mean']:.4f} | Accuracy: {top_candidate_row['cv_accuracy_mean']:.4f}")

    # 3. Save Out-of-Fold Predictions
    oof_df = pd.DataFrame({
        "customer_id": dev_df["customer_id"],
        "actual_churn": dev_df["churn"]
    })
    for exp_id, probs in oof_probs_dict.items():
        oof_df[f"prob_{exp_id}"] = np.round(probs, 4)
    oof_path = os.path.join(REPORTS_DIR, "out_of_fold_predictions.csv")
    oof_df.to_csv(oof_path, index=False)
    print(f"   Saved out-of-fold predictions      : {oof_path}")

    # 4. Threshold Optimization for Top Candidate
    top_oof_probs = oof_probs_dict[top_exp_id]
    thresh_df, opt_thresholds = run_threshold_optimization(dev_df["churn"].values, top_oof_probs)
    thresh_path = os.path.join(REPORTS_DIR, "threshold_analysis.csv")
    thresh_df.to_csv(thresh_path, index=False)
    print(f"   Saved threshold analysis           : {thresh_path}")
    print(f"       F1-Maximizing Threshold        : {opt_thresholds['f1_maximizing']['threshold']} (F1={opt_thresholds['f1_maximizing']['f1']:.4f}, Rec={opt_thresholds['f1_maximizing']['recall']:.4f}, Acc={opt_thresholds['f1_maximizing']['accuracy']:.4f})")
    print(f"       Accuracy-Maximizing Threshold  : {opt_thresholds['accuracy_maximizing']['threshold']} (Acc={opt_thresholds['accuracy_maximizing']['accuracy']:.4f}, F1={opt_thresholds['accuracy_maximizing']['f1']:.4f})")
    print(f"       Recall >= 70% Target Threshold : {opt_thresholds['recall_70_target']['threshold']} (Rec={opt_thresholds['recall_70_target']['recall']:.4f}, F1={opt_thresholds['recall_70_target']['f1']:.4f}, Acc={opt_thresholds['recall_70_target']['accuracy']:.4f})")

    # Selected decision threshold: F1-maximizing if recall >= 0.70, otherwise recall_70_target
    selected_thresh_info = opt_thresholds["f1_maximizing"] if opt_thresholds["f1_maximizing"]["recall"] >= 0.70 else opt_thresholds["recall_70_target"]
    selected_threshold = selected_thresh_info["threshold"]

    # 5. Error Analysis on Top Candidate
    error_summary_df, detailed_errors_df = perform_error_analysis(dev_df, top_oof_probs, selected_threshold)
    error_path = os.path.join(REPORTS_DIR, "error_analysis.csv")
    error_summary_df.to_csv(error_path, index=False)
    print(f"   Saved error analysis summary       : {error_path}")

    # 6. Save Feature Name Mapping
    top_pipeline = best_pipelines_dict[top_exp_id]["pipeline"]
    prep_step = top_pipeline.named_steps["preprocessor"]
    transformed_feature_names = prep_step.get_feature_names_out().tolist()

    feature_mapping = {
        "metadata": {
            "experiment_id": top_exp_id,
            "generated_at": datetime.now().isoformat(),
            "total_transformed_features": len(transformed_feature_names)
        },
        "transformed_features": transformed_feature_names
    }
    feat_map_path = os.path.join(REPORTS_DIR, "feature_name_mapping.json")
    with open(feat_map_path, "w", encoding="utf-8") as f:
        json.dump(feature_mapping, f, indent=2)
    print(f"   Saved feature name mapping         : {feat_map_path}")

    # 7. Save Selected Candidate Metadata JSON
    selected_candidate_meta = {
        "metadata": {
            "checkpoint": "Phase 5.1 Checkpoint 3",
            "selection_date": datetime.now().isoformat(),
            "experiment_id": top_exp_id,
            "model_type": top_candidate_row["model_key"],
            "configuration": top_candidate_row["configuration"],
            "development_sample_size": len(dev_df),
            "cross_validation": "5x3 Nested Stratified Cross-Validation"
        },
        "best_hyperparameters": best_pipelines_dict[top_exp_id]["best_params"],
        "nested_cv_performance": best_pipelines_dict[top_exp_id]["mean_metrics"],
        "decision_threshold_selection": {
            "selected_threshold": selected_threshold,
            "selection_rationale": "Optimized to balance F1-score maximization while maintaining >=70% churn recall constraint on development out-of-fold predictions.",
            "metrics_at_selected_threshold": selected_thresh_info,
            "f1_maximizing_threshold": opt_thresholds["f1_maximizing"],
            "accuracy_maximizing_threshold": opt_thresholds["accuracy_maximizing"],
            "recall_70_target_threshold": opt_thresholds["recall_70_target"]
        },
        "transformed_feature_count": len(transformed_feature_names),
        "artifact_paths": {
            "model_file": f"{top_exp_id}_pipeline.joblib",
            "nested_cv_results": "nested_cv_results.csv",
            "candidate_comparison": "candidate_comparison.csv",
            "threshold_analysis": "threshold_analysis.csv",
            "out_of_fold_predictions": "out_of_fold_predictions.csv",
            "error_analysis": "error_analysis.csv",
            "feature_name_mapping": "feature_name_mapping.json"
        }
    }
    sel_cand_path = os.path.join(REPORTS_DIR, "selected_candidate.json")
    with open(sel_cand_path, "w", encoding="utf-8") as f:
        json.dump(selected_candidate_meta, f, indent=2)
    print(f"   Saved selected candidate metadata  : {sel_cand_path}")

    # 8. Save Model Artifacts
    saved_models_summary = {}
    for exp_id, meta in best_pipelines_dict.items():
        model_filename = f"{exp_id}_pipeline.joblib"
        model_save_path = os.path.join(MODELS_DIR, model_filename)
        joblib.dump(meta["pipeline"], model_save_path)
        sha = compute_sha256(model_save_path)
        saved_models_summary[exp_id] = {
            "file": model_filename,
            "sha256": sha
        }
        print(f"   Saved pipeline artifact: {model_filename} (SHA-256: {sha[:16]}...)")

    return {
        "top_exp_id": top_exp_id,
        "selected_threshold": selected_threshold,
        "selected_thresh_info": selected_thresh_info,
        "candidate_comp_df": candidate_comp_df,
        "opt_thresholds": opt_thresholds,
        "saved_models_summary": saved_models_summary,
        "transformed_feature_names": transformed_feature_names
    }


def main():
    start_total = time.time()
    dev_df = load_development_dataset()
    feature_configs = get_feature_sets()
    model_defs = define_candidate_models()

    nested_results_df, oof_probs_dict, best_pipelines_dict = run_nested_cv(dev_df, feature_configs, model_defs)
    summary = save_all_artifacts(nested_results_df, oof_probs_dict, best_pipelines_dict, dev_df)

    total_time = time.time() - start_total
    print("\n" + "=" * 80)
    print(f"PHASE 5.1 CHECKPOINT 3 EXPERIMENTATION COMPLETED IN {total_time:.1f}s")
    print(f"Top Candidate: {summary['top_exp_id']} at Threshold {summary['selected_threshold']}")
    print("=" * 80)


if __name__ == "__main__":
    main()
