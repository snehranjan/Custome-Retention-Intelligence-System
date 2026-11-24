# PROJECT CONTEXT: Indian E-Commerce Customer Retention Intelligence System

**Project Title:** Indian E-Commerce Customer Retention Intelligence System Using Machine Learning  
**Academic Context:** BCA (Artificial Intelligence & Machine Learning) Final Year / Capstone University Project  
**Repository / Workspace:** `C:\customer churn retention system`  
**Host Environment:** Windows 11 (64-bit AMD64)  
**Python Runtime:** `backend\.venv\Scripts\python.exe` (Python 3.12.10)  
**Node.js / npm:** Node.js v25.2.1, npm 11.6.2  
**Current Milestone Date:** 19 November 2026  
**Final Development Deadline:** Saturday, 21 November 2026, 6:00 PM  
**Academic Presentation / Viva Date:** 23 November 2026  

---

## 1. Project Purpose & Executive Architecture

The system is an end-to-end Machine Learning intelligence platform designed to predict customer churn, segment customer purchasing behavior, analyze operational friction, and generate targeted retention strategies for Indian e-commerce businesses.

```
                                SYSTEM ARCHITECTURE
                                         │
        ┌────────────────────────────────┴────────────────────────────────┐
        ▼                                                                 ▼
┌───────────────────────────────┐                       ┌──────────────────────────────────┐
│   React Frontend Dashboard    │                       │         FastAPI Backend          │
│   (Vite + Tailwind + Recharts)│ <=== REST / JSON ===> │  (Pydantic + Uvicorn + Security) │
└───────────────────────────────┘                       └─────────────────┬────────────────┘
                                                                          │
                        ┌─────────────────────────────────────────────────┼──────────────────────────────┐
                        ▼                                                 ▼                              ▼
        ┌───────────────────────────────┐               ┌──────────────────────────────────┐   ┌───────────────────────────┐
        │       ML Inference Engine     │               │   Customer Segmentation Engine   │   │  Retention Strategy Engine│
        │ (Random Forest Config D,      │               │ (Phase 4 Scaler + K-Means K=5,   │   │ (Rule-Based + Customer    │
        │  tau=0.50, 43 input features) │               │  5 Indian E-Commerce Personas)   │   │  Lifetime Value Priority) │
        └───────────────────────────────┘               └──────────────────────────────────┘   └───────────────────────────┘
```

---

## 2. Technology Stack & Environment Details

| Layer | Technology | Version / Configuration | Purpose |
| :--- | :--- | :--- | :--- |
| **Language** | Python | 3.12.10 (AMD64) | Isolated virtual environment at `backend\.venv` |
| **Data Processing** | Pandas, NumPy | `pandas 3.1.1`, `numpy 2.0.2` | Feature aggregations and array transformations |
| **Machine Learning** | Scikit-learn, Joblib | `scikit-learn 1.9.1`, `joblib 1.6.0` | Pipeline orchestration, Random Forest, K-Means |
| **Visualization** | Matplotlib, Seaborn | `matplotlib 3.11.2`, `seaborn 0.13.2` | Publication-grade EDA and cluster figures |
| **Backend API** | FastAPI, Pydantic, Uvicorn | `fastapi 0.165.0`, `pydantic 2.14.3`, `pydantic-settings 2.16.3`, `uvicorn 0.54.0` | REST API, inference endpoints, validation |
| **Database & Auth (Planned)**| Supabase PostgreSQL & Auth | Remote cloud service with local fallback | User authentication & persistent storage |
| **Frontend UI (Planned)**| React 19, Vite, Tailwind CSS | Node.js `v25.2.1`, npm `11.6.2` | Modern, responsive analytics dashboard |
| **Test Automation** | Pytest | `pytest 9.2.0` | Master CI test harness (`tests/test_all_phases.py`) |

---

## 3. Completed Development History (Phases 0–5.1)

### Phase 0: Environment & Project Setup (Completed)
* Windows environment diagnosed; virtual environment isolated at `backend\.venv`.
* Standard project directories created: `backend/`, `data/`, `docs/`, `frontend/`, `models/`, `reports/`, and `tests/`.
* Direct interpreter execution pattern established: `backend\.venv\Scripts\python.exe` and `npm.cmd`.

### Phase 1: Synthetic Dataset Generation & Referential Integrity (Completed)
* Generated exactly 7,000 customers (`data/raw/customers.csv`, IDs: `IND_CUST_10001`..`17000`).
* Generated 84,225 orders (`data/raw/orders.csv`, IDs: `ORD_100001`..`184225`).
* Observation snapshot cutoff date: **December 31, 2025**.
* Future evaluation churn window: **January 1, 2026 to March 31, 2026 (90 days)**.
* Churn definition: `churn = 1` if customer placed 0 delivered orders in Q1 2026; `churn = 0` if $\ge 1$.
* Synthetic distribution: Retained: 3,793 ($54.19\%$), Churned: 3,207 ($45.81\%$).
* Referentially certified: 10/10 automated checks passed in `backend/ml/validate_data.py`.

