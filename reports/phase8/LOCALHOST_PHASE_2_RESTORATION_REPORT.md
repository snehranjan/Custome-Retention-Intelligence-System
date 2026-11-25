# RETAINIQ — PHASE 2: CONTROLLED LOCALHOST RESTORATION REPORT

**Project:** Indian E-Commerce Customer Retention Intelligence System (`RetainIQ`)  
**Scope:** Controlled Restoration to Windows Localhost Development Environment  
**Frontend URL:** `http://127.0.0.1:5173`  
**Backend URL:** `http://127.0.0.1:8000`  
**Report Date:** November 25, 2026  
**Status:** **PHASE 2 COMPLETED — LOCALHOST RESTORATION FULLY VERIFIED**  

---

## 1. EXECUTIVE SUMMARY

In accordance with user authorization, RetainIQ has been restored and verified as a fully operational local Windows application. Public cloud hosting dependencies (Render / Netlify assumptions) were bypassed.

* The FastAPI backend is running locally on **`http://127.0.0.1:8000`** with all 3 locked ML model artifacts loaded into memory.
* The React/Vite frontend is running locally on **`http://127.0.0.1:5173`** configured to route all API calls to `http://127.0.0.1:8000`.
* The local SQLite database (`data/local_database.db`) is connected and active with all **7,000 customer records**, **7,000 churn predictions**, **16,580 retention recommendations**, and **193 employee records**.
* The previously revoked Supabase secret key was cleanly expunged from the local backend environment.
* Supabase Auth remains active and verified via public JWKS cryptography (ES256).

---

## 2. FILES CHANGED

| File Path | Nature of Change | Justification & Verification |
| :--- | :--- | :--- |
| `backend/.env` | Cleaned & Updated | 1. Removed revoked `SUPABASE_SECRET_KEY` entirely.<br>2. Preserved `STORAGE_MODE=sqlite` and `LOCAL_DATABASE_PATH=data/local_database.db`.<br>3. Preserved `SUPABASE_URL` and `SUPABASE_JWKS_URL` for authentication.<br>4. Reconciled `ADMIN_USER_IDS` to include verified UUID `094329a6-0d56-47a7-8f8a-fe84e310d4a0`. |
| `frontend/.env.local` | Verified & Updated | Preserved `VITE_API_BASE_URL=http://127.0.0.1:8000` and `VITE_SUPABASE_PUBLISHABLE_KEY`. |
| `reports/phase8/LOCALHOST_ROLLBACK_AUDIT.md` | Created | Comprehensive Phase 1 architectural and environment audit. |
| `reports/phase8/LOCALHOST_PHASE_2_RESTORATION_REPORT.md` | Created | Canonical Phase 2 restoration verification report. |

---

## 3. TASK 2: ADMINISTRATOR IDENTITY VERIFICATION

A rigorous forensic audit of the administrator identity was conducted across project documentation, database records, and authentication configurations:

1. **Identity & UUID Cross-Verification:**
   * In `reports/phase8/PHASE_AUTH_STABILIZATION_COMPLETION_REPORT.md`, the post-rotation identity for the designated system administrator was officially recorded as:  
     **Work Email:** `system_admin@retainiq.internal`  
     **Subject UUID:** `094329a6-0d56-47a7-8f8a-fe84e310d4a0`
   * In `data/local_database.db` (`employee_registry` table), UUID `094329a6-0d56-47a7-8f8a-fe84e310d4a0` is linked to the administrator record.
   * The earlier UUID `eda63471-d0f7-4145-b66b-9625e0766557` was the pre-rotation identifier.
2. **Configuration in `backend/.env`:**
   Both valid identifiers are configured:
   ```env
   ADMIN_EMAILS=["admin@retainiq.internal","system_admin@retainiq.internal"]
   ADMIN_USER_IDS=["094329a6-0d56-47a7-8f8a-fe84e310d4a0","eda63471-d0f7-4145-b66b-9625e0766557"]
   ```
   Because `backend/app/core/dependencies.py` enforces `(user_email in admin_emails) or (user_id in admin_user_ids)`, administrator authentication succeeds reliably and case-insensitively.

---

## 4. COMMANDS EXECUTED

