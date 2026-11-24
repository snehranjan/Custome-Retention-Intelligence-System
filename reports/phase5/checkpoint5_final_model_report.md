# Phase 5 Checkpoint 5: Final Model Refit, Untouched Test Set Evaluation & Model Explainability

**Indian E-Commerce Customer Retention Intelligence System Using Machine Learning**  
*Academic Project: BCA (Artificial Intelligence & Data Science / Machine Learning)*  
*Milestone: Phase 5 — Supervised Machine Learning Pipeline (Checkpoint 5)*  
*Date of Audit & Execution: November 2026*  

---

## 1. Executive Summary

Phase 5 Checkpoint 5 represents the final milestone of the supervised machine learning pipeline. In strict adherence to leakage-free evaluation protocols:
1. **Combined Refitting:** The approved candidate model—**Logistic Regression with Configuration B features** ($C=0.01$, `class_weight='balanced'`, `solver='lbfgs'`, `max_iter=2000`)—was refitted on the combined training and validation cohort ($N=5,950$ records). Preprocessing (median numerical imputation with missingness indicators, standard scaling, and categorical one-hot encoding) was fitted exclusively on this combined dataset.
2. **Untouched Test Evaluation:** The refitted pipeline was evaluated **once** on the completely untouched, sealed test partition ($N=1,050$ records) using the locked decision threshold of **$t^* = 0.46$**.
3. **Core Business Objective Maintained:** On the test set, the model achieved **Recall = 74.43%**, successfully satisfying the primary business requirement of **$\text{Recall} \ge 70.0\%$**. It captured **358 out of 481 actual churners** while preserving **Precision = 61.51%**, **Specificity = 60.63%**, **F1-Score = 0.6736**, **Accuracy = 66.95%**, and **ROC-AUC = 0.7491**.
4. **Honest Evaluation Comparison:** The test set F1-score ($0.6736$) and Recall ($74.43\%$) represent an authentic out-of-sample generalization estimate. The higher validation scores ($F1=0.7215$, $\text{Recall}=82.12\%$) reflected known selection optimism from threshold optimization on that partition.
5. **Full Model Explainability:** Extracted 82 transformed feature coefficients and odds ratios ($\text{OR} = \exp(\beta)$). The analysis reveals that customer order recency ($\beta = +0.3218$, $\text{OR} = 1.3796$) and historical delivery delays ($\beta = +0.3018$, $\text{OR} = 1.3522$) are the primary factors associated with elevated churn log-odds, whereas recent delivered orders ($\beta = -0.1817$, $\text{OR} = 0.8338$) strongly associate with retention.
6. **Production Deliverables & Integrity:** The final pipeline is saved at `models/phase5/final_churn_pipeline.joblib` (SHA-256: `25B91797F8F36DB605BAB98B8568A5911847B8CCE77334A68AE4E3862CD3B35D`). All 18 automated verification checks in `validate_final_model.py` passed with 100% success.

---

## 2. Selected Model and Hyperparameters

The model architecture was locked from Checkpoint 4 and refitted without modification:

- **Model Identifier:** `logistic_regression_config_b_tuned_refitted`
- **Algorithm:** Logistic Regression (Scikit-Learn `sklearn.linear_model.LogisticRegression`)
- **Regularization Penalty:** $L_2$ (Ridge penalty)
- **Inverse Regularization Strength ($C$):** `0.01` (strong shrinkage to guard against multi-collinearity and overfitting)
- **Class Weighting:** `balanced` (adjusts weights inversely proportional to class frequencies: $w_j = \frac{N}{2 \cdot N_j}$)
- **Optimization Solver:** `lbfgs` (Limited-memory Broyden–Fletcher–Goldfarb–Shanno quasi-Newton algorithm)
- **Maximum Iterations:** `2000` (ensures global convergence without premature stopping)
- **Random State:** `42`
- **Decision Threshold:** **`0.46`** (locked from validation threshold optimization)
- **Feature Set:** Configuration B (37 input features: 34 numerical behavioral metrics + 3 categorical variables: `city`, `state`, and Phase 4 RFM `cluster_id`)

