# RetainIQ — Stage 8.1: Production Hosting Selection & Backend Deployment Readiness Audit

**Project:** Indian E-Commerce Customer Retention Intelligence System  
**Product:** RetainIQ  
**Target:** Production Backend Hosting Strategy & Architecture Readiness  
**Date Checked:** 25 November 2026  
**Document ID:** `PHASE_RETAINIQ_STAGE_8_1_HOSTING_READINESS_REPORT.md`  
**Workspace:** `C:\customer churn retention system`  
**Frontend URL:** `https://retainiq-77c6be.netlify.app/`  
**Repository:** `https://github.com/snehranjan/Custome-Retention-Intelligence-System`  

---

## 1. Executive Summary

The RetainIQ frontend is successfully deployed and running on Netlify (`https://retainiq-77c6be.netlify.app/`). However, client-side API requests to the backend fail with `Network connection failure contacting backend service: Failed to fetch` because the production build fell back to `http://localhost:8000`, as the FastAPI backend is currently running only on the local development host (`127.0.0.1:8000`).

This audit evaluates the architectural requirements, machine-learning resource demands, package compatibility, and cloud hosting alternatives for deploying the FastAPI backend as an independent cloud service.

---

## 2. Repository & Backend Architecture Inspection

### 2.1 Backend Application Entry Point & Lifespan
- **Entry Point:** `backend/app/main.py` (`create_app` factory & `lifespan` context manager).
- **Startup Sequence:**
  1. `setup_logging()`: Initializes structured operational logging.
  2. `MLServiceBoundary.setup_ml_environment()`: Registers `backend/ml` in `sys.path` and pre-imports `advanced_feature_engineering.py` so custom transformers (`Log1pTransformer`, `CorrelationPruner`) can be unpickled cleanly.
  3. `ModelLoader.load_all()`: Loads locked Random Forest pipeline, segmentation scaler, and K-Means segmentation model into memory during startup.
- **Shutdown Sequence:**
  - `ModelLoader.unload_all()`: Cleanly clears in-memory model caches and releases memory buffers.

### 2.2 Routing & API Architecture
- Versioned API prefix: `/api/v1`
- Endpoints registered:
  - `/api/v1/health`: System health and ML readiness telemetry (public).
  - `/api/v1/auth/me`: Minimal verified identity extraction from Supabase JWT (authenticated).
  - `/api/v1/admin/*`: Administrator verification, employee approval/rejection, user directory, system statistics.
  - `/api/v1/employee/*`: Employee profile and registration workflow.
  - `/api/v1/customers/*`: Customer list, detail, and churn prediction inference.
  - `/api/v1/analytics/*`: Cohort overview, persona segmentation distribution, model performance metrics.
  - `/api/v1/recommendations/*`: Segment-specific customer retention playbooks and ROI impact.
  - `/api/v1/database/*`: Storage connectivity health check.

### 2.3 Required Files for Cloud Deployment
The backend can be deployed independently from the repository without moving or changing existing files. The required files are:
```text
├── requirements.txt                              # Python package dependencies
├── backend/                                      # Application source code
│   ├── app/
│   │   ├── main.py                               # FastAPI application entry point
│   │   ├── core/                                 # Config, security, logging, errors
│   │   ├── routes/                               # Route definitions under /api/v1
│   │   ├── schemas/                              # Pydantic request/response models
│   │   ├── services/                             # Churn, segmentation, import, persistence
│   │   └── repositories/                         # SQLite and Supabase data layers
│   └── ml/
│       └── advanced_feature_engineering.py       # Custom transformers required for RF pipeline
├── models/                                       # Model artifacts (already tracked in Git)
│   ├── phase5_1/final_model/
│   │   └── final_churn_rf_pipeline.joblib        # Locked production RF classifier (2.51 MB)
│   ├── segmentation_scaler.joblib                # RobustScaler for RFM features (3 KB)
│   └── kmeans_customer_segmentation.joblib       # K-Means clustering model K=5 (35 KB)
└── data/                                         # Datasets (CSV fallbacks & offline evaluation)
```

---

## 3. Machine-Learning Deployment Compatibility

### 3.1 Model Artifact Specifications & Invariants
- **Locked Random Forest Pipeline:** `models/phase5_1/final_model/final_churn_rf_pipeline.joblib`
  - **Size:** **2.51 MB**
  - **SHA-256 Checksum:** `24F1F0E33C75B5590906369960DB6E5951EC95DF9AE40384DA60082B3438F301`
  - **Estimator Count:** $B = 150$ trees (`n_estimators = 150`)
  - **Max Tree Depth:** `max_depth = 8`
  - **Min Leaf Size:** `min_samples_leaf = 5`
  - **Decision Boundary:** Locked classification threshold $\tau = 0.50$
  - **Input Schema:** Strictly requires the exact **43 raw Config D features** (40 numerical + 3 categorical).
