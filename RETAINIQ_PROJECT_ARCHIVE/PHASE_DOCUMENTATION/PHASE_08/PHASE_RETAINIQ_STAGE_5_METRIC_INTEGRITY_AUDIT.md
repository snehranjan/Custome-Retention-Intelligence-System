# RETAINIQ — STAGE 5 METRIC INTEGRITY AUDIT & CORRECTION REPORT
## Independent Test Cohort (N = 1,500) Verification & Provenance Alignment
**Date:** 2026-11-24  
**Project:** Indian E-Commerce Customer Retention Intelligence System  
**Product:** RetainIQ  
**Target:** Model Performance Scorecard (`AnalyticsPerformance.jsx`), Backend REST Endpoint (`backend/app/routes/analytics.py`), and Stage 5 Documentation  
**Audit Status:** **AUDIT COMPLETE — 100% MATHEMATICAL & PROVENANCE INTEGRITY RESTORED**

---

## 1. ROOT CAUSE ANALYSIS

An exhaustive forensic trace was performed across the machine learning artifacts, backend API endpoints, frontend component source code, and phase reports to investigate the reported discrepancy:

### Findings:
1. **Authoritative Artifact (`reports/phase5_1/final_evaluation/independent_test_metrics.json`):**
   * Generated during Phase 5.1 Checkpoint 4 (19 Nov 2026).
   * Evaluated on the held-out independent synthetic test cohort ($N = 1,500$, `customers_independent.csv`, SHA-256: `D3B694F9...`).
   * Evaluated using the frozen Random Forest Config D pipeline (`final_churn_rf_pipeline.joblib`, SHA-256: `24F1F0E33C75B5590906369960DB6E5951EC95DF9AE40384DA60082B3438F301`) under the locked decision threshold $\tau = 0.50$.
   * **Exact Recorded Metrics:**
     * Accuracy: **0.689333...** (**68.93%**)
     * Precision: **0.642163...** (**64.22%**)
     * Recall: **0.690014...** (**69.00%**)
     * Specificity: **0.688781...** (**68.88%**)
     * Balanced Accuracy: **0.689398...** (**68.94%**)
     * F1-Score: **0.665230...** (**0.6652**)
     * ROC-AUC: **0.765111...** (**0.7651**)
     * Average Precision (PR-AUC): **0.730769...** (**0.7308**)
     * Brier Score: **0.196994...** (**0.1970**)
   * **Confusion Matrix:** $TN = 571$, $FP = 258$, $FN = 208$, $TP = 463$. Total $N = 1,500$.

2. **Backend REST API (`backend/app/routes/analytics.py`):**
   * Endpoint `GET /api/v1/analytics/model-performance` was already correctly configured to return the exact authoritative values (`accuracy=0.6893`, `precision=0.6422`, `recall=0.6900`, `specificity=0.6888`, `balanced_accuracy=0.6894`, `f1_score=0.6652`, `roc_auc=0.7651`, `average_precision=0.7308`, `brier_score=0.1970`).
   * The backend test suite (`tests/test_phase8_4_8_endpoints.py` lines 308–324) explicitly asserts these exact numbers and passes 100%.

3. **Frontend Component (`AnalyticsPerformance.jsx`):**
   * The primary metric cards in `AnalyticsPerformance.jsx` were dynamically bound to `metrics.*` from `apiClient.analytics.getModelPerformance()`. In live execution, the browser rendered the backend values (68.93%, 64.22%, etc.).
   * However, sub-labels in the card and percentage headers in the confusion matrix contained static string fallbacks (`463 / 671 churners`, `38.07%`, etc.) rather than computing them strictly from the live `confusion_matrix` and `sample_size` object.
   * Furthermore, the hyperparameters dictionary in `analytics.py` had leftover template placeholder values (`n_estimators: 200, max_depth: 12, min_samples_split: 5, min_samples_leaf: 2`) rather than reflecting the real fitted pipeline parameters (`n_estimators: 150, max_depth: 8, min_samples_split: 2, min_samples_leaf: 5`).

4. **Stage 5 Audit Report (`PHASE_RETAINIQ_UNSLOP_STAGE_5_REPORT.md`):**
   * The primary root cause of the perceived discrepancy was a documentation error in Section 3.7 of `PHASE_RETAINIQ_UNSLOP_STAGE_5_REPORT.md`.
   * The report text erroneously cited development cross-validation fold figures and aspirational numbers (`Accuracy: 76.00%`, `ROC-AUC: 0.8329`, `PR-AUC: 0.7712`, `Brier: 0.1685`, `Specificity: 82.95%`), which mathematically conflicted with the confusion matrix ($TN=571, FP=258, FN=208, TP=463$, giving $Accuracy = 1034 / 1500 = 68.93\%$).
   * Specifically, `0.7712` was traced to Fold 2 PR-AUC from the nested cross-validation report (`reports/phase5_1/checkpoint3/checkpoint3_experiment_report.md` line 137).