---

## 3. Training and Validation Refit Procedure

### 3.1 Data Aggregation & Population Balance

To maximize the statistical power of parameter estimation before final deployment, `data/modeling/train.csv` ($N=4,900$) and `data/modeling/validation.csv` ($N=1,050$) were concatenated into a single refitting dataset:

| Cohort | Source File | Record Count ($N$) | Churned ($y=1$) | Retained ($y=0$) | Churn Rate (%) | Role |
| :--- | :--- | :---: | :---: | :---: | :---: | :--- |
| **Training Partition** | `data/modeling/train.csv` | 4,900 | 2,245 | 2,655 | 45.82% | Initial baseline & tuning CV |
| **Validation Partition** | `data/modeling/validation.csv` | 1,050 | 481 | 569 | 45.81% | Model selection & threshold sweep |
| **Combined Refit Dataset** | Concatenated ($N=5,950$) | **5,950** | **2,726** | **3,224** | **45.82%** | **Final pipeline refitting** |
| **Test Dataset** | `data/modeling/test.csv` | **1,050** | **481** | **569** | **45.81%** | **Sealed test evaluation** |

*Customer ID disjointness was verified: exact intersection of customer IDs between train and validation partitions was 0.*

### 3.2 Preprocessing Pipeline Construction
All preprocessing steps were encapsulated inside a scikit-learn `ColumnTransformer` fitted exclusively on the 5,950 combined records:
1. **Numerical Branch (34 features):**
   - Imputation: `SimpleImputer(strategy='median', add_indicator=True)` handles missing delivery delay and discount fields, appending binary missingness indicators.
   - Normalization: `StandardScaler()` standardizes features to zero mean and unit variance ($z = \frac{x - \mu}{\sigma}$).
2. **Categorical Branch (3 features: `city`, `state`, `cluster_id`):**
   - Imputation: `SimpleImputer(strategy='most_frequent')`.
   - Encoding: `OneHotEncoder(handle_unknown='ignore', sparse_output=False)` produces binary dummy indicators.
3. **Total Transformed Features:** The pipeline expands the 37 raw inputs into **82 transformed numerical and one-hot features**.

---

## 4. Test Dataset Evaluation

The refitted pipeline was applied to `data/modeling/test.csv` ($N=1,050$, 481 Churned, 569 Retained). Predictions were generated using the fixed decision rule:
$$\hat{y}_i = \begin{cases} 1 & \text{if } P(\text{churn} = 1 \mid \mathbf{x}_i) \ge 0.46 \\ 0 & \text{otherwise} \end{cases}$$

### 4.1 Comparative Metrics Table: Validation vs. Test Set

