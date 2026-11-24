# ANTIGRAVITY WORKSPACE INSTRUCTIONS & PERMANENT PROJECT RULES
## Indian E-Commerce Customer Retention Intelligence System Using Machine Learning

**Workspace Root:** `C:\customer churn retention system`  
**Host Platform:** Windows 11 (64-bit)  
**Python Virtual Environment:** `backend\.venv\Scripts\python.exe`  
**Current Milestone:** Phase 0–5.1 Complete & Audited. Ready for Phase 7 (FastAPI Backend).  
**Deadline:** Saturday, 21 November 2026, 6:00 PM (Presentation: 23 November 2026).  

---

## 1. MANDATORY STARTUP PROTOCOL FOR FUTURE SESSIONS

Whenever a new Antigravity session starts, **BEFORE performing any action or replying to the user**:

1. **Read Canonical Context Files:**
   * [PROJECT_CONTEXT.md](file:///c:/customer%20churn%20retention%20system/PROJECT_CONTEXT.md): Full technical architecture, completed phase history, feature schema, and cluster mapping.
   * [PROJECT_HANDOFF.md](file:///c:/customer%20churn%20retention%20system/PROJECT_HANDOFF.md): Current development state, next phase checkpoints, and deadline countdown.
   * [DEVELOPMENT_RULES.md](file:///c:/customer%20churn%20retention%20system/DEVELOPMENT_RULES.md): Permanent coding conventions, Windows execution rules, and security policies.
2. **When the user says "Start Phase 7" or similar:**
   * Do NOT ask the user to explain the project again.
   * Proceed directly to **Phase 7.1: Backend Architecture & ML Integration Audit**.
   * Work strictly one checkpoint at a time and stop for approval after each checkpoint.

---

## 2. STRICT MACHINE LEARNING & PREDICTION INTEGRITY INVARIANTS

* **Locked Production Model:**  
  `models/phase5_1/final_model/final_churn_rf_pipeline.joblib`  
  *(Original: `models/phase5_1/checkpoint3/random_forest_config_d_pipeline.joblib`)*  
  **SHA-256 Checksum:** `24F1F0E33C75B5590906369960DB6E5951EC95DF9AE40384DA60082B3438F301`  
  * **RULE 1:** NEVER retrain, refit, or fine-tune this model.
  * **RULE 2:** NEVER alter its locked decision threshold (**$\tau = 0.50$**).
  * **RULE 3:** NEVER use simulated or hardcoded prediction values. All predictions must invoke `pipeline.predict_proba()`.
  * **RULE 4:** Every prediction call must pass the exact **43 raw Config D features** (40 numerical + 3 categorical: `city`, `state`, `cluster_id`).
* **RFM Customer Segmentation:**  
  Assign clusters using pre-fitted `models/segmentation_scaler.joblib` and `models/kmeans_customer_segmentation.joblib` ($K=5$).  
  Official Persona Mappings:
  * Cluster 0: *Champions & High-Value Loyalists*
  * Cluster 1: *At-Risk / Lapsed Low-Value Customers*
  * Cluster 2: *Zero Delivered-Purchase Customers*
  * Cluster 3: *Steady Core Repeaters*
  * Cluster 4: *Recent Low-Ticket / New Promising Customers*

---

## 3. EXECUTION ENVIRONMENT RULES (WINDOWS 11)

* **Python Commands:** Always execute using the virtual environment binary directly:  
  `backend\.venv\Scripts\python.exe <command>`
* **Node/npm Commands:** Always execute using `.cmd` batch files:  
  `& "C:\Program Files\nodejs\npm.cmd" <command>` or `cmd /c "npm <command>"`
* **Never use PowerShell script activation (`activate.ps1`).**

---

## 4. MASTER AUDIT & VALIDATION EVIDENCE

* **All 10 Phase Validation Suites Verified (160/160 checks passed):**  
  Run master test suite: `backend\.venv\Scripts\python.exe -m pytest tests/test_all_phases.py -v`
* **Audit Documentation Directory:** `reports/final_project_audit/`
  * `final_project_audit_report.md`
  * `phase_completion_matrix.csv`
  * `test_execution_results.json`
  * `artifact_integrity_report.json`
  * `known_limitations.md`
  * `project_readiness_report.md`
