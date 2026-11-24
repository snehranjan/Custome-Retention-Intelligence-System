# PERMANENT DEVELOPMENT RULES & ENGINEERING CONVENTIONS

**Project:** Indian E-Commerce Customer Retention Intelligence System Using Machine Learning  
**Workspace:** `C:\customer churn retention system`  
**Applies To:** All future Antigravity sessions, subagents, and human developers.  

---

## 1. Core Operating Principles

1. **One Checkpoint at a Time:** Work systematically through defined checkpoints (e.g., 7.1, 7.2, 7.3). Complete the work, run verification, present the implementation report, and **STOP** to await explicit approval before starting the next checkpoint.
2. **Never Jump Ahead:** Do not anticipate or begin subsequent phases without explicit user instruction.
3. **Inspect Before Modifying:** Always inspect existing source code, configuration files, and schemas before creating or editing files. Avoid blind assumptions.
4. **Reuse, Don't Reinvent:** Reuse established components (e.g., `feature_engineering.py`, `advanced_feature_engineering.py`, model pipelines). Do not create duplicate helper files or duplicate logic.
5. **No Broken Windows:** Never leave a checkpoint with failing tests or unhandled exceptions. If an issue arises, resolve it cleanly before proceeding.

---

## 2. Machine Learning & Prediction Integrity Rules

1. **Strict Model Immutability:**  
   The final Random Forest model (`models/phase5_1/final_model/final_churn_rf_pipeline.joblib`) is permanently locked with SHA-256 `24F1F0E33C75B5590906369960DB6E5951EC95DF9AE40384DA60082B3438F301`.  
   * NEVER retrain or tune this model.
   * NEVER alter its pre-registered decision threshold ($\tau = 0.50$).
   * NEVER change its feature preprocessing steps.
2. **Real Model Inference Mandatory:**  
   In all backend endpoints and frontend views, churn predictions must be computed by passing genuine input features into the loaded scikit-learn pipeline via `pipeline.predict_proba()`.  
   * NEVER mock, hardcode, or simulate prediction probabilities.
3. **Contract Adherence:**  
   Every inference call must provide the exact 43 raw Config D features (40 numerical + 3 categorical: `city`, `state`, `cluster_id`).
4. **Cluster Assignment Fidelity:**  
   Customer segments must be derived using the pre-fitted Phase 4 scaler (`models/segmentation_scaler.joblib`) and K-Means model (`models/kmeans_customer_segmentation.joblib`). Never refit clustering models or modify cluster IDs.

---

## 3. Coding Conventions & Environment Standards

### 3.1 Windows Environment Execution
* Always invoke Python using the virtual environment interpreter path:
  `backend\.venv\Scripts\python.exe <command>`
* Never execute `activate.ps1` or assume PowerShell script activation works due to Windows execution policies.
* Invoke Node/npm via `npm.cmd` or `cmd /c "npm <command>"`.

### 3.2 Python / FastAPI Backend Conventions
* Use Python 3.12 syntax with strict type annotations.
* Define explicit Pydantic v2 schemas for all request payloads and response bodies.
* Organize backend code cleanly under `backend/app/`:
  * `backend/app/main.py`: FastAPI application initialization, CORS, routers.
  * `backend/app/core/`: Configuration, settings, security.
  * `backend/app/models/`: Pydantic request/response schemas.
  * `backend/app/services/`: Business logic (ML inference service, segmentation service, retention service).
  * `backend/app/api/v1/`: API route controllers.
* Handle missing numerical values gracefully (the model's internal `SimpleImputer` handles nulls, but API inputs should allow optional/nullable values).
* Return standard HTTP status codes (`200 OK`, `201 Created`, `400 Bad Request`, `404 Not Found`, `500 Internal Error`).

### 3.3 Security & Credential Handling
* Keep sensitive credentials (database passwords, JWT secret keys, Supabase service keys) strictly in `.env` files.
* Never hardcode secrets in source files or git-committed reports.
* Ensure `.gitignore` protects all `.env` files.

---

## 4. Academic Viva & Presentation Readiness Standards

1. **Code Clarity:** Code must be clean, commented, and readable so a BCA AI & ML student can confidently explain every module during a viva examination.
2. **Defendable Decisions:** Implementation choices must align with standard machine learning theory (e.g., explaining why threshold 0.50 was pre-locked to avoid winner's curse, explaining why the latent oracle ceiling is $73.97\%$).
3. **Professional UI Aesthetics:** The React frontend must look modern, clean, and enterprise-grade:
   * Avoid pitch-black themes or neon color schemes.
   * Prefer a balanced, clean dashboard with subtle shadows, standard typography, and clear visual hierarchy.

---

## 5. Deadline & Priority Directive

* **Final Deadline:** **Saturday, 21 November 2026, 6:00 PM**
* **Priority Order:**
  1. Working, stable backend prediction and customer management APIs.
  2. Working frontend dashboard displaying real metrics and single-customer churn prediction.
  3. Seamless end-to-end integration (frontend talking to backend with zero mock data).
  4. Robust offline demonstration capability (local dataset fallback if remote database fails).
  5. Presentation rehearsal.
* **Non-Goals:** Do not spend time on complex third-party payment integrations, over-engineered CI/CD pipelines, or secondary algorithms. Focus on delivering an exceptional, working, viva-ready retention system.
