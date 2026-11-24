# Phase 5.1 — ML System Completion Report & Web Integration Contract

**Project:** Indian E-Commerce Customer Retention Intelligence System Using Machine Learning  
**Workspace:** `C:\customer churn retention system`  
**Python Environment:** `backend\.venv\Scripts\python.exe`  
**Milestone:** Phase 5.1 — Checkpoint 4 (ML System Completion)  
**Date:** November 19, 2026  
**Auditor & Lead:** Senior ML Engineer, Model Validation Auditor and Project Lead  
**Status:** **MACHINE LEARNING DEVELOPMENT OFFICIALLY COMPLETE — READY FOR BACKEND INTEGRATION**  

---

## 1. Executive Summary & Project Sign-Off

With the successful execution and automated validation of Phase 5.1 Checkpoint 4, the **Machine Learning pipeline development is officially complete**.

The machine learning system has evolved across 5 structured phases:
* **Phase 1 & 2:** Rigorous exploratory data analysis and synthetic cohort generation with strict zero-leakage temporal boundaries (Snapshot: December 31, 2025; Label Window: Q1 2026).
* **Phase 3:** Feature engineering pipeline capturing 34 baseline behavioral and financial signals.
* **Phase 4:** Unsupervised customer segmentation discovering 5 distinct Indian e-commerce personas via K-Means ($K=5$) on normalized RFM metrics.
* **Phase 5:** Baseline model development establishing an initial regularized Logistic Regression benchmark ($66.95\%$ accuracy on historical test set).
* **Phase 5.1:** Advanced optimization implementing velocity momentum ratios, operational friction indices, within-fold correlation pruning, and rigorous 5x3 nested cross-validation across 12 candidate pipelines, culminating in the lock and single-shot independent evaluation of the **Random Forest Configuration D** pipeline.

---

## 2. Final Approved Production Model Specifications

