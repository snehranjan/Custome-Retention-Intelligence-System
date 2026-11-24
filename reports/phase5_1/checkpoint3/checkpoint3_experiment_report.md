# Phase 5.1 — Checkpoint 3: Advanced Model Experimentation, Nested Cross-Validation & Candidate Selection Report

**Project:** Indian E-Commerce Customer Retention Intelligence System Using Machine Learning  
**Workspace:** `C:\customer churn retention system`  
**Milestone:** Phase 5.1 — Checkpoint 3  
**Date:** November 19, 2026  
**Auditor / ML Engineer:** Senior Machine Learning Engineer, ML Researcher & Independent Technical Auditor  
**Status:** **EXPERIMENTATION COMPLETE — CANDIDATE SELECTED FOR PHASE 5.1**  

---

## 1. Executive Summary

Phase 5.1 Checkpoint 3 conducted advanced model experimentation on the complete development dataset ($N = 5,950$ customers, combining original training and validation partitions) using a rigorous **5x3 Nested Stratified Cross-Validation** protocol. 

The primary objective was to investigate whether domain-engineered behavioral features (velocity momentum ratios, operational friction indices, right-skew log transforms) and non-linear tree-based ensembles (Random Forest, Extra Trees, Gradient Boosting, HistGradientBoosting, and Voting Ensembles) can improve generalization beyond the approved Phase 5 Logistic Regression model, moving towards an aspirational accuracy target of 80% with a churn recall constraint of $\ge 70\%$.

### Key Findings
1. **Top-Ranked Model:** **Random Forest with Configuration D (Advanced Features + Correlation Pruning)** achieved the highest out-of-fold generalization performance across the 5 outer folds:
   * **Nested CV Mean F1:** **$0.6944 \pm 0.0145$** (vs. Phase 5 baseline LR Config B F1: $0.6863 \pm 0.0133$)
   * **Nested CV Mean Accuracy:** **$71.34\% \pm 1.63\%$** (vs. Phase 5 baseline LR Config B: $70.30\% \pm 1.48\%$)
   * **Nested CV Mean ROC-AUC:** **$0.7798 \pm 0.0164$** (vs. Phase 5 baseline LR Config B: $0.7724 \pm 0.0171$)
   * **Nested CV Mean Recall:** **$71.02\% \pm 1.31\%$** (maintaining the $\ge 70\%$ recall objective at default threshold $0.50$)
2. **Threshold Optimization:**
   * At default threshold $\tau = 0.50$: Accuracy is **$71.34\%$**, Recall is **$71.02\%$**, and F1 is **$0.6943$**.
   * At threshold $\tau = 0.40$: F1 reaches its global maximum of **$0.7061$**, driving Churn Recall to **$85.77\%$** while Accuracy remains **$67.29\%$** (reducing false negatives from $790$ down to $388$).
3. **Advanced Features Contribution:** The addition of momentum ratios ($R_{30/90}, R_{90/180}$) and the customer friction index produced consistent improvements across all algorithms:
   * For Logistic Regression: F1 improved from $0.6825$ (Config A) $\to 0.6863$ (Config B) $\to \mathbf{0.6888}$ (Config C).
   * For HistGradientBoosting: F1 reached **$0.6889$** and ROC-AUC reached **$0.7802$** on Config C.
   * For Gradient Boosting: ROC-AUC reached **$0.7818$** (highest discriminative capacity across all models).
4. **Latent Oracle Error & Re-evaluation of Accuracy Ceiling:** No model configuration achieved 80% accuracy. The data generating process uses latent customer personas with intrinsic churn propensities ranging from 0.08 (`loyal_vip`) to 0.94 (`zero_order`), producing an oracle error rate conditional on knowing latent personas of $R^*(Z) = \sum w_k \min(p_k, 1-p_k) = 26.03\%$ (oracle accuracy ceiling of $73.97\%$). Because observable features $X$ are noisy proxies of latent personas, the Bayes error conditional on observable features satisfies $R^*(X) \ge 26.03\%$. Therefore, $73.97\%$ is an oracle ceiling assuming latent persona knowledge rather than a proven universal ceiling on $X$. Achieving $71.34\%$ cross-validated accuracy represents strong, defensible performance, confirming that abandoning the arbitrary 80% target is scientifically sound.
5. **Strict Data Isolation:** Zero test datasets (`data/modeling/test.csv`, $N=1,050$) and zero independent cohort records (`customers_independent.csv`, $N=1,500$) were accessed, loaded, or evaluated during this checkpoint.

