# Indian E-Commerce Customer Retention Intelligence System Using Machine Learning

An end-to-end Machine Learning and Analytics system designed to predict customer churn, segment customer purchasing behavior, explain risk factors, and recommend targeted retention strategies for Indian e-commerce businesses.

Built as a university end-semester project for BCA (Artificial Intelligence & Machine Learning).

---

## 🏗️ System Architecture

```
                    +-----------------------------+
                    |        React Frontend       |
                    |   (Vite + Tailwind + Recharts)|
                    +--------------+--------------+
                                   | HTTP / REST (Axios)
                                   v
                    +-----------------------------+
                    |       FastAPI Backend       |
                    +--------------+--------------+
                                   |
         +-------------------------+-------------------------+
         |                         |                         |
         v                         v                         v
+-----------------+       +-----------------+       +-----------------+
|    ML Engine    |       | Data Processing |       | Retention Engine|
| (Scikit-Learn,  |       | (Pandas, NumPy, |       |  (Rule-Based +  |
|  Classification,|       |  Feature Eng,   |       |  Customer Value |
|  Clustering)    |       |  RFM Analysis)  |       |  Prioritization)|
+-----------------+       +-----------------+       +-----------------+
         |                         |                         |
         +-------------------------+-------------------------+
                                   |
                                   v
                    +-----------------------------+
                    |   Data Layer (CSV Storage)  |
                    |  (Future: Supabase Auth/DB) |
                    +-----------------------------+
```

---

## 🛠️ Technology Stack

| Layer | Technologies |
|---|---|
| **Programming Language** | Python 3.12 (explicitly isolated) |
| **Backend Framework** | FastAPI, Uvicorn, Pydantic |
| **Machine Learning** | Scikit-learn, Joblib |
| **Data Processing** | Pandas, NumPy |
| **Frontend UI** | React.js, Vite, Tailwind CSS, Lucide React, Recharts |
| **Database & Auth** | Supabase PostgreSQL & Auth (Integrated in Phase 10) |
| **Data Context** | Indian E-Commerce (INR ₹, UPI/COD/Cards, Indian Cities & Categories) |

---

## 📋 Phased Development Progress

- [x] **Phase 0: Environment & Project Inspection** *(Completed)*
  - Windows environment diagnosed (Python 3.12.10, Node v25.2.1, npm 11.6.2).
  - PowerShell script execution policy workaround established (`backend\.venv\Scripts\python.exe` & `npm.cmd`).
  - Modular project directory structure created.
  - Python 3.12 virtual environment (`backend\.venv`) created and core dependencies installed and verified.
- [x] **Phase 1: Synthetic Data Generation** *(Completed)*
  - Generated exactly 7,000 unique fictional Indian customers (`data/raw/customers.csv`).
  - Generated 84,225 orders (`data/raw/orders.csv`) spanning 2023-01-01 to 2026-03-31.
  - Implemented 31 Dec 2025 snapshot date with 90-day future evaluation window (2026-01-01 to 2026-03-31).
  - Validated temporal partition between historical orders and future orders; ground-truth churn verified against future orders.
  - Passed all 10 automated data integrity & temporal partition checks in `backend/ml/validate_data.py`.
- [x] **Phase 2: Exploratory Data Analysis (EDA)** *(Completed)*
  - Completed comprehensive demographic, transaction, behavioral, and churn comparative analyses using Python 3.12.
  - Strictly partitioned historical orders (72,240 records <= 2025-12-31) from future evaluation orders (11,985 records).
  - Generated and exported 15 professional visualization figures into `reports/figures/`.
  - Compiled detailed 15-section academic findings report into `reports/eda_report.md`.
  - Preserved raw datasets in `data/raw/` with zero modifications (MD5 verified).
- [x] **Phase 3: Data Cleaning & Feature Engineering** *(Completed & Audited)*
  - Engineered 36 customer-level predictive features across RFM, fulfilled purchase recency, purchase velocity (30/90/180-day), friction, payment missingness, and payment channels.
  - Processed dataset saved to `data/processed/customer_features.csv` (7,000 rows × 40 columns).
  - Generated comprehensive schema documentation in `data/processed/feature_manifest.json` with verified roles (`city` and `state` classified as predictive).
  - Compiled detailed technical report in `reports/feature_engineering_report.md`.
  - Successfully passed all 23 automated integrity and anti-leakage checks in `backend/ml/validate_features.py` (including strengthened perturbation and target separation tests).
