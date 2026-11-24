# Phase 3 Feature Engineering & Anti-Leakage Report
## Indian E-Commerce Customer Retention Intelligence System Using Machine Learning

**Academic Evaluation Context:** BCA (Artificial Intelligence & Machine Learning) University End-Semester Project  
**Author:** Technical Machine Learning Development Team  
**Evaluation Date:** 2026-11-19 (Updated with Final Audit Corrections)  
**Snapshot Cutoff Date:** `2025-12-31`  
**Processed Dataset:** `data/processed/customer_features.csv` (7,000 rows × 40 columns)  
**Feature Manifest:** `data/processed/feature_manifest.json`  

---

## 1. Executive Summary & Objective

In Phase 3, we developed, verified, and audited the customer-level feature engineering pipeline ([backend/ml/feature_engineering.py](file:///c:/customer%20churn%20retention%20system/backend/ml/feature_engineering.py)). The objective was to aggregate the multi-year raw transaction history (`orders.csv`, 72,240 historical records) and customer profiles (`customers.csv`, 7,000 records) into a high-dimensional, predictive feature matrix without introducing data leakage.

Every feature was engineered strictly under the **31 December 2025** snapshot boundary. Following an independent technical audit, all requested enhancements—including fulfilled purchase recency (`recency_delivered_days`), delivery fulfillment flag (`has_delivered_order`), zero-order AOV convention (`hist_average_order_value_inr = 0.0`), payment missingness tracking (`hist_payment_missing_count` and `hist_payment_missing_rate`), and predictive role assignment for `city` and `state`—were implemented. All 23 automated validation and anti-leakage tests in [backend/ml/validate_features.py](file:///c:/customer%20churn%20retention%20system/backend/ml/validate_features.py) passed with **0 errors**.

---

## 2. Temporal Boundaries & Anti-Leakage Protocol

```
Historical Observation Window (Features)       Future Ground-Truth Window (Target)
[2023-01-01 -------------------- 2025-12-31] | [2026-01-01 ----------- 2026-03-31]
(72,240 Historical Orders Exclusively Used)   | (11,985 Future Orders - STRICTLY EXCLUDED)
                                             |
                                    SNAPSHOT CUTOFF
```

### Strict Temporal Rules Enforced:
1. **Historical Cutoff:** Every source order contributing to customer behavioral aggregations satisfies:
   $$\text{order\_date} \le \text{2025-12-31}$$
2. **Target Isolation:** The ground-truth target (`churn`) is evaluated strictly in the 90-day window (`2026-01-01` through `2026-03-31`, inclusive).
3. **No Target Contamination:** The target label (`churn`) was completely excluded from feature engineering.
4. **No Premature Global Transformations:** No scalers (StandardScaler, RobustScaler) or imputers were fit on the full 7,000 rows. Feature scaling and imputation will be fit **strictly on training folds** during Phase 5 to eliminate lookahead data leakage.

---

## 3. Feature Taxonomy & Architecture

The processed dataset contains **40 total columns**:
- **2 Identifier Columns:** `customer_id`, `customer_name` (strictly non-predictive).
- **1 Profile Metadata Column:** `signup_date` (account creation date string, non-predictive; its predictive signal is captured in `customer_tenure_days`).
- **1 Ground-Truth Target Label:** `churn` (Binary: 0 = Retained, 1 = Churned).
- **36 Predictive Feature Columns** categorized into distinct behavioral domains:

| Behavioral Domain | Feature Count | Features Included | Primary Analytical Purpose |
|---|---|---|---|
| **Customer Profile** | 4 | `city`, `state`, `customer_tenure_days`, `has_historical_orders` | Captures geographic tier, platform longevity, and account activation status. |
| **RFM: Recency & Fulfillment** | 3 | `recency_days`, `recency_delivered_days`, `has_delivered_order` | Measures order-attempt recency, fulfilled purchase recency, and successful fulfillment status. |
| **RFM: Frequency** | 4 | `hist_order_count`, `hist_delivered_order_count`, `hist_returned_order_count`, `hist_cancelled_order_count` | Distinguishes overall gross orders from successfully completed fulfillment. |
| **RFM: Monetary** | 4 | `hist_total_order_value_inr`, `hist_delivered_order_value_inr`, `hist_total_recorded_discount_inr`, `hist_average_order_value_inr` | Separates gross booking GMV from net delivered value and promotional subsidies. |
| **Purchase Velocity** | 6 | `orders_last_30_days`, `delivered_orders_last_30_days`, `orders_last_90_days`, `delivered_orders_last_90_days`, `orders_last_180_days`, `delivered_orders_last_180_days` | Measures short-term engagement velocity and recent order deceleration across total vs. delivered orders. |
| **Fulfillment & Friction**| 5 | `hist_return_rate`, `hist_cancellation_rate`, `hist_average_delivery_delay_days`, `hist_delivery_delay_missing_count`, `hist_delivery_delay_missing_rate` | Quantifies post-purchase customer dissatisfaction and reverse logistics friction. |
| **Financial & Payment** | 10 | `hist_average_discount_amount_inr`, `hist_discounted_order_count`, `hist_discount_missing_count`, `hist_discount_missing_rate`, `hist_payment_missing_count`, `hist_payment_missing_rate`, `hist_cod_order_count`, `hist_cod_usage_rate`, `hist_upi_order_count`, `hist_upi_usage_rate` | Captures promotional price sensitivity, missing payment tracking, and preferred Indian digital payment modes. |

---

## 4. Rigorous Handling of Edge Cases & Missingness

### A. Zero-History Customers (N = 148, 2.11%)
- **Definition:** Customers who registered prior to 2025-12-31 but never placed an order.
- **Handling Strategy:**
  - `has_historical_orders = 0` (Explicit binary flag).
  - `has_delivered_order = 0` (No delivered orders).
  - `recency_days = NaN` (No order-attempt date exists).
  - `recency_delivered_days = NaN` (No fulfilled purchase date exists).
  - All order counts = `0`, total values = `0.0`, rates = `0.0`.
  - `hist_average_order_value_inr = 0.0` (By deliberate convention: ₹0.00 spent across 0 orders is ₹0.00 AOV).
  - `hist_average_delivery_delay_days = NaN`, `hist_average_discount_amount_inr = NaN`.
  - Preserved transparently for training-fold imputation in Phase 5.

### B. Single-Order Customers (N = 1,830, 26.14%)
- **Definition:** Customers with exactly one historical purchase.
- **Handling Strategy:**
  - `has_historical_orders = 1`.
  - Valid `recency_days` calculated from their sole purchase date.
  - If delivered, `has_delivered_order = 1` and valid `recency_delivered_days`; if cancelled/returned, `has_delivered_order = 0` and `recency_delivered_days = NaN`.
  - Return rate, cancellation rate, COD rate, and UPI rate evaluate cleanly to either `0.0` or `1.0`.

### C. Recency Disambiguation: Attempt Recency vs. Fulfilled Purchase Recency
- In historical orders, 828 customers have a different date for their latest order vs. their latest delivered order (due to cancellations or returns on their most recent order).
- `recency_days`: Measures *engagement / attempt recency* (days since latest order across all statuses).
- `recency_delivered_days`: Measures *fulfilled transaction recency* (days since latest Delivered order). Exactly 6,516 customers have at least one delivered order; 484 customers have NaN (148 zero-history + 336 whose orders were never delivered).

### D. Missing Payment Audit & Tracking
- Exactly 870 historical orders (1.20%) have unrecorded `payment_method`.
- Engineered explicit features: `hist_payment_missing_count` (summing to 870 across all 7,000 customers) and `hist_payment_missing_rate` to capture payment data collection gaps as an informative pattern.

### E. Demographic Missingness
- Missing values in `city` and `state` (46 records, 0.66%) were encoded as `"Unknown"`. Both are categorized as predictive categorical features.

---

## 5. Automated Validation & Anti-Leakage Suite Results

The validation suite ([backend/ml/validate_features.py](file:///c:/customer%20churn%20retention%20system/backend/ml/validate_features.py)) executed 19 structural integrity checks and 4 critical anti-leakage stress tests:

```text
===========================================================================
FEATURE ENGINEERING INTEGRITY & ANTI-LEAKAGE SUITE
===========================================================================
[PASS] Check 01: Processed customer_features.csv exists
       -> Details: data\processed\customer_features.csv
[PASS] Check 02: Exactly 7,000 customer rows
       -> Details: Found 7,000 rows
[PASS] Check 03: Customer IDs are completely unique
       -> Details: Unique IDs: 7,000
[PASS] Check 04: Zero missing customer IDs
       -> Details: Null IDs: 0
[PASS] Check 05: Customer IDs match original raw customers.csv exactly
[PASS] Check 06: Target churn is strictly binary {0, 1} with zero missing values
       -> Details: Churn unique: {0, 1}, Nulls: 0
[PASS] Check 07: Numerical features within valid bounds (Counts >= 0, Rates in [0, 1], Amounts >= 0)
[PASS] Check 08: Customer tenure is strictly non-negative
       -> Details: Min tenure: 6 days
[PASS] Check 09: Order-attempt recency (recency_days) is non-negative and null iff zero-history
       -> Details: Null count: 148, Min recency: 0 days
[PASS] Check 10: Fulfilled recency (recency_delivered_days) non-negative and null iff has_delivered_order == 0
       -> Details: Null count: 484, Min delivered recency: 0 days
[PASS] Check 11: has_delivered_order is binary {0, 1} and 100% consistent with hist_delivered_order_count
       -> Details: Delivered customers: 6,516
[PASS] Check 12: Zero-history AOV convention: hist_average_order_value_inr is exactly 0.0 for zero-order accounts with zero nulls
       -> Details: Zero-order AOV matches: True, Total nulls: 0
[PASS] Check 13: Payment missingness audit: sum matches raw historical orders (870) and rates in [0, 1]
       -> Details: Raw missing: 870, Engineered missing sum: 870
[PASS] Check 14: Order count matches strict historical order subset (order_date <= 2025-12-31)
[PASS] Check 15: Target column 'churn' strictly excluded from predictive features list
       -> Details: 36 predictive features
[PASS] Check 16: Feature manifest documents all 40 columns and specifies verified roles (city/state predictive, IDs identifier, churn target)
       -> Details: Columns: 40, Documented: 40, Roles correct: True
[PASS] Check 17: Exactly one row per customer (Zero duplicates)
[PASS] Check 18: Zero-history customers handled with explicit flags, zero AOV, and clean null recencies (148 customers)
       -> Details: 148 zero-history customers verified
[PASS] Check 19: Single-order customers handled correctly with positive history flag and valid recency (1,830 customers)
       -> Details: 1830 single-order customers verified

---------------------------------------------------------------------------
CRITICAL ANTI-LEAKAGE VERIFICATION TESTS
---------------------------------------------------------------------------
[PASS] Check 20: LEAKAGE TEST A: Source historical orders maximum date <= 2025-12-31
       -> Details: Max historical order date: 2025-12-31
[PASS] Check 21: LEAKAGE TEST B (Strengthened Future Perturbation): In-memory future modification has ZERO impact on features
       -> Details: Zero-history untouched: True, Total divergence across all 36 predictive features: 0.000000
[PASS] Check 22: LEAKAGE TEST C (Target Separation): Target column 'churn' has ZERO influence on feature computation
       -> Details: Feature difference with shuffled target: 0.000000
[PASS] Check 23: LEAKAGE TEST D (Snapshot Consistency): Rolling velocity windows strictly bounded by 2025-12-31
       -> Details: 30-day window max date: 2025-12-31
===========================================================================
ALL 23 VERIFICATION & ANTI-LEAKAGE CHECKS PASSED WITH ZERO ERRORS!
Feature matrix is certified clean, leakage-free, and ready for Phase 4.
===========================================================================
Exit Code: 0
```

---

## 6. Raw Data Immutability Audit

The raw CSV files in `data/raw/` were verified before and after Phase 3 execution:

| Dataset File | Pre-Phase 3 MD5 Hash | Post-Phase 3 MD5 Hash | Status |
|---|---|---|---|
| `data/raw/customers.csv` | `EA39F916F2FA2D432F40F894F63A1715` | `EA39F916F2FA2D432F40F894F63A1715` | **100% Intact** |
| `data/raw/orders.csv` | `7E65B96077288D3DBDA3E50FAF6FD5EB` | `7E65B96077288D3DBDA3E50FAF6FD5EB` | **100% Intact** |

---

## 7. Viva Q&A Guide (BCA Academic Concepts)

> **Viva Question 1: What is Data Leakage, and how did you prevent it during feature engineering?**  
> **Answer:** *"Data leakage occurs when information from outside the training dataset (such as future transactions or the target label itself) is inadvertently introduced into the input features, leading to unrealistically optimistic model metrics that fail in real deployment. We prevented lookahead leakage by establishing a fixed observation snapshot date (2025-12-31) and strictly partitioning raw orders: 72,240 historical orders (<= 2025-12-31) were used for features, while 11,985 future orders (Q1 2026) were strictly reserved for ground-truth churn verification. We programmatically confirmed zero leakage using an automated perturbation test where modifying future orders and injecting orders for zero-history accounts produced exactly 0.000000 divergence in engineered features."*

> **Viva Question 2: Why did you differentiate between order-attempt recency and delivered-purchase recency?**  
> **Answer:** *"In e-commerce, not every order attempt results in a fulfilled purchase. If a customer placed an order 5 days ago that was immediately cancelled, their attempt recency is 5 days, but their last satisfied fulfilled purchase may have been 120 days ago. Conflating the two would mask dissatisfaction and risk of churn. We engineered `recency_days` (latest order attempt across all statuses) and `recency_delivered_days` (latest order with status 'Delivered'). For 828 customers, these two dates diverge, providing powerful churn-predictive signal."*

> **Viva Question 3: How did you handle Average Order Value (AOV) for customers with zero historical orders?**  
> **Answer:** *"For the 148 customers with zero historical orders, their total historical spend is ₹0.00 across 0 orders. Mathematically 0 / 0 is indeterminate (NaN). However, from a business and financial standpoint, their average order value is ₹0.00 because they have spent nothing. Defining `hist_average_order_value_inr = 0.0` for zero-order accounts avoids unnecessary missing-value imputation while remaining mathematically and semantically sound. Their zero-order status is independently captured by the explicit flag `has_historical_orders = 0`."*

> **Viva Question 4: Why didn't you scale features or impute missing values across all 7,000 customers in this phase?**  
> **Answer:** *"Fitting scalers (like StandardScaler) or imputers (like SimpleImputer) on the full dataset before splitting into train/validation/test sets causes Preprocessing Data Leakage, because summary statistics like global mean, standard deviation, and median would leak validation set distribution into the training pipeline. In Phase 3, we aggregated features cleanly and preserved unresolved missingness. In Phase 5, all imputation and scaling transformers will be encapsulated in a Scikit-learn Pipeline and fit strictly on training folds."*
