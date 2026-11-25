# RETAINIQ — LOCALHOST DEVELOPMENT ENVIRONMENT ROLLBACK AUDIT

**Project:** Indian E-Commerce Customer Retention Intelligence System (`RetainIQ`)  
**Scope:** Hosting Cancellation & Complete Localhost Environment Audit  
**Operating System:** Windows 11 (64-bit)  
**Audit Date:** November 25, 2026  
**Audit Status:** **AUDIT COMPLETE — LOCALHOST BASELINE VERIFIED & INTACT**  

---

## 1. PROJECT STRUCTURE & FRAMEWORK IDENTIFICATION

The RetainIQ codebase is structured cleanly into two decoupled subsystems:

```text
C:\customer churn retention system\
├── backend/
│   ├── app/
│   │   ├── core/               # App configuration, security, errors, logging
│   │   ├── repositories/       # Dual storage abstraction: SQLite & Supabase
│   │   ├── routes/             # FastAPI routers: auth, admin, employee, ml, customers, health
│   │   ├── schemas/            # Pydantic v2 domain & API schemas
│   │   ├── services/           # Business logic: ML boundary, loader, employee registry
│   │   └── main.py             # FastAPI entry point (app = create_app())
│   ├── ml/                     # ML pipelines & transformers (advanced_feature_engineering.py)
│   ├── .venv/                  # Dedicated Python 3.12 virtual environment
│   ├── .env                    # Local backend environment file (Ignored by Git)
│   ├── .env.example            # Sanitized backend environment template
│   └── requirements.txt        # Full backend dependencies (16 packages)
├── frontend/
│   ├── src/
│   │   ├── components/         # Design system & shared UI components
│   │   ├── context/            # AuthContext (Supabase Auth session provider)
│   │   ├── lib/                # apiClient.js (REST client), supabase.js (Auth singleton)
│   │   ├── pages/              # Showcase, Dashboard, AdminPortal, EmployeeLogin
│   │   ├── App.jsx             # Root React component & client router
│   │   └── main.jsx            # Vite DOM mount entry point
│   ├── dist/                   # Production build artifacts
│   ├── .env.local              # Local frontend environment file (Ignored by Git)
│   ├── .env.example            # Sanitized frontend environment template
│   ├── package.json            # Vite + React 18 dependencies
│   └── vite.config.js          # Vite build & local dev server configuration
├── data/
│   ├── local_database.db       # Primary local SQLite database (17.96 MB, 6 tables)
│   └── modeling/               # Feature datasets & splits
├── models/
│   ├── phase5_1/final_model/   # Locked Production Random Forest Pipeline (Config D)
│   ├── segmentation_scaler.joblib  # Locked RFM standardizer
│   └── kmeans_customer_segmentation.joblib  # Locked K-Means (K=5) model
├── reports/                    # Phase documentation & audits
├── tests/                      # Automated pytest test suites (123 passing tests)
├── requirements.txt            # Root-level requirements (synchronized)
└── pytest.ini                  # Master pytest configuration
```

### Frameworks & Runtimes:
* **Frontend:** React 18.3.1 with Vite 6.4.6, Tailwind CSS, Lucide icons.
* **Backend:** FastAPI 0.115.0 on Python 3.12.10 (64-bit), Uvicorn 0.32.0 ASGI server.
* **Machine Learning:** Scikit-Learn 1.5.0, Joblib 1.4.0, Pandas 2.2.0, NumPy 1.26.4.
* **Entry Points:**
  * Backend: `backend.app.main:app`
  * Frontend: `frontend/index.html` -> `frontend/src/main.jsx`
* **Local Run Commands:**
  * Backend: `backend\.venv\Scripts\python.exe -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000`
  * Frontend: `cmd /c "cd frontend && npm run dev -- --host 127.0.0.1 --port 5173"`

---

## 2. ENVIRONMENT CONFIGURATION AUDIT

### 2.1 Backend Environment (`backend/.env`)
* **Current Storage Mode:** `STORAGE_MODE=sqlite`
* **Local Database Path:** `LOCAL_DATABASE_PATH=data/local_database.db`
* **Supabase Auth URL:** `SUPABASE_URL=https://hyngxdkuanugcvqhkaas.supabase.co`
* **Supabase JWKS URL:** `SUPABASE_JWKS_URL=https://hyngxdkuanugcvqhkaas.supabase.co/auth/v1/.well-known/jwks.json`
* **Administrator Whitelist:** `ADMIN_EMAILS=["admin@retainiq.internal","system_admin@retainiq.internal"]`
* **Administrator Subject UUIDs:** `ADMIN_USER_IDS=["eda63471-d0f7-4145-b66b-9625e0766557"]`  
  *(Note: Production error displayed subject UUID `094329a6-0d56-47a7-8f8a-fe84e310d4a0` for `system_admin@retainiq.internal`. Adding this UUID to `ADMIN_USER_IDS` guarantees local administrator verification).*

### 2.2 Frontend Environment (`frontend/.env.local`)
* **Backend REST API Base URL:** `VITE_API_BASE_URL=http://localhost:8000`
* **Supabase URL:** `VITE_SUPABASE_URL=https://hyngxdkuanugcvqhkaas.supabase.co`
* **Supabase Public Key:** `VITE_SUPABASE_PUBLISHABLE_KEY=sb_publishable_NaJSKZOjztFxbMD_SOY0xA_aqwuEPf1`

