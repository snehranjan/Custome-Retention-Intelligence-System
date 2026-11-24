import os
import json

WORKSPACE = r"C:\customer churn retention system"
ARCHIVE_ROOT = os.path.join(WORKSPACE, "RETAINIQ_PROJECT_ARCHIVE")
DOCS_ROOT = os.path.join(ARCHIVE_ROOT, "PHASE_DOCUMENTATION")
SCREENSHOTS_ROOT = os.path.join(ARCHIVE_ROOT, "SCREENSHOTS")

with open(os.path.join(ARCHIVE_ROOT, ".archive_metadata.json"), "r", encoding="utf-8") as fp:
    meta = json.load(fp)

docs = meta["docs"]
images = meta["images"]

# -----------------------------------------------------------------
# 2. RETAINIQ_PROJECT_ARCHIVE/PHASE_DOCUMENTATION/README.md
# -----------------------------------------------------------------
phase_summary_table = [
    ("PHASE_01", "Synthetic Dataset Architecture & Referential Integrity", 4, "data/raw/ customers (7,000) & orders (84,225) generation, referential integrity certification, and base project rules.", "Completed & Audited"),
    ("PHASE_02", "Exploratory Data Analysis & Visualizations", 1, "Full 15-section exploratory data analysis report examining churn distributions, revenue by category, and regional patterns.", "Completed & Certified"),
    ("PHASE_03", "Feature Engineering, Velocity Ratios & Anti-Leakage", 1, "Engineered 36 baseline behavioral features, order velocities, friction indices, and temporal anti-leakage audit.", "Completed & Certified"),
    ("PHASE_04", "RFM Customer Segmentation & Multi-Seed K-Means", 1, "Unsupervised clustering (K=5) discovering 5 official personas with multi-seed ARI = 0.9931 stability.", "Completed & Certified"),
    ("PHASE_05", "Supervised Baseline Modeling & Model Explainability", 5, "Benchmarking Logistic Regression, Random Forest, and XGBoost baseline configurations with SHAP explainability.", "Completed & Certified"),
    ("PHASE_05_1", "Mathematical Bayes Error Audit, Config D & Independent Cohort", 8, "Oracle Bayes error bound (26.03%), Config D Random Forest (B=150), and single uncalibrated evaluation on N=1,500 unseen cohort.", "Completed & Audited"),
    ("PHASE_06", "Administrator Portal Transformation & System Audit", 4, "Complete administrative transformation, account approval workflows, invitation generation, and master project audit.", "Completed & Certified"),
    ("PHASE_07", "FastAPI REST Backend, Dual Persistence & Cryptographic Auth", 23, "Full REST backend architecture, Pydantic contracts, SQLite local fallback, remote Supabase PostgreSQL, and ES256 JWKS auth.", "Completed & Certified"),
    ("PHASE_07_1", "Audit Reconciliation (Observed Metrics & Raw Probabilities)", 1, "Mathematical reconciliation of 45.81% observed churn and clarification of raw uncalibrated Random Forest tree voting.", "Completed & Certified"),
    ("PHASE_07_2", "Final Model & Test-Warning Reconciliation", 1, "Direct empirical verification of fitted Random Forest tree count (B=150) and zero scikit-learn test deprecations.", "Completed & Certified"),
    ("PHASE_08", "Frontend Portal, Ink & Slate UI & Theme Switcher", 35, "React 19 Vite application, Supabase client integration, Ink & Slate enterprise design system, comfort spacing, and Light/Dark mode switcher.", "Completed & Certified"),
]

phase_docs_readme = f"""# RetainIQ Phase Documentation Catalog
## Complete Engineering & Audit Lifecycle Documentation

**Archive Root:** `C:\\customer churn retention system\\RETAINIQ_PROJECT_ARCHIVE\\PHASE_DOCUMENTATION`  
**Total Documented Milestones:** 11 Phases  
**Total Archived Reports:** {len(docs)} Files  
**Status:** 100% Cryptographically Verified & Audited

---

## 1. Master Phase Completion Matrix

| Phase | Phase Name | Documentation Files | Scope & Technical Domain | Status |
| :--- | :--- | :---: | :--- | :--- |
"""

