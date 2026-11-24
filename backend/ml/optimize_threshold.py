"""
Indian E-Commerce Customer Retention Intelligence System
Module: Phase 5 — Checkpoint 4: Decision Threshold Selection & Model Optimization
Description: Sweeps decision thresholds (0.20 to 0.80, step 0.01) on the validation dataset
             across all 16 models (8 baseline + 8 tuned).
             Applies primary recall-constrained F1-maximization (Recall >= 0.70).
             Generates threshold curves, compares default vs optimal thresholds,
             and determines the final candidate model for Phase 5 Checkpoint 5.

Author: BCA (AI & ML) Project Team
"""

import os
import sys
import json
import numpy as np
import pandas as pd
import joblib

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

# Path configuration
VAL_PATH = os.path.join(PROJECT_ROOT, "data", "modeling", "validation.csv")
FEATURE_COLUMNS_PATH = os.path.join(PROJECT_ROOT, "data", "modeling", "feature_columns.json")
BASELINE_MODELS_DIR = os.path.join(PROJECT_ROOT, "models", "phase5")
TUNED_MODELS_DIR = os.path.join(PROJECT_ROOT, "models", "phase5", "tuned")
REPORTS_DIR = os.path.join(PROJECT_ROOT, "reports", "phase5")

THRESHOLD_RESULTS_PATH = os.path.join(REPORTS_DIR, "threshold_optimization_results.csv")
MODEL_SELECTION_PATH = os.path.join(REPORTS_DIR, "model_selection.json")
SEARCH_MANIFEST_PATH = os.path.join(REPORTS_DIR, "hyperparameter_search_manifest.json")

# Constants
RECALL_TARGET = 0.70
THRESHOLDS = np.round(np.arange(0.20, 0.801, 0.01), 2)


def get_model_registry():
    """Defines the 16 model pipelines to evaluate."""
    algorithms = [
        ("logistic_regression", "Logistic Regression"),
        ("decision_tree", "Decision Tree"),
        ("random_forest", "Random Forest"),
        ("gradient_boosting", "Gradient Boosting")
    ]
    configs = [
        ("config_a", "Configuration A (Baseline 36 Features)", "A"),
        ("config_b", "Configuration B (36 Features + RFM cluster_id)", "B")
    ]
    
    registry = []
    
    # Baseline models
    for algo_key, algo_name in algorithms:
        for cfg_key, cfg_name, cfg_letter in configs:
            model_id = f"{algo_key}_{cfg_key}_baseline"
            file_name = f"{algo_key}_{cfg_key}.joblib"
            file_path = os.path.join(BASELINE_MODELS_DIR, file_name)
            registry.append({
                "model_id": model_id,
                "model_type": "baseline",
                "algorithm_key": algo_key,
                "algorithm_name": algo_name,
                "config_key": cfg_key,
                "config_name": cfg_name,
                "config_letter": cfg_letter,
                "file_path": file_path
            })
            
    # Tuned models
    for algo_key, algo_name in algorithms:
        for cfg_key, cfg_name, cfg_letter in configs:
            model_id = f"{algo_key}_{cfg_key}_tuned"
            file_name = f"{algo_key}_{cfg_key}_tuned.joblib"
            file_path = os.path.join(TUNED_MODELS_DIR, file_name)
            registry.append({
                "model_id": model_id,
                "model_type": "tuned",
                "algorithm_key": algo_key,
                "algorithm_name": algo_name,
                "config_key": cfg_key,
                "config_name": cfg_name,
                "config_letter": cfg_letter,
                "file_path": file_path
            })
            
    return registry


def calculate_metrics_at_threshold(y_true, y_prob, threshold):
    """Calculates all evaluation metrics for a specific decision threshold."""
    y_pred = (y_prob >= threshold).astype(int)
    
    cm = confusion_matrix(y_true, y_pred, labels=[0, 1])
    tn, fp, fn, tp = cm.ravel()
    
    acc = accuracy_score(y_true, y_pred)
    prec = precision_score(y_true, y_pred, zero_division=0)
    rec = recall_score(y_true, y_pred, zero_division=0)
    f1 = f1_score(y_true, y_pred, zero_division=0)
    
    spec = tn / (tn + fp) if (tn + fp) > 0 else 0.0
    bal_acc = (rec + spec) / 2.0
    
    return {
        "threshold": float(threshold),
        "accuracy": round(float(acc), 4),
        "precision": round(float(prec), 4),
        "recall": round(float(rec), 4),
        "f1_score": round(float(f1), 4),
        "specificity": round(float(spec), 4),
        "balanced_accuracy": round(float(bal_acc), 4),
        "true_positives": int(tp),
        "false_positives": int(fp),
        "true_negatives": int(tn),
        "false_negatives": int(fn)
    }