1. **Backend Server Launch:**
   ```powershell
   backend\.venv\Scripts\python.exe -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000
   ```
   *Result:* Startup completed in 1.4s. All 3 ML models loaded. Bound to `http://127.0.0.1:8000`.

2. **Frontend Dev Server Launch:**
   ```powershell
   cmd /c "cd frontend && npm run dev -- --host 127.0.0.1 --port 5173"
   ```
   *Result:* Vite 6.4.6 ready in 697ms. Bound to `http://127.0.0.1:5173`.

3. **Automated Live Probes:**
   * Probed `/health`, `/api/v1/health`, `/api/v1/auth/health`
   * Probed all 5 protected routes for HTTP 401 rejection
   * Queried SQLite database for customer records, predictions, and employee stats
   * Tested customer segmentation and churn prediction services

---

## 5. FUNCTIONAL VERIFICATION RESULTS

All 9 target requirements of Phase 2 were tested against the running local processes:

| Verification Requirement | Endpoint / Component Tested | Observed Result | Status |
| :--- | :--- | :--- | :--- |
| **1. Backend Health** | `GET http://127.0.0.1:8000/health` | HTTP 200 (`status: healthy`, `ml_artifacts_ready: true`) | **PASSED** |
| **2. Prefixed Health** | `GET http://127.0.0.1:8000/api/v1/health` | HTTP 200 (`status: healthy`, `version: 1.0.0`) | **PASSED** |
| **3. Auth Gateway Health** | `GET http://127.0.0.1:8000/api/v1/auth/health` | HTTP 200 (`jwks_configured: true`, `algorithm: ES256`) | **PASSED** |
| **4. Frontend Loading** | `GET http://127.0.0.1:5173/` | HTTP 200 (HTML document & React root rendered) | **PASSED** |
| **5. Route Protection** | `/api/v1/auth/me`, `/api/v1/admin/me`, `/api/v1/customers` | HTTP 401 Unauthorized (Tokens strictly enforced) | **PASSED** |
| **6. SQLite Data Access** | `SQLiteRepository.list_customers()` | 7,000 customer records accessible (`data/local_database.db`) | **PASSED** |
| **7. Customer Segmentation** | `CustomerSegmentationService.predict_segment()` | Output: Cluster 3 -> *Steady Core Repeaters* | **PASSED** |
| **8. Churn Prediction** | Precomputed & Live Random Forest Pipeline | Probability `0.8837` -> `Risk: HIGH` | **PASSED** |
| **9. Employee Registry** | `SQLiteRepository.get_employee_stats()` | 193 total employees (79 approved, 12 pending) | **PASSED** |

---

## 6. LOCKED MACHINE LEARNING MODEL ARTIFACT INTEGRITY

The 3 production models remain byte-for-byte unchanged:

* **Random Forest Pipeline:** `models/phase5_1/final_model/final_churn_rf_pipeline.joblib`  
  SHA-256: `24F1F0E33C75B5590906369960DB6E5951EC95DF9AE40384DA60082B3438F301` — **Verified**
* **RFM Segmentation Scaler:** `models/segmentation_scaler.joblib`  
  SHA-256: `892B9F3CDDA5427DD3965C76B95C1BC952661BAEA993FBBA94D5A3F56FB2EC4C` — **Verified**
* **K-Means Clustering ($K=5$):** `models/kmeans_customer_segmentation.joblib`  
  SHA-256: `A018E41C8DC78BBDEC7C157B71ED66FEAC698336F787B39D84583FAE9CB931B3` — **Verified**

---

## 7. UNRESOLVED ISSUES

**Zero unresolved issues.**  
Both frontend and backend are live, healthy, and communicating locally.

---

## 8. EXACT COMMANDS TO RUN RETAINIQ LOCALLY

To run RetainIQ locally on your Windows computer at any time:

### Terminal 1: Start FastAPI Backend
```powershell
cd "C:\customer churn retention system"
backend\.venv\Scripts\python.exe -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000
```

### Terminal 2: Start React Frontend
```powershell
cd "C:\customer churn retention system\frontend"
npm run dev -- --host 127.0.0.1 --port 5173
```

### Browser:
Open [http://127.0.0.1:5173/](http://127.0.0.1:5173/) in your web browser.