### Phase 2: Exploratory Data Analysis & Visualizations (Completed)
* 15 publication-grade visualization figures exported to `reports/figures/` (`01_churn_distribution.png` through `15_missing_values_summary.png`).
* Strict historical vs. future order partition enforced (72,240 historical vs. 11,985 future orders).
* Full 15-section report compiled in `reports/eda_report.md`.

### Phase 3: Data Cleaning, Predictive Feature Engineering & Anti-Leakage (Completed)
* Aggregated 7,000 customer feature rows with 40 columns (`data/processed/customer_features.csv`).
* Engineered 36 baseline predictive features (tenure, recency, counts, spends, velocities, friction, discounts, UPI/COD channels).
* Anti-leakage verified: Future order perturbation test ($0.0$ divergence) and target separation test ($0.0$ divergence).
* Passed all 23 automated checks in `backend/ml/validate_features.py`.

### Phase 4: RFM Analysis & Unsupervised Customer Segmentation (Completed)
* Unsupervised K-Means clustering with $K = 5$ on normalized $\log(1 + \text{RFM})$ features.
* Saved production scaler (`models/segmentation_scaler.joblib`) and model (`models/kmeans_customer_segmentation.joblib`).
* Multi-seed stability confirmed: Mean Adjusted Rand Index (ARI) = **$0.9931$** across 5 seeds.
* Cleanly isolated all 484 zero-delivered customers into Cluster 2 with 100% purity.
* All 26 checks passed in `backend/ml/validate_segmentation.py`.

#### Approved Official Cluster Mapping:
| Cluster ID | Segment Name | Customer Count | Population % | Behavioral Profile |
| :---: | :--- | :---: | :---: | :--- |
| **0** | **Champions & High-Value Loyalists** | 1,569 | 22.41% | High order count, high spend (AOV ₹1,800+), low returns, low churn |
| **1** | **At-Risk / Lapsed Low-Value Customers** | 1,723 | 24.61% | High recency days, single or few historical orders, high churn propensity |
| **2** | **Zero Delivered-Purchase Customers** | 484 | 6.91% | 148 never-ordered + 336 unfulfilled (cancelled/returned only), recency = 1117.0 |
| **3** | **Steady Core Repeaters** | 2,000 | 28.57% | Consistent repeat buyers, moderate ticket size, balanced payment methods |
| **4** | **Recent Low-Ticket / New Promising Customers** | 1,224 | 17.49% | Low recency days, lower lifetime order count, highly sensitive to discounts |

### Phase 5: Supervised ML Baseline Pipeline (Completed)
* Created stratified splits: Train ($4,900$, $70\%$), Validation ($1,050$, $15\%$), Historical Test ($1,050$, $15\%$) in `data/modeling/`.
* Evaluated Configuration A (36 features) and Configuration B (37 features with `cluster_id`).
* Selected tuned Logistic Regression Configuration B benchmark ($\tau = 0.46$): Test Accuracy: $66.95\%$, Recall: $74.43\%$, ROC-AUC: $0.7491$.
* Passed all 58 automated checks across Phase 5 validation scripts.

### Phase 5.1: Advanced ML Optimization & Independent Evaluation (Completed)
* **Generator Audit:** Proved latent oracle error conditional on knowing latent personas is $26.03\%$ (accuracy ceiling $73.97\%$). On observable features, $R^*(X) \ge 26.03\%$. Arbitrary 80% accuracy target was mathematically unfeasible and was formally abandoned.
* **Independent Test Cohort:** Generated sealed cohort of 1,500 unseen customers (`customers_independent.csv`, IDs: `IND_CUST_50001`..`51500`, SHA-256: `D3B694F9...`).
* **Advanced Features:** Engineered momentum ratios ($R_{30/90}, R_{90/180}$), friction index (`delay_friction_score`), and within-fold `CorrelationPruner(threshold=0.85)` yielding 73 transformed features.
* **5x3 Nested Stratified CV:** Evaluated 12 model-configuration combinations on 5,950 development records. Selected **Random Forest Configuration D** (Nested CV Mean F1: $0.6944$, Accuracy: $71.34\%$, ROC-AUC: $0.7798$).
* **Fitted Sample Size Verification:** Conclusively proved pipeline was refitted on all 5,950 development records (`weighted_n_node_samples == 5950.0`).
* **Model Lock & Single Independent Evaluation:** Locked model at pre-registered threshold $\tau = 0.50$. Scored 1,500 unseen customers once with zero post-hoc tuning:
  * **Test Accuracy:** **$68.93\%$** ($1,034 / 1,500$)
  * **Test Recall:** **$69.00\%$** ($463 / 671$)
  * **Test Precision:** **$64.22\%$** ($463 / 721$)
  * **Test F1-Score:** **$0.6652$**
  * **Test ROC-AUC:** **$0.7651$**
  * **Test PR-AUC:** **$0.7308$**
  * **Confusion Matrix:** **TN = 571, FP = 258, FN = 208, TP = 463**

---

## 4. Final Locked Machine Learning Model