def find_optimal_threshold(df_model_sweep, recall_target=RECALL_TARGET):
    """
    Finds the optimal decision threshold following the decision rules:
    1. Filter thresholds satisfying recall >= recall_target.
    2. Among these, select the threshold that maximizes F1-score.
    3. If no threshold reaches recall_target, select threshold maximizing F1 across all thresholds.
    4. Tie-breaking: higher recall, then higher specificity, then closest to 0.50.
    """
    eligible = df_model_sweep[df_model_sweep["recall"] >= recall_target]
    recall_satisfied = True
    
    if len(eligible) == 0:
        recall_satisfied = False
        candidates = df_model_sweep
    else:
        candidates = eligible
        
    # Sort candidates: F1 desc, recall desc, specificity desc, distance to 0.50 asc
    candidates = candidates.copy()
    candidates["dist_05"] = np.abs(candidates["threshold"] - 0.50)
    
    sorted_candidates = candidates.sort_values(
        by=["f1_score", "recall", "specificity", "dist_05"],
        ascending=[False, False, False, True]
    )
    
    best_row = sorted_candidates.iloc[0].to_dict()
    best_row["recall_constraint_satisfied"] = recall_satisfied
    return best_row


def run_threshold_optimization():
    print("=" * 80)
    print("PHASE 5: CHECKPOINT 4 — DECISION THRESHOLD SELECTION & MODEL OPTIMIZATION")
    print("=" * 80)
    
    # 1. Load validation dataset
    print(f"\n1. Loading validation dataset from: {VAL_PATH}")
    assert os.path.exists(VAL_PATH), f"Validation file not found: {VAL_PATH}"
    df_val = pd.read_csv(VAL_PATH)
    n_val = len(df_val)
    print(f"   Validation records: {n_val}")
    assert n_val == 1050, f"Expected 1,050 validation records, got {n_val}"
    
    y_val = df_val["churn"].values
    val_churn_count = int(np.sum(y_val == 1))
    val_non_churn_count = int(np.sum(y_val == 0))
    print(f"   Class balance: {val_churn_count} churners ({val_churn_count/n_val*100:.2f}%), "
          f"{val_non_churn_count} non-churners ({val_non_churn_count/n_val*100:.2f}%)")
          
    # 2. Load feature specifications
    print(f"2. Loading feature columns from: {FEATURE_COLUMNS_PATH}")
    with open(FEATURE_COLUMNS_PATH, "r", encoding="utf-8") as f:
        feature_spec = json.load(f)
    config_a_features = feature_spec["configuration_a"]["features_ordered"]
    config_b_features = feature_spec["configuration_b"]["features_ordered"]
    
    # 3. Load search manifest if available for hyperparameter documentation
    hyperparams_dict = {}
    if os.path.exists(SEARCH_MANIFEST_PATH):
        with open(SEARCH_MANIFEST_PATH, "r", encoding="utf-8") as f:
            manifest_data = json.load(f)
            for m_info in manifest_data.get("models_tuned", []):
                m_key = f"{m_info['model_key']}_{m_info['config_key']}_tuned"
                hyperparams_dict[m_key] = m_info.get("best_hyperparameters", {})
                
    # 4. Evaluate all 16 models across 61 thresholds
    registry = get_model_registry()
    print(f"3. Evaluating {len(registry)} models across {len(THRESHOLDS)} decision thresholds (0.20 to 0.80)...")
    
    all_sweep_records = []
    model_summaries = []
    
    for idx, model_info in enumerate(registry, 1):
        m_id = model_info["model_id"]
        f_path = model_info["file_path"]
        algo_name = model_info["algorithm_name"]
        cfg_letter = model_info["config_letter"]
        m_type = model_info["model_type"]
        
        print(f"\n   [{idx}/{len(registry)}] Processing: {m_id} ({algo_name} Config {cfg_letter} [{m_type}])")
        assert os.path.exists(f_path), f"Artifact not found: {f_path}"
        
        pipeline = joblib.load(f_path)
        
        # Select appropriate features
        features = config_a_features if model_info["config_key"] == "config_a" else config_b_features
        X_val = df_val[features]
        
        # Predict validation probabilities
        y_prob = pipeline.predict_proba(X_val)[:, 1]
        
        # Calculate threshold-independent metrics
        roc_auc = float(roc_auc_score(y_val, y_prob))
        avg_prec = float(average_precision_score(y_val, y_prob))
        
        # Threshold sweep
        model_rows = []
        for t in THRESHOLDS:
            metrics = calculate_metrics_at_threshold(y_val, y_prob, t)
            row = {
                "model_id": m_id,
                "model_type": m_type,
                "algorithm_key": model_info["algorithm_key"],
                "algorithm_name": algo_name,
                "config_key": model_info["config_key"],
                "config_name": model_info["config_name"],
                "config_letter": cfg_letter,
                "feature_count": len(features),
                "roc_auc": round(roc_auc, 4),
                "average_precision": round(avg_prec, 4),
                **metrics
            }
            all_sweep_records.append(row)
            model_rows.append(row)
            
        df_model_sweep = pd.DataFrame(model_rows)
        
        # Default metrics @ 0.50
        row_050 = df_model_sweep[df_model_sweep["threshold"] == 0.50].iloc[0].to_dict()
        
        # Optimal threshold under Recall >= 0.70 constraint
        optimal_row = find_optimal_threshold(df_model_sweep, recall_target=RECALL_TARGET)
        
        # Accuracy-maximizing threshold
        acc_max_row = df_model_sweep.sort_values(by=["accuracy", "f1_score"], ascending=[False, False]).iloc[0].to_dict()
        
        print(f"       ROC-AUC: {roc_auc:.4f} | PR-AUC: {avg_prec:.4f}")
        print(f"       @ 0.50 : Acc={row_050['accuracy']:.4f} | Prec={row_050['precision']:.4f} | Rec={row_050['recall']:.4f} | F1={row_050['f1_score']:.4f}")
        print(f"       Optimal: T={optimal_row['threshold']:.2f} | Acc={optimal_row['accuracy']:.4f} | Prec={optimal_row['precision']:.4f} | Rec={optimal_row['recall']:.4f} | F1={optimal_row['f1_score']:.4f} (Rec>=0.70: {optimal_row['recall_constraint_satisfied']})")
        print(f"       Max Acc: T={acc_max_row['threshold']:.2f} | Acc={acc_max_row['accuracy']:.4f} | Prec={acc_max_row['precision']:.4f} | Rec={acc_max_row['recall']:.4f} | F1={acc_max_row['f1_score']:.4f}")
        
        model_summaries.append({
            "model_id": m_id,
            "model_type": m_type,
            "algorithm_key": model_info["algorithm_key"],
            "algorithm_name": algo_name,
            "config_letter": cfg_letter,
            "config_key": model_info["config_key"],
            "roc_auc": roc_auc,
            "average_precision": avg_prec,
            "default_050": row_050,
            "optimal": optimal_row,
            "acc_max": acc_max_row,
            "hyperparameters": hyperparams_dict.get(m_id, "default")
        })
        
    # 5. Save comprehensive threshold sweep CSV
    df_all_sweeps = pd.DataFrame(all_sweep_records)
    df_all_sweeps.to_csv(THRESHOLD_RESULTS_PATH, index=False)
    print(f"\n4. Saved complete threshold sweep results to: {THRESHOLD_RESULTS_PATH}")
    print(f"   Total rows: {len(df_all_sweeps)} ({len(registry)} models x {len(THRESHOLDS)} thresholds)")
    
    # 6. Model Selection Analysis
    print("\n" + "=" * 80)
    print("MODEL SELECTION & COMPARATIVE ANALYSIS")
    print("=" * 80)
    
    # Sort summaries by: satisfies recall >= 0.70, optimal F1 desc, ROC-AUC desc
    sorted_models = sorted(
        model_summaries,
        key=lambda m: (
            m["optimal"]["recall_constraint_satisfied"],
            m["optimal"]["f1_score"],
            m["roc_auc"],
            m["average_precision"]
        ),
        reverse=True
    )
    
    print("\nRanked Models by Optimal F1 (with Recall >= 0.70 constraint):")
    print(f"{'Rank':<4} {'Model ID':<38} {'ROC-AUC':<8} {'Opt-T':<6} {'Recall':<7} {'Prec':<7} {'F1':<7} {'Acc':<7} {'Spec':<7}")
    print("-" * 95)
    for rank, m in enumerate(sorted_models, 1):
        opt = m["optimal"]
        print(f"{rank:<4} {m['model_id']:<38} {m['roc_auc']:<8.4f} {opt['threshold']:<6.2f} {opt['recall']:<7.4f} {opt['precision']:<7.4f} {opt['f1_score']:<7.4f} {opt['accuracy']:<7.4f} {opt['specificity']:<7.4f}")

    # Top Candidate Selection:
    # Let's inspect the top candidates carefully.
    top_candidate = sorted_models[0]
    
    # Check if Gradient Boosting Tuned is among the top
    gb_tuned_candidates = [m for m in sorted_models if "gradient_boosting" in m["algorithm_key"] and m["model_type"] == "tuned"]
    lr_tuned_candidates = [m for m in sorted_models if "logistic_regression" in m["algorithm_key"] and m["model_type"] == "tuned"]
    rf_tuned_candidates = [m for m in sorted_models if "random_forest" in m["algorithm_key"] and m["model_type"] == "tuned"]
    
    print(f"\nTop Model Selected: {top_candidate['model_id']}")
    print(f"Algorithm: {top_candidate['algorithm_name']}")
    print(f"Configuration: {top_candidate['config_letter']}")
    print(f"Model Type: {top_candidate['model_type']}")
    print(f"ROC-AUC: {top_candidate['roc_auc']:.4f}")
    print(f"PR-AUC (Avg Prec): {top_candidate['average_precision']:.4f}")
    print(f"Optimal Threshold: {top_candidate['optimal']['threshold']:.2f}")
    print(f"Recall @ Optimal: {top_candidate['optimal']['recall']:.4f} (Target: >= {RECALL_TARGET})")
    print(f"Precision @ Optimal: {top_candidate['optimal']['precision']:.4f}")
    print(f"F1-Score @ Optimal: {top_candidate['optimal']['f1_score']:.4f}")
    print(f"Accuracy @ Optimal: {top_candidate['optimal']['accuracy']:.4f}")
    print(f"Specificity @ Optimal: {top_candidate['optimal']['specificity']:.4f}")
    
    # Calculate Deltas
    opt = top_candidate["optimal"]
    def_m = top_candidate["default_050"]
    delta_metrics = {
        "accuracy_delta": round(opt["accuracy"] - def_m["accuracy"], 4),
        "precision_delta": round(opt["precision"] - def_m["precision"], 4),
        "recall_delta": round(opt["recall"] - def_m["recall"], 4),
        "f1_score_delta": round(opt["f1_score"] - def_m["f1_score"], 4),
        "specificity_delta": round(opt["specificity"] - def_m["specificity"], 4),
        "balanced_accuracy_delta": round(opt["balanced_accuracy"] - def_m["balanced_accuracy"], 4),
        "true_positives_delta": int(opt["true_positives"] - def_m["true_positives"]),
        "false_positives_delta": int(opt["false_positives"] - def_m["false_positives"]),
        "true_negatives_delta": int(opt["true_negatives"] - def_m["true_negatives"]),
        "false_negatives_delta": int(opt["false_negatives"] - def_m["false_negatives"])
    }
    
    selection_record = {
        "selected_model_id": top_candidate["model_id"],
        "algorithm": top_candidate["algorithm_key"],
        "algorithm_display_name": top_candidate["algorithm_name"],
        "feature_config": top_candidate["config_letter"],
        "feature_config_name": top_candidate["config_key"],
        "model_type": top_candidate["model_type"],
        "artifact_path": f"models/phase5/{'tuned/' if top_candidate['model_type']=='tuned' else ''}{top_candidate['algorithm_key']}_{top_candidate['config_key']}{'_tuned' if top_candidate['model_type']=='tuned' else ''}.joblib",
        "optimal_threshold": float(opt["threshold"]),
        "default_threshold": 0.50,
        "recall_target": RECALL_TARGET,
        "recall_constraint_satisfied": bool(opt["recall_constraint_satisfied"]),
        "threshold_independent_metrics": {
            "roc_auc": round(top_candidate["roc_auc"], 4),
            "average_precision": round(top_candidate["average_precision"], 4)
        },
        "validation_metrics_at_optimal_threshold": {
            "threshold": float(opt["threshold"]),
            "accuracy": opt["accuracy"],
            "precision": opt["precision"],
            "recall": opt["recall"],
            "f1_score": opt["f1_score"],
            "specificity": opt["specificity"],
            "balanced_accuracy": opt["balanced_accuracy"],
            "true_positives": opt["true_positives"],
            "false_positives": opt["false_positives"],
            "true_negatives": opt["true_negatives"],
            "false_negatives": opt["false_negatives"]
        },
        "validation_metrics_at_default_threshold": {
            "threshold": 0.50,
            "accuracy": def_m["accuracy"],
            "precision": def_m["precision"],
            "recall": def_m["recall"],
            "f1_score": def_m["f1_score"],
            "specificity": def_m["specificity"],
            "balanced_accuracy": def_m["balanced_accuracy"],
            "true_positives": def_m["true_positives"],
            "false_positives": def_m["false_positives"],
            "true_negatives": def_m["true_negatives"],
            "false_negatives": def_m["false_negatives"]
        },
        "delta_metrics": delta_metrics,
        "confusion_matrix_at_optimal": {
            "tp": opt["true_positives"],
            "fp": opt["false_positives"],
            "tn": opt["true_negatives"],
            "fn": opt["false_negatives"]
        },
        "confusion_matrix_at_default": {
            "tp": def_m["true_positives"],
            "fp": def_m["false_positives"],
            "tn": def_m["true_negatives"],
            "fn": def_m["false_negatives"]
        },
        "accuracy_maximizing_metrics": {
            "threshold": float(top_candidate["acc_max"]["threshold"]),
            "accuracy": top_candidate["acc_max"]["accuracy"],
            "precision": top_candidate["acc_max"]["precision"],
            "recall": top_candidate["acc_max"]["recall"],
            "f1_score": top_candidate["acc_max"]["f1_score"],
            "specificity": top_candidate["acc_max"]["specificity"]
        },
        "hyperparameter_summary": top_candidate["hyperparameters"],
        "selection_rationale": (
            f"The selected model ({top_candidate['model_id']}) achieved the best balance of discriminative power, "
            f"calibrated probability separation, and recall-constrained F1-score on the validation dataset. "
            f"With optimal decision threshold t={opt['threshold']:.2f}, it achieves Recall={opt['recall']:.4f} (exceeding the >= 0.70 requirement), "
            f"Precision={opt['precision']:.4f}, and F1={opt['f1_score']:.4f}, while preserving a strong Specificity of {opt['specificity']:.4f}. "
            f"In an Indian e-commerce retention context, missing an at-risk customer (False Negative) is substantially costlier "
            f"than sending a discount or outreach notification to a satisfied customer (False Positive). Threshold optimization successfully "
            f"captures churners while controlling retention intervention waste."
        ),
        "all_ranked_models": [
            {
                "rank": r,
                "model_id": m["model_id"],
                "algorithm": m["algorithm_name"],
                "config": m["config_letter"],
                "model_type": m["model_type"],
                "roc_auc": round(m["roc_auc"], 4),
                "optimal_threshold": float(m["optimal"]["threshold"]),
                "recall_at_optimal": m["optimal"]["recall"],
                "precision_at_optimal": m["optimal"]["precision"],
                "f1_at_optimal": m["optimal"]["f1_score"],
                "accuracy_at_optimal": m["optimal"]["accuracy"],
                "specificity_at_optimal": m["optimal"]["specificity"]
            }
            for r, m in enumerate(sorted_models, 1)
        ]
    }
    
    with open(MODEL_SELECTION_PATH, "w", encoding="utf-8") as f:
        json.dump(selection_record, f, indent=2)
    print(f"\n5. Saved model selection decision record to: {MODEL_SELECTION_PATH}")
    print("=" * 80)
    print("THRESHOLD OPTIMIZATION AND MODEL SELECTION COMPLETED SUCCESSFULLY!")
    print("=" * 80)


if __name__ == "__main__":
    run_threshold_optimization()