**Finding:** The frontend `.env.local` was **already pointed to `http://localhost:8000`**. No remote Render URL was ever hardcoded into the frontend source code.

---

## 3. RENDER-SPECIFIC CONFIGURATION AUDIT

* **`render.yaml`:** **None found.** No infrastructure-as-code or Render blueprint file was ever created or committed.
* **Procfile / runtime.txt:** **None found.**
* **CORS Settings (`backend/app/main.py`):**
  `BACKEND_CORS_ORIGINS` already explicitly includes:
  * `http://localhost:5173`
  * `http://127.0.0.1:5173`
  * `http://localhost:3000`
  * `http://127.0.0.1:3000`
  * `https://retainiq-77c6be.netlify.app`
  Localhost origins are fully permitted and active by default.
* **Hosting-Specific Documentation:**
  Only three markdown audit reports in `reports/phase8/` (`PHASE_RETAINIQ_STAGE_8_1_HOSTING_READINESS_REPORT.md`, `PHASE_RETAINIQ_STAGE_8_2_DEPLOYMENT_PREPARATION_REPORT.md`, `PHASE_RETAINIQ_STAGE_8_3_DEPLOYMENT_REPORT.md`) discuss Render. No application code depends on Render.

---

## 4. SUPABASE AUTHENTICATION & DATABASE INTEGRATION STATUS

### 4.1 Supabase Authentication (Active & Operational)
* The frontend authentication flow (`frontend/src/lib/supabase.js`) communicates directly with Supabase Auth for sign-in, session persistence, and token issuance.
* The backend JWT verification engine (`backend/app/core/security.py`) contacts the public JWKS endpoint:  
  `https://hyngxdkuanugcvqhkaas.supabase.co/auth/v1/.well-known/jwks.json`
* **Verification:** Cryptographic signature verification of ES256 tokens was tested and confirmed **100% operational (HTTP 200, active public key verified)**. It does **NOT** require a secret service role key.

### 4.2 Database Storage Layer (Local SQLite Fully Preserved)
* **Revoked Secret Key Status:** As confirmed by the owner and validated via audit probe, the previously exposed Supabase secret key has been revoked and correctly returns `HTTP 401 Unauthorized` on PostgREST.
* **Local Database Status (`data/local_database.db`):**
  The local SQLite database is completely intact (17.96 MB) and contains the entire enterprise dataset:
  * `customers`: **7,000 rows**
  * `customer_predictions`: **7,000 rows**
  * `customer_segments`: **7,000 rows**
  * `retention_recommendations`: **16,580 rows**
  * `employee_registry`: **193 rows**
  * `schema_migrations`: **2 rows**
* **Finding:** When `STORAGE_MODE=sqlite`, the backend serves all customer profiles, churn predictions, segmentation analytics, and employee reviews entirely from `data/local_database.db` with zero reliance on remote database calls.

---

## 5. GIT & CODE MODIFICATION STATUS

* **Current Branch:** `main`
* **HEAD Commit:** `8579da5265130b1f0b87cff64f1ca933c1ac36a7` (`8579da5`)
* **Working Tree State:**
  * `modified: requirements.txt`: Root requirements was synchronized with `backend/requirements.txt` to include `pydantic-settings`, `python-dotenv`, `httpx`, and `pytest-timeout`. These are required backend packages that belong in requirements.
  * No code regressions or breaking changes were introduced.

---

## 6. LOCKED MACHINE LEARNING MODEL ARTIFACT INTEGRITY

All three locked production models remain byte-for-byte unchanged:

| Model Artifact | File Path | File Size | SHA-256 Checksum | Integrity Status |
| :--- | :--- | :--- | :--- | :--- |
| **Random Forest Pipeline (Config D)** | `models/phase5_1/final_model/final_churn_rf_pipeline.joblib` | 2.5073 MB | `24F1F0E33C75B5590906369960DB6E5951EC95DF9AE40384DA60082B3438F301` | **MATCH (Locked)** |
| **RFM Segmentation Scaler** | `models/segmentation_scaler.joblib` | 0.0009 MB | `892B9F3CDDA5427DD3965C76B95C1BC952661BAEA993FBBA94D5A3F56FB2EC4C` | **MATCH (Locked)** |
| **K-Means Clustering ($K=5$)** | `models/kmeans_customer_segmentation.joblib` | 0.0275 MB | `A018E41C8DC78BBDEC7C157B71ED66FEAC698336F787B39D84583FAE9CB931B3` | **MATCH (Locked)** |

---

## 7. IDENTIFIED ACTIONS FOR PHASE 2 LOCALHOST RESTORATION

1. **Reconcile `ADMIN_USER_IDS` in `backend/.env`:**
   Add `"094329a6-0d56-47a7-8f8a-fe84e310d4a0"` alongside `"eda63471-d0f7-4145-b66b-9625e0766557"` in `ADMIN_USER_IDS` so that logging in locally as `system_admin@retainiq.internal` grants immediate administrator privileges.
2. **Remove Revoked Secret Key from `backend/.env`:**
   Clear out the revoked `SUPABASE_SECRET_KEY` so no expired credential lingers in local configuration.
3. **Verify Local Ports:**
   * Backend binds to `127.0.0.1:8000`.
   * Frontend binds to `127.0.0.1:5173`.
4. **End-to-End Local Execution & Verification:**
   Launch both services locally, execute health checks, and verify customer and prediction endpoints.
