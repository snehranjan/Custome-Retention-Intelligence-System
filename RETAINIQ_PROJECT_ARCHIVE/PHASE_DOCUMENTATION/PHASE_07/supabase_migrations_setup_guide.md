# SUPABASE DATABASE SETUP & MIGRATION EXECUTION GUIDE
## Indian E-Commerce Customer Retention Intelligence System Using Machine Learning

**Project Workspace:** `C:\customer churn retention system`  
**Target Environment:** Supabase Cloud PostgreSQL  
**Project URL:** `https://hyngxdkuanugcvqhkaas.supabase.co`  
**Publishable Key:** `sb_publishable_NaJSKZOjztFxbMD_SOY0xA_aqwuEPf1`  
**Execution File:** `reports/phase7/supabase_migrations_execution.sql`  
**Verification File:** `reports/phase7/supabase_migrations_verification.sql`  

---

## 1. Overview & Safety Architecture

This guide walks you through applying migrations **001 through 007** directly to your remote Supabase project using the official Supabase Dashboard SQL Editor.

### Safety Invariants Built Into the Migration:
* **Strict Transaction:** Wrapped in `BEGIN ... COMMIT` to guarantee all-or-nothing execution.
* **Idempotent Statements:** All table creations use `CREATE TABLE IF NOT EXISTS`, and all index creations use `CREATE INDEX IF NOT EXISTS`.
* **Zero Destructive Operations:** Does not contain `DROP`, `TRUNCATE`, or destructive `ALTER` statements.
* **Zero Credential Exposure:** Contains zero passwords, API tokens, or secret keys.
* **Zero Anonymous Exposure:** Row Level Security (RLS) is enabled on all tables, and unauthenticated anonymous access is explicitly denied (`FOR ALL TO anon USING (false)`).

---

## 2. Step-by-Step Execution Instructions

### Step 1: Open the Supabase Dashboard
1. Open your web browser and navigate to:  
   [https://supabase.com/dashboard](https://supabase.com/dashboard)
2. Sign in to your account.

### Step 2: Select the Target Project
1. In the project list, select your project:
   * **Project Name:** Customer Retention Intelligence (or matching project)
   * **Project Reference ID:** `hyngxdkuanugcvqhkaas`
   * **Direct URL:** [https://supabase.com/dashboard/project/hyngxdkuanugcvqhkaas](https://supabase.com/dashboard/project/hyngxdkuanugcvqhkaas)

### Step 3: Open the SQL Editor
1. In the left navigation sidebar, click on the **SQL Editor** icon (represented by the `>_` terminal / database icon).
2. Click the **"+ New query"** button at the top of the SQL Editor to open a fresh SQL tab.

### Step 4: Load and Execute `supabase_migrations_execution.sql`
1. On your local machine, open the execution script:
   [reports/phase7/supabase_migrations_execution.sql](file:///c:/customer%20churn%20retention%20system/reports/phase7/supabase_migrations_execution.sql)
2. Select all text (`Ctrl + A`) and copy it (`Ctrl + C`).
3. Paste the entire SQL script into the Supabase SQL Editor.
4. Click the green **Run** button (or press `Ctrl + Enter` / `Cmd + Enter`).

### Step 5: Confirm Execution Success
1. Confirm that the execution panel at the bottom displays:
   ```text
   Success. No rows returned.
   ```
2. If any error appears, copy the error message and do not proceed to verification.

---

## 3. Verification Instructions

### Step 6: Load and Execute `supabase_migrations_verification.sql`
1. In the Supabase SQL Editor, click **"+ New query"** to open a second clean tab.
2. Open the local verification script:
   [reports/phase7/supabase_migrations_verification.sql](file:///c:/customer%20churn%20retention%20system/reports/phase7/supabase_migrations_verification.sql)
3. Select all text (`Ctrl + A`) and copy it (`Ctrl + C`).
4. Paste the script into the query editor and click **Run**.

### Step 7: Inspect Verification Outputs
Verify the following 8 query results returned by Supabase:

1. **Table Presence (Query 1):**  
   * Confirms `schema_migrations`, `customers`, `customer_predictions`, `customer_segments`, and `retention_recommendations` exist in `public`.
   * Result: `PASSED (All required tables present)`
2. **Migration Tracking (Query 2):**  
   * Displays 7 rows in `schema_migrations` (`001` through `007`).
3. **Column Specifications (Query 3):**  
   * Confirms `customer_id VARCHAR(50)`, `churn INTEGER`, `churn_probability NUMERIC(6,4)`, `cluster_id INTEGER`, etc.
4. **Primary & Foreign Keys (Query 4):**  
   * Confirms primary keys on all tables.
   * Confirms foreign keys to `customers(customer_id) ON DELETE CASCADE`.
   * Confirms nullable link `prediction_id REFERENCES customer_predictions(prediction_id) ON DELETE SET NULL`.
5. **Domain CHECK Constraints (Query 5):**  
   * `churn IN (0, 1)`
   * `churn_probability BETWEEN 0.0 AND 1.0`
   * `cluster_id IN (0, 1, 2, 3, 4)`
   * `segment_name IN ('Champions & High-Value Loyalists', ...)` (All 5 personas)
   * `priority IN ('HIGH', 'MEDIUM', 'LOW')`
6. **Performance & Partial Unique Indexes (Query 6):**  
   * Confirms `uq_current_customer_segment` partial index on `(customer_id) WHERE is_current = TRUE`.
   * Confirms lookup indexes on `churn`, `city, state`, `risk_tier`, etc.
7. **Row Level Security Activation (Query 7):**  
   * All 4 application tables show: `PASSED (RLS Enabled)`.
8. **Policy Safety Audit (Query 8):**  
   * All policies for role `anon` show: `PASSED (Anonymous access blocked)`.

---

## 4. Next Steps After Execution

Once you have executed both scripts in your Supabase Dashboard:

1. Let me know that the execution succeeded (or provide any error logs if an issue arose).
2. Once confirmed, I will run the local live connectivity probe test:
   ```powershell
   backend\.venv\Scripts\python.exe -m pytest tests/test_supabase_repository.py::test_safe_real_supabase_health_probe -v
   ```
3. With the remote schema active, the application will be ready for live remote customer synchronization.
