# RetainIQ — Netlify Production Backend Connectivity & Authentication Repair Audit
**Date:** 25 November 2026  
**Document ID:** `PHASE_RETAINIQ_NETLIFY_PRODUCTION_CONNECTIVITY_REPORT.md`  
**Target:** Production Connectivity & Role Resolution Diagnostic  
**Deployed Frontend:** `https://retainiq-77c6be.netlify.app/`  
**Repository:** `https://github.com/snehranjan/Custome-Retention-Intelligence-System`  

---

## 1. Executive Summary & Root Cause Analysis

### Identified Problem
When users authenticate with Supabase on the deployed Netlify frontend (`https://retainiq-77c6be.netlify.app/`), client-side authentication succeeds and identity is verified via Supabase. However, post-authentication role checks on both the Employee Login page and the Administrator portal immediately display:
- `Backend Status: Check Failed`
- `Network connection failure contacting backend service: Failed to fetch`
- Administrators are shown an **"Employee Access Authorization Pending"** screen.

### Root Cause 1: Undeployed Backend & Localhost Fallback
1. **Frontend Environment Variable:** The frontend API client (`frontend/src/lib/apiClient.js`) relies strictly on the environment variable **`VITE_API_BASE_URL`**:
   ```javascript
   const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL || "http://localhost:8000").replace(/\/$/, "");
   ```
2. **Missing Production Variable in Netlify:** Netlify site `retainiq-77c6be` (Site ID: `4090bc22-256b-4e58-9f1f-a0f10e5fd004`) was inspected using Netlify MCP API tools. It contains **zero** environment variables (`[]`).
3. **Baked-in Localhost Target:** Because `frontend/.env.local` is correctly git-ignored and no production environment variable was configured in Netlify, the compiled Vite production bundle deployed to Netlify embedded the default fallback: `http://localhost:8000`.
4. **Browser Mixed Content & Unreachable Network:** When users visit `https://retainiq-77c6be.netlify.app/`, the browser attempts to fetch `http://localhost:8000/api/v1/...`. Modern browsers block mixed-content insecure HTTP requests from HTTPS sites, and external visitors have no backend running on their local device at port 8000, causing an immediate `TypeError: Failed to fetch`.
5. **No Cloud Backend Service Exists:** The RetainIQ FastAPI service with its locked Random Forest model (150 trees, 43 Config D features, joblib artifact) is currently **only running locally on the Windows host** (`http://127.0.0.1:8000`). No production cloud backend deployment exists on Render, Railway, Fly.io, AWS, Heroku, or GCP. Netlify cannot natively execute a persistent Python Uvicorn ASGI machine learning server.

### Root Cause 2: Role Resolution Fallthrough in `EmployeeLoginPage.jsx`
1. When an administrator signs in, `EmployeeLoginPage.jsx` calls `apiClient.admin.getProfile()` (`GET /api/v1/admin/me`).
2. When this call throws a network connection error (`err.status === 0` / `Failed to fetch`), the `.catch()` block erroneously caught **all** errors indiscriminately (instead of only HTTP 403 Forbidden) and fell through to call `checkEmployeeClearance()`.
3. `checkEmployeeClearance()` called `apiClient.employee.getProfile()` (`GET /api/v1/employee/me`), which also failed with a network error.
4. Because `employeeStatusCategory` remained `null` and `isAdmin` remained `false`, the JSX render logic fell into its default fallback branch: `<Building2 /> Employee Access Authorization Pending (Policy: ADMIN-CONTROLLED EMPLOYEE ACCOUNTS)`.
5. This caused administrators to believe their accounts were pending employee approval, when in reality the backend was simply unreachable.

---

## 2. Configuration & Netlify Environment Verification

### Frontend Configuration Details
- **API Client:** `frontend/src/lib/apiClient.js`
- **Exact Environment Variable Name:** `VITE_API_BASE_URL`
- **Exact Supabase Variables:** `VITE_SUPABASE_URL`, `VITE_SUPABASE_PUBLISHABLE_KEY`
- **Trailing-Slash / Path Handling:** `API_BASE_URL.replace(/\/$/, "")` strips trailing slashes; `cleanEndpoint` ensures a leading slash, constructing `${API_BASE_URL}/api/v1/...`.
- **Netlify Site Inspected:** `retainiq-77c6be` (`4090bc22-256b-4e58-9f1f-a0f10e5fd004`)
- **Netlify Deploy Context Checked:** Production environment variables returned `[]` (empty).

### Required Netlify Production Configuration
To connect the deployed frontend to a live cloud backend once provisioned, Netlify must be configured with:
- **Variable Name:** `VITE_API_BASE_URL`
- **Required Format:** `https://<your-backend-domain>` (HTTPS, no trailing slash, no `/api/v1` suffix).
- **Example:** `https://api.retainiq.yourdomain.com` or `https://retainiq-backend.onrender.com`

---

## 3. Backend Deployment Status

| Property | Status / Finding |
| :--- | :--- |
| **Backend Hosting Provider** | **None (Localhost only)** — No cloud infrastructure provisioned |
| **Production Backend URL** | **Not Deployed** (`http://127.0.0.1:8000` active on Windows host only) |
| **Startup Command** | `backend\.venv\Scripts\python.exe -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000` |
| **Local Health Endpoint** | `http://127.0.0.1:8000/api/v1/health` &rarr; `HTTP 200 {"status": "healthy"}` |
| **Production Health Endpoint** | **NOT TESTED** (No public cloud backend exists) |
| **ML Artifact Status** | Locked Random Forest pipeline ($B=150, \tau=0.50$, SHA-256: `24F1F0E3...3438F301`) and KMeans ($K=5$) fully loaded into memory |
| **Supabase Connectivity** | Configured in `backend/.env` with ES256/JWKS cryptographic token verification |