- **Segmentation Scaler:** `models/segmentation_scaler.joblib` (**3 KB**)
- **K-Means Cluster Model:** `models/kmeans_customer_segmentation.joblib` (**35 KB**, $K=5$ personas)
- **Combined Artifact Storage Footprint:** **~2.55 MB** (Extremely lightweight).

### 3.2 Empirical Memory Benchmarking
Benchmarked using Python 3.12 runtime and memory tracing (`tracemalloc`):
- **Base memory before loading models:** ~0.00 MB delta
- **Memory delta upon loading all 3 artifacts:** **+3.20 MB**
- **Memory after running batch inference on 1,500 customer records:** **11.26 MB**
- **Peak traced memory during batch inference:** **12.89 MB**
- **FastAPI Uvicorn Process Resident Set Size (RSS):** **~85 MB to 125 MB RAM**

### 3.3 Storage & Execution Characteristics
- **Startup Loading:** The application loads all ML models into memory once at container startup inside the FastAPI lifespan context. Inference requests execute in memory in **< 15 ms** per customer with zero disk I/O.
- **Persistent Disk Storage:** **Not required in production.** When configured with `STORAGE_MODE=supabase`, all state (customer records, audit logs, employee accounts) persists in the cloud Supabase database. The container root filesystem can be completely ephemeral.
- **Git Inclusion:** All model artifacts (`models/`) are already checked into Git (commit `a6ef58a` on branch `main`). No external AWS S3, Google Cloud Storage, or Hugging Face blob downloading steps are required during build.

---

## 4. Hosting Provider Comparison