---

## 2. Input Data Verification & Boundary Isolation

```
                               DATASET ARCHITECTURE & BOUNDARIES
                                               │
               ┌───────────────────────────────┴───────────────────────────────┐
               ▼                                                               ▼
    DEVELOPMENT DATASET (N = 5,950)                               SEALED TEST BENCHMARKS (DO NOT TOUCH)
               │                                                               │
   ┌───────────┴───────────┐                                       ┌───────────┴───────────┐
   ▼                       ▼                                       ▼                       ▼
train.csv              validation.csv                         test.csv            customers_independent.csv
(N = 4,900)            (N = 1,050)                           (N = 1,050)                 (N = 1,500)
       └───────┬───────┘                                     [Phase 5 Baseline]      [Phase 5.1 Sealed Cohort]
               ▼                                              SHA: 93926052...            SHA: D3B694F9...
   5x3 Nested Stratified CV
```

* **Development Records:** $N = 5,950$ customers ($4,900$ train + $1,050$ validation).
* **Customer ID Uniqueness:** Exactly $5,950$ unique customer IDs (`IND_CUST_10001` through `IND_CUST_17000` excluding test indices).
* **Class Distribution:** Retained ($0$): $3,224$ ($54.18\%$), Churned ($1$): $2,726$ ($45.82\%$).
* **Guard Verification:** Cryptographic checksums of `data/modeling/test.csv` and `data/independent_test/raw/customers_independent.csv` were verified before and after execution; zero test records were loaded into memory.

---

## 3. Feature-Name Compatibility Audit & Fixes Implemented

