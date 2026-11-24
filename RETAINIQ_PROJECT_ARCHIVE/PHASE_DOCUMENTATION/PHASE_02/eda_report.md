# Exploratory Data Analysis (EDA) Report
## Indian E-Commerce Customer Retention Intelligence System Using Machine Learning

**Academic Context:** BCA (Artificial Intelligence & Machine Learning) University End-Semester Project  
**Author:** Technical Project Development Team  
**Evaluation Date:** 2026-11-19  
**Target Platform:** Indian E-Commerce Multi-Category Retail  

---

## 1. Project Overview & Objective

The objective of this exploratory data analysis (EDA) is to rigorously analyze customer purchasing behaviors, transaction patterns, order fulfillment metrics, and demographic distributions in an Indian e-commerce setting. This analysis establishes the empirical foundation for customer segmentation (Phase 4), churn prediction modeling (Phase 5), and targeted retention recommendations (Phase 6).

---

## 2. Dataset Description & Schemas

The raw data consists of two relational CSV tables located in `data/raw/`:

1. **`customers.csv` (7,000 records, 7 attributes):** Contains customer demographics (`customer_id`, `customer_name`, `signup_date`, `city`, `state`), the observation snapshot date (`2025-12-31`), and the ground-truth binary retention label (`churn`).
2. **`orders.csv` (84,225 records, 10 attributes):** Contains transaction records (`order_id`, `customer_id`, `order_date`, `order_amount_inr`, `category`, `payment_method`, `discount_amount_inr`, `order_status`, `return_status`, `delivery_delay_days`).

---

## 3. Synthetic Data Disclaimer

> [!IMPORTANT]
> **Synthetic Data Disclaimer:**  
> All records, customer names, addresses, and order histories analyzed in this report are fictional synthetic data generated via reproducible simulation (`backend/ml/generate_data.py`, Random Seed: 42).  
> The observed metrics (including the 45.81% churn rate) are direct mathematical outcomes of the simulation parameters and must **not** be presented or cited as proprietary market research or empirical industry statistics of any real commercial Indian enterprise.

---

## 4. Observation Snapshot & Future Label Window Definitions

To prevent **Data Leakage (Lookahead Bias)**, a strict temporal cutoff is enforced:

- **Observation Snapshot Cutoff:** `2025-12-31`
- **Historical Analysis Dataset:** All orders with `order_date <= 2025-12-31` (72,240 records). Only these records are used to analyze customer purchasing behavior.
- **Future Label Evaluation Window:** `2026-01-01` through `2026-03-31`, inclusive (90 calendar days, 11,985 records).
- **Target Churn Definition:**
  $$\text{churn} = \begin{cases} 1 & \text{if } \text{Count(Orders}_{[2026-01-01, 2026-03-31]}) = 0 \\ 0 & \text{if } \text{Count(Orders}_{[2026-01-01, 2026-03-31]}) \ge 1 \end{cases}$$

---

## 5. Dataset Dimensions & Churn Distribution

| Metric | Measured Value | Percentage |
|---|---|---|
| **Total Customer Count** | **7,000** | 100.00% |
| **Retained Customers (`churn = 0`)** | **3,793** | **54.19%** |
| **Churned Customers (`churn = 1`)** | **3,207** | **45.81%** |
| **Total Orders (All Time)** | **84,225** | 100.00% |
| **Historical Orders (`<= 2025-12-31`)** | **72,240** | 85.77% |
| **Future Validation Orders (`> 2025-12-31`)** | **11,985** | 14.23% |

![Customer Churn Distribution](figures/01_churn_distribution.png)

---

## 6. Customer Demographic & Tenure Insights

Demographic analysis reveals balanced representation across major Indian metropolitan hubs and growth centers:

- **Geographic Spread:** Customers span 12 major Indian states and 22 cities. The top 5 represented states are:
  - **Maharashtra:** 1,006 customers (14.37%)
  - **Gujarat:** 654 customers (9.34%)
  - **Tamil Nadu:** 630 customers (9.00%)
  - **Karnataka:** 624 customers (8.91%)
  - **Uttar Pradesh:** 614 customers (8.77%)
- **Missing Demographics:** Exactly 46 customer records (0.66%) lack city and state entries. In accordance with data science best practices, these are preserved without imputation during EDA.
- **Platform Tenure:**
  - **Mean Tenure:** 430.9 days (1.18 years)
  - **Median Tenure:** 401.0 days
  - **Range:** Early adopters registered in January 2023 (1095 days) up to new registrations in late December 2025 (6 days).

![Customer Geographic Distribution by State](figures/02_customers_by_state.png)
![Customer Signup Timeline](figures/03_signup_timeline.png)

---

## 7. Historical Transaction & Revenue Insights (Historical Orders Only)