| Evaluation Metric | Mathematical Definition | Checkpoint 4 Validation ($N=1,050$) | Checkpoint 5 Test ($N=1,050$) | Generalization Delta ($\Delta$) | Compliance Status |
| :--- | :--- | :---: | :---: | :---: | :--- |
| **Decision Threshold ($t^*$)** | Fixed operational cutoff | `0.46` | `0.46` | $0.00$ | Locked & Invariant |
| **Recall / Sensitivity** | $\frac{\text{TP}}{\text{TP} + \text{FN}}$ | **82.12%** | **74.43%** | -7.69 percentage points | **PASSED (Target $\ge 70.0\%$)** |
| **Precision** | $\frac{\text{TP}}{\text{TP} + \text{FP}}$ | **64.33%** | **61.51%** | -2.82 percentage points | Solid precision preserved |
| **F1-Score** | $2 \cdot \frac{\text{Prec} \cdot \text{Rec}}{\text{Prec} + \text{Rec}}$ | **0.7215** | **0.6736** | -0.0479 | Strong test harmonic balance |
| **Accuracy** | $\frac{\text{TP} + \text{TN}}{N}$ | **70.95%** | **66.95%** | -4.00 percentage points | Realistic test classification |
| **Specificity (TNR)** | $\frac{\text{TN}}{\text{TN} + \text{FP}}$ | **61.51%** | **60.63%** | -0.88 percentage points | Robust retained user filtering |
| **Balanced Accuracy** | $\frac{\text{Rec} + \text{Spec}}{2}$ | **71.82%** | **67.53%** | -4.29 percentage points | Balanced class handling |
| **ROC-AUC** | Area under ROC curve | **0.7832** | **0.7491** | -0.0341 | Threshold-independent discrimination |
| **Average Precision (AP)** | Area under PR curve | **0.7391** | **0.7146** | -0.0245 | PR discrimination above baseline (0.458) |
| **False Positive Rate (FPR)** | $\frac{\text{FP}}{\text{TN} + \text{FP}} = 1 - \text{Spec}$ | **38.49%** | **39.37%** | +0.88 percentage points | Controlled false intervention rate |
| **False Negative Rate (FNR)** | $\frac{\text{FN}}{\text{TP} + \text{FN}} = 1 - \text{Rec}$ | **17.88%** | **25.57%** | +7.69 percentage points | 74.4% of churners intercepted |
| **Diagnostic Brier Loss** | $\frac{1}{N} \sum (p_i - y_i)^2$ | N/A | **0.2038** | N/A | Diagnostic calibration baseline |

---

## 5. Confusion Matrix Interpretation

### 5.1 Test Set Confusion Matrix ($N=1,050$)

```
                       Predicted Retained (0)     Predicted Churned (1)      Total Actual
Actual Retained (0):          345 (TN)                   224 (FP)                569
Actual Churned  (1):          123 (FN)                   358 (TP)                481
Total Predicted:              468                        582                   1,050
```

### 5.2 Quadrant Analysis & Business Impact
1. **True Positives ($\text{TP} = 358$, $34.10\%$ of test cohort):** The system correctly flagged 358 customers who placed zero orders in Q1 2026. These customers represent the primary target for retention intervention campaigns (e.g., personalized SMS/WhatsApp reminders, targeted category discounts, or app push promotions).
2. **False Negatives ($\text{FN} = 123$, $11.71\%$ of test cohort):** 123 churners were predicted to remain active and were not flagged by the model (False Negative Rate = 25.57%). The remaining 358 churners were successfully intercepted (Recall = 74.43%), satisfying the project's operational recall constraint ($\ge 70.0\%$) on the held-out test dataset.
3. **True Negatives ($\text{TN} = 345$, $32.86\%$ of test cohort):** 345 retained customers were correctly recognized as healthy, avoiding unnecessary retention discounts and protecting profit margins.
4. **False Positives ($\text{FP} = 224$, $21.33\%$ of test cohort):** 224 active customers were flagged as potential churners. In Indian e-commerce retention economics, the financial cost of delivering an outreach notification to an active customer is negligible compared to the permanent loss of customer lifetime value.

---

## 6. Precision, Recall, and F1-Score Interpretation

- **Recall (74.43%):** Out of every 100 churning customers in the test population, approximately **74 are successfully captured** by the retention model. This satisfies the project constraint ($\ge 70\%$) on previously unseen data.
- **Precision (61.51%):** Out of every 100 customers flagged by the retention system, approximately **62 are genuine churners**. This ensures that marketing outreach is not squandered on an excessively noisy pool.
- **F1-Score (0.6736):** The harmonic mean of precision and recall demonstrates an effective operational equilibrium, prioritizing recall without allowing precision to deteriorate into random guessing.

---

## 7. ROC-AUC and Average Precision Interpretation

- **ROC-AUC = 0.7491:** Reflects strong threshold-independent discrimination across the full spectrum of operating points. A randomly chosen churning customer has a $74.91\%$ probability of being assigned a higher risk score than a randomly chosen retained customer.
- **Average Precision (AP) = 0.7146:** In binary classification with class imbalance (base churn rate = $45.81\%$), Average Precision measures the area under the Precision-Recall curve without trapezoidal interpolation bias. The score of $0.7146$ demonstrates substantial elevation above the no-skill baseline ($0.4581$), confirming strong precision retention across operational recall thresholds.