| Criteria | Render | Railway | Fly.io | Koyeb |
| :--- | :--- | :--- | :--- | :--- |
| **Free Tier Available?** | **Yes (Free Web Service)** | **No** (Hobby plan is $5/mo usage credit) | **Yes** ($5/mo credit with credit card) | **Yes (Free Eco Tier)** |
| **Monthly Pricing (USD)** | Free: $0<br>Starter (Always-On): $7/mo | Hobby: $5/mo base + usage | Free: $0 (up to $5 allowance)<br>Paid: Pay-as-you-go | Free: $0<br>Starter: $5.40/mo |
| **Approximate Monthly Cost (INR)** | **Free: ₹0**<br>Starter: ~₹585 | ~₹420 | **Free: ₹0**<br>Scale: ~₹310–₹550 | **Free: ₹0**<br>Scale: ~₹450 |
| **RAM Allocation** | 512 MB (Free & Starter) | Up to 8 GB per replica | 256 MB or 512 MB shared | 512 MB |
| **CPU Allocation** | 0.1 vCPU (Free), 0.5 vCPU (Starter) | Shared vCPU (unthrottled) | 1 shared CPU | 0.1 vCPU |
| **Sleep / Cold Start Behavior** | **Spins down after 15 min idle** (~30–50s wake-up delay on Free) | **Always-on (Zero sleep)** on Hobby plan | Machines stop on idle if configured; zero sleep if set to keep alive | **Zero sleep** on Free Nano/Micro |
| **Persistent Storage** | Ephemeral on Free; paid disk option | 5 GB volume included | 5 GB volume allowance | Ephemeral |
| **Python 3.12 Support** | Native (auto-detects `requirements.txt`) | Native (Nixpacks / Buildpacks) | Via Dockerfile | Native or Dockerfile |
| **FastAPI / Uvicorn Support** | Native startup command | Native startup command | Native startup command | Native startup command |
| **GitHub Integration** | Native 1-click continuous deploy | Native 1-click continuous deploy | Via CLI or GitHub Actions | Native 1-click continuous deploy |
| **Automatic HTTPS** | Free managed SSL (`.onrender.com`) | Free managed SSL (`.up.railway.app`) | Free managed SSL (`.fly.dev`) | Free managed SSL (`.koyeb.app`) |
| **Environment Variable Tooling** | Built-in web UI & secret masking | Built-in web UI & secret masking | Web UI & CLI (`fly secrets`) | Built-in web UI |
| **ML Inference Adequacy** | **Excellent** (FastAPI needs ~120 MB RAM; 512 MB is plenty) | **Excellent** | **Good** (requires 512MB machine) | **Excellent** |
| **University Demo Reliability** | **High** (Wake container 2 min prior to demo, or use $7 Starter) | **Very High** (Always warm, sub-100ms response) | Medium (CLI setup overhead) | High |
| **Documentation & Reference** | [Render Pricing](https://render.com/pricing)<br>*(Checked 25 Nov 2026)* | [Railway Pricing](https://railway.com/pricing)<br>*(Checked 25 Nov 2026)* | [Fly.io Pricing](https://fly.io/docs/about/pricing/)<br>*(Checked 25 Nov 2026)* | [Koyeb Pricing](https://www.koyeb.com/pricing)<br>*(Checked 25 Nov 2026)* |

---

## 5. Architectural Recommendations

### 5.1 Best Completely Free Option: Render (Free Web Service)
- **Cost:** **$0 / month (₹0)**
- **Why:** 
  - Connects directly to `https://github.com/snehranjan/Custome-Retention-Intelligence-System` with zero credit card required.
  - Automatically provisions an HTTPS endpoint (e.g. `https://retainiq-api.onrender.com`).
  - 512 MB RAM comfortably accommodates our 120 MB FastAPI process footprint.
  - Auto-deploys on every `git push` to `main`.
- **Known Trade-Off:** Spins down after 15 minutes of inactivity. The first request after an idle period takes ~30–50 seconds to boot the container (all subsequent requests respond in < 25 ms).

### 5.2 Best Low-Cost / Zero-Sleep Option: Railway (Hobby Plan)
- **Cost:** **$5 / month (~₹420 INR)**
- **Why:** 
  - Guaranteed 24/7 uptime with **zero sleep / zero spin-down**.
  - No cold-start latency whatsoever.
  - Generous compute headroom (unthrottled vCPU, per-second metering).

### 5.3 Best Option for University Demonstration
- **Recommendation:** **Render Free Tier with Pre-Demo Warmup** (or **Render Starter at $7 / ₹585** for the evaluation month).
- **Presentation Strategy:**
  1. If using the Free Tier, simply open `https://<your-render-url>/api/v1/health` in a browser 2 minutes before the presentation starts. This wakes the container and keeps it hot and responsive for the entire duration of the evaluation session.
  2. If 100% instant response guarantee without pre-warming is required, upgrading Render to the $7/month Starter plan for a single billing cycle eliminates the 15-minute sleep timer.

### 5.4 Final Recommended Architecture Combination
```text
┌───────────────────────────────────────────────┐
│              NETLIFY (Frontend)               │
│     https://retainiq-77c6be.netlify.app       │
│  - React 18, Vite, Tailwind, Ink & Slate      │
│  - SPA Routing (_redirects + netlify.toml)    │
│  - Env: VITE_API_BASE_URL (Render HTTPS URL)  │
└───────────────────────┬───────────────────────┘
                        │ HTTPS REST Calls
                        ▼
┌───────────────────────────────────────────────┐
│            RENDER (FastAPI Backend)           │
│       https://retainiq-api.onrender.com       │
│  - Python 3.12, Uvicorn, FastAPI              │
│  - In-Memory Scikit-Learn Model (B=150, τ=0.5)│
│  - K-Means Customer Persona Segmentation (K=5)│
│  - Strict CORS for Netlify Frontend Origin    │
└───────────────────────┬───────────────────────┘
                        │ ES256 / JWKS Validation
                        ▼
┌───────────────────────────────────────────────┐
│               SUPABASE (Cloud)                │
│    https://hyngxdkuanugcvqhkaas.supabase.co   │
│  - Client Authentication (ES256 JWT tokens)   │
│  - User Directory & Profile Identity          │
│  - Customer Data & Predictions Storage        │
└───────────────────────────────────────────────┘
```

---

## 6. Deployment Prerequisites & Required Configuration

### 6.1 Required Build & Startup Commands
- **Root Directory:** `.` (repository root)
- **Build Command:** `pip install -r requirements.txt`
- **Start Command:** `uvicorn backend.app.main:app --host 0.0.0.0 --port $PORT`

### 6.2 Environment Variable NAMES (No Secrets Printed)
When creating the backend Web Service on the cloud provider, configure these variable names in the provider's dashboard:

| Variable Name | Purpose | Example / Required Format |
| :--- | :--- | :--- |
| `ENVIRONMENT` | Server execution mode | `production` |
| `DEBUG` | FastAPI debug mode | `false` |
| `PORT` | Container listen port | `10000` (Render default) or auto-assigned |
| `LOG_LEVEL` | Logging verbosity | `INFO` |
| `BACKEND_CORS_ORIGINS` | Permitted frontend origins | `["https://retainiq-77c6be.netlify.app","https://retainiq-retention-system.netlify.app"]` |
| `STORAGE_MODE` | Active repository layer | `supabase` (or `sqlite` with bundled fallback) |
| `SUPABASE_URL` | Supabase project URL | `https://hyngxdkuanugcvqhkaas.supabase.co` |
| `SUPABASE_PUBLISHABLE_KEY` | Public client anon key | *(From existing Supabase dashboard)* |
| `SUPABASE_SECRET_KEY` | Server-side service key | *(From existing Supabase dashboard)* |
| `SUPABASE_JWKS_URL` | Authoritative JWKS URL | `https://hyngxdkuanugcvqhkaas.supabase.co/auth/v1/.well-known/jwks.json` |
| `ADMIN_EMAILS` | Authorized admin list | `["admin@retainiq.internal","system_admin@retainiq.internal","snehranjan30@gmail.com"]` |
| `ADMIN_USER_IDS` | Authorized admin IDs | *(Optional JSON array)* |
| `AUTHORIZED_EMPLOYEE_EMAILS`| Fallback employee list | `["employee@retainiq.internal"]` |

*(Security Note: Exact secret credentials must be copied directly from `backend/.env` into Render's secure Environment Settings. Never commit them to Git).*

### 6.3 Netlify Environment Variable Update
Once the backend is live at `https://<app-name>.onrender.com`:
- In Netlify Site Settings for `retainiq-77c6be` &rarr; **Environment variables**:
  - **Key:** `VITE_API_BASE_URL`
  - **Value:** `https://<app-name>.onrender.com`
- Trigger a redeploy on Netlify so Vite builds the frontend bundle with the live production backend URL.

---

## 7. Potential Deployment Risks & Mitigations

1. **Cold-Start Delay on Free Tier:**
   - *Risk:* Demonstrating the project to university evaluators after 15 minutes of inactivity may trigger a 30–50 second loading pause on initial login.
   - *Mitigation:* Ping the `/api/v1/health` endpoint 2 minutes before the presentation starts, or upgrade to Render Starter ($7) for the presentation week.
2. **Missing `backend/ml` in Module Resolution:**
   - *Risk:* Unpickling the Random Forest model could fail with `ModuleNotFoundError: No module named 'advanced_feature_engineering'`.
   - *Mitigation:* Verified that `MLServiceBoundary.setup_ml_environment()` in `backend/app/main.py` explicitly registers `backend/ml` in `sys.path` prior to unpickling.
3. **CORS Rejection:**
   - *Risk:* Cloud backend rejects requests from `https://retainiq-77c6be.netlify.app`.
   - *Mitigation:* Verified that `backend/app/core/config.py` contains `https://retainiq-77c6be.netlify.app` in `BACKEND_CORS_ORIGINS` (committed in `a6ef58a`).
4. **Mixed Content Errors:**
   - *Risk:* Browser blocks requests if `VITE_API_BASE_URL` uses `http://` instead of `https://`.
   - *Mitigation:* Render provisions automatic TLS certificates; Netlify will use `https://`.

---

## 8. Proposed Deployment Sequence (Awaiting User Approval)

Upon explicit user authorization:
1. **Step 1:** User creates a free Web Service on [Render.com](https://render.com) linked to GitHub repository `snehranjan/Custome-Retention-Intelligence-System`.
2. **Step 2:** Configure the build settings (`pip install -r requirements.txt`) and startup command (`uvicorn backend.app.main:app --host 0.0.0.0 --port $PORT`).
3. **Step 3:** Enter the backend environment variables in Render's dashboard.
4. **Step 4:** Deploy and verify `GET https://<app-name>.onrender.com/api/v1/health` returns `HTTP 200 {"status": "healthy"}`.
5. **Step 5:** Add `VITE_API_BASE_URL = https://<app-name>.onrender.com` in Netlify site settings.
6. **Step 6:** Trigger a Netlify deploy and verify live end-to-end authentication and model inference on `https://retainiq-77c6be.netlify.app/`.

---

## 9. Compliance & Stop Protocol

In strict adherence to project invariants and the Stage 8.1 specification:
- **No cloud hosting accounts have been created.**
- **No hosting services have been purchased.**
- **No secret keys or credentials have been exposed or committed.**
- **The locked Random Forest model and K-Means segmentation artifacts remain unmodified.**
- **Local test results have not been misrepresented as cloud deployments.**

*Audit complete. Awaiting explicit user approval before proceeding to deployment execution.*
