# Phase 5.1 — Checkpoint 2: Independent Synthetic Evaluation Cohort Report

**Project:** Indian E-Commerce Customer Retention Intelligence System Using Machine Learning  
**Workspace:** `C:\customer churn retention system`  
**Milestone:** Phase 5.1 — Checkpoint 2 & 2.1: Independent Synthetic Test Cohort Audit  
**Date:** November 19, 2026  
**Status:** AUDITED, CORRECTED & SEALED  

---

## 1. Executive Summary & Objective

In Phase 5, the model evaluation protocol evaluated eight trained supervised pipelines and tuned decision thresholds on the validation set, refitting the selected model on combined training and validation data and assessing final performance on `data/modeling/test.csv`. 

To support Phase 5.1 advanced model optimization experiments without data snooping or selection bias on historical evaluation sets, an **independent synthetic evaluation cohort** of exactly $N = 1,500$ customers was generated. 

This dataset has been generated with a distinct pseudorandom seed (`2026`), assigned isolated identifier ranges, validated across 14 automated integrity assertions, and permanently sealed in `data/independent_test/raw/`. It has been read solely for structural integrity auditing and cryptographic verification; it remains strictly sealed against model training, feature selection, hyperparameter tuning, decision threshold optimization, and performance scoring until the final Phase 5.1 milestone.

---

## 2. Cohort Specification & Generation Parameters

The independent cohort was synthesized using generative logic in `backend/ml/generate_independent_cohort.py`, mirroring the real-world behavioral dynamics of Indian e-commerce platforms while ensuring non-overlapping pseudorandom paths.

| Parameter | Specification | Verification Result |
| :--- | :--- | :--- |
| **Generation Script** | `backend/ml/generate_independent_cohort.py` | Executed successfully |
| **Validation Script** | `backend/ml/validate_independent_cohort.py` | 14 / 14 checks passed |
| **Random Seed** | `2026` | Isolated instance (`np.random.default_rng(2026)`) |
| **Customer Population ($N$)** | Exactly 1,500 | 1,500 unique rows verified |
| **Customer ID Range** | `IND_CUST_50001` through `IND_CUST_51500` | Fully contiguous, zero gaps |
| **Total Orders Generated** | 17,585 orders | 100% unique order records |
| **Order ID Range** | `ORD_500001` through `ORD_517585` | Fully contiguous, zero gaps |
| **Verified Signup Date Range** | `2023-01-18` to `2025-12-25` | Observed in generated data (all prior to snapshot cutoff) |
| **Order History Window** | `2023-02-16` to `2025-12-31` | 15,082 historical transactions |
| **Snapshot Cutoff Date** | `2025-12-31` | Invariant across all 1,500 customer records |
| **Future Label Window** | `2026-01-01` to `2026-03-31` (90 days) | 2,503 future transactions |

---

## 3. Strict Set Disjointness & Identity Isolation

To prevent identifier collision or cross-contamination with historical Phase 1–5 datasets:

- **Customer ID Set Disjointness:**  
  $$\{ \text{customer\_id}_{\text{Phase 1}} \} \cap \{ \text{customer\_id}_{\text{Independent}} \} = \emptyset$$  
  Phase 1 customers span `IND_CUST_10001`–`IND_CUST_17000` ($N = 7,000$). Independent customers span `IND_CUST_50001`–`IND_CUST_51500` ($N = 1,500$). The intersection is exactly $0$ records.

- **Order ID Set Disjointness:**  
  $$\{ \text{order\_id}_{\text{Phase 1}} \} \cap \{ \text{order\_id}_{\text{Independent}} \} = \emptyset$$  
  Phase 1 orders span `ORD_100001`–`ORD_184225` ($84,225$ orders). Independent orders span `ORD_500001`–`ORD_517585` ($17,585$ orders). The intersection is exactly $0$ records.

- **Referential Integrity:**  
  $100\%$ of the $17,585$ transactions reference valid customer IDs within the `IND_CUST_50001`–`IND_CUST_51500` domain. Zero orphaned order records exist.

---

## 4. Ground Truth Churn Target Consistency

The target label `churn` was audited against transactional reality during the 90-day future evaluation window (`2026-01-01` to `2026-03-31`):

$$\text{churn} = 1 \iff \sum_{t \in \text{future}} \mathbf{1}_{\{\text{order}_t\}} = 0$$

- **Audit of Churned Customers ($n = 671$):**  
  Every single customer with $\text{churn} = 1$ has exactly $0$ transactions between January 1, 2026 and March 31, 2026. Zero churned customers placed future orders.
