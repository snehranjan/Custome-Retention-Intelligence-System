# Known Limitations & Academic Disclosures

**Project:** Indian E-Commerce Customer Retention Intelligence System Using Machine Learning  
**Workspace:** `C:\customer churn retention system`  
**Milestone:** Final Master Audit  
**Auditor & Lead:** Senior ML Engineer, QA Automation Engineer and Project Lead  
**Audience:** Academic Review Board, Viva Examiners, and Software Engineering Team  

---

## 1. Purpose of this Document

In accordance with rigorous academic and scientific standards, this document formally records all known theoretical, statistical, operational, and environmental limitations of the completed machine learning system.

These disclosures must be transparently communicated during the university viva examination and project demonstration.

---

## 2. Statistical & Machine Learning Limitations

### 2.1 Synthetic Data Nature & Generalization Scope
* **Simulation Mechanics:** All 7,000 baseline customer records and 1,500 independent cohort records were synthetically generated using parameterized Poisson arrival processes, category price boundaries, and Indian demographic distributions (`backend/ml/generate_data.py`).
* **Academic Scope:** The data realistically simulates velocity momentum, logistics delivery delays, discount sensitivity, and payment channel habits (UPI vs. COD). However, real-world customer churn exhibits additional latent complexities (such as app uninstalls, competitor price changes, marketing ad fatigue, and customer support ticket sentiment) that are not modeled here.
* **Citation Rule:** The synthetic churn rate ($45.82\%$ in development, $44.73\%$ in independent test) is strictly an outcome of the generation parameters and must not be cited as an empirical Indian e-commerce industry benchmark.

### 2.2 Latent Oracle Error Ceiling vs. Universal Accuracy Claims
* **Data-Generating Ground Truth:** Customer churn is defined as zero delivered orders during the 90-day evaluation window (Q1 2026). In the generator, future order arrival is simulated via stochastic Bernoulli realizations parameterized by latent customer personas:
  * `loyal_vip`: $p = 0.08$ (share 15%, irreducible noise $0.08$)
  * `steady`: $p = 0.22$ (share 25%, irreducible noise $0.22$)
  * `occasional`: $p = 0.45$ (share 25%, irreducible noise $0.45$)
  * `dissatisfied`: $p = 0.68$ (share 20%, irreducible noise $0.32$)
  * `dormant`: $p = 0.88$ (share 13%, irreducible noise $0.12$)
  * `zero_order`: $p = 0.94$ (share 2%, irreducible noise $0.06$)
* **Oracle Error Bound:** An oracle with perfect knowledge of the customer's unobserved latent persona $Z$ incurs a minimum theoretical error of:
  $$R^*(Z) = \sum_{k=1}^6 w_k \cdot \min(p_k, 1 - p_k) = \mathbf{26.03\%} \implies \text{Accuracy}_{\text{Oracle Ceiling}} = \mathbf{73.97\%}$$
* **Observable Feature Ceiling:** Because observable features $X$ are noisy historical projections of $Z$, the true Bayes error satisfies $R^*(X) \ge R^*(Z) \approx 26.03\%$. Therefore, $73.97\%$ is an oracle ceiling assuming latent knowledge, not a universal constant for all possible feature sets. Achieving **$71.34\%$ development CV accuracy** and **$68.93\%$ independent test accuracy** represents high-quality convergence near this theoretical bound. Pursuing an arbitrary 80% accuracy target on this data generating process was mathematically unfeasible without label leakage.

### 2.3 Active Customer Transition Uncertainty (The Primary Error Mode)
* **Error Distribution:** In the error analysis of development out-of-fold predictions, accounts that were dormant ($0$ orders in the last 90 days) or had zero delivered orders exhibited $\approx 99\%–100\%$ churn recall.
* **The Difficult Cohort:** However, **$70.1\%$ of all false negatives** occurred among **Active Recent Accounts** (customers who placed an order within the last 30 days of the snapshot date but subsequently ceased purchasing).
* **Root Cause:** In a snapshot-based batch model, active recent purchasers have positive recency and healthy frequency signals up to December 31, 2025. Their sudden cessation of activity in Q1 2026 is stochastic. Capturing these transitions requires real-time clickstream telemetry (e.g., browse session drop-offs or cart abandonment) rather than quarterly batch order history.

### 2.4 Decision Threshold Locking vs. Optimization
* **Pre-Locked Threshold ($\tau = 0.50$):** In Checkpoint 4, the evaluation threshold was locked at $0.50$ prior to unsealing the independent test cohort. At this threshold, the model achieved **$68.93\%$ accuracy**, **$69.00\%$ recall**, and **$64.22\%$ precision**.
* **Development Diagnostic ($\tau = 0.40$):** During development experimentation, sweeping 62 thresholds across pooled development OOF predictions revealed that $\tau = 0.40$ maximized F1 ($0.7061$) and elevated recall to $85.77\%$. However, this is an empirical sample maximum. To prevent post-hoc data snooping, $\tau = 0.50$ was maintained as the locked standard.

---

## 3. System Architecture & Engineering Limitations

### 3.1 Windows PowerShell Execution Policy Restrictions
* **Issue:** On the host Windows development environment, default PowerShell script execution policies prevent the direct invocation of `.ps1` activation scripts (`activate.ps1` or `npm.ps1`).
* **Sanctioned Solution:** All commands in backend development, validation, and documentation invoke the virtual environment binary directly:
  `backend\.venv\Scripts\python.exe <script_path>`
  `npm.cmd <command>` or `cmd /c "npm <command>"`

### 3.2 Single-Node Batch Architecture
* **Scope:** The system is designed for single-node deployment supporting small to medium e-commerce datasets ($< 1,000,000$ transactions). It operates using local memory with Pandas and Scikit-learn.
* **Production Scaling Requirement:** If scaling to enterprise multi-million customer datasets, feature engineering should be migrated to Apache Spark / PySpark or dbt on Snowflake/BigQuery.

---

## 4. Academic Viva Presentation Guidance

When presenting to the viva committee:
1. **Highlight Methodological Integrity:** Emphasize that the independent test set was sealed and evaluated strictly once with a pre-locked threshold of $0.50$.
2. **Explain the Generalization Delta:** Transparently explain why accuracy moved from $71.34\%$ on development CV to $68.93\%$ on unseen test data (the winner's curse / candidate selection optimism disclosed in Checkpoint 3.1).
3. **Defend the Decision to Abandon 80% Accuracy:** Show the mathematical derivation of the $26.03\%$ latent oracle error to prove that claiming 80% accuracy on this dataset would have indicated data leakage or academic dishonesty.