---

## 2. AUTHORITATIVE METRIC SOURCE

* **Authoritative Source File:**  
  `reports/phase5_1/final_evaluation/independent_test_metrics.json`  
  **Evaluation Milestone:** Phase 5.1 Checkpoint 4  
  **Dataset:** Phase 5.1 Independent Synthetic Test Cohort (`customers_independent.csv`, $N = 1,500$)  
  **Pipeline Artifact:** `models/phase5_1/final_model/final_churn_rf_pipeline.joblib`  
  **Cryptographic Hash (SHA-256):** `24F1F0E33C75B5590906369960DB6E5951EC95DF9AE40384DA60082B3438F301`  
  **Locked Decision Threshold:** $\tau = 0.50$  

* **Secondary Model Lock Manifest:**  
  `reports/phase5_1/final_evaluation/final_model_lock_manifest.json`  

---

## 3. BEFORE / AFTER COMPARISON MATRIX

| Metric / Parameter | Erroneous Stage 5 Report Citation | Authoritative Value (`independent_test_metrics.json`) | Corrected Component / Report Value | Status |
| :--- | :--- | :--- | :--- | :--- |
| **Accuracy** | 76.00% | 0.689333 (68.93%) | **68.93%** | **ALIGNED** |
| **Balanced Accuracy** | 75.98% | 0.689398 (68.94%) | **68.94%** | **ALIGNED** |
| **Recall (Sensitivity)** | 69.00% | 0.690014 (69.00%) | **69.00%** | **VERIFIED** |
| **Precision** | 64.22% | 0.642163 (64.22%) | **64.22%** | **VERIFIED** |
| **F1-Score** | 0.6652 | 0.665230 (0.6652) | **0.6652** | **VERIFIED** |
| **Specificity** | 82.95% | 0.688781 (68.88%) | **68.88%** | **ALIGNED** |
| **ROC-AUC** | 0.8329 | 0.765111 (0.7651) | **0.7651** | **ALIGNED** |
| **Average Precision (PR-AUC)** | 0.7712 | 0.730769 (0.7308) | **0.7308** | **ALIGNED** |
| **Brier Score** | 0.1685 | 0.196994 (0.1970) | **0.1970** | **ALIGNED** |
| **Confusion Matrix (TN)** | 571 (38.07%) | 571 (38.07%) | **571 (38.07%)** | **VERIFIED** |
| **Confusion Matrix (FP)** | 258 (17.20%) | 258 (17.20%) | **258 (17.20%)** | **VERIFIED** |
| **Confusion Matrix (FN)** | 208 (13.87%) | 208 (13.87%) | **208 (13.87%)** | **VERIFIED** |
| **Confusion Matrix (TP)** | 463 (30.87%) | 463 (30.87%) | **463 (30.87%)** | **VERIFIED** |
| **RF `n_estimators`** | 200 | 150 (Fitted Pipeline Step `clf`) | **150** | **ALIGNED** |
| **RF `max_depth`** | 12 / 15 | 8 (Fitted Pipeline Step `clf`) | **8** | **ALIGNED** |
| **RF `min_samples_split`** | 5 / 10 | 2 (Fitted Pipeline Step `clf`) | **2** | **ALIGNED** |
| **RF `min_samples_leaf`** | 2 | 5 (Fitted Pipeline Step `clf`) | **5** | **ALIGNED** |

---

## 4. MATHEMATICAL VERIFICATION OF CONFUSION MATRIX CONSISTENCY

From the verified confusion matrix:
$$TN = 571, \quad FP = 258, \quad FN = 208, \quad TP = 463, \quad N = 1,500$$

1. **Total Population Balance:**
   $$TN + FP + FN + TP = 571 + 258 + 208 + 463 = 1,500 \quad \checkmark$$
2. **Actual Ground Truth Classes:**
   * Retained ($y = 0$): $TN + FP = 571 + 258 = 829$ instances ($55.27\%$).
   * Churned ($y = 1$): $FN + TP = 208 + 463 = 671$ instances ($44.73\%$).
   * Total: $829 + 671 = 1,500 \quad \checkmark$