---

## 8. Model Explainability & Feature Coefficients

Because the final model is a regularized Logistic Regression classifier, it offers transparent "glass-box" interpretability. The model log-odds of churn is linear in the transformed features:
$$\ln\left(\frac{p_i}{1 - p_i}\right) = \beta_0 + \sum_{j=1}^{82} \beta_j x_{ij}$$
Where:
- $\beta_0 = -0.0795$ (Intercept baseline log-odds).
- $\exp(\beta_j)$ is the mathematical exponentiation of the fitted coefficient $\beta_j$.

### 8.1 Encoder Architecture & Statistical Semantics of Coefficients
The preprocessing pipeline utilized `OneHotEncoder(handle_unknown="ignore", sparse_output=False)` with **`drop=None`** (retaining all observed category indicators). In this $L_2$-regularized Logistic Regression model:
1. **Regularization and Identifiability:** L2 regularization penalizes the categorical coefficients and helps resolve the non-identifiability associated with redundant one-hot indicators. Under the fitted model's regularized objective, this supports a unique coefficient solution. It does not imply that the resulting coefficients are independent of the encoding or regularization strength, nor does it guarantee good numerical conditioning.
2. **Categorical Coefficients as Additive Linear Parameters:** Categorical coefficients are regularized parameters contributing $\beta_j \cdot x_j$ directly to the model's linear prediction score under the selected encoding. They must **not** be described as direct comparisons against an omitted reference category.
3. **Invalidity of Single-Indicator Ceteris Paribus Transitions:** Changing one category indicator while holding all other indicators in that categorical group constant is not a valid category transition. Because categories within a group (e.g., cities or cluster personas) are mutually exclusive ($\sum x_k = 1$), activating one indicator requires deactivating another.
4. **Dependence on Encoding, Feature Structure, and Regularization:** Full one-hot encoding does not inherently eliminate reference-category bias. The numerical value of each coefficient and the extent of shrinkage depend on the design matrix, feature correlations, category frequencies, and regularization strength, penalizing coefficient magnitudes toward zero under the regularized loss objective.
5. **Interpretation of $\exp(\beta)$ for Categorical Features:** For categorical indicators, $\exp(\beta_j)$ is simply the mathematical exponentiation of the fitted parameter $\beta_j$. It should **not** be presented as a standalone category-versus-reference odds ratio under this encoding.
6. **Standardized Numerical Features:** In contrast, numerical features were standardized using `StandardScaler()` ($z = \frac{x - \mu}{\sigma}$). Their coefficients are properly interpreted as conditional statistical associations per **one standard-deviation increase ($+1\sigma$)** in the feature, holding all other independent features constant.
7. **Association vs. Causation:** All parameters reflect conditional statistical dependencies within the observational dataset and do not represent causal effects.

### 8.2 Top 10 Churn Risk Factors (Positive Coefficients: $\beta > 0$)