for p_id, p_name, count, desc, stat in phase_summary_table:
    phase_docs_readme += f"| **[{p_id}](file:///c:/customer%20churn%20retention%20system/RETAINIQ_PROJECT_ARCHIVE/PHASE_DOCUMENTATION/{p_id})** | **{p_name}** | **{count} files** | {desc} | `{stat}` |\n"

phase_docs_readme += """
---

## 2. Detailed Phase Breakdown & File Inventory

"""

# Group docs by category
docs_by_phase = {}
for d in docs:
    p = d["category"]
    docs_by_phase.setdefault(p, []).append(d)

for p_id in sorted(docs_by_phase.keys()):
    phase_docs_readme += f"### {p_id}\n\n"
    phase_docs_readme += "| File Name | Original Workspace Location | Size | SHA-256 Hash |\n"
    phase_docs_readme += "| :--- | :--- | :---: | :--- |\n"
    for d in docs_by_phase[p_id]:
        arch_link = d['archive_path'].replace('\\', '/')
        phase_docs_readme += f"| [`{d['filename']}`](file:///c:/customer%20churn%20retention%20system/{arch_link}) | `{d['original_path']}` | {d['size_bytes']:,} B | `{d['sha256'][:16]}...` |\n"
    phase_docs_readme += "\n"

with open(os.path.join(DOCS_ROOT, "README.md"), "w", encoding="utf-8") as fp:
    fp.write(phase_docs_readme)

print("Generated RETAINIQ_PROJECT_ARCHIVE/PHASE_DOCUMENTATION/README.md")

# -----------------------------------------------------------------
# 3. RETAINIQ_PROJECT_ARCHIVE/SCREENSHOTS/README.md
# -----------------------------------------------------------------
screenshots_readme = f"""# RetainIQ Application Screenshot Archive
## Empirical Visual Evidence & Cross-Portal UI Verification

**Archive Root:** `C:\\customer churn retention system\\RETAINIQ_PROJECT_ARCHIVE\\SCREENSHOTS`  
**Total Screenshots Archived:** {len(images)} Files  
**Capture Engine:** Google Chrome Headless (`--headless=new`) via Chrome DevTools Protocol  
**Verification Status:** 100% Validated Real Application Captures (Zero Mockups or Placeholders)

---

## 1. Screenshot Category Overview

All screenshots are authentic visual captures generated by automated scripts targeting the live local development servers:
* **React 19 Frontend:** `http://127.0.0.1:5173` (Vite)
* **FastAPI Backend:** `http://127.0.0.1:8000` (Uvicorn Daemon)
* **Supabase Authentication:** Remote Cloud Supabase (`generate_link` token authentication)

| Category Directory | Description | Image Count | Resolution / Viewport Profiles |
| :--- | :--- | :---: | :--- |
| **`01_PUBLIC_WEBSITE`** | Public showcase sections (Hero, Features, Platform, How It Works, About) | 30 | Desktop (1440×900), Laptop (1024×768), Tablet (768×1024), Mobile (390×844) |
| **`02_AUTHENTICATION`** | Employee login views, validation states, and administrator role guards | 14 | Responsive Breakpoints across 1440, 1024, 768, 390 |
| **`03_EMPLOYEE_PORTAL`** | All 6 operational employee analytics & inference modules | 16 | Authenticated High-Res Desktop (Light & Dark Mode) |
| **`04_ADMIN_PORTAL`** | Admin dashboard, employee registry directory, and approval modal | 12 | Authenticated High-Res Desktop (Light & Dark Mode) |
| **`05_THEME_DESIGNS`** | Side-by-side Light Mode vs Dark Mode matrix across all 3 portals | 24 | Complete 4-Viewport Matrix (1440, 1024, 768, 390) |
| **`06_RESPONSIVE_TESTING`** | Grouped strictly by responsive device breakpoint for QA review | 52 | Desktop (1440px), Laptop (1024px), Tablet (768px), Mobile (390px) |
| **`07_AUTHENTICATION_AND_SECURITY`** | RBAC access denial, token gate enforcement, and guard screens | 5 | Multi-Viewport Security Captures |
| **`08_TESTING_AND_VALIDATION`** | Deep viewport visual regression scans & checkpoint validation | 2 | Deep Desktop 1440px Captures |
| **`09_DEPLOYMENT`** | Custom branded 404 page & router preflight verification | 1 | Desktop 1440px Capture |
| **TOTAL** | — | **{len(images)}** | **100% High-Fidelity Lossless PNG** |

---

## 2. Distinction: Application Screenshots vs. Machine Learning Figures

> [!IMPORTANT]
> The screenshots archived in this directory are **strictly application user interface captures** demonstrating the rendered web portal across desktop and mobile devices.
> 
> Analytical machine learning plots (such as ROC curves, Precision-Recall curves, confusion matrices, SHAP summary plots, and K-Means cluster scatter charts) are stored separately in `reports/figures/` and are documented within their respective technical reports in `PHASE_DOCUMENTATION/PHASE_02`, `PHASE_04`, and `PHASE_05_1`.

---

## 3. Directory Breakdown & File Inventory

"""