All transaction metrics are strictly derived from the 72,240 historical orders:

### Financial Summary & Metric Definitions Audit

> [!IMPORTANT]
> **Accounting & Metric Disclaimers:**  
> 1. **Synthetic Order-Value Metrics:** These values are synthetic transaction metrics calculated directly from simulated e-commerce records. They represent gross order amounts and merchandise values, **not** audited company revenue, corporate accounting turnover, or platform earnings.  
> 2. **`skipna=True` Calculation Limitation:** The calculation of *Delivered-Order Value After Recorded Discounts* utilizes Pandas `skipna=True` for missing discount values (`discount_amount_inr`), which computationally treats missing recorded discounts as zero in this summary. It must **not** be assumed that a missing discount value implies that no discount was applied.  
> 3. **Unrecorded Delivery Delays:** Missing values in `delivery_delay_days` (1,474 historical orders, 2.04%) represent untracked or unrecorded fulfillment entries in the raw log and must **not** be assumed to indicate on-time delivery.

| Metric Name | Incurred Amount (INR) | Included Order Statuses | Treatment of Returns | Treatment of Cancellations | Discounts Subtracted? | Mathematical Formulation |
|---|---|---|---|---|---|---|
| **Booked Gross Order Value (GMV)** | **₹323,444,389.16** | All statuses (`Delivered`, `Returned`, `Cancelled` - 72,240 orders) | Included at sticker price | Included at sticker price | **No** (Gross booking amount) | $\sum_{i \in \text{All Hist}} \text{amount}_i$ |
| **Promotional Discounts Extended** | **₹30,834,723.84** | All statuses where discount applied | Included | Included | N/A (Total recorded discount subsidy) | $\sum_{i \in \text{All Hist}} \text{discount}_i$ |
| **Delivered-Order Gross Sales Value** | **₹279,485,155.77** | **Only `Delivered`** (62,350 orders) | **Excluded** (0 returns included) | **Excluded** (0 cancels included) | **No** (Gross sticker price of delivered items) | $\sum_{i \in \text{Delivered}} \text{amount}_i$ |
| **Delivered-Order Value After Recorded Discounts** | **₹252,873,228.02** | **Only `Delivered`** (62,350 orders) | **Excluded** (0 returns included) | **Excluded** (0 cancels included) | **Yes** (Delivered gross minus ₹26.61M recorded delivered discounts; `skipna=True`) | $\sum_{i \in \text{Delivered}} (\text{amount}_i - \text{discount}_i)$ |

### Detailed Breakdown by Order Status
| Order Status | Order Count | Volume Share | Gross Order Value (INR) | Promotional Discounts (INR) | Net Amount (INR) | Transaction Status |
|---|---|---|---|---|---|---|
| **Delivered** | 62,350 | 86.31% | ₹279,485,155.77 | ₹26,611,927.75 | ₹252,873,228.02 | Completed & retained delivery |
| **Returned** | 5,779 | 8.00% | ₹25,458,095.62 | ₹2,488,897.85 | ₹22,969,197.77 | Returned items (reverse logistics cost) |
| **Cancelled** | 4,111 | 5.69% | ₹18,501,137.77 | ₹1,733,898.24 | ₹16,767,239.53 | Pre-dispatch cancellation |
| **Total Historical** | **72,240** | **100.00%** | **₹323,444,389.16** | **₹30,834,723.84** | **₹292,609,665.32** | Cumulative historical bookings |

### Order Amount Statistics
- **Mean Order Value:** INR ₹4477.36
- **Median Order Value:** INR ₹1977.33
- **Standard Deviation:** INR ₹6881.12
- **Min / Max Amount:** INR ₹150.14 / INR ₹34998.01
- **Skewness:** +2.75 (Right-skewed due to high-value consumer electronics).

### Category Performance
| Category | Order Volume | Gross Revenue (INR) | Average Order Value |
|---|---|---|---|
| **Electronics** | 10,365 | ₹188,139,862.04 | ₹18151.46 |
| **Home** | 10,344 | ₹46,462,412.55 | ₹4491.73 |
| **Sports** | 10,302 | ₹27,651,259.19 | ₹2684.07 |
| **Fashion** | 10,341 | ₹25,385,927.50 | ₹2454.88 |
| **Grocery** | 10,193 | ₹15,472,560.69 | ₹1517.96 |
| **Beauty** | 10,423 | ₹12,385,955.83 | ₹1188.33 |
| **Books** | 10,272 | ₹7,946,411.36 | ₹773.60 |

![Revenue by Product Category](figures/06_revenue_by_category.png)
![Order Amount Distribution](figures/05_order_amount_distribution.png)

