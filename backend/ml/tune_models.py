"""
Indian E-Commerce Customer Retention Intelligence System
Module: Phase 5 — Checkpoint 4: Controlled Training-Only Hyperparameter Optimization
Description: Conducts controlled hyperparameter tuning exclusively on training.csv (N=4,900)
             using 5-Fold Stratified Cross-Validation (random_state=42).
             Tunes all eight model combinations, fits best pipelines on full training data,
             saves tuned artifacts to models/phase5/tuned/, and evaluates on validation.csv.

Author: BCA (AI & ML) Project Team
"""

import os
import sys
import json
import time
import datetime
import pandas as pd
import numpy as np
import joblib

import sklearn
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.linear_model import LogisticRegression
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.model_selection import StratifiedKFold, GridSearchCV, RandomizedSearchCV, cross_validate
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    roc_auc_score, average_precision_score, balanced_accuracy_score,
    confusion_matrix
)

# Ensure project root and backend/ml are on sys.path
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "..", ".."))
sys.path.insert(0, SCRIPT_DIR)
sys.path.insert(0, PROJECT_ROOT)

from train_models import build_preprocessor

# Path configuration
TRAIN_PATH = os.path.join("data", "modeling", "train.csv")
VAL_PATH = os.path.join("data", "modeling", "validation.csv")
FEATURE_COLUMNS_PATH = os.path.join("data", "modeling", "feature_columns.json")
SPLIT_MANIFEST_PATH = os.path.join("data", "modeling", "split_manifest.json")

TUNED_MODELS_DIR = os.path.join("models", "phase5", "tuned")
REPORTS_DIR = os.path.join("reports", "phase5")

TUNED_CV_RESULTS_PATH = os.path.join(REPORTS_DIR, "tuned_cv_results.csv")
TUNED_VAL_RESULTS_PATH = os.path.join(REPORTS_DIR, "tuned_validation_results.csv")
SEARCH_MANIFEST_PATH = os.path.join(REPORTS_DIR, "hyperparameter_search_manifest.json")

RANDOM_STATE = 42
CV_FOLDS = 5


def get_search_spaces():
    """Returns the hyperparameter tuning configurations for all four algorithms."""
    return {
        "logistic_regression": {
            "display_name": "Logistic Regression",
            "needs_scaling": True,
            "search_type": "grid",
            "param_grid": {
                "classifier__C": [0.01, 0.1, 1.0, 10.0, 100.0],
                "classifier__class_weight": [None, "balanced"],
                "classifier__solver": ["lbfgs"],
                "classifier__max_iter": [2000],
                "classifier__random_state": [RANDOM_STATE]
            },
            "base_estimator": LogisticRegression()
        },
        "decision_tree": {
            "display_name": "Decision Tree",
            "needs_scaling": False,
            "search_type": "grid",
            "param_grid": {
                "classifier__max_depth": [4, 6, 8, 10],
                "classifier__min_samples_split": [5, 10, 20],
                "classifier__min_samples_leaf": [2, 5, 10],
                "classifier__criterion": ["gini", "entropy"],
                "classifier__random_state": [RANDOM_STATE]
            },
            "base_estimator": DecisionTreeClassifier()
        },
        "random_forest": {
            "display_name": "Random Forest",
            "needs_scaling": False,
            "search_type": "randomized",
            "n_iter": 15,
            "param_distributions": {
                "classifier__n_estimators": [200, 300, 400],
                "classifier__max_depth": [None, 10, 15, 20],
                "classifier__min_samples_split": [2, 5, 10],
                "classifier__min_samples_leaf": [1, 2, 4],
                "classifier__max_features": ["sqrt", "log2"],
                "classifier__class_weight": [None, "balanced"],
                "classifier__random_state": [RANDOM_STATE]
            },
            "base_estimator": RandomForestClassifier(n_jobs=-1)
        },
        "gradient_boosting": {
            "display_name": "Gradient Boosting",
            "needs_scaling": False,
            "search_type": "randomized",
            "n_iter": 15,
            "param_distributions": {
                "classifier__n_estimators": [100, 150, 200, 250],
                "classifier__learning_rate": [0.03, 0.05, 0.08, 0.10],
                "classifier__max_depth": [2, 3, 4],
                "classifier__min_samples_split": [5, 10, 15],
                "classifier__min_samples_leaf": [2, 3, 5, 10],
                "classifier__random_state": [RANDOM_STATE]
            },
            "base_estimator": GradientBoostingClassifier()
        }
    }