Prior to cross-validation, the defects discovered in Checkpoint 2.2 were formally resolved in [advanced_feature_engineering.py](file:///c:/customer%20churn%20retention%20system/backend/ml/advanced_feature_engineering.py):

1. **`Log1pTransformer.get_feature_names_out()`:** Implemented standard scikit-learn API returning input feature names or `self.feature_names_in_`.
2. **`CorrelationPruner.get_feature_names_out()`:** Implemented standard scikit-learn API applying the frozen integer index mask `self.keep_indices_` to incoming column names from `StandardScaler` / `SimpleImputer`.
3. **End-to-End Alignment Test:** Calling `preprocessor.get_feature_names_out()` on fitted pipelines returns exactly $73$ feature names, aligning 1:1 with the $73$ columns produced by `preprocessor.transform(X)`:
   * First 5 numerical features: `num__customer_tenure_days`, `num__recency_days`, `num__has_delivered_order`, `num__hist_delivered_order_count`, `num__hist_returned_order_count`.
   * Last 5 categorical features: `cat__cluster_id_0`, `cat__cluster_id_1`, `cat__cluster_id_2`, `cat__cluster_id_3`, `cat__cluster_id_4`.

---

## 4. Nested Stratified Cross-Validation Methodology

To prevent optimistic selection bias and hyperparameter overfitting, a **5x3 Nested Stratified Cross-Validation** protocol was enforced:

```
OUTER CV (5 Folds, Stratified, Seed=42)
For each Outer Fold k = 1..5:
  ├── Outer Training Partition (80%, N = 4,760)
  │     └── INNER CV (3 Folds, Stratified, Seed=42)
  │           ├── Inner Train (66.7%, N = 3,173) ──> Fit Pipeline (Log1p, Impute, Scale, Prune, Estimator)
  │           └── Inner Holdout (33.3%, N = 1,587) ──> Score F1 Metric
  │           └── Select Best Hyperparameters by Mean Inner F1
  │     └── Refit Best Pipeline on FULL Outer Training Partition (N = 4,760)
  └── Outer Holdout Partition (20%, N = 1,190)
        └── Predict Out-of-Fold Probabilities (y_prob) & Classes (y_pred)
        └── Calculate Unbiased Outer Fold Metrics
```

* **Zero Information Leakage:** Imputation medians, standard scaling means/variances, and correlation pruning matrices were fit strictly inside the inner training splits during hyperparameter selection, and on the outer training slice during outer model refitting. Outer holdout folds were never seen during fitting.
* **Complete OOF Coverage:** Every development customer ($N=5,950$) received exactly one out-of-fold prediction.

---

## 5. Experiment Configurations and Algorithms

### Feature Configurations
* **Configuration A (Phase 3 Baseline):** 34 baseline numerical features + 2 demographic categoricals (`city`, `state`) = **36 features**.
* **Configuration B (Phase 5 Baseline):** Configuration A + categorical RFM persona (`cluster_id`) = **37 features**.
* **Configuration C (Advanced Behavioral):** Configuration B + 6 advanced features (`velocity_ratio_30_90`, `velocity_ratio_90_180`, `has_orders_last_90_days`, `has_orders_last_180_days`, `delay_friction_score`, `missing_friction_score`) + `Log1pTransformer` = **43 features**.
* **Configuration D (Advanced + Within-Fold Correlation Pruning):** Configuration C + within-fold `CorrelationPruner(threshold=0.85)` with protected columns `velocity_ratio_30_90` and `delay_friction_score` = **Dynamic ($\approx 29$ numerical + $44$ one-hot = $73$ columns)**.

### Algorithms Evaluated
1. **Logistic Regression** (L-BFGS, L2 penalty, scale numerical)
2. **Decision Tree** (CART)
3. **Random Forest** (150 trees, max_depth tuning, min_samples_leaf tuning)
4. **Extra Trees Classifier** (150 randomized trees)
5. **Gradient Boosting Classifier** (Deviance loss, shrinkage tuning)
6. **HistGradientBoosting Classifier** (Histogram-based gradient boosting)
7. **Soft Voting Classifier Ensemble** (Soft probability averaging of top diverse models: Logistic Regression + Random Forest + HistGradientBoosting)

---

## 6. Hyperparameter Search Spaces

| Model | Hyperparameters Swept | Inner CV Metric | Selection Strategy |
| :--- | :--- | :---: | :--- |
| **Logistic Regression** | `clf__C`: `[0.01, 0.1, 1.0]`<br>`clf__class_weight`: `['balanced', None]` | F1 Score | 3-Fold Stratified Grid Search |
| **Decision Tree** | `clf__max_depth`: `[5, 8, 12]`<br>`clf__min_samples_leaf`: `[10, 25]`<br>`clf__class_weight`: `['balanced', None]` | F1 Score | 3-Fold Stratified Grid Search |
| **Random Forest** | `clf__n_estimators`: `[150]`<br>`clf__max_depth`: `[8, 12]`<br>`clf__min_samples_leaf`: `[5, 15]`<br>`clf__class_weight`: `['balanced', None]` | F1 Score | 3-Fold Stratified Grid Search |
| **Extra Trees** | `clf__n_estimators`: `[150]`<br>`clf__max_depth`: `[8, 12]`<br>`clf__min_samples_leaf`: `[5, 15]`<br>`clf__class_weight`: `['balanced', None]` | F1 Score | 3-Fold Stratified Grid Search |
| **Gradient Boosting** | `clf__n_estimators`: `[100]`<br>`clf__learning_rate`: `[0.05, 0.1]`<br>`clf__max_depth`: `[3, 5]`<br>`clf__subsample`: `[0.85, 1.0]` | F1 Score | 3-Fold Stratified Grid Search |
| **HistGradientBoosting** | `clf__max_iter`: `[100]`<br>`clf__learning_rate`: `[0.05, 0.1]`<br>`clf__max_depth`: `[4, 6]`<br>`clf__class_weight`: `['balanced', None]` | F1 Score | 3-Fold Stratified Grid Search |
| **Voting Ensemble** | Fixed optimal base estimators with soft voting weights `(1, 1, 1)` | F1 Score | 3-Fold Stratified Holdout Score |

---

## 7. Fold-Level Results

Fold-level metrics for the top candidates from [nested_cv_results.csv](file:///c:/customer%20churn%20retention%20system/reports/phase5_1/checkpoint3/nested_cv_results.csv):

### Top Candidate: `random_forest_config_d`
| Outer Fold | Accuracy | Precision | Recall | F1 Score | ROC-AUC | PR-AUC | Balanced Acc | Best Selected Params |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| **Fold 1** | 0.7092 | 0.6728 | 0.7070 | 0.6894 | 0.7678 | 0.7356 | 0.7091 | `max_depth=8, min_samples_leaf=5, weight='balanced'` |
| **Fold 2** | 0.7303 | 0.6975 | 0.7248 | 0.7109 | 0.8037 | 0.7712 | 0.7298 | `max_depth=8, min_samples_leaf=5, weight='balanced'` |
| **Fold 3** | 0.7084 | 0.6754 | 0.6972 | 0.6861 | 0.7758 | 0.7410 | 0.7075 | `max_depth=8, min_samples_leaf=5, weight='balanced'` |
| **Fold 4** | 0.7294 | 0.7042 | 0.7046 | 0.7044 | 0.7850 | 0.7495 | 0.7275 | `max_depth=8, min_samples_leaf=5, weight='balanced'` |
| **Fold 5** | 0.6908 | 0.6481 | 0.7174 | 0.6811 | 0.7667 | 0.7237 | 0.6928 | `max_depth=8, min_samples_leaf=5, weight='balanced'` |
| **Mean $\pm$ Std** | **$0.7134 \pm 0.0163$** | **$0.6796 \pm 0.0213$** | **$0.7102 \pm 0.0131$** | **$0.6944 \pm 0.0145$** | **$0.7798 \pm 0.0164$** | **$0.7442 \pm 0.0208$** | **$0.7132 \pm 0.0155$** | Highly stable fold-to-fold |

---

## 8. Candidate Comparison and Ranking

All 12 evaluated model and configuration combinations ranked by Nested CV F1 score from [candidate_comparison.csv](file:///c:/customer%20churn%20retention%20system/reports/phase5_1/checkpoint3/candidate_comparison.csv):

| Rank | Model Experiment ID | Configuration | Nested CV F1 ($\mu \pm \sigma$) | Nested CV ROC-AUC | Nested CV Accuracy | Nested CV Recall | Nested CV Precision |
| :---: | :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **1** | **`random_forest_config_d`** | **Config D** | **$0.6944 \pm 0.0145$** | **$0.7798 \pm 0.0164$** | **$71.34\% \pm 1.63\%$** | **$71.02\%$** | **$67.96\%$** |
| 2 | `hist_gradient_boosting_config_c` | Config C | $0.6889 \pm 0.0080$ | $0.7802 \pm 0.0116$ | $71.21\% \pm 1.14\%$ | $69.55\%$ | $68.29\%$ |
| 3 | `logistic_regression_config_c` | Config C | $0.6888 \pm 0.0141$ | $0.7745 \pm 0.0175$ | $70.59\% \pm 1.58\%$ | $71.02\%$ | $66.89\%$ |
| 4 | `hist_gradient_boosting_config_d` | Config D | $0.6882 \pm 0.0094$ | $0.7801 \pm 0.0125$ | $70.99\% \pm 1.15\%$ | $69.85\%$ | $67.86\%$ |
| 5 | `random_forest_config_c` | Config C | $0.6874 \pm 0.0084$ | $0.7806 \pm 0.0119$ | $70.92\% \pm 1.07\%$ | $69.74\%$ | $67.83\%$ |
| 6 | `logistic_regression_config_b` | Config B | $0.6863 \pm 0.0133$ | $0.7724 \pm 0.0171$ | $70.30\% \pm 1.48\%$ | $70.91\%$ | $66.52\%$ |
| 7 | `voting_ensemble_config_c` | Config C | $0.6851 \pm 0.0085$ | $0.7794 \pm 0.0128$ | $70.72\% \pm 0.99\%$ | $69.48\%$ | $67.58\%$ |
| 8 | `logistic_regression_config_d` | Config D | $0.6841 \pm 0.0116$ | $0.7740 \pm 0.0171$ | $70.34\% \pm 1.35\%$ | $70.07\%$ | $66.84\%$ |
| 9 | `logistic_regression_config_a` | Config A | $0.6825 \pm 0.0128$ | $0.7721 \pm 0.0172$ | $69.75\% \pm 1.44\%$ | $70.95\%$ | $65.78\%$ |
| 10 | `extra_trees_config_c` | Config C | $0.6825 \pm 0.0139$ | $0.7749 \pm 0.0152$ | $69.98\% \pm 1.34\%$ | $70.40\%$ | $66.30\%$ |
| 11 | `gradient_boosting_config_c` | Config C | $0.6792 \pm 0.0057$ | **$0.7818 \pm 0.0097$** | **$71.38\% \pm 0.92\%$** | $66.14\%$ | $69.84\%$ |
| 12 | `decision_tree_config_c` | Config C | $0.6709 \pm 0.0162$ | $0.7711 \pm 0.0163$ | $70.77\% \pm 1.45\%$ | $65.22\%$ | $69.54\%$ |

---

## 9. Decision Threshold Optimization Analysis

Using out-of-fold predicted probabilities ($N = 5,950$) from `random_forest_config_d`, decision thresholds from $\tau = 0.20$ to $0.81$ (62 increments, step $0.01$) were systematically evaluated:

```
THRESHOLD OPTIMIZATION TRADE-OFF CURVE
Threshold    Accuracy    Precision    Recall      F1-Score    Balanced Acc
  0.35        64.59%      57.24%      89.73%      0.6990        66.53%
  0.38        66.30%      58.92%      87.38%      0.7038        67.93%
  0.40        67.29%      60.01%      85.77%      0.7061 ★      68.72%  <-- F1-MAXIMIZING THRESHOLD
  0.42        68.03%      61.12%      83.09%      0.7043        69.20%
  0.45        69.55%      63.53%      78.72%      0.7031        70.26%
  0.48        70.52%      65.88%      73.95%      0.6969        70.79%
  0.50        71.34% ★    67.91%      71.02% ★    0.6943        71.32% ★<-- ACCURACY-MAX & RECALL >= 70% TARGET
  0.52        70.96%      68.73%      67.17%      0.6794        70.67%
  0.55        70.99%      70.66%      62.73%      0.6646        70.35%
```

### Optimal Operating Points
1. **F1-Maximizing Threshold ($\tau = 0.40$):**
   * **F1:** **$0.7061$** | **Recall:** **$85.77\%$** ($2,338 / 2,726$ churners caught) | **Accuracy:** **$67.29\%$** | **Precision:** **$60.01\%$**
   * False Negatives: **$388$** (minimizes missed churners for high-value retention campaigns)
2. **Balanced Operating Point / Accuracy-Maximizing Threshold ($\tau = 0.50$):**
   * **Accuracy:** **$71.34\%$** | **Recall:** **$71.02\%$** ($\ge 70\%$ constraint satisfied) | **F1:** **$0.6943$** | **Precision:** **$67.91\%$**
   * False Negatives: **$790$** | False Positives: **$915$** | True Positives: **$1,936$** | True Negatives: **$2,309$**

---

## 10. Behavioral Error Analysis

Out-of-fold prediction errors ($N = 5,950$) from the top model were analyzed across behavioral cohorts:

| Customer Behavioral Cohort | Sample Count ($n$) | Actual Churn Rate | Accuracy at $\tau = 0.40$ | Churn Recall | Precision | True Positives | False Negatives | False Positives |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Overall Development Population** | 5,950 | 45.82% | 67.29% | 85.77% | 60.01% | 2,338 | 388 | 1,558 |
| **Zero Historical Orders** (`has_historical_orders == 0`) | 127 | 96.06% | 96.06% | 100.00% | 96.06% | 122 | **0** | 5 |
| **Zero Delivered Orders** (`has_delivered_order == 0`) | 422 | 75.83% | 75.83% | 100.00% | 75.83% | 320 | **0** | 102 |
| **Dormant Accounts** (`orders_last_90_days == 0`) | 1,593 | 70.18% | 70.56% | 98.75% | 70.81% | 1,104 | **14** | 455 |
| **High Logistics Delay** (`delay >= 4.0` days) | 492 | 71.34% | 71.34% | 100.00% | 71.34% | 351 | **0** | 141 |
| **High Return Rate** (`return_rate >= 0.20`) | 961 | 60.35% | 62.64% | 97.76% | 62.10% | 567 | **13** | 346 |
| **Active Recent Accounts** (`orders_last_30_days >= 1`) | 2,726 | 32.80% | 70.25% | 69.57% | 53.57% | 622 | **272** | 539 |

### Error Analysis Insights
* **Edge Case Dominance:** Zero-order accounts, zero-delivered accounts, and dormant accounts exhibit $\approx 99\%–100\%$ churn recall. The model effectively never misses customers who have established dormant or failed transaction patterns.
* **Core Error Source:** The majority of false negatives ($272 / 388 = 70.1\%$) occur among **Active Recent Accounts** (customers who placed an order within the last 30 days of the snapshot cutoff but subsequently ceased purchasing). These accounts exhibit healthy historical signals up to the cutoff date, making their subsequent cessation of activity stochastic and inherently difficult to anticipate.

---

## 11. Selected Candidate Pipeline and Technical Justification

### Selected Pipeline: `random_forest_config_d`
* **Algorithm:** Random Forest Classifier (`sklearn.ensemble.RandomForestClassifier`)
* **Optimal Hyperparameters:** `n_estimators=150, max_depth=8, min_samples_leaf=5, class_weight='balanced', random_state=42`
* **Feature Configuration:** Configuration D (34 Baseline Numerical + 6 Advanced Numerical + 3 Categorical + Log1p + CorrelationPruner at threshold $0.85$ with protected momentum and friction features)
* **Training Sample Count:** Refitted on 100% of the development dataset ($N = 5,950$ customers; root node weighted sample count: 5,950.0)
* **Saved Model Artifact:** [random_forest_config_d_pipeline.joblib](file:///c:/customer%20churn%20retention%20system/models/phase5_1/checkpoint3/random_forest_config_d_pipeline.joblib) (SHA-256: `24F1F0E33C75B5590906369960DB6E5951EC95DF9AE40384DA60082B3438F301`)

### Technical Justification
1. **Empirical Superiority:** Achieved the highest Nested Cross-Validation F1 ($0.6944 \pm 0.0145$), outperforming all linear models, decision trees, and competing gradient boosting pipelines.
2. **Constraint Satisfaction:** At threshold $0.50$, it delivers $71.34\%$ accuracy and $71.02\%$ recall, fully satisfying the operational recall constraint ($\ge 70\%$) while providing superior discrimination ($ROC\text{-}AUC = 0.7798$).
3. **Collinearity Resilience:** The integration of within-fold `CorrelationPruner` effectively eliminated redundant missingness indicators and collinear aggregations, stabilizing split candidate distributions and improving F1 over unpruned Random Forest ($0.6944$ vs. $0.6874$).
4. **Fold Stability:** Low cross-validation variance across folds ($\sigma_{\text{F1}} = 0.0145, \sigma_{\text{Acc}} = 0.0163$) demonstrates robust generalization across diverse development splits.

---

## 12. Non-Comparable Reference Benchmark Comparison

> **METHODOLOGICAL NOTICE:**  
> The table below provides an informal context comparison against the historical Phase 5 final evaluation.  
> **These evaluations are NOT directly comparable.** The Phase 5 result was evaluated once on an independent test slice ($N = 1,050$), whereas the Checkpoint 3 results represent out-of-fold generalization across the full development dataset ($N = 5,950$) under 5x3 nested cross-validation.

| Metric | Phase 5 Historic Test Benchmark (LR Config B, $\tau=0.46$, $N=1,050$) | Phase 5.1 Nested CV Baseline (LR Config B, $\tau=0.50$, $N=5,950$) | Phase 5.1 Selected Candidate (RF Config D, $\tau=0.50$, $N=5,950$) | Phase 5.1 Selected Candidate (RF Config D, $\tau=0.40$, $N=5,950$) |
| :--- | :---: | :---: | :---: | :---: |
| **Accuracy** | 66.95% | 70.30% | **71.34%** | 67.29% |
| **Recall** | 74.43% | 70.91% | **71.02%** | **85.77%** |
| **Precision** | 61.51% | 66.52% | **67.96%** | 60.01% |
| **F1 Score** | 0.6736 | 0.6863 | **0.6944** | **0.7061** |
| **ROC-AUC** | 0.7491 | 0.7724 | **0.7798** | **0.7798** |

---

## 13. Leakage and Integrity Verification

All 12 automated integrity assertions were executed via [validate_checkpoint3.py](file:///c:/customer%20churn%20retention%20system/backend/ml/validate_checkpoint3.py):

| Verification Check | Target Integrity Invariant | Outcome |
| :--- | :--- | :---: |
| **Check 1: Report Artifacts** | All 7 required Checkpoint 3 CSV/JSON files exist in `reports/phase5_1/checkpoint3/` | **PASS** |
| **Check 2: OOF Coverage** | Exactly 5,950 development customers have 1-to-1 OOF predictions | **PASS** |
| **Check 3: Test ID Isolation** | 0 historical test IDs and 0 independent cohort IDs in OOF predictions | **PASS** |
| **Check 4: Outer CV Folds** | Exactly 5 outer stratified folds logged with complete holdout coverage | **PASS** |
| **Check 5: Probabilities Validity** | All 12 candidate probability arrays are strictly finite and bounded in $[0.0, 1.0]$ | **PASS** |
| **Check 6: Feature Name Schema** | Transformed feature schema logged with exactly 73 features | **PASS** |
| **Check 7: Threshold Sweep** | 62 threshold increments ($0.20 \dots 0.81$) evaluated cleanly on OOF predictions | **PASS** |
| **Check 8: Metadata Consistency** | `selected_candidate.json` matches top experiment `random_forest_config_d` | **PASS** |
| **Check 9: Deserialization Fidelity**| Saved `.joblib` pipeline reloaded cleanly with matching inference method | **PASS** |
| **Check 10: Error Analysis** | Error analysis segmented across 8 behavioral customer cohorts | **PASS** |
| **Check 11: Candidate Ranking** | 12 candidates compared and ranked by nested cross-validation F1 | **PASS** |
| **Check 12: Cryptographic Invariance** | All original Phase 0–5 raw files, production model, and sealed cohort remain untouched | **PASS** |

---

## 14. Cryptographic Artifact Hashes

### Development Model Artifacts (`models/phase5_1/checkpoint3/`)
| Model Pipeline File | Size | SHA-256 Checksum |
| :--- | :---: | :--- |
| **`random_forest_config_d_pipeline.joblib` (SELECTED)** | 2,629,147 B | `24F1F0E33C75B5590906369960DB6E5951EC95DF9AE40384DA60082B3438F301` |
| `hist_gradient_boosting_config_c_pipeline.joblib` | 205,906 B | `ACD44D582FE0EBF2DFD7AD4D532C91151063B036B04A4825893115832EF6276B` |
| `logistic_regression_config_c_pipeline.joblib` | 11,882 B | `BBBCD1DE44F9A1D5D8BB4ED3A024CE21B2B5386E429C262B8708C29B38986582` |
| `hist_gradient_boosting_config_d_pipeline.joblib` | 203,186 B | `18F4FE9CB02BEE6EC4DE5B5BE9221A8B4BAB3CF265B5FA204BA99A21E17D10D9` |
| `random_forest_config_c_pipeline.joblib` | 2,049,803 B | `2FF7AE3418A086F3207454E2A7CDD35FF11EC09FB70A563ED0F799D996CBA876` |
| `logistic_regression_config_b_pipeline.joblib` | 9,658 B | `E9A7A69D8F324E2C16E2552EDB89897E6C58431FFB137771D629CF26E2164490` |
| `voting_ensemble_config_c_pipeline.joblib` | 6,918,501 B | `1D16376A8078205ED563DFF83F0448441E11A51C6C620DCE6E18EBB80BC788CE` |
| `logistic_regression_config_d_pipeline.joblib` | 12,522 B | `0980F7887CE814505403F475F72744141485354B6BDC284F5825792C2921E0F8` |
| `logistic_regression_config_a_pipeline.joblib` | 9,370 B | `30D6C54A12AE52BC9F8ADC496CE704860C0C2FE71CFE24BB6B11E130665CBF0F` |
| `extra_trees_config_c_pipeline.joblib` | 2,935,243 B | `28FF3EEE613FF8046496DFA87CF4F7DF6F9EB5BD482E8450FA8094BE6597DCB6` |
| `gradient_boosting_config_c_pipeline.joblib` | 153,517 B | `622FE1B3EA59766FAA33AEC067E1970565295072D865BC3CB39B127F06D065AD` |
| `decision_tree_config_c_pipeline.joblib` | 25,076 B | `AFB823154B9AF98B82C10C2F0550431DFE000B55E54AB086C9712A73D67EF7DF` |

### Core System Artifacts (Strictly Invariant)
* **Phase 5 Production Model:** `models/phase5/final_churn_pipeline.joblib` (`25B91797F8F36DB605BAB98B8568A5911847B8CCE77334A68AE4E3862CD3B35D`)
* **Phase 1 Customers:** `data/raw/customers.csv` (`DF6219AA4E2BDDE8FFF419272B9F2C1DE0602473248619E90566BC7D498AB70E`)
* **Phase 1 Orders:** `data/raw/orders.csv` (`AB632B3092F732B3B25BAAD096B191C1ACA777CB8D42B29EABB815A266C558E7`)
* **Historical Test Set:** `data/modeling/test.csv` (`93926052072C2C0AF6FC3E7279385B0B31C898CC9798FBC1EF78FBA1CAEDBD67`)
* **Sealed Independent Customers:** `data/independent_test/raw/customers_independent.csv` (`D3B694F9F3488BB1CAF81C49603A9E322396F48ADDBA6E96246BD91B211F53B4`)
* **Sealed Independent Orders:** `data/independent_test/raw/orders_independent.csv` (`BE7B293A283A90E7AC78F92D681BE4D0ACA58C3CC2235BCC7EDCBF2348FBAF8E`)
* **Sealed Independent Manifest:** `data/independent_test/raw/independent_cohort_manifest.json` (`6320757631ED9F8A598D32EFD8EA7CB095960B9885517F2FCAA80A1FA2FA236C`)

---

## 15. Limitations & Recommendations for Checkpoint 4

1. **Aspirational 80% Accuracy Target vs. Latent Oracle Error Ceiling:**  
   The best achieved cross-validated accuracy is **$71.34\%$** (with $ROC\text{-}AUC = 0.7798$). As analyzed, the underlying synthetic churn generation process incorporates Bernoulli stochastic outcomes governed by latent personas (`loyal_vip` at 0.08, `steady` at 0.22, `occasional` at 0.45, `dissatisfied` at 0.68, `dormant` at 0.88, and `zero_order` at 0.94), giving an oracle error rate conditional on knowing latent personas of $26.03\%$ (oracle ceiling of $73.97\%$). Because observable features $X$ only imperfectly capture latent personas, the true Bayes error on observable features satisfies $R^*(X) \ge 26.03\%$. While $73.97\%$ is an oracle ceiling assuming latent knowledge and not a proven universal ceiling on $X$, achieving $71.34\%$ accuracy without future leakage is strong and defensible. Pursuing 80% accuracy is mathematically unfeasible without label leakage.
2. **Active Customer Transition Uncertainty:**  
   The primary error mode ($70.1\%$ of false negatives) stems from active recent purchasers who cease purchasing without prior warning signals.
3. **Recommendation for Checkpoint 4:**  
   Proceed to **Phase 5.1 Checkpoint 4: Candidate Validation, Final Model Comparison & Production Selection**. In Checkpoint 4, the selected Random Forest Configuration D pipeline will be audited, its threshold operational trade-offs finalized, and its candidate refit protocol prepared for final unsealing.

---

## 16. Checkpoint 3.1 — Methodology Audit & Optimism Disclosures

A formal, independent methodology audit was conducted in Checkpoint 3.1. Detailed findings and proofs are documented in [checkpoint3_1_methodology_audit.md](file:///c:/customer%20churn%20retention%20system/reports/phase5_1/checkpoint3_1_methodology_audit.md).

### 16.1 Formal University Project Decision
The project leadership confirmed satisfaction with the **$71.34\%$ cross-validated accuracy** ($ROC\text{-}AUC = 0.7798$) achieved on development data. The arbitrary 80% accuracy target is formally abandoned. No data manipulation, leakage, label distortion, or customer exclusion will be permitted.

### 16.2 Disclosures on Candidate Selection and Threshold Optimism
* **Unbiased Generalization at Default Threshold ($\tau = 0.50$):**  
  The 5x3 Nested CV metrics ($F1 = 0.6944 \pm 0.0145$, Accuracy = $71.34\% \pm 1.63\%$) provide an unbiased generalization estimate for the pipeline at default threshold.
* **Candidate Selection Optimism (Winner's Curse):**  
  Because `random_forest_config_d` was chosen as the best performer among 12 evaluated configurations on the same CV splits, its sample mean F1 includes positive selection variance.
* **Threshold Selection Optimism on OOF Pool ($\tau = 0.40$):**  
  The threshold $\tau = 0.40$ ($F1 = 0.7061$, $\text{Recall} = 85.77\%$) was identified by sweeping 62 thresholds across pooled out-of-fold predictions. This represents an **empirical maximum** on the development sample. It is subject to threshold selection optimism and must be independently verified on the sealed test cohort.

### 16.3 Refit Verification on 100% Development Cohort
Inspection of `models/phase5_1/checkpoint3/random_forest_config_d_pipeline.joblib` confirmed that all 150 decision trees have root node sample weight `weighted_n_node_samples[0] == 5950.0`. The saved model pipeline was fitted on the complete development dataset ($N = 5,950$), not on an outer fold subset.

### 16.4 Transformed Feature Schema Alignment
The transformed feature space contains exactly **73 features** (29 numerical + 44 one-hot encoded dummy variables), verified to match 1:1 between `pipeline.named_steps["preprocessor"].get_feature_names_out()` and `pipeline.named_steps["preprocessor"].transform(X)`.

### 16.5 Final Audit Status
All 12 automated integrity assertions in `backend/ml/validate_checkpoint3.py` passed cleanly, and all historical and sealed independent test datasets remain cryptographically intact.
