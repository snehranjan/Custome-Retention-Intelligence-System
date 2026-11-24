# PHASE 7.4 — CHECKPOINT 2 AUDIT REPORT: DATABASE SCHEMA & MIGRATION DESIGN
**Project:** Indian E-Commerce Customer Retention Intelligence System Using Machine Learning  
**Workspace Root:** `C:\customer churn retention system`  
**Host Platform:** Windows 11 (64-bit)  
**Python Environment:** `backend\.venv\Scripts\python.exe`  
**Milestone:** Phase 7.4 (Database Integration & SQLite Fallback) — Checkpoint 2 Complete  
**Date:** 21 November 2026  
**Auditor / Engineer:** Senior Backend Engineer, Supabase Database Architect, PostgreSQL Engineer & Independent QA Auditor  

---

## 1. EXECUTIVE SUMMARY & VERIFICATION VERDICT

In accordance with Phase 7.4 Checkpoint 2 objectives, a dual-storage relational schema and migration engine have been designed, implemented, and rigorously tested. The architecture provides full parity between **Supabase PostgreSQL** (for production cloud deployment) and **local persistent SQLite** (for autonomous, offline, zero-network fallback).

All 13 automated schema and migration tests executed successfully with **zero errors and zero regressions**.

### Checkpoint 2 Status Matrix
| Component / Verification Gate | Status | Evidence / Test Identifier |
| :--- | :--- | :--- |
| **PostgreSQL Migration DDLs (Supabase)** | **COMPLETE (7/7)** | `backend/database/migrations/001-007` |
| **SQLite Schema & Migration Engine** | **COMPLETE** | `backend/database/sqlite_schema.sql`, `sqlite_migrator.py` |
| **Git Exclusion of SQLite Files** | **COMPLETE** | `.gitignore` entries `*.db`, `*.sqlite`, `data/*.db` |
| **Schema Validation Test Suite** | **PASSED (13/13)** | `tests/test_database_schema.py` |
| **Regression Test Suite (API & ML)** | **PASSED (32/32)** | `tests/test_api_foundation.py`, `tests/test_ml_integration.py` |
| **All-Phase Master Audit Suite** | **PASSED (10/10)** | `tests/test_all_phases.py` |
| **Locked ML Model Invariant Hashes** | **VERIFIED (100%)** | SHA-256 match on all 4 core artifacts |

---

## 2. DUAL-STORAGE ARCHITECTURE & SCHEMA SPECIFICATION

The schema is normalized to 3NF while accommodating high-throughput batch inference and historical prediction auditing for Indian e-commerce retention intelligence.

### 2.1 Table Schemas & Relational Contracts

#### 1. `schema_migrations`
* **Purpose:** Idempotent migration version control.
* **Columns:**
  * `version` (INT, PK): Sequential migration version number.
  * `migration_name` (VARCHAR(255), NOT NULL): Migration filename.
  * `applied_at` (TIMESTAMP WITH TIME ZONE, NOT NULL): UTC execution timestamp.
  * `checksum` (VARCHAR(64), NULL): SHA-256 script content checksum.

#### 2. `customers`
* **Purpose:** Canonical customer profiles imported from `data/raw/customers.csv` (7,000 synthetic customers).
* **Key Columns & Types:**
  * `customer_id` (VARCHAR(64), PK): Preserves string IDs (`IND_CUST_10001` to `IND_CUST_17000`).
  * `signup_date` (DATE / TEXT, NOT NULL): Customer registration date.
  * `city` (VARCHAR(100), NULLABLE): Accommodates the known 46 EDA missing cities.
  * `state` (VARCHAR(100), NULLABLE): Accommodates the known 46 EDA missing states.
  * Demographic, transactional, browsing, RFM, and support metrics (40 numeric features).
  * `churn` (INTEGER, NOT NULL): Ground truth historical churn indicator (`CHECK (churn IN (0, 1))`).
  * `created_at`, `updated_at` (TIMESTAMPTZ, NOT NULL).