- [x] **Phase 4: Customer Segmentation** *(Completed, Audited & Verified)*
  - Implemented unsupervised RFM customer segmentation using K-Means clustering ($K=5$) on `data/processed/customer_features.csv`.
  - Evaluated Elbow curve and Silhouette analysis across $K \in [2, 10]$ (optimal $K=5$, Silhouette = 0.4065, Inertia = 3,534.7; documented $K=3$ vs $K=5$ trade-off).
  - Cleanly isolated all 484 zero-delivered customers into a dedicated cohort (Cluster 2: "Zero Delivered-Purchase Customers", separating 148 never-purchased and 336 unfulfilled accounts) while discovering 4 distinct active purchasing personas: Champions, Steady Repeaters, Promising New Customers, and Lapsed Low-Value Customers.
  - Verified stability across 5 random seeds (Mean Pairwise ARI = 0.9931).
  - Exported production models and outputs: `models/kmeans_customer_segmentation.joblib`, `models/segmentation_scaler.joblib`, `data/processed/customer_segments.csv`, `data/processed/cluster_profiles.csv`, and 6 publication-grade figures in `reports/figures/`.
  - Passed all 23 automated validation and reproducibility checks in `backend/ml/validate_segmentation.py`.
- [x] **Phase 5: Supervised ML Baseline Pipeline** *(Completed & Audited)*
  - Constructed leakage-free stratified partitions (4,900 Train / 1,050 Validation / 1,050 Test).
  - Evaluated Configuration A (36 baseline features) and Configuration B (37 features including RFM persona).
  - Trained and cross-validated Logistic Regression, Decision Tree, Random Forest, and Gradient Boosting.
  - Selected tuned Logistic Regression Configuration B benchmark (Test Accuracy: 66.95%, Recall: 74.43%, ROC-AUC: 0.7491 at locked threshold 0.46).
  - Passed all 18 validation checks in `backend/ml/validate_final_model.py`.
- [x] **Phase 5.1: Advanced ML Optimization & Independent Evaluation** *(Completed & Audited)*
  - Generated sealed independent synthetic evaluation cohort (1,500 customers, 17,585 orders).
  - Engineered advanced behavioral features (momentum ratios R30/90, R90/180, and customer friction index) with Log1p transformations and within-fold correlation pruning (CorrelationPruner).
  - Conducted 5x3 Nested Stratified Cross-Validation across 12 candidate model/configuration pipelines on the 5,950-customer development dataset.
  - Selected Random Forest Configuration D (150 trees, max_depth=8, min_samples_leaf=5) as the top performer (Nested CV Accuracy: 71.34%, F1: 0.6944, ROC-AUC: 0.7798).
  - Cryptographically locked final model artifact (`models/phase5_1/checkpoint3/random_forest_config_d_pipeline.joblib`, SHA-256: `24F1F0E33C75B5590906369960DB6E5951EC95DF9AE40384DA60082B3438F301`) and locked threshold at 0.50.
  - Conducted single independent evaluation on 1,500 unseen customers: Accuracy 68.93%, Recall 69.00%, Precision 64.22%, F1 0.6652, ROC-AUC 0.7651.
  - Passed all 12 validation checks in `backend/ml/validate_final_ml.py`. Master pytest test suite verified (10/10 passed).
- [ ] **Phase 6: Retention Recommendation Engine**
  - Explainable business rules linking customer value, return habits, and churn risk to targeted interventions.
- [ ] **Phase 7: FastAPI Backend Development**
  - High-performance REST endpoints with Pydantic validation, CORS, error handling, and Swagger docs.
- [ ] **Phase 8: React Frontend Dashboard**
  - Enterprise analytics UI with sidebar navigation, overview metrics, explorer, and prediction simulator.
- [ ] **Phase 9: Frontend & Backend Integration**
  - End-to-end integration via Axios, live charts, real predictions, and interactive filters.
- [ ] **Phase 10: Supabase Database & Authentication**
  - Employee auth and database persistence with fallback to local demonstration mode.