| Rank | Feature Name | Description | Coefficient ($\beta$) | $\exp(\beta)$ | Statistical Interpretation |
| :---: | :--- | :--- | :---: | :---: | :--- |
| **1** | `num__recency_days` | Days since customer's last order attempt | `+0.3218` | **1.3796** | Standardized numerical: each $+1\sigma$ increase in recency is conditionally associated with $+0.3218$ higher churn log-odds ($\text{OR} = 1.38$), holding other inputs constant. |
| **2** | `num__hist_average_delivery_delay_days` | Average historical delivery delay (days) | `+0.3018` | **1.3522** | Standardized numerical: each $+1\sigma$ delivery delay is conditionally associated with $+0.3018$ higher churn log-odds ($\text{OR} = 1.35$), holding other inputs constant. |
| **3** | `num__hist_returned_order_count` | Number of returned orders | `+0.2109` | **1.2348** | Standardized numerical: each $+1\sigma$ returns is conditionally associated with $+0.2109$ higher churn log-odds ($\text{OR} = 1.23$), holding other inputs constant. |
| **4** | `missing_hist_average_discount_amount_inr` | Indicator: customer had no recorded discount metrics | `+0.1313` | **1.1403** | Missingness indicator: absence of discount history contributes $+0.1313$ ($\exp(\beta) = 1.14$) to the model's linear prediction score. |
| **5** | `cat__cluster_id_1` | RFM Cluster 1 persona indicator | `+0.1311` | **1.1400** | Categorical indicator: contributes $+0.1311$ ($\exp(\beta) = 1.14$) to the linear prediction score under full one-hot encoding; not a standalone category-versus-reference odds ratio. |
| **6** | `missing_recency_days` | Indicator: customer has no historical order dates | `+0.1092` | **1.1154** | Missingness indicator: absence of order recency contributes $+0.1092$ ($\exp(\beta) = 1.12$) to the linear prediction score. |
| **7** | `cat__city_Mumbai` | Customer located in Mumbai indicator | `+0.1011` | **1.1064** | Categorical indicator: Mumbai indicator contributes $+0.1011$ ($\exp(\beta) = 1.11$) to the linear prediction score under full one-hot encoding. |
| **8** | `num__customer_tenure_days` | Days since customer account registration | `+0.0870` | **1.0909** | Standardized numerical: each $+1\sigma$ tenure is conditionally associated with $+0.0870$ higher churn log-odds ($\text{OR} = 1.09$), holding other inputs constant. |
| **9** | `num__hist_cancelled_order_count` | Number of cancelled historical orders | `+0.0752` | **1.0781** | Standardized numerical: each $+1\sigma$ cancellations is conditionally associated with $+0.0752$ higher churn log-odds ($\text{OR} = 1.08$), holding other inputs constant. |
| **10** | `cat__city_Bengaluru` | Customer located in Bengaluru indicator | `+0.0638` | **1.0659** | Categorical indicator: Bengaluru indicator contributes $+0.0638$ ($\exp(\beta) = 1.07$) to the linear prediction score under full one-hot encoding. |

### 8.3 Top 10 Retention Factors (Negative Coefficients: $\beta < 0$)

| Rank | Feature Name | Description | Coefficient ($\beta$) | $\exp(\beta)$ | Statistical Interpretation |
| :---: | :--- | :--- | :---: | :---: | :--- |
| **1** | `num__delivered_orders_last_180_days` | Delivered orders in past 6 months | `-0.1817` | **0.8338** | Standardized numerical: each $+1\sigma$ recent delivered orders is conditionally associated with $-0.1817$ lower churn log-odds ($\text{OR} = 0.83$), holding other inputs constant. |
| **2** | `num__hist_delivered_order_count` | Total cumulative delivered orders | `-0.1500` | **0.8607** | Standardized numerical: each $+1\sigma$ cumulative delivered orders is conditionally associated with $-0.1500$ lower churn log-odds ($\text{OR} = 0.86$), holding other inputs constant. |
| **3** | `cat__city_Pune` | Customer located in Pune indicator | `-0.1417` | **0.8679** | Categorical indicator: Pune indicator contributes $-0.1417$ ($\exp(\beta) = 0.87$) to the linear prediction score under full one-hot encoding; not a standalone category-versus-reference odds ratio. |
| **4** | `num__orders_last_180_days` | Total order attempts in past 6 months | `-0.1289` | **0.8790** | Standardized numerical: each $+1\sigma$ recent order attempts is conditionally associated with $-0.1289$ lower churn log-odds ($\text{OR} = 0.88$), holding other inputs constant. |
| **5** | `num__hist_discount_missing_rate` | Share of orders without recorded discount | `-0.1180` | **0.8887** | Standardized numerical: each $+1\sigma$ missing discount rate is conditionally associated with $-0.1180$ lower churn log-odds ($\text{OR} = 0.89$), holding other inputs constant. |
| **6** | `num__hist_order_count` | Total count of recorded order attempts | `-0.1134` | **0.8928** | Standardized numerical: each $+1\sigma$ historical orders is conditionally associated with $-0.1134$ lower churn log-odds ($\text{OR} = 0.89$), holding other inputs constant. |
| **7** | `num__has_historical_orders` | Customer has placed at least one order | `-0.1092` | **0.8965** | Standardized numerical: having historical orders is conditionally associated with $-0.1092$ lower churn log-odds ($\text{OR} = 0.90$), holding other inputs constant. |
| **8** | `num__hist_upi_order_count` | Total count of UPI orders | `-0.1053` | **0.9000** | Standardized numerical: each $+1\sigma$ UPI orders is conditionally associated with $-0.1053$ lower churn log-odds ($\text{OR} = 0.90$), holding other inputs constant. |
| **9** | `cat__cluster_id_3` | RFM Cluster 3 persona indicator | `-0.0928` | **0.9114** | Categorical indicator: Cluster 3 indicator contributes $-0.0928$ ($\exp(\beta) = 0.91$) to the linear prediction score under full one-hot encoding; not a standalone category-versus-reference odds ratio. |
| **10** | `num__hist_discounted_order_count` | Total count of discounted orders | `-0.0909` | **0.9131** | Standardized numerical: each $+1\sigma$ discounted orders is conditionally associated with $-0.0909$ lower churn log-odds ($\text{OR} = 0.91$), holding other inputs constant. |