#### 3. `customer_predictions`
* **Purpose:** Audit-compliant logging of ML inference from the locked Random Forest pipeline.
* **Key Columns & Constraints:**
  * `prediction_id` (VARCHAR(64), PK): Unique UUID string.
  * `customer_id` (VARCHAR(64), NOT NULL, FK `customers(customer_id)` ON DELETE CASCADE).
  * `churn_probability` (NUMERIC(6,5) / REAL, NOT NULL): $P(\text{churn})$, `CHECK (churn_probability >= 0.0 AND churn_probability <= 1.0)`.
  * `retained_probability` (NUMERIC(6,5) / REAL, NOT NULL): $P(\text{retained})$, `CHECK (retained_probability >= 0.0 AND retained_probability <= 1.0)`.
  * `probability_sum_check`: `CHECK (abs(churn_probability + retained_probability - 1.0) <= 0.001)`.
  * `predicted_churn` (INTEGER, NOT NULL): Binary decision `CHECK (predicted_churn IN (0, 1))`.
  * `decision_threshold` (NUMERIC(4,3) / REAL, NOT NULL): Fixed at 0.50 (`CHECK (decision_threshold = 0.50)`).
  * `risk_tier` (VARCHAR(20), NOT NULL): `CHECK (risk_tier IN ('CRITICAL', 'HIGH', 'MEDIUM', 'LOW', 'MINIMAL'))`.
  * `model_name` (VARCHAR(100), NOT NULL): `'final_churn_rf_pipeline'`.
  * `model_version` (VARCHAR(50), NOT NULL): `'phase5_1'`.
  * `model_checksum` (VARCHAR(64), NOT NULL): Enforces SHA-256 `24F1F0E33C75B5590906369960DB6E5951EC95DF9AE40384DA60082B3438F301`.
  * `top_risk_factors` (TEXT / JSON, NULLABLE): Ranked risk feature contributions.
  * `created_at` (TIMESTAMPTZ, NOT NULL).

#### 4. `customer_segments`
* **Purpose:** RFM behavioral clustering from the locked $K=5$ KMeans model.
* **Key Columns & Constraints:**
  * `segment_id` (VARCHAR(64), PK): Unique UUID string.
  * `customer_id` (VARCHAR(64), NOT NULL, FK `customers(customer_id)` ON DELETE CASCADE).
  * `cluster_id` (INTEGER, NOT NULL): `CHECK (cluster_id IN (0, 1, 2, 3, 4))`.
  * `persona_name` (VARCHAR(100), NOT NULL): Enforces exact 5 official persona strings:
    * `'Champions & High-Value Loyalists'`
    * `'At-Risk / Lapsed Low-Value Customers'`
    * `'Zero Delivered-Purchase Customers'`
    * `'Steady Core Repeaters'`
    * `'Recent Low-Ticket / New Promising Customers'`
  * `recency_score`, `frequency_score`, `monetary_score` (NUMERIC(10,2) / REAL, NOT NULL).
  * `is_current` (BOOLEAN / INTEGER, NOT NULL DEFAULT TRUE/1).
  * **Partial Unique Index:** `uq_current_customer_segment` on `(customer_id) WHERE is_current = TRUE / 1`. Guarantees exactly one active segment per customer while preserving historical segment transitions.

#### 5. `retention_recommendations`
* **Purpose:** Actionable, prioritized business retention interventions.
* **Key Columns & Constraints:**
  * `recommendation_id` (VARCHAR(64), PK): Unique UUID string.
  * `customer_id` (VARCHAR(64), NOT NULL, FK `customers(customer_id)` ON DELETE CASCADE).
  * `prediction_id` (VARCHAR(64), NULLABLE, FK `customer_predictions(prediction_id)` ON DELETE SET NULL).
  * `strategy_category` (VARCHAR(100), NOT NULL).
  * `title` (VARCHAR(255), NOT NULL), `description` (TEXT, NOT NULL), `suggested_action` (TEXT, NOT NULL).
  * `priority` (VARCHAR(20), NOT NULL): `CHECK (priority IN ('HIGH', 'MEDIUM', 'LOW'))`.
  * `recommendation_status` (VARCHAR(30), NOT NULL): `CHECK (recommendation_status IN ('PENDING', 'IN_PROGRESS', 'APPLIED', 'DISMISSED', 'EXPIRED'))`.
  * `estimated_impact` (VARCHAR(255), NULLABLE), `coupon_code` (VARCHAR(50), NULLABLE).
  * `created_at`, `updated_at` (TIMESTAMPTZ, NOT NULL).

---

## 3. FILES IMPLEMENTED & MODIFIED