- [ ] **Phase 11: End-to-End Testing & Verification**
  - Comprehensive unit and integration testing across all layers.
- [ ] **Phase 12: University Documentation & Viva Preparation**
  - Project report, architecture diagrams, ER diagrams, data flow diagrams, viva Q&A guide.

## 📊 Synthetic Dataset Architecture & Schema (Phase 1)

All customer records and order histories are synthetic simulations generated using `backend/ml/generate_data.py` (Random Seed: 42). They do not represent real proprietary customer data or actual Indian e-commerce market statistics.

### 1. `data/raw/customers.csv` (7,000 records)
| Column Name | Type | Description | Sample Value |
|---|---|---|---|
| `customer_id` | String | Unique customer identifier | `IND_CUST_10001` |
| `customer_name` | String | Fictional Indian name | `Aarav Sharma` |
| `signup_date` | Date (YYYY-MM-DD) | Platform registration date | `2023-08-14` |
| `city` | String | Indian tier 1 & 2 cities (0.66% intentional missing for EDA) | `Indore` |
| `state` | String | Corresponding Indian state (0.66% intentional missing for EDA) | `Madhya Pradesh` |
| `snapshot_date` | Date (YYYY-MM-DD) | Feature observation cutoff date | `2025-12-31` |
| `churn` | Integer (0 or 1) | Ground-truth churn target label | `0` (Retained) / `1` (Churned) |

### 2. `data/raw/orders.csv` (84,225 records)
| Column Name | Type | Description | Sample Value |
|---|---|---|---|
| `order_id` | String | Unique transaction identifier | `ORD_100001` |
| `customer_id` | String | Reference to `customers.csv` | `IND_CUST_10001` |
| `order_date` | Date (YYYY-MM-DD) | Transaction timestamp | `2024-05-20` |
| `order_amount_inr` | Float | Gross order amount in INR (₹) | `4299.50` |
| `category` | String | Product category (Electronics, Fashion, Grocery, Beauty, Home, Books, Sports) | `Electronics` |
| `payment_method` | String | Payment mode (UPI, COD, Credit Card, etc., 1.21% missing for EDA) | `UPI` |
| `discount_amount_inr`| Float | Promotional discount applied (1.80% missing for EDA) | `350.00` |
| `order_status` | String | Delivery status (Delivered, Cancelled, Returned) | `Delivered` |
| `return_status` | String | Reverse logistics status (Not Returned, Returned, Return Requested) | `Not Returned` |
| `delivery_delay_days`| Float | Days delayed beyond estimated SLA (2.05% missing for EDA) | `0.0` |

### 3. Churn Definition, Synthetic Distribution & Strict Temporal Separation Rules
- **Observation Snapshot Date:** `2025-12-31`
- **Future Evaluation Window:** `2026-01-01` through `2026-03-31`, inclusive (90 days).
- **Label Definition:**
  - `churn = 1`: Customer placed **zero** orders between `2026-01-01` and `2026-03-31`.
  - `churn = 0`: Customer placed **one or more** orders between `2026-01-01` and `2026-03-31`.
- **Synthetic Churn Distribution:**
  - Retained (`churn = 0`): 3,793 (54.19%)
  - Churned (`churn = 1`): 3,207 (45.81%)
  - *Academic Note on Synthetic Distribution:* The 45.81% churn rate is strictly an outcome of our synthetic simulation, its defined persona distributions, and selected behavioral generation parameters. It is an academic modeling artifact and must not be cited or interpreted as a real Indian e-commerce industry benchmark or empirical market statistic.
- **Scope of Current Validation vs. Future Feature Pipeline:**
  - The validation suite in `backend/ml/validate_data.py` confirms raw data referential integrity and verifies that raw orders are strictly partitioned into historical (`order_date <= 2025-12-31`) and future (`2026-01-01` to `2026-03-31`) subsets.
  - This validation proves raw data temporal separation, but **does not yet prove that a future feature-engineering pipeline is leakage-free**. That feature-level verification will be implemented and tested during Phase 3.
