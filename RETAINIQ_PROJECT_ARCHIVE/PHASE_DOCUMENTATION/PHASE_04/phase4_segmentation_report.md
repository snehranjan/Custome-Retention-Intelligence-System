# Phase 4 Customer Segmentation & RFM Clustering Report (Audited Version)
## Indian E-Commerce Customer Retention Intelligence System Using Machine Learning

**Academic Context:** BCA (Artificial Intelligence & Machine Learning) University End-Semester Project  
**Author:** Technical Machine Learning Development Team  
**Evaluation Date:** 2026-11-19 (Updated with Comprehensive Analytical Audit)  
**Observation Snapshot Date:** `2025-12-31`  
**Clustering Dataset:** `data/processed/customer_segments.csv` (7,000 customers × 9 columns)  
**Cluster Profiles:** `data/processed/cluster_profiles.csv` (5 clusters)  
**Model & Scaler Artifacts:** `models/kmeans_customer_segmentation.joblib`, `models/segmentation_scaler.joblib`  
**Manifest & Metrics:** `data/processed/segmentation_manifest.json`, `data/processed/segmentation_metrics.json`  

---

> [!NOTE]
> **Academic & Synthetic Simulation Disclaimer:**  
> All 7,000 customer records and order histories evaluated in this report were generated synthetically for university research and end-semester project evaluation. None of the customer profiles, spending figures, or churn metrics represent audited corporate financials or actual Indian e-commerce industry statistics.

---

## 1. Executive Summary & Objective