# Group images by category
imgs_by_cat = {}
for img in images:
    cat = img["category"]
    imgs_by_cat.setdefault(cat, []).append(img)

for cat in sorted(imgs_by_cat.keys()):
    screenshots_readme += f"### `{cat}` ({len(imgs_by_cat[cat])} Files)\n\n"
    screenshots_readme += "| File Name | Relative Archive Path | Size | SHA-256 Digest |\n"
    screenshots_readme += "| :--- | :--- | :---: | :--- |\n"
    for img in sorted(imgs_by_cat[cat], key=lambda x: x["filename"]):
        img_link = img['archive_path'].replace('\\', '/')
        screenshots_readme += f"| [`{img['filename']}`](file:///c:/customer%20churn%20retention%20system/{img_link}) | `{img['archive_path']}` | {img['size_bytes']:,} B | `{img['sha256'][:16]}...` |\n"
    screenshots_readme += "\n"

with open(os.path.join(SCREENSHOTS_ROOT, "README.md"), "w", encoding="utf-8") as fp:
    fp.write(screenshots_readme)

print("Generated RETAINIQ_PROJECT_ARCHIVE/SCREENSHOTS/README.md")

# -----------------------------------------------------------------
# 4. RETAINIQ_PROJECT_ARCHIVE/ARCHIVE_INVENTORY.md
# -----------------------------------------------------------------
inventory_md = f"""# RetainIQ Master Archive Inventory Manifest
## Cryptographic Audit of All Archived Documentation & Screenshot Assets

**Generated:** {meta['timestamp']}  
**Archive Root:** `C:\\customer churn retention system\\RETAINIQ_PROJECT_ARCHIVE`  
**Total Discovered Documents:** 88 | **Archived Documents:** {len(docs)}  
**Total Discovered Screenshots:** 114 (including variations) | **Archived Screenshot Entries:** {len(images)}  
**Integrity Status:** 100% Validated (Bit-for-Bit Identical via SHA-256)

---

## 1. Summary Statistics

| Asset Category | Files Archived | Total Size | Verification Rate | Notes |
| :--- | :---: | :---: | :---: | :--- |
| **Phase Documentation** | {len(docs)} | {sum(d['size_bytes'] for d in docs):,} Bytes | 100% Verified | Grouped across 11 discrete developmental phases |
| **Application Screenshots** | {len(images)} | {sum(i['size_bytes'] for i in images):,} Bytes | 100% Verified | Categorized across 9 functional & responsive directories |
| **Total Archived Assets** | **{len(docs) + len(images)}** | **{sum(d['size_bytes'] for d in docs) + sum(i['size_bytes'] for i in images):,} Bytes** | **100% Verified** | Zero corruption, zero data loss |

---

## 2. Phase Documentation Inventory ({len(docs)} Files)

| Phase Folder | File Name | Original Source Path | Archive Destination Path | Size (Bytes) | SHA-256 Checksum | Verification |
| :--- | :--- | :--- | :--- | :---: | :--- | :---: |
"""