### Payment Modes & Logistics
- **Payment Distribution:** UPI is the predominant payment method (32,667 orders, 45.77%), followed by Cash on Delivery (17,318 orders, 24.27%) and Credit Cards (10,107 orders, 14.16%).
- **Delivery Reliability:** 65.84% of orders were delivered on schedule. Delayed orders average 2.9 days past the delivery promise.

![Payment Method Distribution](figures/07_payment_method_distribution.png)
![Order Status Distribution](figures/08_order_status_distribution.png)
![Return Status Distribution](figures/09_return_status_distribution.png)
![Delivery Delay Distribution](figures/10_delivery_delay_distribution.png)

---

## 8. Customer Purchasing Behavior Insights

Aggregating historical transactions at the customer level reveals distinct behavioral segments and edge cases:

- **Customer Purchasing Cohorts:**
  - **Zero Historical Orders:** 148 customers (2.11%) signed up prior to the snapshot date but never completed an order.
  - **Single-Order Buyers (One-and-Done):** 1,830 customers (26.14%) completed exactly one purchase.
  - **Multi-Order Repeat Buyers:** 5,022 customers (71.74%) placed multiple purchases, with active power buyers placing up to 60+ orders.
- **Recency Distribution:** Days since the customer's last purchase as of `2025-12-31` exhibits a median of 35 days and a mean of 107.1 days.

![Order Frequency Distribution](figures/04_order_frequency_distribution.png)
![Recency Distribution](figures/11_recency_distribution.png)

---

## 9. Churn-Related Comparative Observations

Comparing customers across the binary churn target (`churn = 0` vs `churn = 1`) reveals substantial descriptive divergence across multiple operational dimensions:

| Customer Behavioral Metric | Retained Customers (`churn = 0`) | Churned Customers (`churn = 1`) | Relative Difference |
|---|---|---|---|
| **Customer Count** | **3,793** | **3,207** | - |
| **Mean Order Frequency** | **13.95 orders** | **6.03 orders** | -56.8% |
| **Median Order Frequency** | **9 orders** | **3 orders** | -66.7% |
| **Mean Total Spend** | **INR ₹62,554.14** | **INR ₹26,871.38** | -57.0% |
| **Median Total Spend** | **INR ₹37,317.90** | **INR ₹10,365.86** | -72.2% |
| **Median Purchase Recency** | **23 days** | **61 days** | **+165.2% (2.65x higher)** |
| **Mean Purchase Recency** | **54.4 days** | **169.3 days** | **+211.3% (3.11x higher)** |
| **Mean Return Rate** | **7.99%** | **11.31%** | +41.5% |
| **Mean Delivery Delay** | **0.89 days** | **1.50 days** | +67.2% |

> [!WARNING]
> **Correlation vs. Causation:**  
> While churned customers exhibit significantly higher purchase recency, lower order frequency, and higher delivery friction, statistical correlation does **not** establish direct causation. These variables represent strong candidate features for predictive classification, but individual customer attrition may be influenced by unobserved external factors.

![Historical Spending by Churn Group](figures/12_spending_by_churn.png)
![Historical Order Frequency by Churn Group](figures/13_order_frequency_by_churn.png)
![Recency Density by Churn Group](figures/14_recency_by_churn.png)

---

## 10. Data Quality & Missing-Value Audit Across Temporal Windows

An audit of the raw files confirms high overall integrity with documented missingness in selected business columns. Missing values are partitioned by temporal window:

| Attribute | Historical Orders (`<= 2025-12-31`, N = 72,240) | Future Label Window (`> 2025-12-31`, N = 11,985) | All Orders Combined (N = 84,225) | Recommended Preprocessing Strategy (Phase 3) |
|---|---|---|---|---|
| `payment_method` | 870 (1.20%) | 151 (1.26%) | 1,021 (1.21%) | Impute mode ('UPI') or sentinel 'Unspecified' |
| `discount_amount_inr` | 1,293 (1.79%) | 223 (1.86%) | 1,516 (1.80%) | Impute with 0.0 (indicates no promo code used) |
| `delivery_delay_days` | 1,474 (2.04%) | 255 (2.13%) | 1,729 (2.05%) | Impute with 0 (baseline on-time SLA fulfillment) |

Customer Demographics (`customers.csv`, N = 7,000):
- `city`: 46 missing (0.66%)
- `state`: 46 missing (0.66%)
- `customer_id`, `signup_date`, `snapshot_date`, `churn`: **0 missing (100% complete)**

- **Referential & ID Integrity:** 0 duplicate customer IDs, 0 duplicate order IDs, and 0 orphan orders.
- **Value Bounds:** 0 negative order values, 0 negative discounts, and 0 negative delay values.

![Missing Value Summary](figures/15_missing_values_summary.png)

---

## 11. Statistical Outlier Analysis & Scaling Clarification