- **Mandatory Rules for Subsequent Phases:**
  1. **Historical Features Only:** All customer features (RFM, order velocity, returns, delays, discounts) must be computed exclusively from orders with `order_date <= 2025-12-31`.
  2. **Target Window Boundary:** The ground-truth churn label is defined strictly within `2026-01-01` through `2026-03-31`, inclusive.
  3. **Strict No-Leakage Invariant:** Future orders (`order_date > 2025-12-31`), future customer activity, or future churn labels must **never** be used as model input features or during feature scaling and transformation.

### 4. `data/processed/customer_features.csv` (7,000 records × 36 columns)
Customer-level feature matrix aggregated strictly from historical orders (`<= 2025-12-31`):
- **Identifiers & Target:** `customer_id`, `customer_name`, `signup_date`, `churn` (0 = Retained, 1 = Churned).
- **Profile:** `city`, `state`, `customer_tenure_days`, `has_historical_orders`.
- **Recency:** `recency_days` (Days from last historical purchase to 2025-12-31; NaN for 148 zero-order accounts).
- **Frequency:** `hist_order_count`, `hist_delivered_order_count`, `hist_returned_order_count`, `hist_cancelled_order_count`.
- **Monetary:** `hist_total_order_value_inr`, `hist_delivered_order_value_inr`, `hist_total_recorded_discount_inr`, `hist_average_order_value_inr`.
- **Velocity (Recorded):** `orders_last_30_days`, `orders_last_90_days`, `orders_last_180_days` (all ending on 2025-12-31).
- **Velocity (Delivered):** `delivered_orders_last_30_days`, `delivered_orders_last_90_days`, `delivered_orders_last_180_days`.
- **Friction:** `hist_return_rate`, `hist_cancellation_rate`, `hist_average_delivery_delay_days`, `hist_delivery_delay_missing_count`, `hist_delivery_delay_missing_rate`.
- **Payment & Discount Channels:** `hist_average_discount_amount_inr`, `hist_discounted_order_count`, `hist_discount_missing_count`, `hist_discount_missing_rate`, `hist_cod_order_count`, `hist_cod_usage_rate`, `hist_upi_order_count`, `hist_upi_usage_rate`.
- **Full Specification:** Detailed metadata, types, and formulas cataloged in `data/processed/feature_manifest.json`.

---

## 🤖 Production Machine Learning Model (Phase 5.1 Final Lock)

- **Selected Candidate:** Random Forest Classifier (Configuration D)
- **Model Path:** `models/phase5_1/final_model/final_churn_rf_pipeline.joblib`
- **Original Path:** `models/phase5_1/checkpoint3/random_forest_config_d_pipeline.joblib`
- **SHA-256 Checksum:** `24F1F0E33C75B5590906369960DB6E5951EC95DF9AE40384DA60082B3438F301`
- **Training Dataset:** 5,950 customers (100% Development Cohort)
- **Locked Decision Threshold:** `0.50`
- **Independent Test Cohort Performance (N = 1,500 Unseen Customers):**
  - **Accuracy:** 68.93%
  - **Recall:** 69.00%
  - **Precision:** 64.22%
  - **F1-Score:** 0.6652
  - **ROC-AUC:** 0.7651
  - **PR-AUC (Average Precision):** 0.7308
  - **Balanced Accuracy:** 68.94%
  - **Brier Score:** 0.1970
  - **Confusion Matrix:** TN=571, FP=258, FN=208, TP=463

---

## ⚙️ Development Environment & Execution Guide (Windows)

Due to Windows PowerShell execution policy restrictions, always execute the virtual environment binaries directly without relying on PowerShell activation scripts:

```powershell
# Run the Master Pytest Test Suite across all phases (10/10 passed)
backend\.venv\Scripts\python.exe -m pytest tests/test_all_phases.py -v

# Run individual phase validation suites
backend\.venv\Scripts\python.exe backend/ml/validate_final_ml.py

# Run Python scripts directly with the virtual environment interpreter
backend\.venv\Scripts\python.exe backend/ml/<script_name>.py

# Run FastAPI backend server (Phase 7)
backend\.venv\Scripts\python.exe -m uvicorn backend.app.main:app --reload --port 8000

# Run npm commands using cmd or direct batch files
cmd /c "npm run dev"
# Or
& "C:\Program Files\nodejs\npm.cmd" run dev
```