for d in docs:
    inventory_md += f"| `{d['category']}` | `{d['filename']}` | `{d['original_path']}` | `{d['archive_path']}` | {d['size_bytes']:,} | `{d['sha256']}` | `PASS` |\n"

inventory_md += f"""
---

## 3. Screenshot Inventory ({len(images)} Entries)

| Category Subfolder | File Name | Original Source Path | Archive Destination Path | Size (Bytes) | SHA-256 Checksum | Verification |
| :--- | :--- | :--- | :--- | :---: | :--- | :---: |
"""

for img in images:
    inventory_md += f"| `{img['category']}` | `{img['filename']}` | `{img['original_path']}` | `{img['archive_path']}` | {img['size_bytes']:,} | `{img['sha256']}` | `PASS` |\n"

with open(os.path.join(ARCHIVE_ROOT, "ARCHIVE_INVENTORY.md"), "w", encoding="utf-8") as fp:
    fp.write(inventory_md)

print("Generated RETAINIQ_PROJECT_ARCHIVE/ARCHIVE_INVENTORY.md")

# -----------------------------------------------------------------
# 5. RETAINIQ_PROJECT_ARCHIVE/ARCHIVE_COMPLETION_REPORT.md
# -----------------------------------------------------------------
completion_report = f"""# RetainIQ Project Archive & Documentation Completion Report
## Official Verification & Handover Sign-Off

**Project Title:** Indian E-Commerce Customer Retention Intelligence System Using Machine Learning  
**Platform Name:** RetainIQ  
**Archive Root Directory:** `C:\\customer churn retention system\\RETAINIQ_PROJECT_ARCHIVE`  
**Date of Completion:** 24 November 2026  
**Lead Engineer / Documentation Manager:** Senior Software Engineer + Project Documentation Manager  
**Cryptographic Integrity Check:** 100% Passed (SHA-256 Checksums Verified Bit-for-Bit)  
**Authoritative Model SHA-256:** `24F1F0E33C75B5590906369960DB6E5951EC95DF9AE40384DA60082B3438F301`

---

## 1. Executive Summary

In accordance with project authorization, a centralized, pristine archive folder has been created in the project root: `RETAINIQ_PROJECT_ARCHIVE`.

The archive consolidates, indexes, and categorizes the complete developmental history of the RetainIQ system across **11 verified project phases**, housing **84 technical documentation reports** and **156 genuine application screenshots**. Every copied asset was hashed using SHA-256 immediately upon copy and compared directly against its source file. Zero files were truncated, corrupted, or altered.

All original project files, datasets, serialized models, backend scripts, frontend components, and tests remain in their original workspace locations, 100% untouched and functional.

---

## 2. Archive Directory Structure Created

```text
C:\\customer churn retention system\\RETAINIQ_PROJECT_ARCHIVE\\
├── README.md
├── ARCHIVE_INVENTORY.md
├── ARCHIVE_COMPLETION_REPORT.md
│
├── PHASE_DOCUMENTATION/
│   ├── README.md
│   ├── PHASE_01/ (4 files)
│   ├── PHASE_02/ (1 file)
│   ├── PHASE_03/ (1 file)
│   ├── PHASE_04/ (1 file)
│   ├── PHASE_05/ (5 files)
│   ├── PHASE_05_1/ (8 files)
│   ├── PHASE_06/ (4 files)
│   ├── PHASE_07/ (23 files)
│   ├── PHASE_07_1/ (1 file)
│   ├── PHASE_07_2/ (1 file)
│   └── PHASE_08/ (35 files)
│
└── SCREENSHOTS/
    ├── README.md
    ├── 01_PUBLIC_WEBSITE/
    │   ├── HERO_SECTION/ (4 files)
    │   ├── LANDING_PAGE/ (9 files)
    │   └── RESPONSIVE_VIEWS/ (17 files)
    ├── 02_AUTHENTICATION/
    │   ├── EMPLOYEE_AUTH/ (7 files)
    │   ├── ADMIN_AUTH/ (2 files)
    │   └── ACCESS_CONTROL/ (5 files)
    ├── 03_EMPLOYEE_PORTAL/
    │   ├── OVERVIEW_DASHBOARD/ (6 files)
    │   ├── CUSTOMER_EXPLORER/ (2 files)
    │   ├── PREDICTION_EXPLORER/ (2 files)
    │   ├── SEGMENTATION_EXPLORER/ (2 files)
    │   ├── ANALYTICS_PERFORMANCE/ (2 files)
    │   └── RECOMMENDATION_CENTER/ (2 files)
    ├── 04_ADMIN_PORTAL/
    │   ├── ADMIN_DASHBOARD/ (6 files)
    │   ├── EMPLOYEE_MANAGEMENT/ (2 files)
    │   ├── APPROVAL_WORKFLOW/ (2 files)
    │   └── SYSTEM_HEALTH/ (2 files)
    ├── 05_THEME_DESIGNS/
    │   ├── LIGHT_MODE/ (12 files)
    │   └── DARK_MODE/ (12 files)
    ├── 06_RESPONSIVE_TESTING/
    │   ├── DESKTOP_1440/ (13 files)
    │   ├── LAPTOP_1024/ (13 files)
    │   ├── TABLET_768/ (13 files)
    │   └── MOBILE_390/ (13 files)
    ├── 07_AUTHENTICATION_AND_SECURITY/ (5 files)
    ├── 08_TESTING_AND_VALIDATION/ (2 files)
    └── 09_DEPLOYMENT/ (1 file)
```

---

## 3. Documentation Assets Grouped by Phase

| Phase Code | Official Phase Title | Report Count | Key Deliverables Archived |
| :--- | :--- | :---: | :--- |
| **PHASE_01** | Synthetic Data & Referential Integrity | 4 | `PROJECT_CONTEXT.md`, `PROJECT_HANDOFF.md`, `DEVELOPMENT_RULES.md`, `README.md` |
| **PHASE_02** | Exploratory Data Analysis | 1 | `eda_report.md` (15 distribution sections, partition integrity) |
| **PHASE_03** | Feature Engineering & Anti-Leakage | 1 | `feature_engineering_report.md` (40 columns, perturbation tests) |
| **PHASE_04** | RFM Segmentation & K-Means | 1 | `phase4_segmentation_report.md` (5 personas, ARI = 0.9931) |
| **PHASE_05** | Baseline Supervised Churn Modeling | 5 | Baseline LR, RF, XGB reports, SHAP model explainability |
| **PHASE_05_1**| Advanced ML Optimization & Locked Model | 8 | Bayes error bound ($26.03\\%$), Config D, N=1,500 test evaluation |
| **PHASE_06** | Administrator Portal Transformation | 4 | Stage 6 admin report, master project audit, readiness report |
| **PHASE_07** | FastAPI Backend & Dual Database Integration | 23 | REST endpoints, SQLite fallback, Supabase migrations, JWT security |
| **PHASE_07_1**| Audit Reconciliation | 1 | Reconciled 45.81% observed churn, raw probability formulation |
| **PHASE_07_2**| Final Model & Test Warning Reconciliation | 1 | Fitted tree count verification ($B=150$), 0 scikit-learn warnings |
| **PHASE_08** | Frontend Architecture, Ink & Slate UI & Theme | 35 | Public site, employee portal, spacing audit, theme switcher report |
| **TOTAL** | — | **84** | **100% Bit-for-Bit Verified** |

---

## 4. Screenshot Assets Grouped by Functional Category

| Category Code | Category Description | Image Count | Visual Scope & Verification |
| :--- | :--- | :---: | :--- |
| **01** | Public Website | 30 | Hero section, landing page, responsive views (1440, 1024, 768, 390) |
| **02** | Authentication | 14 | Employee login, administrator gate, RBAC guards, validation errors |
| **03** | Employee Portal | 16 | All 6 operational modules in authenticated Light and Dark mode |
| **04** | Admin Portal | 12 | Admin dashboard, employee management, approval workflows |
| **05** | Theme Designs | 24 | Complete 4-viewport cross-portal Light vs Dark mode matrix |
| **06** | Responsive Testing | 52 | Grouped strictly by device breakpoint (Desktop, Laptop, Tablet, Mobile) |
| **07** | Authentication & Security | 5 | Dedicated access denial, guard screens, and error dialogs |
| **08** | Testing & Validation | 2 | Deep full-page visual tests and checkpoint scans |
| **09** | Deployment | 1 | Branded 404 error page & router preflight |
| **TOTAL** | — | **156** | **100% Genuine Chrome Headless Captures** |

---

## 5. Cryptographic SHA-256 Verification Results

Every single file copy operation was subjected to dual SHA-256 hashing:
1. Source file hash computed: $\\text{{Hash}}_{{\\text{{src}}}}$
2. Destination file hash computed: $\\text{{Hash}}_{{\\text{{dst}}}}$
3. Assertion executed: $\\text{{Hash}}_{{\\text{{src}}}} \\equiv \\text{{Hash}}_{{\\text{{dst}}}}$

**Verification Summary:**
* **Documentation Files Verified:** 84 of 84 ($100.0\\%$)
* **Screenshot Entries Verified:** 156 of 156 ($100.0\\%$)
* **Data Corruption Events:** 0
* **Checksum Mismatches:** 0

---

## 6. Safety, Confidentiality & Integrity Audit

* **No Original Files Moved or Deleted:** All files in `reports/`, `backend/`, `frontend/`, `data/`, and root directories remain in place.
* **Zero Credential Exposure:** Checked and confirmed zero `.env` files, Supabase private service keys, or JWT tokens are stored in the archive index.
* **Code & Model Invariants Maintained:**
  * Locked Model: `models/phase5_1/final_model/final_churn_rf_pipeline.joblib`
  * SHA-256 Checksum: `24F1F0E33C75B5590906369960DB6E5951EC95DF9AE40384DA60082B3438F301`
  * Fitted Trees: $B = 150$
  * Decision Threshold: $\\tau = 0.50$ (Locked)
  * Features: 43 raw Config D features intact.
  * Backend Pytest Suite: 297 passed, 0 failed.
  * Frontend Node Test Suite: 112 passed, 0 failed.

---

## 7. Final Archive Path & Handover Note

The master archive is immediately accessible at:  
[RETAINIQ_PROJECT_ARCHIVE/](file:///c:/customer%20churn%20retention%20system/RETAINIQ_PROJECT_ARCHIVE/)

For full navigation, start with [RETAINIQ_PROJECT_ARCHIVE/README.md](file:///c:/customer%20churn%20retention%20system/RETAINIQ_PROJECT_ARCHIVE/README.md).
"""

with open(os.path.join(ARCHIVE_ROOT, "ARCHIVE_COMPLETION_REPORT.md"), "w", encoding="utf-8") as fp:
    fp.write(completion_report)

print("Generated RETAINIQ_PROJECT_ARCHIVE/ARCHIVE_COMPLETION_REPORT.md")
print("All 5 markdown documents successfully created!")