Using the standard Interquartile Range (IQR) rule ($Q_1 - 1.5 \times \text{IQR}$ to $Q_3 + 1.5 \times \text{IQR}$):

- **Order Amounts:** $Q_1 = \text{INR } ₹1008.10$, $Q_3 = \text{INR } ₹4135.76$, $\text{IQR} = \text{INR } ₹3127.66$. Upper threshold is INR ₹8827.26.
- **Outlier Interpretation:** The 8,094 orders (11.20%) identified above the IQR threshold are **statistical tail outliers, NOT incorrect or corrupt records**. In an e-commerce platform catalog featuring premium consumer electronics (e.g. televisions, laptops, and smartphones up to ₹35,000), these represent authentic, high-value transactions. They **must be preserved** and will not be removed or artificially clipped.
- **Feature Scaling Strategy:** We do not commit to a specific scaling method in EDA. The preprocessing pipeline in Phase 3 and Phase 5 will systematically compare scaling requirements for candidate algorithms: distance-sensitive algorithms (e.g., Logistic Regression) require feature scaling (such as StandardScaler or RobustScaler), whereas tree-based ensembles (Random Forest, Gradient Boosting) are invariant to monotonic scaling.

---

## 12. Statistical Reference Tables

### A. Numerical Variables in Historical Orders
| Column | Count | Mean | Std | Min | 25% | 50% | 75% | Max | Skewness |
|---|---|---|---|---|---|---|---|---|---|
| `order_amount_inr` | 72,240 | 4477.36 | 6881.12 | 150.14 | 1008.10 | 1977.33 | 4135.76 | 34998.01 | +2.75 |
| `discount_amount_inr` | 70,947 | 434.62 | 964.96 | 0.00 | 0.00 | 120.72 | 386.81 | 8654.17 | +4.19 |
| `delivery_delay_days` | 70,766 | 0.94 | 1.91 | 0.00 | 0.00 | 0.00 | 1.00 | 11.00 | +2.73 |

### B. Customer-Level Aggregated Metrics
| Metric | Count | Mean | Std | Min | 25% | 50% | 75% | Max | Skewness |
|---|---|---|---|---|---|---|---|---|---|
| `hist_order_count` | 7,000 | 10.32 | 12.70 | 0 | 1 | 6 | 14 | 65 | +2.12 |
| `hist_total_spend` | 7,000 | ₹46,206.34 | ₹61,220.34 | ₹0.00 | ₹4,064.34 | ₹24,199.69 | ₹61,694.58 | ₹519,628.95 | +2.27 |
| `recency_days` | 7,000 | 107.1 | 187.2 | 0 | 12 | 35 | 96 | 1087 | +2.83 |
| `tenure_days` | 7,000 | 430.9 | 279.3 | 6 | 190 | 401 | 645 | 1095 | -0.36 |

---

## 13. Summary of Key Analytical Findings

1. **Recency is the Most Pronounced Differentiating Factor:** Churned customers exhibit a median recency of 61 days compared to only 23 days for retained customers (2.65x higher, or +165.2%).
2. **Order Velocity & Engagement Gap:** Retained customers average more than double the historical order count (14.0 vs 6.0, a 56.8% reduction for churned accounts) and more than double the lifetime expenditure.
3. **Logistics & Quality Friction:** Higher delivery delays (+67.2%) and return frequencies (+41.5%) correlate strongly with customer attrition, highlighting friction points in reverse logistics and courier fulfillment SLAs.
4. **Clean Baseline:** The raw datasets contain 0 referential integrity violations and minimal missingness (<2.1% in any field), ensuring clean preprocessing.

---

## 14. Academic Limitations

- The underlying data is synthetic and generated with predetermined behavioral distributions (Poisson order arrivals, log-normal pricing).
- Unobserved factors common in live commercial applications (marketing campaign attribution, competitor discount wars, customer service chat transcripts) are not represented in this dataset.

---

## 15. Technical Recommendations for Phase 3 (Feature Engineering)

1. **RFM Metrics:** Engineer standard Recency, Frequency, and Monetary (RFM) metrics strictly from historical orders (`<= 2025-12-31`).
2. **Friction Indicators:** Calculate customer-level return rates, cancellation rates, and average delivery delay days.
3. **Behavioral Velocity:** Compute recent order volume features (Orders placed in the last 30 days and last 90 days before snapshot date).
4. **Channel Preferences:** Derive UPI vs. COD usage rates and discount reliance percentages.
5. **Zero-Order Handling:** Properly handle zero-order customers by imputing zero spend/orders and setting recency equal to customer tenure.
6. **Leakage Safeguard:** Enforce automated assert statements verifying that future order dates (`> 2025-12-31`) never enter the feature computation pipeline.