In Phase 4, we implemented and rigorously audited an unsupervised machine learning customer segmentation pipeline ([backend/ml/customer_segmentation.py](file:///c:/customer%20churn%20retention%20system/backend/ml/customer_segmentation.py)) using Recency-Frequency-Monetary (RFM) behavioral analysis and K-Means clustering.

The core objective was to discover natural customer behavioral cohorts across the 7,000 fictional Indian e-commerce customer base strictly under the **31 December 2025** observation boundary, without supervision or data leakage. The target label (`churn`) and customer identifiers (`customer_id`, `customer_name`, `signup_date`) were completely excluded from the clustering pipeline.

Following a thorough independent technical audit, this report resolves key analytical nuances:
1. Clarifies the statistical origin of negative monetary skewness (zero-inflation effect).
2. Explicitly analyzes the mathematical vs. commercial trade-offs between $K=3$ and $K=5$.
3. Distinguishes subgroups within the zero-delivered cohort and clarifies return/cancellation rate denominators.
4. Explains why inertia across differently scaled feature spaces is not directly comparable.
5. Adopts rigorous statistical wording for stability claims.
6. Cryptographically verifies both MD5 and SHA-256 hashes of all raw datasets.

All 23 automated integrity, reproducibility, and stability checks in [backend/ml/validate_segmentation.py](file:///c:/customer%20churn%20retention%20system/backend/ml/validate_segmentation.py) passed with **0 errors**.

---

## 2. Dataset & Input Feature Architecture

Clustering was performed using the verified feature dataset from Phase 3 ([data/processed/customer_features.csv](file:///c:/customer%20churn%20retention%20system/data/processed/customer_features.csv)).

```
+-----------------------------------------------------------------------------------------+
|                                7,000 Total Customer Records                             |
+-----------------------------------------------------------------------------------------+
                                             |
                  +--------------------------+--------------------------+
                  |                                                     |
                  v                                                     v
    +---------------------------+                         +---------------------------+
    | 6,516 Active Customers    |                         |  484 Zero-Delivered       |
    | (Delivered Orders >= 1)   |                         |  Customers                |
    | Valid Delivered Recency   |                         |  (148 Never-Purchased +   |
    | Spend: INR 151 to 480k    |                         |   336 Unfulfilled Orders) |
    | Freq: 1 to 65 orders      |                         |  Spend: INR 0.00          |
    +---------------------------+                         +---------------------------+
```

### Strict Unsupervised Data Isolation Protocol:
1. **Forbidden Clustering Inputs:** The ground-truth target (`churn`), customer identifiers (`customer_id`, `customer_name`), and account registration date (`signup_date`) were strictly excluded from feature transformation, scaling, K-Means fitting, and hyperparameter selection.
2. **Post-Clustering Cross-Tabulation Only:** Ground-truth `churn` is referenced strictly after final model convergence to calculate descriptive cross-cluster churn rates for evaluation comparison.

---

## 3. Audit 1: Detailed Monetary Transformation Analysis

The raw monetary feature (`hist_delivered_order_value_inr`) exhibits severe right-skewness due to power-law e-commerce spending patterns. Applying $\log(1 + x)$ yields an aggregate skewness of **-1.8688** across all 7,000 customers.

### Statistical Investigation: Overcorrection vs. Zero-Inflation
An independent distribution audit reveals that the negative skewness is **not** an overcorrection of the active purchasing distribution, but rather the mathematical consequence of **zero-inflation**:

| Statistical Metric | Raw Monetary (All 7,000) | Raw Monetary (Active 6,516) | $\log(1+x)$ (All 7,000) | $\log(1+x)$ (Active 6,516) |
|---|---|---|---|---|
| **Mean** | ₹39,926.45 | ₹42,892.14 | 8.9965 | 9.6647 |
| **Median** | ₹18,103.68 | ₹21,732.31 | 9.8039 | 9.9866 |
| **Standard Deviation** | ₹56,851.60 | ₹57,835.92 | 2.9250 | 1.6528 |
| **Skewness** | **+2.4621** (Severe Right) | **+2.3827** (Severe Right) | **-1.8688** (Zero-Spike) | **-0.4230** (Near-Normal!) |
| **Min (0th %ile)** | ₹0.00 | ₹150.86 | 0.0000 | 5.0230 |
| **1st Percentile** | ₹0.00 | ₹346.54 | 0.0000 | 5.8509 |
| **25th Percentile** | ₹3,051.47 | ₹4,459.52 | 8.0237 | 8.4030 |
| **50th Percentile** | ₹18,103.68 | ₹21,732.31 | 9.8039 | 9.9866 |
| **75th Percentile** | ₹51,767.25 | ₹55,669.92 | 10.8545 | 10.9272 |
| **95th Percentile** | ₹165,179.46 | ₹170,690.84 | 12.0148 | 12.0476 |
| **99th Percentile** | ₹266,582.36 | ₹270,510.34 | 12.4934 | 12.5081 |
| **Max (100th %ile)** | ₹479,694.01 | ₹479,694.01 | 13.0809 | 13.0809 |

### Empirical Insights:
1. **Active Customer Normalization:** When isolating the 6,516 customers who actually completed delivered orders, `log1p` monetary skewness is **-0.4230**. In statistics, any skewness between $-0.5$ and $+0.5$ is classified as **approximately symmetric**.
2. **Zero-Inflation Effect:** The remaining 484 customers have spend = ₹0.00, resulting in $\log(1 + 0) = 0.0000$. These 484 identical zero values create an isolated point mass at zero on the far left, while the 6,516 active observations span from 5.02 to 13.08. This structural zero spike produces the aggregate $-1.8688$ skewness.
3. **Comparison Against Un-transformed Alternatives:**
   - **Candidate B (Raw Features + RobustScaler):** Silhouette score appears high (0.5434), but it produces a degenerate segmentation: **Cluster 0 contains 4,177 customers (59.7% of the entire customer base)**, completely failing to segment normal customers because extreme spenders pull centroids outward.
   - **Candidate C (Raw Features + StandardScaler):** Similarly collapses into an uninformative giant cluster of 3,605 customers (51.5%).
   - **Candidate A (Current log1p + StandardScaler):** Produces balanced, actionable clusters (sizes: 2000, 1723, 1569, 1224, 484) and isolates zero-delivered accounts with 100% purity.

**Verdict:** The `log1p` transformation is mathematically and commercially the superior choice. Its negative skewness across the pooled dataset is an expected, harmless manifestation of zero-inflation that enables K-Means to cleanly partition unactivated accounts from active customers.

---

## 4. Audit 2: Rigorous Evaluation of $K = 3$ versus $K = 5$

The previous validation suite reported Silhouette scores across $K \in [2, 10]$:
- $K=2$: 0.4213
- **$K=3$: 0.4412 (Highest mathematical silhouette score)**
- $K=4$: 0.3898
- **$K=5$: 0.4065 (Selected optimal configuration)**
- $K=6$: 0.3943
- $K=7$: 0.3712

### Direct Side-by-Side Comparison:

| Evaluation Dimension | $K = 3$ Configuration | $K = 5$ Configuration (Selected) | Analytical Comparison |
|---|---|---|---|
| **Silhouette Score** | **0.4412** | **0.4065** | $K=3$ has a higher silhouette due to wider geometric margins between 3 coarse centroids. |
| **Clustering Inertia (WCSS)** | **6,544.5** | **3,534.7** | **$K=5$ reduces within-cluster variance by 46.0%** (-3,009.8 points). |
| **Cluster Sizes** | 3,330 (47.6%), 3,185 (45.5%), 485 (6.9%) | 2,000 (28.6%), 1,723 (24.6%), 1,569 (22.4%), 1,224 (17.5%), 484 (6.9%) | $K=3$ splits 93.1% of customers into two massive, undifferentiated blocks. $K=5$ is well-balanced. |
| **Smallest Cluster Size** | 485 (6.93%) | 484 (6.91%) | Identical coverage of the zero-delivered cohort. |
| **High-Value Separation** | **Collapsed:** Merges Champions (₹113k spend, 25 orders) and Steady Repeaters (₹39k spend, 8.6 orders) into one group. | **Separated:** Distinctly isolates Champions ($N=1,569$) from Steady Repeaters ($N=2,000$). | $K=5$ prevents diluting high-tier VIP retention budgets on mid-tier buyers. |
| **Low-Value Separation** | **Severely Flawed:** Merges Recent Trial Buyers (Recency 14.8 days) with Lapsed/Dormant Accounts (Recency 274.8 days) into one group. | **Separated:** Distinguishes New Promising Customers ($N=1,224$, Recency 14.8d) from Lapsed Customers ($N=1,723$, Recency 274.8d). | **Fatal in $K=3$:** Would trigger "We Miss You Win-Back" discounts for customers who bought yesterday! |
| **Observed Churn Rates** | C0: 76.3%, C1: 29.7%, C2: 56.8% | C0: 19.6%, C1: 66.9%, C2: 76.2%, C3: 43.0%, C4: 42.4% | $K=5$ reveals stark churn polarity (19.6% Champions vs. 66.9% Lapsed). |
| **Stability (5 Seeds ARI)** | Mean ARI = 0.9952 (Min = 0.9900) | Mean ARI = 0.9931 (Min = 0.9846) | Both configurations are exceptionally stable across seeds. |

### Technical Decision Justification:
While $K=3$ maximizes the mathematical silhouette coefficient, it produces **severe commercial over-aggregation**. In an e-commerce retention engine, treating a recent trial buyer (bought 14 days ago) the same as a lapsed customer (inactive for 9 months) would cause marketing failure. 

$K=5$ cuts within-cluster variance nearly in half ($46\%$ inertia reduction), forms a distinct elbow on the WCSS curve, exhibits a strong silhouette rebound to $0.4065$, and yields five actionable personas. Therefore, **$K = 5$ is confirmed as the superior practical model**.

---

## 5. Audit 3: Zero-Delivered-Purchase Cohort Deep Dive

The 484 customers assigned to Cluster 2 comprise two distinct behavioral subgroups:
1. **Never-Purchased Customers ($N = 148, 30.58\%$ of cohort):** Customers who registered prior to 31 Dec 2025 but never placed an order (`hist_order_count = 0`).
2. **Attempted but Unfulfilled Customers ($N = 336, 69.42\%$ of cohort):** Customers who placed orders (`hist_order_count > 0`), but **100% of their attempted orders resulted in Cancellations or Returns** prior to fulfillment.

### Rigorous Audit of Subgroup Friction & Denominators:
We audited the exact mathematical calculation of return and cancellation rates for this cohort and established a clean separation between pooled order-level rates, true customer-level averages, and undefined accounts:

1. **Pooled Order-Level Rates (Across all 368 Attempted Orders from 336 Customers):**
   - Direct source order reconciliation from `data/raw/orders.csv` ($\text{order\_date} \le \text{2025-12-31}$):
     - Total attempted orders = **368**
     - Returned orders = **207** $\rightarrow$ **Pooled Return Rate = 56.25%** ($207 / 368$)
     - Cancelled orders = **161** $\rightarrow$ **Pooled Cancellation Rate = 43.75%** ($161 / 368$)
     - Note: $207 + 161 = 368$ (100.0% friction). Every single attempted order by these customers failed to be fulfilled!

2. **True Customer-Level Averages (Arithmetic Mean Across the 336 Attempting Customers):**
   - For each of the 336 customers with $\ge 1$ attempted order:
     $$\text{Individual Return Rate} = \frac{\text{hist\_returned\_order\_count}}{\text{hist\_order\_count}}, \quad \text{Individual Cancellation Rate} = \frac{\text{hist\_cancelled\_order\_count}}{\text{hist\_order\_count}}$$
   - Arithmetic mean across these 336 individual customer ratios:
     - **Mean Customer-Level Return Rate:** **0.5645** (**56.45%**)
     - **Mean Customer-Level Cancellation Rate:** **0.4355** (**43.55%**)
     - Sum of customer-level rates = $56.45\% + 43.55\% = 100.00\%$

3. **Undefined Rates (148 Never-Purchased Accounts):**
   - Exactly **148 customers** placed 0 historical orders.
   - For these accounts, $0 / 0$ is mathematically **undefined** ($\text{NaN}$). They are strictly excluded from customer-level rate averages.
   - *Previous reporting discrepancy disclosed:* In earlier unweighted averaging across all 484 accounts, these 148 undefined accounts had $0.0$ silently substituted into the numerator: $(336 \times 0.5645 + 148 \times 0) / 484 = 39.19\%$ return rate and $(336 \times 0.4355 + 148 \times 0) / 484 = 30.23\%$ cancellation rate. This reporting defect has now been completely corrected in [data/processed/cluster_profiles.csv](file:///c:/customer%20churn%20retention%20system/data/processed/cluster_profiles.csv) and [data/processed/segmentation_metrics.json](file:///c:/customer%20churn%20retention%20system/data/processed/segmentation_metrics.json).

### Sensitivity Analysis on Imputed Recency:
We evaluated whether setting imputed recency to 1,087, 1,117, 1,200, 1,500, or 2,000 days affects cluster assignment:
- For all tested values $\in [1087, 2000]$, the zero-delivered cluster remained **100% pure (all 484 customers grouped together)**.
- Adjusted Rand Index comparing 1,087 vs. 1,117 days was **0.9996**.
- Comparing the 1-Stage K-Means model with a 2-Stage rule-based model yielded an ARI of **0.8128** across active customers.

### Umbrella Terminology Update:
In accordance with audit directives, Cluster 2 is designated as:
**"Zero Delivered-Purchase Customers"** (encompassing both never-purchased and attempted-unfulfilled subgroups).

---

## 6. Audit 4: Scaler Comparison & Inertia Comparability

When comparing `StandardScaler` vs. `RobustScaler`:
- **StandardScaler:** Silhouette Score = **0.4065** | Inertia = 3,534.7
- **RobustScaler:** Silhouette Score = **0.3990** | Inertia = 2,089.5

> [!WARNING]
> **Statistical Disclosure on Inertia Comparability:**  
> Inertia (WCSS) values from differently scaled feature spaces cannot be compared directly as absolute measures of clustering quality. StandardScaler divides by standard deviation ($\sigma$), whereas RobustScaler divides by Interquartile Range ($\text{IQR} = Q_3 - Q_1$). Because $\text{IQR} > \sigma$ in moderately skewed data, coordinates under RobustScaler are compressed, mechanically shrinking Euclidean distances and producing lower raw inertia numbers without reflecting tighter clusters.

`StandardScaler` was confirmed as the superior scaler because log-transformation had already stabilized tail variance, and unit-variance scaling ensures equal spherical weighting across all 3 RFM axes.

---

## 7. Audit 5: Cluster Stability Across Initializations

To verify reproducibility, we refit K-Means across 5 deterministic random seeds (`42`, `100`, `2024`, `7`, `999`) and computed pairwise Adjusted Rand Index (ARI):

| Pairwise Seed Comparison | Adjusted Rand Index (ARI) | Cluster Assignment Stability |
|---|---|---|
| Seed 42 vs. Seed 100 | **0.9967** | Near-perfect convergence |
| Seed 42 vs. Seed 2024 | **0.9861** | Near-perfect convergence |
| Seed 42 vs. Seed 7 | **0.9963** | Near-perfect convergence |
| Seed 42 vs. Seed 999 | **0.9985** | Near-perfect convergence |
| Seed 100 vs. Seed 2024 | **0.9887** | Near-perfect convergence |
| Seed 100 vs. Seed 7 | **0.9996** | Near-perfect convergence |
| Seed 100 vs. Seed 999 | **0.9958** | Near-perfect convergence |
| Seed 2024 vs. Seed 7 | **0.9891** | Near-perfect convergence |
| Seed 2024 vs. Seed 999 | **0.9846** | Near-perfect convergence |
| Seed 7 vs. Seed 999 | **0.9954** | Near-perfect convergence |
| **Mean Pairwise ARI** | **0.9931** | **Highly stable across the tested random initializations.** |

*Note: In accordance with audit instructions, this stability metric proves robustness across tested initializations; it does not claim generalization to unseen future data distributions.*

---

## 8. Final Customer Persona Profiles & Retention Actions

Final centroid profiles based on **original, unscaled metrics** across all 7,000 customers:

| Cluster ID | Persona Name | Customer Count | Base Share | Mean Recency | Mean Fulfilled Frequency | Mean Delivered Spend (INR) | Mean Return Rate (Attempting Customers) | Mean Cancellation Rate (Attempting Customers) | Observed Churn Rate* |
|---|---|---|---|---|---|---|---|---|---|
| **0** | **Champions & High-Value Loyalists** | 1,569 | 22.41% | 12.8 days | 25.1 orders | ₹113,448.30 | 5.96% | 3.87% | **19.57%** |
| **3** | **Steady Core Repeaters** | 2,000 | 28.57% | 76.3 days | 8.6 orders | ₹39,265.08 | 10.25% | 7.68% | **43.00%** |
| **4** | **Recent Low-Ticket / New Promising** | 1,224 | 17.49% | 14.8 days | 2.7 orders | ₹10,694.52 | 6.12% | 4.45% | **42.40%** |
| **1** | **At-Risk / Lapsed Low-Value Customers** | 1,723 | 24.61% | 274.8 days | 1.4 orders | ₹5,725.21 | 5.97% | 4.78% | **66.86%** |
| **2** | **Zero Delivered-Purchase Customers** | 484 | 6.91% | N/A | 0.0 orders | ₹0.00 | **56.45%** (N=336) | **43.55%** (N=336) | **76.24%** |

*\*Notes:*
- *For Cluster 2, return and cancellation rates are calculated strictly across the 336 customers who attempted historical orders; the 148 never-purchased customers have undefined rates and are excluded.*
- *Churn rates were cross-tabulated strictly post-clustering for descriptive evaluation.*

### Actionable Retention Recommendations:
1. **Champions & High-Value Loyalists (Cluster 0):** Dedicated VIP concierge support, festive sale early access, premium loyalty points, free expedited delivery.
2. **Steady Core Repeaters (Cluster 3):** Cross-category personalized recommendation carousels, tiered milestone discount vouchers ($10^{\text{th}}$ order celebration voucher), cashback on digital UPI payments.
3. **Recent Low-Ticket / New Promising Customers (Cluster 4):** Post-purchase nurture journey with product tutorials, bundle-and-save incentives, time-limited second-purchase celebratory coupon valid for 21 days.
4. **At-Risk / Lapsed Low-Value Customers (Cluster 1):** Automated "We Miss You" SMS/WhatsApp re-engagement campaigns, deep reactivation discount codes, category preference discovery survey with instant INR 150 wallet credit.
5. **Zero Delivered-Purchase Customers (Cluster 2):** Logistics serviceability audit, first-purchase guarantee with free return insurance, INR 200 first-purchase coupon on prepaid UPI orders.

---

## 9. Visualizations Architecture

All 6 publication-grade figures are generated and verified in [reports/figures/](file:///c:/customer%20churn%20retention%20system/reports/figures/):

1. [reports/figures/phase4_elbow_method.png](file:///c:/customer%20churn%20retention%20system/reports/figures/phase4_elbow_method.png): WCSS vs. $K \in [2, 10]$ showing the distinct elbow bend at $K=5$.
2. [reports/figures/phase4_silhouette_scores.png](file:///c:/customer%20churn%20retention%20system/reports/figures/phase4_silhouette_scores.png): Silhouette score bar chart highlighting the rebound peak at $K=5$ (0.4065).
3. [reports/figures/phase4_cluster_distribution.png](file:///c:/customer%20churn%20retention%20system/reports/figures/phase4_cluster_distribution.png): Customer counts and percentages across all 5 personas.
4. [reports/figures/phase4_rfm_cluster_profiles.png](file:///c:/customer%20churn%20retention%20system/reports/figures/phase4_rfm_cluster_profiles.png): 3-panel bar charts displaying mean Recency, Frequency, and Monetary spend across clusters.
5. [reports/figures/phase4_cluster_scatter_pca.png](file:///c:/customer%20churn%20retention%20system/reports/figures/phase4_cluster_scatter_pca.png): 2D PCA projection capturing 91.2% total variance with centroid markers.
6. [reports/figures/phase4_cluster_comparison_heatmap.png](file:///c:/customer%20churn%20retention%20system/reports/figures/phase4_cluster_comparison_heatmap.png): Min-max normalized heatmap comparing all 5 personas across 9 operational dimensions.

---

## 10. Automated Validation Suite Results

Running `backend\.venv\Scripts\python.exe backend\ml\validate_segmentation.py`:

```text
===========================================================================
PHASE 4: CUSTOMER SEGMENTATION VALIDATION SUITE (AUDITED VERSION)
===========================================================================
[PASS] Check 01: Source customer_features.csv exists
       -> Details: data\processed\customer_features.csv
[PASS] Check 02: Exactly 7,000 segmented customer records
       -> Details: Found 7,000 records
[PASS] Check 03: Customer IDs are completely unique
       -> Details: Unique IDs: 7,000
[PASS] Check 04: Every source customer from Phase 3 is represented
[PASS] Check 05: Every customer receives exactly one cluster (Zero duplicate assignments)
[PASS] Check 06: Cluster IDs are valid integers {0, 1, 2, 3, 4}
       -> Details: Cluster IDs found: {0, 1, 2, 3, 4}
[PASS] Check 07: Zero missing cluster assignments
       -> Details: Null clusters: 0
[PASS] Check 08: No customer identifiers used as clustering inputs
       -> Details: Clustering inputs: ['recency_delivered_days', 'hist_delivered_order_count', 'hist_delivered_order_value_inr']
[PASS] Check 09: Target column 'churn' strictly excluded from clustering inputs
       -> Details: Entirely unsupervised
[PASS] Check 10: Feature order in manifest exactly matches expected RFM inputs
       -> Details: Manifest order: ['recency_delivered_days', 'hist_delivered_order_count', 'hist_delivered_order_value_inr']
[PASS] Check 11: Scaler and K-Means artifacts can be successfully reloaded
       -> Details: Model: models\kmeans_customer_segmentation.joblib, Scaler: models\segmentation_scaler.joblib
[PASS] Check 12: Reloaded model and scaler produce 100% identical cluster assignments
       -> Details: Mismatches: 0
[PASS] Check 13: Monetary transformation audit verified (Active skewness = -0.42, Zero-inflation skewness = -1.87)
       -> Details: Raw skew all/active: 2.46/2.38, Log1p skew all/active: -1.87/-0.42
[PASS] Check 14: K=3 vs K=5 comparison verified (K=3 Silhouette=0.4412, K=5 Silhouette=0.4065 with 46% lower inertia)
       -> Details: K=3: Sil=0.4412, Inertia=6544.5 | K=5: Sil=0.4065, Inertia=3534.7
[PASS] Check 15: Zero-delivered cohort subgroups verified (148 never-purchased + 336 attempted unfulfilled = 484)
       -> Details: Never-purchased: 148, Attempted unfulfilled: 336, Total: 484
[PASS] Check 16: Zero-delivered cohort cleanly isolated into Cluster 2 with 100% purity
       -> Details: Cluster 2 count: 484, Zero-delivered in Cluster 2: 484/484
[PASS] Check 17: Undefined recency handling verified (Observation boundary: max_recency + 30 = 1117.0 days)
       -> Details: Max recency: 1087.0, Imputed boundary: 1117.0
[PASS] Check 18: Cluster 2 zero-delivered cohort subgroups verified (148 zero orders + 336 attempted unfulfilled = 484)
       -> Details: Never-purchased (zero orders): 148, Attempted unfulfilled: 336, Total C2: 484
[PASS] Check 19: Pooled order-level friction rates verified on 368 orders (207 returned [56.25%], 161 cancelled [43.75%], strictly <= 2025-12-31)
       -> Details: Historical orders: 368 (207 Ret + 161 Canc = 368, Deliv: 0), Pooled Ret: 0.5625, Pooled Canc: 0.4375, Future orders excluded: 189
[PASS] Check 20: Customer-level averages verified across 336 attempting accounts (Mean Ret: 56.45%, Mean Canc: 43.55%, 148 undefined excluded)
       -> Details: Denominator: 336, Mean Ret: 0.5645, Mean Canc: 0.4355, Undefined accounts: 148, Profile row: Ret=0.5645, Canc=0.4355
[PASS] Check 21: Statistical guard test: Customer-level rate is NOT substituted by pooled rate (0.5645 != 0.5625 and != 0.3919)
       -> Details: Customer-level: 0.5645 != Pooled: 0.5625 and != Conflated: 0.3919 (Guard Test Passed)
[PASS] Check 22: All 6 required publication-grade visualizations exist and are non-empty
       -> Details: 6 figures verified in reports\figures
[PASS] Check 23: Cluster profiles output matches customer segment assignments exactly
       -> Details: Segment counts: {3: 2000, 1: 1723, 0: 1569, 4: 1224, 2: 484}
[PASS] Check 24: Cluster percentages sum to approximately 100.0%
       -> Details: Sum of percentages: 99.99%
[PASS] Check 25: Cluster stability verified across multiple seeds (Mean ARI >= 0.95)
       -> Details: Mean Pairwise ARI: 0.9931
[PASS] Check 26: Raw CSV datasets remain 100% cryptographically unchanged (MD5 & SHA-256 verified)
       -> Details: customers SHA256: DF6219AA4E2BDDE8..., orders SHA256: AB632B3092F732B3...
===========================================================================
ALL 26 VALIDATION & REPRODUCIBILITY CHECKS PASSED WITH ZERO ERRORS!
Phase 4 Customer Segmentation is fully audited, certified, and reproducible.
===========================================================================
```

---

## 11. Raw Dataset Cryptographic Audit

| File Path | MD5 Hash | SHA-256 Hash | Integrity Status |
|---|---|---|---|
| [data/raw/customers.csv](file:///c:/customer%20churn%20retention%20system/data/raw/customers.csv) | `EA39F916F2FA2D432F40F894F63A1715` | `DF6219AA4E2BDDE8FFF419272B9F2C1DE0602473248619E90566BC7D498AB70E` | **100% Intact** |
| [data/raw/orders.csv](file:///c:/customer%20churn%20retention%20system/data/raw/orders.csv) | `7E65B96077288D3DBDA3E50FAF6FD5EB` | `AB632B3092F732B3B25BAAD096B191C1ACA777CB8D42B29EABB815A266C558E7` | **100% Intact** |
| [data/processed/customer_features.csv](file:///c:/customer%20churn%20retention%20system/data/processed/customer_features.csv) | `6D9CA7E9C4E27F701C189E8F4609F6A5` | `3B8CFF35A9012A7E6524FEC962D400BE58D29399BF4DF7A80DE7283B69B4C628` | **100% Intact** |

---

## 12. Academic Viva Q&A Guide (BCA Defense Ready)

> **Viva Question 1: Why is the log1p monetary skewness negative (-1.8688) across the full dataset? Does it mean the feature was overcorrected?**  
> **Answer:** *"No, it does not mean overcorrection. For active customers who placed delivered orders ($N=6,516$), `log1p` monetary skewness is -0.4230, which falls cleanly within the $[-0.5, +0.5]$ symmetric range. The aggregate -1.8688 skewness across all 7,000 customers is caused by zero-inflation: 484 customers have zero historical delivered spend, mapping to an exact point mass at $\log(1 + 0) = 0.0$. Because the active distribution spans from 5.02 to 13.08, this isolated cluster of 484 zeroes creates an artificial negative tail. This zero-inflation is analytically beneficial because it allows K-Means to cleanly separate unactivated registrations from active purchasing tiers."*

> **Viva Question 2: Why did you choose $K = 5$ when $K = 3$ produced a higher silhouette score (0.4412 vs 0.4065)?**  
> **Answer:** *"In clustering evaluation, mathematical silhouette score must be balanced with commercial interpretability and within-cluster variance. While $K=3$ achieves a higher silhouette score due to wide geometric separation between fewer centroids, it causes severe commercial over-aggregation: it collapses Champions (spending ₹1.13 Lakhs across 25 orders) and Steady Repeaters (spending ₹39k) into a single 45.5% cluster, and lumps hot trial buyers (bought 14 days ago) with cold dormant customers (inactive for 9 months) into a single 47.6% cluster. In a retention system, sending win-back discounts to new buyers who purchased yesterday would be disastrous. $K=5$ reduces within-cluster variance (inertia) by 46.0% (from 6,544.5 to 3,534.7), exhibits a clear elbow inflection, rebounds in silhouette score to 0.4065, and provides five actionable personas necessary for targeted retention."*

> **Viva Question 3: How did you ensure that zero-delivered customers were handled without data leakage or arbitrary dates?**  
> **Answer:** *"For the 484 customers with no delivered purchase history (148 never-purchased and 336 with cancelled/returned orders only), their delivered order count and spend were preserved as 0 and ₹0.00. Rather than fabricating an order date, we assigned an explicit observation boundary value: $\max(\text{recency}) + 30 = 1117.0\text{ days}$, representing absence of fulfilled transactions within or immediately before the 3-year observation window. In sensitivity tests across imputed values from 1,087 to 2,000 days, K-Means consistently and cleanly isolated all 484 zero-delivered customers into Cluster 2 with 100% purity (ARI > 0.95)."*