def tune_and_evaluate():
    print("=" * 80)
    print("PHASE 5: CHECKPOINT 4 — CONTROLLED HYPERPARAMETER OPTIMIZATION (TRAINING DATA ONLY)")
    print("=" * 80)

    os.makedirs(TUNED_MODELS_DIR, exist_ok=True)
    os.makedirs(REPORTS_DIR, exist_ok=True)

    # 1. Load training dataset
    print(f"\n1. Loading training dataset from: {TRAIN_PATH}")
    df_train = pd.read_csv(TRAIN_PATH)
    n_train = len(df_train)
    assert n_train == 4900, f"Expected 4,900 training records, got {n_train}"
    y_train = df_train["churn"]

    # 2. Load validation dataset
    print(f"2. Loading validation dataset from: {VAL_PATH}")
    df_val = pd.read_csv(VAL_PATH)
    n_val = len(df_val)
    assert n_val == 1050, f"Expected 1,050 validation records, got {n_val}"
    y_val = df_val["churn"].values

    # 3. Load feature specifications
    print(f"3. Loading feature allowlist specifications from: {FEATURE_COLUMNS_PATH}")
    with open(FEATURE_COLUMNS_PATH, "r", encoding="utf-8") as f:
        fmeta = json.load(f)

    cfg_a_cols = fmeta["configuration_a"]["features_ordered"]
    cfg_a_cat = fmeta["configuration_a"]["categorical_features"]
    cfg_a_num = fmeta["configuration_a"]["numerical_features"]

    cfg_b_cols = fmeta["configuration_b"]["features_ordered"]
    cfg_b_cat = fmeta["configuration_b"]["categorical_features"]
    cfg_b_num = fmeta["configuration_b"]["numerical_features"]

    configs = {
        "config_a": {
            "name": "Configuration A (Baseline 36 Features)",
            "feature_cols": cfg_a_cols,
            "cat_cols": cfg_a_cat,
            "num_cols": cfg_a_num,
            "feature_count": 36
        },
        "config_b": {
            "name": "Configuration B (36 Features + RFM cluster_id)",
            "feature_cols": cfg_b_cols,
            "cat_cols": cfg_b_cat,
            "num_cols": cfg_b_num,
            "feature_count": 37
        }
    }

    cv = StratifiedKFold(n_splits=CV_FOLDS, shuffle=True, random_state=RANDOM_STATE)
    search_spaces = get_search_spaces()

    search_manifest = {}
    cv_summary_records = []
    val_summary_records = []

    print(f"\n4. Beginning controlled 5-fold cross-validation tuning on training data...")
    print("-" * 80)

    comb_idx = 1
    for m_key, m_info in search_spaces.items():
        for c_key, c_info in configs.items():
            comb_name = f"{m_info['display_name']} [{c_info['name']}]"
            artifact_name = f"{m_key}_{c_key}_tuned.joblib"
            artifact_path = os.path.join(TUNED_MODELS_DIR, artifact_name)

            print(f"\n[{comb_idx}/8] Tuning: {comb_name}")
            print(f"      Search Type: {m_info['search_type'].upper()} | Optimization Metric: F1-Score (Positive=1)")

            # Build pipeline
            preprocessor = build_preprocessor(
                categorical_cols=c_info["cat_cols"],
                numerical_cols=c_info["num_cols"],
                scale_numerical=m_info["needs_scaling"]
            )
            base_pipeline = Pipeline([
                ("preprocessor", preprocessor),
                ("classifier", m_info["base_estimator"])
            ])

            X_train = df_train[c_info["feature_cols"]]

            # Execute search
            t_search_start = time.time()
            if m_info["search_type"] == "grid":
                search = GridSearchCV(
                    base_pipeline,
                    param_grid=m_info["param_grid"],
                    cv=cv,
                    scoring="f1",
                    n_jobs=-1,
                    refit=True
                )
            else:
                search = RandomizedSearchCV(
                    base_pipeline,
                    param_distributions=m_info["param_distributions"],
                    n_iter=m_info["n_iter"],
                    cv=cv,
                    scoring="f1",
                    n_jobs=-1 if m_key != "random_forest" else 1,
                    random_state=RANDOM_STATE,
                    refit=True
                )

            search.fit(X_train, y_train)
            search_duration = time.time() - t_search_start

            best_params = search.best_params_
            # Strip 'classifier__' prefix for cleaner reporting
            clean_best_params = {k.replace("classifier__", ""): v for k, v in best_params.items()}
            best_f1_cv = search.best_score_

            print(f"      Search Duration: {search_duration:.2f}s")
            print(f"      Best Training CV F1: {best_f1_cv:.4f}")
            print(f"      Best Hyperparameters: {clean_best_params}")

            # Refit best pipeline is automatic via refit=True
            best_pipeline = search.best_estimator_

            # Save tuned artifact
            joblib.dump(best_pipeline, artifact_path)
            file_size_kb = os.path.getsize(artifact_path) / 1024.0
            print(f"      Saved Tuned Artifact: {artifact_path} ({file_size_kb:.1f} KB)")

            # Run full 5-fold cross-validation on the best pipeline to compute all supporting metrics
            supporting_scoring = {
                "accuracy": "accuracy",
                "precision": "precision",
                "recall": "recall",
                "f1": "f1",
                "roc_auc": "roc_auc",
                "average_precision": "average_precision",
                "balanced_accuracy": "balanced_accuracy"
            }
            eval_cv = cross_validate(
                best_pipeline,
                X_train,
                y_train,
                cv=cv,
                scoring=supporting_scoring,
                return_train_score=False,
                n_jobs=-1 if m_key != "random_forest" else 1
            )

            cv_metrics_mean = {k.replace("test_", ""): round(float(np.mean(v)), 4) for k, v in eval_cv.items() if k.startswith("test_")}
            cv_metrics_std = {k.replace("test_", ""): round(float(np.std(v)), 4) for k, v in eval_cv.items() if k.startswith("test_")}

            cv_summary_records.append({
                "model_key": m_key,
                "model_name": m_info["display_name"],
                "config_key": c_key,
                "config_name": c_info["name"],
                "feature_count": c_info["feature_count"],
                "search_type": m_info["search_type"],
                "best_cv_f1": round(best_f1_cv, 4),
                "cv_accuracy_mean": cv_metrics_mean["accuracy"],
                "cv_accuracy_std": cv_metrics_std["accuracy"],
                "cv_precision_mean": cv_metrics_mean["precision"],
                "cv_precision_std": cv_metrics_std["precision"],
                "cv_recall_mean": cv_metrics_mean["recall"],
                "cv_recall_std": cv_metrics_std["recall"],
                "cv_f1_mean": cv_metrics_mean["f1"],
                "cv_f1_std": cv_metrics_std["f1"],
                "cv_roc_auc_mean": cv_metrics_mean["roc_auc"],
                "cv_roc_auc_std": cv_metrics_std["roc_auc"],
                "cv_pr_auc_mean": cv_metrics_mean["average_precision"],
                "cv_pr_auc_std": cv_metrics_std["average_precision"],
                "cv_balanced_accuracy_mean": cv_metrics_mean["balanced_accuracy"],
                "cv_balanced_accuracy_std": cv_metrics_std["balanced_accuracy"],
                "search_duration_sec": round(search_duration, 2),
                "best_parameters": json.dumps(clean_best_params)
            })

            # Evaluate tuned pipeline on validation.csv at default threshold 0.50
            X_val = df_val[c_info["feature_cols"]]
            pos_idx = list(best_pipeline.named_steps["classifier"].classes_).index(1)
            y_val_proba = best_pipeline.predict_proba(X_val)[:, pos_idx]
            y_val_pred = (y_val_proba >= 0.50).astype(int)

            val_acc = accuracy_score(y_val, y_val_pred)
            val_prec = precision_score(y_val, y_val_pred, zero_division=0)
            val_rec = recall_score(y_val, y_val_pred, zero_division=0)
            val_f1 = f1_score(y_val, y_val_pred, zero_division=0)
            val_auc = roc_auc_score(y_val, y_val_proba)
            val_pr_auc = average_precision_score(y_val, y_val_proba)
            val_bal_acc = balanced_accuracy_score(y_val, y_val_pred)
            tn, fp, fn, tp = confusion_matrix(y_val, y_val_pred).ravel()
            val_spec = tn / (tn + fp) if (tn + fp) > 0 else 0.0

            print(f"      Validation @ 0.50: Acc={val_acc:.4f} | Prec={val_prec:.4f} | Rec={val_rec:.4f} | F1={val_f1:.4f} | ROC-AUC={val_auc:.4f}")
            print(f"      Confusion Matrix: TP={tp}, FP={fp}, TN={tn}, FN={fn} | Specificity={val_spec:.4f}")

            val_summary_records.append({
                "model_key": m_key,
                "model_name": m_info["display_name"],
                "config_key": c_key,
                "config_name": c_info["name"],
                "feature_count": c_info["feature_count"],
                "threshold": 0.50,
                "accuracy": round(val_acc, 4),
                "precision": round(val_prec, 4),
                "recall": round(val_rec, 4),
                "f1_score": round(val_f1, 4),
                "roc_auc": round(val_auc, 4),
                "average_precision": round(val_pr_auc, 4),
                "balanced_accuracy": round(val_bal_acc, 4),
                "specificity": round(val_spec, 4),
                "true_positives": int(tp),
                "false_positives": int(fp),
                "true_negatives": int(tn),
                "false_negatives": int(fn),
                "best_hyperparameters": json.dumps(clean_best_params)
            })

            search_manifest[f"{m_key}_{c_key}"] = {
                "model_key": m_key,
                "model_name": m_info["display_name"],
                "config_key": c_key,
                "config_name": c_info["name"],
                "feature_count": c_info["feature_count"],
                "search_type": m_info["search_type"],
                "search_duration_sec": round(search_duration, 2),
                "best_cv_f1": round(best_f1_cv, 4),
                "best_parameters": clean_best_params,
                "cv_metrics_mean": cv_metrics_mean,
                "cv_metrics_std": cv_metrics_std,
                "validation_at_0_50": {
                    "accuracy": round(val_acc, 4),
                    "precision": round(val_prec, 4),
                    "recall": round(val_rec, 4),
                    "f1_score": round(val_f1, 4),
                    "roc_auc": round(val_auc, 4),
                    "average_precision": round(val_pr_auc, 4),
                    "balanced_accuracy": round(val_bal_acc, 4),
                    "specificity": round(val_spec, 4),
                    "confusion_matrix": {"tp": int(tp), "fp": int(fp), "tn": int(tn), "fn": int(fn)}
                },
                "artifact_path": artifact_path,
                "file_size_kb": round(file_size_kb, 1)
            }
            comb_idx += 1

    # Save tuned CV results
    df_cv_summary = pd.DataFrame(cv_summary_records)
    df_cv_summary.to_csv(TUNED_CV_RESULTS_PATH, index=False)
    print(f"\n5. Saved tuned CV summary to: {TUNED_CV_RESULTS_PATH}")

    # Save tuned validation results
    df_val_summary = pd.DataFrame(val_summary_records)
    df_val_summary.to_csv(TUNED_VAL_RESULTS_PATH, index=False)
    print(f"6. Saved tuned validation results to: {TUNED_VAL_RESULTS_PATH}")

    # Save search manifest
    full_manifest = {
        "metadata": {
            "title": "Phase 5 Checkpoint 4 Hyperparameter Search & Tuning Manifest",
            "generation_timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "training_dataset": TRAIN_PATH,
            "training_rows": n_train,
            "tuning_objective": "f1_score",
            "cross_validation": "5-fold StratifiedKFold (random_state=42)"
        },
        "search_results": search_manifest
    }
    with open(SEARCH_MANIFEST_PATH, "w", encoding="utf-8") as f:
        json.dump(full_manifest, f, indent=2)
    print(f"7. Saved hyperparameter search manifest to: {SEARCH_MANIFEST_PATH}")

    print("=" * 80)
    print("HYPERPARAMETER OPTIMIZATION COMPLETED SUCCESSFULLY!")
    print("=" * 80)


if __name__ == "__main__":
    tune_and_evaluate()