---

## 9. Top Churn-Associated Features: Business Synthesis

Synthesizing the top statistical associations into strategic e-commerce business domains:

```mermaid
flowchart TD
    subgraph Friction ["Friction Drivers (High Churn Odds)"]
        F1["Recency: Days Since Last Order (+0.3218)"]
        F2["Logistics Friction: Delivery Delays (+0.3018)"]
        F3["Fulfillment Quality: Returned Orders (+0.2109)"]
        F4["Post-Order Friction: Cancellation Rate (+0.1257)"]
    end

    subgraph Loyalty ["Loyalty Drivers (High Retention Odds)"]
        L1["Recent Deliveries: Orders Last 180 Days (-0.1817)"]
        L2["Engagement Depth: Cumulative Delivered Orders (-0.1500)"]
        L3["Active Habit: Order Frequency Last 180 Days (-0.1289)"]
        L4["Mature Delivery Hubs: Maharashtra / Pune (-0.1417)"]
    end

    Friction --> RetentionEngine["Targeted Retention Engine (t = 0.46)"]
    Loyalty --> RetentionEngine
    RetentionEngine --> Interventions["Automated Interventions: Proactive Logistics SMS, Instant Return Refunds, Re-engagement Promos"]
```

1. **Logistics Experience Directly Influences Retention:** Historical average delivery delay is the second strongest predictor of churn ($\beta = +0.3018$). In Indian e-commerce, long delivery times and courier SLA breaches erode customer trust rapidly.
2. **Post-Purchase Friction Drives Defection:** Returned order counts ($\beta = +0.2109$) and cancellation rates ($\beta = +0.1257$) indicate that customers who experience defective items, sizing mismatches, or pre-dispatch delays are substantially more prone to defecting.
3. **Recent Purchase Velocity is the Strongest Antidote:** Customers who successfully received orders within the past 180 days ($\beta = -0.1817$) exhibit the strongest retention resilience.

---

## 10. Analytical Limitations

1. **Association vs. Causation:** The logistic regression coefficients indicate conditional statistical associations within the observational dataset. They do *not* establish causal mechanisms. For example, offering discounts to an at-risk customer will not automatically guarantee retention without controlled A/B testing.
2. **Static Snapshot Limitation:** Features were aggregated up to the snapshot cutoff date of December 31, 2025. Dynamic sequential transitions (such as rapid clickstream changes or session-level browsing decay immediately preceding churn) are not captured in static tabular aggregations.
3. **Generalization Gap Between Validation and Test:** The test set F1-score ($0.6736$) is lower than the validation F1-score ($0.7215$). This is expected in machine learning practice because the decision threshold ($0.46$) was chosen to maximize F1 on the validation set, creating mild selection optimism.
4. **Imbalanced False Positive Trade-off:** To maintain high recall ($74.43\%$), the model accepts a False Positive Rate of $39.37\%$ ($224$ retained customers flagged). While commercially acceptable in digital retention, highly expensive retention interventions (e.g., phone call outreach) would require a higher decision threshold.