| Component | Final Specification |
| :--- | :--- |
| **Model Algorithm** | `RandomForestClassifier` (`sklearn.ensemble.RandomForestClassifier`) |
| **Pipeline Architecture** | `Pipeline(steps=[('preprocessor', ColumnTransformer), ('clf', RandomForestClassifier)])` |
| **Feature Configuration** | Configuration D (34 Baseline Numerical + 6 Advanced Numerical + 3 Categorical + Log1p + CorrelationPruner at 0.85) |
| **Training Dataset** | Full Development Cohort ($N = 5,950$ customers combining train + validation) |
| **Fitted Sample Size** | 5,950 records (all 150 tree root node sample weights = 5,950.0) |
| **Locked Threshold** | **$\tau = 0.50$** (Pre-locked standard decision threshold) |
| **Original Model Path** | [random_forest_config_d_pipeline.joblib](file:///c:/customer%20churn%20retention%20system/models/phase5_1/checkpoint3/random_forest_config_d_pipeline.joblib) |
| **Production Model Path** | [final_churn_rf_pipeline.joblib](file:///c:/customer%20churn%20retention%20system/models/phase5_1/final_model/final_churn_rf_pipeline.joblib) |
| **Cryptographic SHA-256** | `24F1F0E33C75B5590906369960DB6E5951EC95DF9AE40384DA60082B3438F301` |
| **Segmentation Scaler** | [segmentation_scaler.joblib](file:///c:/customer%20churn%20retention%20system/models/segmentation_scaler.joblib) |
| **K-Means Model** | [kmeans_customer_segmentation.joblib](file:///c:/customer%20churn%20retention%20system/models/kmeans_customer_segmentation.joblib) |
| **Hyperparameters** | `n_estimators=150, max_depth=8, min_samples_leaf=5, class_weight='balanced', random_state=42` |

---

## 3. Independent Evaluation Scorecard

Evaluated on the sealed independent synthetic test cohort ($N = 1,500$ customers) at the locked threshold $\tau = 0.50$:

```
INDEPENDENT EVALUATION SCORECARD (N = 1,500)
┌───────────────────────────────────────┬──────────────┬────────────────────────┐
│ Metric                                │ Actual Value │ Reconciliation         │
├───────────────────────────────────────┼──────────────┼────────────────────────┤
│ Accuracy                              │   68.93%     │ 1,034 / 1,500 correct  │
│ Recall (Sensitivity)                  │   69.00%     │ 463 / 671 churn caught │
│ Precision (PPV)                       │   64.22%     │ 463 / 721 flags true   │
│ Specificity (TNR)                     │   68.88%     │ 571 / 829 retained OK  │
│ Balanced Accuracy                     │   68.94%     │ (69.00% + 68.88%) / 2  │
│ F1-Score                              │   0.6652     │ Harmonic mean of P & R │
│ ROC-AUC                               │   0.7651     │ Overall discrimination │
│ Average Precision (PR-AUC)            │   0.7308     │ Precision-Recall curve │
│ False Positive Rate (FPR)             │   31.12%     │ 258 false alarms       │
│ False Negative Rate (FNR)             │   31.00%     │ 208 missed churners    │
│ Brier Score (Calibration)             │   0.1970     │ Probability MSE        │
└───────────────────────────────────────┴──────────────┴────────────────────────┘
```

---

## 4. Frontend & Backend Inference Contract (FastAPI Integration)

This section provides the exact technical specification for tomorrow's web application development (FastAPI backend and UI integration).

### 4.1 System Inference Architecture
```
                                INFERENCE WORKFLOW
                                        │
           Raw Customer & Order Data (JSON payload from Frontend/API)
                                        │
                                        ▼
   ┌────────────────────────────────────────────────────────────────────────┐
   │ 1. Feature Engineering:                                                │
   │    Compute tenure, recency, order counts, returns, discounts, delays   │
   └────────────────────────────────────┬───────────────────────────────────┘
                                        │
                                        ▼
   ┌────────────────────────────────────────────────────────────────────────┐
   │ 2. RFM Cluster Assignment:                                             │
   │    - recency_delivered_days (fillna with 1117.0)                       │
   │    - log_rfm = log1p([recency, delivered_count, delivered_spend])      │
   │    - X_scaled = segmentation_scaler.transform(log_rfm)                 │
   │    - cluster_id = kmeans_model.predict(X_scaled)[0]                    │
   └────────────────────────────────────┬───────────────────────────────────┘
                                        │
                                        ▼
   ┌────────────────────────────────────────────────────────────────────────┐
   │ 3. Advanced Behavioral Features:                                       │
   │    - velocity_ratio_30_90 = (orders_30 + 0.1)/(orders_90/3 + 0.1)     │
   │    - velocity_ratio_90_180 = (orders_90 + 0.1)/(orders_180/2 + 0.1)   │
   │    - delay_friction_score = avg_delay * (1 + return_rate + cancel_rate)│
   └────────────────────────────────────┬───────────────────────────────────┘
                                        │
                                        ▼
   ┌────────────────────────────────────────────────────────────────────────┐
   │ 4. Model Inference:                                                    │
   │    Pass exact 43-column DataFrame to pipeline.predict_proba()          │
   │    prob = pipeline.predict_proba(X)[:, 1][0]                           │
   │    churn_prediction = 1 if prob >= 0.50 else 0                         │
   └────────────────────────────────────┬───────────────────────────────────┘
                                        │
                                        ▼
   JSON Response (Churn Probability, Risk Tier, Key Drivers, Recommendations)
```

### 4.2 Required Input Feature Schema (43 Raw Columns)
The model expects a pandas DataFrame containing exactly the following 43 columns in any column order (the internal `ColumnTransformer` handles sub-column selection):

#### Numerical Inputs (40 Columns)
1. `customer_tenure_days` (float/int): Days since account signup.
2. `has_historical_orders` (int, 0 or 1): 1 if customer placed $\ge 1$ order, 0 otherwise.
3. `recency_days` (float): Days since most recent order of any status.
4. `recency_delivered_days` (float, nullable): Days since most recent *delivered* order (NaN for zero-delivered accounts).
5. `has_delivered_order` (int, 0 or 1): 1 if customer has $\ge 1$ delivered order, 0 otherwise.
6. `hist_order_count` (int): Total lifetime orders placed.
7. `hist_delivered_order_count` (int): Total delivered lifetime orders.
8. `hist_returned_order_count` (int): Total returned orders.
9. `hist_cancelled_order_count` (int): Total cancelled orders.
10. `hist_total_order_value_inr` (float): Gross lifetime transaction spend in INR.
11. `hist_delivered_order_value_inr` (float): Net delivered lifetime spend in INR.
12. `hist_total_recorded_discount_inr` (float): Total discounts availed in INR.
13. `hist_average_order_value_inr` (float): Lifetime average order value in INR.
14. `orders_last_30_days` (int): Orders placed in the last 30 days.
15. `orders_last_90_days` (int): Orders placed in the last 90 days.
16. `orders_last_180_days` (int): Orders placed in the last 180 days.
17. `delivered_orders_last_30_days` (int): Delivered orders in the last 30 days.
18. `delivered_orders_last_90_days` (int): Delivered orders in the last 90 days.
19. `delivered_orders_last_180_days` (int): Delivered orders in the last 180 days.
20. `hist_return_rate` (float, nullable): Ratio of returned orders to delivered orders (NaN for zero-delivered).
21. `hist_cancellation_rate` (float, nullable): Ratio of cancelled orders to total orders (NaN for zero-order).
22. `hist_average_delivery_delay_days` (float, nullable): Average delivery delay past promised delivery date (NaN for zero-delivered).
23. `hist_delivery_delay_missing_count` (int): Count of delivered orders with missing delay records.
24. `hist_delivery_delay_missing_rate` (float): Proportion of delivered orders with missing delay records.
25. `hist_average_discount_amount_inr` (float): Average discount amount per order.
26. `hist_discounted_order_count` (int): Count of orders where discounts were applied.
27. `hist_discount_missing_count` (int): Count of orders with missing discount values.
28. `hist_discount_missing_rate` (float): Proportion of orders with missing discount values.
29. `hist_payment_missing_count` (int): Count of orders with missing payment method.
30. `hist_payment_missing_rate` (float): Proportion of orders with missing payment method.
31. `hist_cod_order_count` (int): Lifetime orders paid via Cash on Delivery.
32. `hist_cod_usage_rate` (float): Proportion of lifetime orders paid via COD.
33. `hist_upi_order_count` (int): Lifetime orders paid via UPI.
34. `hist_upi_usage_rate` (float): Proportion of lifetime orders paid via UPI.
35. `velocity_ratio_30_90` (float, nullable): Momentum ratio: $\frac{\text{orders}_{30} + 0.1}{\text{orders}_{90}/3 + 0.1}$ (NaN if $\text{orders}_{90} == 0$).
36. `velocity_ratio_90_180` (float, nullable): Momentum ratio: $\frac{\text{orders}_{90} + 0.1}{\text{orders}_{180}/2 + 0.1}$ (NaN if $\text{orders}_{180} == 0$).
37. `has_orders_last_90_days` (int, 0 or 1): 1 if $\text{orders}_{90} > 0$, else 0.
38. `has_orders_last_180_days` (int, 0 or 1): 1 if $\text{orders}_{180} > 0$, else 0.
39. `delay_friction_score` (float, nullable): Friction index: $\text{delay} \times (1 + \text{return\_rate} + \text{cancel\_rate})$ (NaN if zero delivered).
40. `missing_friction_score` (int, 0 or 1): 1 if delay_friction_score is NaN, else 0.

#### Categorical Inputs (3 Columns)
41. `city` (string): Customer city (e.g., "Bengaluru", "Delhi", "Mumbai", or "Unknown").
42. `state` (string): Customer state (e.g., "Karnataka", "Maharashtra", or "Unknown").
43. `cluster_id` (int/string): RFM persona cluster ID (0, 1, 2, 3, or 4).

### 4.3 Missing-Value Semantics Handled Internally
The production pipeline automatically and safely handles missing values using its internal `SimpleImputer(strategy='median', add_indicator=True)` and categorical `OneHotEncoder(handle_unknown='ignore')`. The API does not need to impute numerical fields manually before passing them to the pipeline.

### 4.4 Model Loading and Inference Code Pattern (Python / FastAPI)
```python
import joblib
import numpy as np
import pandas as pd

# Load frozen model artifacts at server startup
MODEL_PATH = "models/phase5_1/final_model/final_churn_rf_pipeline.joblib"
SCALER_PATH = "models/segmentation_scaler.joblib"
KMEANS_PATH = "models/kmeans_customer_segmentation.joblib"

pipeline = joblib.load(MODEL_PATH)
segmentation_scaler = joblib.load(SCALER_PATH)
kmeans_model = joblib.load(KMEANS_PATH)
LOCKED_THRESHOLD = 0.50


def assign_rfm_cluster(recency_deliv, deliv_count, deliv_spend):
    """Assigns RFM cluster ID using Phase 4 K-Means pipeline."""
    # Impute recency if customer has 0 delivered orders
    rec_val = 1117.0 if (pd.isna(recency_deliv) or recency_deliv is None) else float(recency_deliv)
    log_rfm = np.log1p([[rec_val, float(deliv_count), float(deliv_spend)]])
    scaled_rfm = segmentation_scaler.transform(log_rfm)
    return int(kmeans_model.predict(scaled_rfm)[0])


def predict_churn(customer_features_df: pd.DataFrame):
    """
    Accepts a 1-row DataFrame containing all 43 required Config D features.
    Returns probability, prediction class, and risk level.
    """
    prob = float(pipeline.predict_proba(customer_features_df)[:, 1][0])
    is_churn = 1 if prob >= LOCKED_THRESHOLD else 0

    # Risk Tiering logic for frontend visualization
    if prob >= 0.70:
        risk_tier = "High Risk"
        recommendation = "Immediate intervention: personalized discount offer or VIP support outreach."
    elif prob >= 0.50:
        risk_tier = "Moderate Risk"
        recommendation = "Targeted retention: re-engagement push notification with relevant category discounts."
    elif prob >= 0.30:
        risk_tier = "Low Risk"
        recommendation = "Standard loyalty engagement: regular promotional newsletters."
    else:
        risk_tier = "Very Low Risk"
        recommendation = "High loyalty: premium customer cross-selling or referral incentives."

    return {
        "churn_probability": round(prob, 4),
        "is_churn_predicted": is_churn,
        "decision_threshold": LOCKED_THRESHOLD,
        "risk_tier": risk_tier,
        "retention_recommendation": recommendation,
    }
```

### 4.5 Sample Prediction Request and Response Payload

#### Sample Request Payload (`POST /api/v1/predict`)
```json
{
  "customer_id": "IND_CUST_99001",
  "city": "Bengaluru",
  "state": "Karnataka",
  "customer_tenure_days": 412,
  "has_historical_orders": 1,
  "recency_days": 38.0,
  "recency_delivered_days": 38.0,
  "has_delivered_order": 1,
  "hist_order_count": 8,
  "hist_delivered_order_count": 7,
  "hist_returned_order_count": 1,
  "hist_cancelled_order_count": 0,
  "hist_total_order_value_inr": 14250.0,
  "hist_delivered_order_value_inr": 12800.0,
  "hist_total_recorded_discount_inr": 1500.0,
  "hist_average_order_value_inr": 1781.25,
  "orders_last_30_days": 0,
  "orders_last_90_days": 1,
  "orders_last_180_days": 3,
  "delivered_orders_last_30_days": 0,
  "delivered_orders_last_90_days": 1,
  "delivered_orders_last_180_days": 3,
  "hist_return_rate": 0.1429,
  "hist_cancellation_rate": 0.0,
  "hist_average_delivery_delay_days": 1.2,
  "hist_delivery_delay_missing_count": 0,
  "hist_delivery_delay_missing_rate": 0.0,
  "hist_average_discount_amount_inr": 187.5,
  "hist_discounted_order_count": 5,
  "hist_discount_missing_count": 0,
  "hist_discount_missing_rate": 0.0,
  "hist_payment_missing_count": 0,
  "hist_payment_missing_rate": 0.0,
  "hist_cod_order_count": 2,
  "hist_cod_usage_rate": 0.25,
  "hist_upi_order_count": 5,
  "hist_upi_usage_rate": 0.625,
  "velocity_ratio_30_90": 0.2308,
  "velocity_ratio_90_180": 0.6875,
  "has_orders_last_90_days": 1,
  "has_orders_last_180_days": 1,
  "delay_friction_score": 1.3715,
  "missing_friction_score": 0,
  "cluster_id": 0
}
```

#### Sample Response Payload (`200 OK`)
```json
{
  "customer_id": "IND_CUST_99001",
  "churn_probability": 0.5842,
  "is_churn_predicted": 1,
  "decision_threshold": 0.50,
  "risk_tier": "Moderate Risk",
  "rfm_cluster": {
    "cluster_id": 0,
    "segment_name": "Champions & High-Value Loyalists",
    "description": "High-value buyers with frequent purchases, high spend, and low cancellation rates."
  },
  "behavioral_indicators": {
    "velocity_trend": "Decelerating (Ratio 30/90 = 0.23)",
    "days_since_last_purchase": 38,
    "friction_level": "Low (Score = 1.37)"
  },
  "retention_recommendation": "Targeted retention: re-engagement push notification with relevant category discounts.",
  "model_metadata": {
    "model_family": "RandomForestClassifier",
    "version": "Phase 5.1 Final Candidate",
    "sha256": "24F1F0E33C75B5590906369960DB6E5951EC95DF9AE40384DA60082B3438F301"
  }
}
```

---

## 5. Academic & Viva Limitations for University Presentation

When presenting this project to the academic viva committee, the following disclosures must be highlighted to demonstrate professional machine learning maturity:

1. **Synthetic Data Nature:**  
   The underlying dataset was synthetically generated using realistic Indian e-commerce parameters. While the features realistically simulate order velocities, logistics delays, and UPI/COD payments, real-world customer churn exhibits additional latent complexities (such as app uninstalls, customer support sentiment, and competitive marketing exposure) that are not modeled here.
2. **Latent Oracle Error Ceiling:**  
   Ground-truth churn is governed by individual Bernoulli purchasing decisions with stochastic propensities ranging from 0.08 to 0.94. The oracle error rate conditional on knowing latent customer personas is $26.03\%$ (oracle accuracy ceiling of $73.97\%$). Reaching $68.93\%$ accuracy on an independent test cohort sits within $\approx 5\%$ of this latent theoretical ceiling, demonstrating sound statistical convergence.
3. **Active Customer Transition Uncertainty:**  
   The primary source of false negatives ($70\%$ of all misses) stems from active recent purchasers who cease purchasing abruptly without prior warning signals. Capturing these sudden churn events requires real-time clickstream or session telemetry rather than batch order snapshots.
4. **Pre-Locked Threshold Integrity:**  
   The decision threshold was strictly locked at $0.50$ prior to unsealing the independent test cohort. No post-hoc tuning was performed, confirming that the reported $68.93\%$ accuracy represents genuine, unbiased out-of-sample generalization.

---

## 6. Final ML Milestone Sign-Off

* [x] **Model Lock Verified:** SHA-256 `24F1F0E33C75B5590906369960DB6E5951EC95DF9AE40384DA60082B3438F301`
* [x] **Independent Evaluation Completed:** 1,500 unseen records scored cleanly
* [x] **Validation Suite Passed:** 12/12 automated assertions confirmed in `validate_final_ml.py`
* [x] **FastAPI Inference Contract Documented:** Ready for web backend implementation
* [x] **Academic Disclosures Formalized:** Ready for university presentation

**ML PIPELINE COMPLETE. Awaiting user instruction before starting Phase 6 web integration.**