1. [`.gitignore`](file:///c:/customer%20churn%20retention%20system/.gitignore):
   * Appended exclusions for SQLite databases and lock journals: `*.db`, `*.db-journal`, `*.sqlite`, `*.sqlite3`, `data/*.db`, `data/local_database.db`.
2. [`backend/database/__init__.py`](file:///c:/customer%20churn%20retention%20system/backend/database/__init__.py):
   * Initialized `backend.database` module.
3. **PostgreSQL Migration Scripts (`backend/database/migrations/`):**
   * [`001_create_schema_migrations.sql`](file:///c:/customer%20churn%20retention%20system/backend/database/migrations/001_create_schema_migrations.sql): Version tracking table DDL.
   * [`002_create_customers.sql`](file:///c:/customer%20churn%20retention%20system/backend/database/migrations/002_create_customers.sql): Customer profiles table DDL.
   * [`003_create_customer_predictions.sql`](file:///c:/customer%20churn%20retention%20system/backend/database/migrations/003_create_customer_predictions.sql): Prediction history table DDL.
   * [`004_create_customer_segments.sql`](file:///c:/customer%20churn%20retention%20system/backend/database/migrations/004_create_customer_segments.sql): Segmentation and persona table DDL.
   * [`005_create_retention_recommendations.sql`](file:///c:/customer%20churn%20retention%20system/backend/database/migrations/005_create_retention_recommendations.sql): Retention recommendations table DDL.
   * [`006_create_indexes_and_constraints.sql`](file:///c:/customer%20churn%20retention%20system/backend/database/migrations/006_create_indexes_and_constraints.sql): Secondary B-Tree and partial unique indexes.
   * [`007_enable_rls_and_policies.sql`](file:///c:/customer%20churn%20retention%20system/backend/database/migrations/007_enable_rls_and_policies.sql): Enables RLS and configures explicit unauthenticated deny policies.
4. [`backend/database/sqlite_schema.sql`](file:///c:/customer%20churn%20retention%20system/backend/database/sqlite_schema.sql):
   * Monolithic, SQLite-compatible DDL enabling foreign keys, enforcing check constraints, and configuring indexes.
5. [`backend/database/sqlite_migrator.py`](file:///c:/customer%20churn%20retention%20system/backend/database/sqlite_migrator.py):
   * Migration utility class `SQLiteMigrator` managing versioned, transactional, and idempotent SQLite schema creation and status inspection.
6. [`tests/test_database_schema.py`](file:///c:/customer%20churn%20retention%20system/tests/test_database_schema.py):
   * Comprehensive 13-case test suite covering idempotency, table presence, primary keys, cascading foreign keys, nullable foreign keys, check constraints, partial unique indexes, and nullable columns.

---

## 4. SUPABASE & POSTGRESQL READINESS

### 4.1 PostgREST & Supabase Connection Parameters
* **Supabase Project URL:** `https://hyngxdkuanugcvqhkaas.supabase.co`
* **Publishable / Anon Key:** `sb_publishable_NaJSKZOjztFxbMD_SOY0xA_aqwuEPf1`
* **JWKS Endpoint:** `https://hyngxdkuanugcvqhkaas.supabase.co/auth/v1/.well-known/jwks.json`
* **Secret Key Status:** Not populated in local `backend/.env` (safe fallback to SQLite mode is active).

### 4.2 Row-Level Security (RLS) Architecture
* **Table-Level Protection:** Enabled on all 4 core tables:
  ```sql
  ALTER TABLE customers ENABLE ROW LEVEL SECURITY;
  ALTER TABLE customer_predictions ENABLE ROW LEVEL SECURITY;
  ALTER TABLE customer_segments ENABLE ROW LEVEL SECURITY;
  ALTER TABLE retention_recommendations ENABLE ROW LEVEL SECURITY;
  ```
* **Explicit Public Deny Policy:** To guarantee that the `anon` publishable key cannot arbitrarily query, extract, modify, or delete customer retention data from client browsers, explicit deny policies are applied:
  ```sql
  CREATE POLICY "deny_anon_access_customers" ON customers FOR ALL TO anon USING (false);
  ```
* **Phase 7.5 Role Separation Note:** In accordance with project security invariants, full multi-tenant staff/employee RBAC (e.g., Marketing vs Ops) will be bound during Phase 7.5 (JWT Auth & Role-Based Access Control). At present, backend operations authenticate via Supabase `service_role` (which bypasses RLS) or run directly in local SQLite mode.

---

## 5. AUTOMATED TEST SUITE EXECUTION RESULTS

### 5.1 Database Schema Test Suite (`tests/test_database_schema.py`)
Executed via: `backend\.venv\Scripts\python.exe -m pytest tests/test_database_schema.py -v`

```text
tests/test_database_schema.py::test_migration_tracking_and_idempotency PASSED [  7%]
tests/test_database_schema.py::test_table_presence PASSED                [ 15%]
tests/test_database_schema.py::test_primary_keys PASSED                  [ 23%]
tests/test_database_schema.py::test_foreign_key_enforcement PASSED       [ 30%]
tests/test_database_schema.py::test_nullable_foreign_key_in_recommendations PASSED [ 38%]
tests/test_database_schema.py::test_duplicate_customer_id_rejected PASSED [ 46%]
tests/test_database_schema.py::test_partial_unique_index_active_segment PASSED [ 53%]
tests/test_database_schema.py::test_customer_churn_check_constraint PASSED [ 61%]
tests/test_database_schema.py::test_prediction_probability_bounds_and_sum PASSED [ 69%]
tests/test_database_schema.py::test_segment_cluster_and_persona_check_constraints PASSED [ 76%]
tests/test_database_schema.py::test_recommendation_priority_and_status_check PASSED [ 84%]
tests/test_database_schema.py::test_customers_nullable_city_state PASSED [ 92%]
tests/test_database_schema.py::test_performance_indexes_created PASSED   [100%]

============================= 13 passed in 3.21s ==============================
```

### 5.2 API Foundation & ML Integration Regression Suites
Executed via: `backend\.venv\Scripts\python.exe -m pytest tests/test_api_foundation.py tests/test_ml_integration.py -v`

```text
============================= 32 passed in 4.59s ==============================
```
* **Result:** All 12 FastAPI foundation tests and all 20 ML/Segmentation engine integration tests passed without regressions.

---

## 6. LOCKED MACHINE LEARNING ARTIFACT INVARIANCE

To confirm zero data corruption or artifact drift during Checkpoint 2 implementation, all SHA-256 checksums were verified against canonical hashes:

| Artifact | Canonical SHA-256 Hash | Checkpoint 2 Audit Hash | Status |
| :--- | :--- | :--- | :--- |
| **Final Random Forest Model** | `24F1F0E33C75B5590906369960DB6E5951EC95DF9AE40384DA60082B3438F301` | `24F1F0E33C75B5590906369960DB6E5951EC95DF9AE40384DA60082B3438F301` | **MATCH** |
| **Segmentation Scaler** | `892B9F3CDDA5427DD3965C76B95C1BC952661BAEA993FBBA94D5A3F56FB2EC4C` | `892B9F3CDDA5427DD3965C76B95C1BC952661BAEA993FBBA94D5A3F56FB2EC4C` | **MATCH** |
| **K-Means Segmentation Model** | `A018E41C8DC78BBDEC7C157B71ED66FEAC698336F787B39D84583FAE9CB931B3` | `A018E41C8DC78BBDEC7C157B71ED66FEAC698336F787B39D84583FAE9CB931B3` | **MATCH** |
| **Raw Customers Dataset** | `DF6219AA4E2BDDE8FFF419272B9F2C1DE0602473248619E90566BC7D498AB70E` | `DF6219AA4E2BDDE8FFF419272B9F2C1DE0602473248619E90566BC7D498AB70E` | **MATCH** |

---

## 7. KNOWN LIMITATIONS & OUTSTANDING ACTIONS

1. **Remote Supabase Direct Migration:**
   * Applying migrations directly to the remote Supabase PostgreSQL instance requires either:
     a) Running SQL migrations via Supabase SQL Editor web console; or
     b) Providing the `SUPABASE_SERVICE_ROLE_KEY` in `backend/.env`.
   * The system is currently configured for autonomous offline development (`STORAGE_MODE=sqlite`). Once the secret key is provided, the same migration scripts will execute against PostgREST/PostgreSQL.
2. **Phase 7.5 Auth Integration:**
   * Staff-specific and role-based policies (e.g. `auth.jwt() -> role = 'retention_manager'`) will be added during Phase 7.5.

---

## 8. CHECKPOINT 2 CONCLUSION & NEXT STEP

**Checkpoint 2 is 100% complete and validated.**

In strict accordance with the mandatory workflow rules:
* Checkpoint 2 is finished and fully audited.
* Implementation of **Checkpoint 3: SQLite Repository** will NOT proceed until explicit user confirmation is received.