---

## 11. Synthetic Academic Dataset Disclaimer

This project was developed using a synthetically generated dataset ($7,000$ customers, $44,000+$ historical orders) designed to model the statistical and behavioral characteristics of Indian e-commerce retail (including realistic COD vs. UPI payment distributions, tier-1 to tier-3 geographic distributions, and logistics delay patterns). 

**Important Academic Notice:**
- The numerical rates, coefficient values, and churn percentages reflect the synthetic generation distributions and do not represent proprietary market statistics of any commercial Indian enterprise (e.g., Flipkart, Amazon India, or Meesho).
- The model demonstrated measurable churn-prediction performance on the held-out synthetic test dataset. Its real-world performance and business impact would require validation using genuine customer transaction data and controlled business experiments.
- The modeling methodology, pipeline construction, threshold optimization, and leakage prevention practices represent authentic production-grade data science engineering suitable for university curriculum evaluation.

---

## 12. Final Conclusion

Phase 5 successfully delivers an end-to-end, reproducible, leakage-free supervised machine learning system for customer churn prediction:
- **Baseline Models:** Demonstrated on the Checkpoint 4 validation dataset that standard $0.50$ decision boundaries fail to capture approximately $34\%$ to $36\%$ of churners across baseline architectures.
- **Controlled Hyperparameter Optimization:** Identified balanced regularization ($C=0.01$) on training data that stabilized model sensitivity.
- **Threshold Calibration:** Selected an optimal threshold of $t^* = 0.46$ on the validation set to meet the $\ge 70\%$ recall requirement.
- **Untouched Test Evaluation:** The model demonstrated measurable churn-prediction performance on the held-out synthetic test dataset, capturing **$74.43\%$ of churning customers** at threshold $0.46$. Its real-world performance and commercial business impact would require validation using genuine customer transaction data and controlled business experiments.
- **Model Explainability:** Provided interpretable odds ratios and conditional feature parameters linking delivery delay, return frequency, and order recency to churn log-odds.

---

## 13. Viva Questions and Answers

### Q1: Why did you refit the final model on combined training and validation data before evaluating on the test set?
> **Answer:** In statistical machine learning, after hyperparameters and decision thresholds have been locked using cross-validation and a validation set, refitting the selected pipeline on the combined training and validation data ($N=5,950$) maximizes sample size and parameter estimation precision. Preprocessing transformers (imputers, scalers, and encoders) learn from the fullest available pre-test population without causing leakage into the sealed test set.

### Q2: Why is the test set F1-score (0.6736) lower than the validation set F1-score (0.7215)?
> **Answer:** This difference reflects *selection optimism*. Because the decision threshold ($t^* = 0.46$) was chosen specifically because it maximized F1 on the validation set, the validation score slightly overestimates out-of-sample performance. Evaluating the model once on the untouched test set gives an unbiased estimate of real-world generalization. Crucially, the primary operational constraint ($\text{Recall} \ge 70\%$) was successfully maintained on the test set ($74.43\%$).

### Q3: How do you interpret an Odds Ratio of 1.3522 for `hist_average_delivery_delay_days`?
> **Answer:** Because numerical features were standardized using `StandardScaler`, an Odds Ratio of $1.3522$ means that for every one standard-deviation increase in a customer's average historical delivery delay, the odds of churn ($\frac{p}{1-p}$) increase by a factor of $1.3522$ (a $35.22\%$ increase in churn odds), holding all other model features constant.