---

## 4. CORS Verification & Repair

### Investigation
Prior to this audit, `backend/app/core/config.py` restricted `BACKEND_CORS_ORIGINS` to:
```python
BACKEND_CORS_ORIGINS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]
```
Requests originating from `https://retainiq-77c6be.netlify.app` would have been rejected by FastAPI's `CORSMiddleware`.

### Applied Correction
Updated `backend/app/core/config.py` and environment defaults to permit:
- `"https://retainiq-77c6be.netlify.app"`
- `"https://retainiq-retention-system.netlify.app"`

Verified that `CORSMiddleware` in `backend/app/main.py`:
- Allows `allow_credentials=True`
- Allows standard HTTP methods (`GET`, `POST`, `PUT`, `DELETE`, `OPTIONS`)
- Allows standard headers including `Authorization` and `Content-Type`
- Uses strict origin matching (no wildcard `*` with credentials).

---

## 5. Authentication & Role Resolution State Machine Repair

### Changes in `frontend/src/pages/EmployeeLoginPage.jsx`
1. **Network Error Discrimination:** In `useEffect`, the catch handler for `apiClient.admin.getProfile()` was updated to inspect `err.status`:
   - If `err.status === 403` or `err.isForbiddenError`: The user is authenticated but genuinely lacks administrator privileges &rarr; correctly proceeds to `checkEmployeeClearance()`.
   - If `err.status !== 403` (e.g. status 0 / network failure): Does **not** fall through to employee clearance. Halts verification and sets:
     `verificationStatus = "failed"`
     `verificationError = "Failed to contact backend authorization service."`
2. **Dedicated Error Presentation:** The render tree was updated so that when `verificationStatus === "failed"`, the UI displays a dedicated **"Backend Authorization Service Unreachable"** alert card with target API URL and retry button, eliminating the misleading "Employee Access Authorization Pending" card.

---

## 6. Test & Verification Results

| Test Case | Expected Result | Actual Result | Status |
| :--- | :--- | :--- | :---: |
| **Public Website** | Loads successfully | HTTP 200 on `https://retainiq-77c6be.netlify.app/` | **PASS** |
| **Local Backend Health** | HTTP 200 | HTTP 200 on `http://127.0.0.1:8000/api/v1/health` | **PASS** |
| **Production Health Endpoint** | HTTP 200 | **NOT TESTED** (No cloud backend deployed) | **NOT TESTED** |
| **Frontend-to-Backend (Local)** | Successful API exchange | Verified on `http://127.0.0.1:5173` | **PASS** |
| **Frontend-to-Backend (Netlify)**| Successful API exchange | Fails: Netlify bundle points to localhost | **CONFIRMED BLOCKED** |
| **CORS Configuration** | Permits production Netlify origin | Configured in `backend/app/core/config.py` | **PASS** |
| **Admin Verification (Backend)** | HTTP 200 for authorized admin | HTTP 200 on `/api/v1/admin/me` with admin token | **PASS** |
| **Employee Verification (Backend)**| HTTP 200 for approved employee | HTTP 200 on `/api/v1/employee/me` with employee token | **PASS** |
| **Cross-Portal Authorization (Admin -> Employee)** | HTTP 403 unless approved | Enforced server-side by `require_authorized_employee` | **PASS** |
| **Cross-Portal Authorization (Employee -> Admin)** | HTTP 403 | Enforced server-side by `require_admin_user` | **PASS** |
| **Unauthenticated Protected Request** | HTTP 401 | Returns HTTP 401 Unauthorized with uniform envelope | **PASS** |
| **Frontend Unit & Component Suites** | All tests pass | **112 / 112 passed** across 42 suites | **PASS** |
| **Master Phase Test Suite** | All tests pass | **10 / 10 passed** | **PASS** |
| **Locked Model SHA-256** | `24F1F0E3...3438F301` | **Intact bit-for-bit** | **PASS** |

---

## 7. What is Missing & Recommended Next Steps

Per strict prompt constraints, no cloud hosting has been purchased or provisioned, keys have not been rotated, and no fake success has been claimed from local tests.

To achieve complete end-to-end production connectivity between Netlify and the backend:
1. **Deploy FastAPI Backend to a Cloud Container Platform:**
   - Deploy the Python FastAPI backend to Render, Railway, Fly.io, or an AWS/GCP container instance with Python 3.12, `requirements.txt`, and the locked model artifacts in `models/`.
   - Set the required backend environment variables (`SUPABASE_URL`, `SUPABASE_JWKS_URL`, `SUPABASE_SECRET_KEY`, `ADMIN_EMAILS`, etc.).
2. **Add `VITE_API_BASE_URL` to Netlify:**
   - In Netlify Site Settings for `retainiq-77c6be` &rarr; **Environment variables**, set:
     `VITE_API_BASE_URL = https://<deployed-backend-url>`
3. **Trigger Netlify Rebuild:**
   - Trigger a deploy on Netlify so Vite recompiles the client bundle with the production HTTPS backend URL.