* **Algorithm:** `sklearn.ensemble.RandomForestClassifier`
* **Architecture:** Scikit-learn Pipeline with ColumnTransformer preprocessor:
  `Log1pTransformer -> SimpleImputer(strategy='median', add_indicator=True) -> StandardScaler -> CorrelationPruner(threshold=0.85) -> RandomForestClassifier`
* **Approved Model Artifact:** [random_forest_config_d_pipeline.joblib](file:///c:/customer%20churn%20retention%20system/models/phase5_1/checkpoint3/random_forest_config_d_pipeline.joblib)
* **Production Deployment Copy:** [final_churn_rf_pipeline.joblib](file:///c:/customer%20churn%20retention%20system/models/phase5_1/final_model/final_churn_rf_pipeline.joblib)
* **Cryptographic SHA-256 Checksum:** `24F1F0E33C75B5590906369960DB6E5951EC95DF9AE40384DA60082B3438F301`
* **Locked Decision Threshold:** **$\tau = 0.50$** (Pre-locked standard; no post-hoc tuning)
* **Hyperparameters:** `n_estimators=150, max_depth=8, min_samples_leaf=5, class_weight='balanced', random_state=42`
* **Training Sample Size:** Exactly 5,950 records (all 150 tree root sample weights = 5,950.0)

---

## 5. Model Input Contract (43 Raw Features)

The production pipeline expects a pandas DataFrame containing exactly the following **43 raw columns**:

### 40 Numerical Inputs:
1. `customer_tenure_days`
2. `has_historical_orders`
3. `recency_days`
4. `recency_delivered_days` (nullable, NaN for zero-delivered)
5. `has_delivered_order`
6. `hist_order_count`
7. `hist_delivered_order_count`
8. `hist_returned_order_count`
9. `hist_cancelled_order_count`
10. `hist_total_order_value_inr`
11. `hist_delivered_order_value_inr`
12. `hist_total_recorded_discount_inr`
13. `hist_average_order_value_inr`
14. `orders_last_30_days`
15. `orders_last_90_days`
16. `orders_last_180_days`
17. `delivered_orders_last_30_days`
18. `delivered_orders_last_90_days`
19. `delivered_orders_last_180_days`
20. `hist_return_rate` (nullable)
21. `hist_cancellation_rate` (nullable)
22. `hist_average_delivery_delay_days` (nullable)
23. `hist_delivery_delay_missing_count`
24. `hist_delivery_delay_missing_rate`
25. `hist_average_discount_amount_inr`
26. `hist_discounted_order_count`
27. `hist_discount_missing_count`
28. `hist_discount_missing_rate`
29. `hist_payment_missing_count`
30. `hist_payment_missing_rate`
31. `hist_cod_order_count`
32. `hist_cod_usage_rate`
33. `hist_upi_order_count`
34. `hist_upi_usage_rate`
35. `velocity_ratio_30_90` (nullable, momentum ratio)
36. `velocity_ratio_90_180` (nullable, momentum ratio)
37. `has_orders_last_90_days`
38. `has_orders_last_180_days`
39. `delay_friction_score` (nullable, friction index)
40. `missing_friction_score`

### 3 Categorical Inputs:
41. `city` (string)
42. `state` (string)
43. `cluster_id` (int: 0, 1, 2, 3, or 4 derived from Phase 4 K-Means)

---

## 6. Important Artifact Paths and Cryptographic Checksums

* `data/raw/customers.csv`: `DF6219AA4E2BDDE8FFF419272B9F2C1DE0602473248619E90566BC7D498AB70E`
* `data/raw/orders.csv`: `AB632B3092F732B3B25BAAD096B191C1ACA777CB8D42B29EABB815A266C558E7`
* `data/processed/customer_features.csv`: `3B8CFF35A9012A7E6524FEC962D400BE58D29399BF4DF7A80DE7283B69B4C628`
* `data/modeling/test.csv`: `93926052072C2C0AF6FC3E7279385B0B31C898CC9798FBC1EF78FBA1CAEDBD67`
* `data/independent_test/raw/customers_independent.csv`: `D3B694F9F3488BB1CAF81C49603A9E322396F48ADDBA6E96246BD91B211F53B4`
* `data/independent_test/raw/orders_independent.csv`: `BE7B293A283A90E7AC78F92D681BE4D0ACA58C3CC2235BCC7EDCBF2348FBAF8E`
* `models/segmentation_scaler.joblib`: `892B9F3CDDA5427DD3965C76B95C1BC952661BAEA993FBBA94D5A3F56FB2EC4C`
* `models/kmeans_customer_segmentation.joblib`: `A018E41C8DC78BBDEC7C157B71ED66FEAC698336F787B39D84583FAE9CB931B3`
* `models/phase5/final_churn_pipeline.joblib`: `25B91797F8F36DB605BAB98B8568A5911847B8CCE77334A68AE4E3862CD3B35D`
* `models/phase5_1/checkpoint3/random_forest_config_d_pipeline.joblib`: `24F1F0E33C75B5590906369960DB6E5951EC95DF9AE40384DA60082B3438F301`
* `models/phase5_1/final_model/final_churn_rf_pipeline.joblib`: `24F1F0E33C75B5590906369960DB6E5951EC95DF9AE40384DA60082B3438F301`