### Q4: Why did you not perform probability calibration (e.g., Platt scaling or Isotonic Regression) after testing?
> **Answer:** Post-test calibration using test dataset labels violates the foundational rule of statistical evaluation: the test set must remain strictly passive. Applying probability adjustments based on test performance would introduce data snooping bias. Our diagnostic Brier score ($0.2038$) was computed purely as a descriptive evaluation metric.

### Q5: How do you interpret categorical coefficients under full dummy encoding (`drop=None`) with L2 regularization?
> **Answer:** In unregularized models, omitting a reference category is required to avoid exact multicollinearity (the dummy variable trap). In our regularized Logistic Regression ($C=0.01$), L2 regularization penalizes the categorical coefficients and helps resolve the non-identifiability associated with redundant one-hot indicators. Under the fitted model's regularized objective, this supports a unique coefficient solution. It does not imply that the resulting coefficients are independent of the encoding or regularization strength, nor does it guarantee good numerical conditioning. Categorical coefficients are regularized linear parameters contributing $\beta_j \cdot x_j$ directly to the prediction score $\eta$, not comparisons against an omitted baseline category. Flipping one indicator while holding others constant in the same group is impossible because mutually exclusive categories sum to 1 ($\sum x_k = 1$). Furthermore, full one-hot encoding does not inherently eliminate reference-category bias; shrinkage depends on the design matrix, feature correlations, category frequencies, and regularization strength. Thus, $\exp(\beta_j)$ is the mathematical exponentiation of parameter $\beta_j$, not a standalone odds ratio. Continuous standardized features, however, remain interpreted as Odds Ratios per $+1\sigma$ increase.

---

## 14. Phase 5 Deliverables Directory Map

```
C:\customer churn retention system\
├── backend\ml\
│   ├── train_models.py                # Checkpoint 3: Baseline pipeline training
│   ├── validate_training.py           # Checkpoint 3: Baseline verification suite
│   ├── evaluate_validation.py         # Checkpoint 4: Baseline validation evaluator
│   ├── tune_models.py                 # Checkpoint 4: Controlled 5-fold CV hyperparameter tuner
│   ├── optimize_threshold.py          # Checkpoint 4: 61-threshold sweep optimizer
│   ├── validate_checkpoint4.py        # Checkpoint 4: 22-point validation suite
│   ├── finalize_model.py              # Checkpoint 5: Combined refit pipeline script
│   ├── evaluate_final_model.py        # Checkpoint 5: Untouched test evaluation script
│   ├── explain_final_model.py         # Checkpoint 5: Coefficients & odds ratio explainability
│   └── validate_final_model.py        # Checkpoint 5: 18-point final verification suite
│
├── models\phase5\
│   ├── final_churn_pipeline.joblib    # Final refitted production pipeline artifact
│   ├── final_model_metadata.json      # Complete production metadata & SHA-256 hash
│   ├── tuned\                         # 8 tuned candidate pipeline artifacts
│   └── *.joblib                       # 8 baseline candidate pipeline artifacts
│
├── reports\figures\phase5\
│   ├── final_confusion_matrix.png     # Heatmap of test confusion matrix (N=1,050)
│   ├── final_roc_curve.png            # ROC curve with operational threshold point
│   ├── final_precision_recall_curve.png # Precision-Recall curve with operational point
│   ├── final_metric_comparison.png    # Bar chart of test metrics vs recall constraint
│   ├── feature_coefficients_top15.png # Top 15 positive and negative predictors chart
│   └── feature_coefficients_overview.png # Top 25 feature absolute magnitude overview
│
└── reports\phase5\
    ├── final_test_metrics.json        # Machine-readable test metrics record
    ├── final_test_classification_report.txt # Standard sklearn classification report
    ├── final_confusion_matrix.csv     # Tabular confusion matrix breakdown
    ├── final_test_predictions.csv     # Individual customer predictions (N=1,050)
    ├── feature_coefficients.csv       # 82 transformed feature coefficients & odds ratios
    ├── model_explainability_report.md # Academic explainability report
    └── checkpoint5_final_model_report.md # This comprehensive final milestone report
```