- **Audit of Retained Customers ($n = 829$):**  
  Every single customer with $\text{churn} = 0$ completed at least $1$ transaction (mean: $3.02$ orders, max: $9$ orders) in the 90-day window. Zero retained customers have zero future orders.
- **Mathematical Equivalence:** Strict equivalence $\text{churn} = 1 \iff \text{FutureOrders} = 0$ is $100.0\%$ preserved.

---

## 5. Descriptive Statistical Comparison (Phase 1 vs. Independent Cohort)

To verify that the independent cohort was synthesized from consistent behavioral mechanics without identity leakage, statistical distribution checks were conducted comparing the Phase 1 cohort ($N=7,000$) and the Independent cohort ($N=1,500$):

### 5.1 Churn Class Distribution
- **Phase 1 Cohort:** $3,207$ churned ($45.81\%$), $3,793$ retained ($54.19\%$)
- **Independent Cohort:** $671$ churned ($44.73\%$), $829$ retained ($55.27\%$)
- **Chi-Square Contingency Test:**  
  $$\chi^2 = 0.5391, \quad p\text{-value} = 0.4628 \quad (p > 0.05)$$  
  **Interpretation:** No statistically significant difference in churn class proportion was detected between cohorts at the $\alpha = 0.05$ significance level. This failure to reject the null hypothesis demonstrates statistical consistency, but does not prove distributional identity.

### 5.2 Order Status Distribution
| Order Status | Phase 1 Count | Phase 1 Pct | Independent Count | Independent Pct |
| :--- | :--- | :--- | :--- | :--- |
| **Delivered** | 74,335 | 88.26% | 15,432 | 87.76% |
| **Returned** | 5,779 | 6.86% | 1,282 | 7.29% |
| **Cancelled** | 4,111 | 4.88% | 871 | 4.95% |
| **Total** | 84,225 | 100.00% | 17,585 | 100.00% |

### 5.3 Payment Method Proportions
| Payment Method | Phase 1 Proportion | Independent Proportion | Absolute Difference |
| :--- | :--- | :--- | :--- |
| **UPI** | 45.85% | 45.90% | +0.05% |
| **COD** | 24.24% | 24.00% | -0.24% |
| **Credit Card** | 14.13% | 14.17% | +0.04% |
| **Debit Card** | 7.89% | 7.78% | -0.11% |
| **Net Banking** | 4.90% | 5.14% | +0.24% |
| **Wallet** | 3.00% | 3.01% | +0.01% |

### 5.4 Continuous Feature Checks & Methodological Limitations
- **Customer-Level Orders Per Customer Kolmogorov-Smirnov Test:**  
  $$KS = 0.0120, \quad p\text{-value} = 0.9939 \quad (p > 0.05)$$  
  Customer-level observations are independent between accounts; no statistically significant divergence in purchase counts was detected.
- **Order-Level Order Amount (INR) Kolmogorov-Smirnov Test:**  
  $$KS = 0.0055, \quad p\text{-value} = 0.7777 \quad (p > 0.05)$$  
  > **METHODOLOGICAL LIMITATION & INDEPENDENCE CAVEAT:**  
  > The two-sample Kolmogorov-Smirnov test formally assumes independent and identically distributed (i.i.d.) observations. Transactions within `orders.csv` and `orders_independent.csv` are clustered by customer (repeated measures per account with intra-customer behavioral correlation). Treating clustered transactions as independent observations violates the strict i.i.d. assumption.  
  > Therefore, the order-level KS test must be interpreted purely as a **heuristic descriptive check** of empirical alignment, not as mathematical proof of distributional equivalence.

---

## 6. Cryptographic Manifest & Integrity Hashes

The generated independent cohort files and manifest have been hashed using SHA-256:

| Artifact | File Path | File Size | SHA-256 Checksum |
| :--- | :--- | :--- | :--- |
| **Independent Customers** | `data/independent_test/raw/customers_independent.csv` | 134,167 bytes | `D3B694F9F3488BB1CAF81C49603A9E322396F48ADDBA6E96246BD91B211F53B4` |
| **Independent Orders** | `data/independent_test/raw/orders_independent.csv` | 1,738,197 bytes | `BE7B293A283A90E7AC78F92D681BE4D0ACA58C3CC2235BCC7EDCBF2348FBAF8E` |
| **Independent Manifest** | `data/independent_test/raw/independent_cohort_manifest.json` | 1,424 bytes | `6320757631ED9F8A598D32EFD8EA7CB095960B9885517F2FCAA80A1FA2FA236C` |

Simultaneously, the Phase 1 raw data files and Phase 5 final model were verified to be cryptographically unmodified:

| Prior Artifact | File Path | Expected SHA-256 | Verified Match |
| :--- | :--- | :--- | :--- |
| **Phase 1 Customers** | `data/raw/customers.csv` | `DF6219AA4E2BDDE8FFF419272B9F2C1DE0602473248619E90566BC7D498AB70E` | **MATCH (Invariant)** |
| **Phase 1 Orders** | `data/raw/orders.csv` | `AB632B3092F732B3B25BAAD096B191C1ACA777CB8D42B29EABB815A266C558E7` | **MATCH (Invariant)** |
| **Phase 5 Final Model** | `models/phase5/final_churn_pipeline.joblib` | `25B91797F8F36DB605BAB98B8568A5911847B8CCE77334A68AE4E3862CD3B35D` | **MATCH (Invariant)** |

---

## 7. Seal Declaration & Protocol Adherence

> **FORMAL SEAL DECLARATION:**  
> The independent test cohort in `data/independent_test/raw/` has been read solely for structural integrity auditing, foreign-key verification, and cryptographic hash verification.
> 
> It remains strictly **SEALED** against:
> 1. **Predictive Model Training:** No supervised learning algorithm will fit parameters or coefficients on these records.
> 2. **Feature Selection:** No pruning, correlation selection, or feature ranking will be informed by these records.
> 3. **Hyperparameter Tuning:** No optimization search (grid, randomized, or Bayesian) will evaluate against this cohort.
> 4. **Threshold Optimization:** No decision threshold or classification cutoff will be tuned using these records.
> 5. **Model-Performance Evaluation:** No forward inference or metric scoring will be conducted until the final Phase 5.1 evaluation milestone.
> 
> All Phase 5.1 model exploration in Checkpoints 3 and 4 will be restricted strictly to the development datasets (`train.csv` and `validation.csv`, combined $N = 5,950$). The original Phase 5 test dataset (`data/modeling/test.csv`, $N = 1,050$) remains an untouched historical benchmark.

---

## 8. Checkpoint 2.1 — Integrity and Methodology Corrections

During the Checkpoint 2.1 independent technical audit, the following findings, verifications, and corrections were resolved:

1. **Signup Date Inconsistency Corrected:**  
   The prior draft cited an unverified range ("February 2023 through October 2025" and "2023-01-01 to 2025-10-31"). Direct inspection of `customers_independent.csv` established that the actual observed customer registration dates span from **January 18, 2023** (`2023-01-18`) through **December 25, 2025** (`2025-12-25`). All signups occur strictly prior to the snapshot cutoff date of `2025-12-31`.

2. **Randomness and Reproducibility Verified:**  
   Inspection of `generate_independent_cohort.py` verified that random generation relies strictly on isolated generator instances:
   ```python
   rng_np = np.random.default_rng(seed)
   rng_py = random.Random(seed)
   ```
   No global NumPy random state (`np.random.seed` or `np.random.choice`) is used.  
   To prove reproducibility without modifying the sealed cohort, the generation process was executed inside an isolated temporary directory:
   - Seed `2026` produced output files byte-for-byte identical to `customers_independent.csv` (`D3B694F9F3488BB1CAF81C49603A9E322396F48ADDBA6E96246BD91B211F53B4`) and `orders_independent.csv` (`BE7B293A283A90E7AC78F92D681BE4D0ACA58C3CC2235BCC7EDCBF2348FBAF8E`).
   - A different seed (`2027`) produced entirely distinct customer profiles (`ECB02CF1...`) and order histories (`F6D69133...`).
   - The Phase 1 generator (`backend/ml/generate_data.py`) default seed (`42`) and outputs remain 100% invariant.

3. **Statistical Interpretation Language Corrected:**  
   Statements claiming that hypothesis tests proved "identical distributions" were revised. Non-significant test outcomes ($\chi^2 = 0.5391, p = 0.4628$; $KS = 0.0055, p = 0.7777$) indicate that no statistically significant differences were detected given the sample size, which does not constitute proof of distributional identity.

4. **Clustering Limitation Disclosed:**  
   The order-level Kolmogorov-Smirnov test does not account for customer-level clustering. Repeated transactions by the same customer violate observation independence; the order-level test is therefore documented as a heuristic check rather than a formal proof.

5. **Clarified Sealing Definition:**  
   The definition of "sealed" was explicitly refined to distinguish between permitted read-only structural validation (verifying row counts, dates, disjointness, hashes) and prohibited predictive interactions (model training, feature selection, hyperparameter tuning, threshold optimization, and performance scoring).