3. **Predicted Classes at $\tau = 0.50$:**
   * Predicted Retained ($\hat{y} = 0$): $TN + FN = 571 + 208 = 779$ instances ($51.93\%$).
   * Predicted Churned ($\hat{y} = 1$): $FP + TP = 258 + 463 = 721$ instances ($48.07\%$).
   * Total: $779 + 721 = 1,500 \quad \checkmark$
4. **Accuracy:**
   $$\text{Accuracy} = \frac{TP + TN}{N} = \frac{463 + 571}{1500} = \frac{1034}{1500} \approx 0.689333 \implies \mathbf{68.93\%} \quad \checkmark$$
5. **Precision (Positive Predictive Value):**
   $$\text{Precision} = \frac{TP}{TP + FP} = \frac{463}{463 + 258} = \frac{463}{721} \approx 0.642164 \implies \mathbf{64.22\%} \quad \checkmark$$
6. **Recall (Sensitivity / True Positive Rate):**
   $$\text{Recall} = \frac{TP}{TP + FN} = \frac{463}{463 + 208} = \frac{463}{671} \approx 0.690015 \implies \mathbf{69.00\%} \quad \checkmark$$
7. **Specificity (True Negative Rate):**
   $$\text{Specificity} = \frac{TN}{TN + FP} = \frac{571}{571 + 258} = \frac{571}{829} \approx 0.688782 \implies \mathbf{68.88\%} \quad \checkmark$$
8. **Balanced Accuracy:**
   $$\text{Balanced Accuracy} = \frac{\text{Recall} + \text{Specificity}}{2} = \frac{0.690015 + 0.688782}{2} = 0.689398 \implies \mathbf{68.94\%} \quad \checkmark$$
9. **F1-Score (Harmonic Mean):**
   $$\text{F1} = 2 \times \frac{\text{Precision} \times \text{Recall}}{\text{Precision} + \text{Recall}} = 2 \times \frac{0.642164 \times 0.690015}{0.642164 + 0.690015} = \frac{0.886205}{1.332179} \approx \mathbf{0.6652} \quad \checkmark$$

All metrics are now 100% mathematically congruent across the dataset, API response, UI presentation, and documentation.

---

## 5. FILES CHANGED

1. **`backend/app/routes/analytics.py`:**
   * Corrected `hyperparameters` dictionary to match fitted pipeline steps (`n_estimators: 150`, `max_depth: 8`, `min_samples_split: 2`, `min_samples_leaf: 5`).
2. **`frontend/src/components/dashboard/AnalyticsPerformance.jsx`:**
   * Bound sub-labels dynamically to `confusion_matrix` (`{confusion_matrix.true_positives} / {confusion_matrix.true_positives + confusion_matrix.false_negatives} churners`, etc.).
   * Bound confusion matrix percentages dynamically to `(value / perfData.sample_size) * 100`.
3. **`reports/phase8/PHASE_RETAINIQ_UNSLOP_STAGE_5_REPORT.md`:**
   * Corrected Section 3.7 documentation to accurately reflect the authoritative independent test metrics (Accuracy: 68.93%, Balanced Accuracy: 68.94%, Specificity: 68.88%, ROC-AUC: 0.7651, PR-AUC: 0.7308, Brier Score: 0.1970).

---

## 6. VERIFICATION EVIDENCE

| Test Suite / Build Step | Scope | Result | Execution Time |
| :--- | :--- | :--- | :--- |
| **Frontend Unit Test Suite** | `npm test -- --run` (37 suites, 101 tests) | **101 / 101 PASSED** (0 failed) | 433.31 ms |
| **Production Bundle Compiler**| `npm run build` (Vite 6.4.6, 2,070 modules) | **✓ BUILT CLEANLY** (Exit code 0) | 7.20 s |
| **Backend Test Suite** | `pytest tests/test_all_phases.py tests/ -q` | **297 / 297 PASSED** (0 failed) | 43.57 s |
| **FastAPI REST Endpoint** | `GET /api/v1/analytics/model-performance` | **HTTP 200 OK** (Exact matching metrics) | < 50 ms |

---

## 7. UNRESOLVED DISCREPANCIES

* **Zero unresolved discrepancies remain.**
* All components, backend models, JSON artifacts, and reports are in absolute alignment.

---

## 8. INVARIANTS STATUS & STOP CONDITION

* **Locked Model:** `models/phase5_1/final_model/final_churn_rf_pipeline.joblib` (SHA-256: `24F1F0E33C75B5590906369960DB6E5951EC95DF9AE40384DA60082B3438F301`) unmodified.
* **Locked Decision Boundary:** Strictly $\tau = 0.50$.
* **STOP CONDITION:** Audit complete. Stage 6 (Administrator Portal) has NOT been started. Awaiting explicit user review and approval.
