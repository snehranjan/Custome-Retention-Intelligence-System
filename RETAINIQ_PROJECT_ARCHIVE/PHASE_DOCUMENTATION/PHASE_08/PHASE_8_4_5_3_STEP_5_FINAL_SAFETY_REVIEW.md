# RETAINIQ — PHASE 8.4.5.3 (STEP 5)
# FINAL SQL SAFETY CORRECTIONS — PRE-EXECUTION APPROVAL GATE REPORT

**Project:** RetainIQ — Indian E-Commerce Customer Retention Intelligence System Using Machine Learning  
**Workspace Root:** `C:\customer churn retention system`  
**Target Migration:** `backend/database/migrations/008_create_employee_registry.sql`  
**Execution Mode:** Local Pre-Execution Hardening and Static/Automated Validation Suite  
**Date:** 23 November 2026  
**Auditor:** Senior Database Architect, PostgreSQL Security Engineer & Backend QA Lead  
**Status:** **APPROVED — READY FOR MANUAL REMOTE EXECUTION**

---

## 1. EXACT CORRECTIONS MADE IN STEP 5

In accordance with the pre-execution safety gate specifications, the migration script `backend/database/migrations/008_create_employee_registry.sql` was hardened with four critical catalog-level corrections:

### 1.1 RLS Policy NULL-Safe Validation (`IS DISTINCT FROM 'false'`)
- **Previous Vulnerability:** Relied on `!= 'false'`, which evaluates to `NULL` (falsy) if `qual` or `with_check` is `NULL`, potentially failing to catch missing or unconfigured policy expressions.
- **Remediation Implemented:**
  ```sql
  v_norm_qual := trim(both ' ()' from v_policy_qual);
  v_norm_with_check := trim(both ' ()' from v_policy_with_check);

  IF v_norm_qual IS DISTINCT FROM 'false' THEN
      RAISE EXCEPTION 'Schema integrity preflight failure: policy USING expression is "%" (expected explicit "false"). Aborting migration.', v_policy_qual;
  END IF;

  IF v_norm_with_check IS DISTINCT FROM 'false' THEN
      RAISE EXCEPTION 'Schema integrity preflight failure: policy WITH CHECK expression is "%" (expected explicit "false"). Aborting migration.', v_policy_with_check;
  END IF;

  IF v_policy_cmd IS DISTINCT FROM 'ALL' THEN
      RAISE EXCEPTION 'Schema integrity preflight failure: policy command is "%" (expected "ALL"). Aborting migration.', v_policy_cmd;
  END IF;

  IF v_policy_roles IS NULL OR NOT ('anon' = ANY(v_policy_roles) AND 'authenticated' = ANY(v_policy_roles)) THEN
      RAISE EXCEPTION 'Schema integrity preflight failure: policy roles do not target both anon and authenticated (found: %). Aborting migration.', coalesce(array_to_string(v_policy_roles, ', '), 'NULL');
  END IF;
  ```
- **Safety Guarantee:** Rejects NULL expressions, non-false expressions (e.g. `1=2`, `true`), missing roles, or commands other than `ALL`.

---

### 1.2 Exact Status CHECK Constraint Validation
- **Previous Weakness:** Extracted single-quoted literals, which could accept permissive compound expressions (e.g., `CHECK (status IN ('INVITED', ...) OR 1=1)` or `CHECK (status IN (...) OR status IS NULL)`).
- **Remediation Implemented:**
  1. Enforced single-column check constraint via `c.conkey`:
     ```sql
     AND c.conkey = ARRAY[(
         SELECT a.attnum FROM pg_attribute a 
         WHERE a.attrelid = t.oid AND a.attname = 'status'
     )]
     ```
  2. Banned permissive and unexpected boolean keywords (`OR`, `IS NULL`, `TRUE`, `FALSE`, `LIKE`, `ILIKE`, `NOT`):
     ```sql
     IF v_norm_check ~* '\b(OR|IS NULL|TRUE|FALSE|LIKE|ILIKE|NOT)\b' THEN
         RAISE EXCEPTION 'Schema integrity preflight failure: CHECK constraint contains unexpected logical operator or clause. Found: %. Aborting.', v_status_check_def;
     END IF;
     ```
  3. Enforced strict AST structural deparsed syntax:
     ```sql
     IF v_norm_check !~* '^CHECK \(\(\(?status\)?(?:::text)? = ANY \(ARRAY\[(.*?)\]\)\)\)$' THEN
         RAISE EXCEPTION 'Schema integrity preflight failure: CHECK constraint does not match exact structural pattern "CHECK ((status = ANY (ARRAY[...])))". Found: %. Aborting.', v_status_check_def;
     END IF;
     ```
  4. Enforced exact count and distinct sorted set of statuses:
     ```sql
     IF v_status_count != 5 OR v_found_statuses IS DISTINCT FROM ARRAY['APPROVED', 'INVITED', 'PENDING', 'REJECTED', 'SUSPENDED'] THEN
         RAISE EXCEPTION 'Schema integrity preflight failure: CHECK constraint on status does not enforce exactly the five permitted statuses. Found % statuses: %. Definition: %. Aborting.',
             v_status_count, coalesce(array_to_string(v_found_statuses, ', '), 'none'), v_status_check_def;
     END IF;
     ```
- **Safety Guarantee:** Rejects composite checks, permissive expressions, missing statuses, and unauthorized additional statuses.

---

### 1.3 Exact Single-Column Constraint Validation (Reject Composite Constraints)
- **Previous Weakness:** Checked `a.attnum = ANY(c.conkey)`. If a composite constraint existed (e.g. `PRIMARY KEY (employee_id, work_email)`), this check evaluated to `TRUE`.
- **Remediation Implemented:**
  ```sql
  -- 1d. Primary Key: strictly on single column employee_id
  SELECT EXISTS (
      SELECT 1 
      FROM pg_constraint c
      JOIN pg_class t ON t.oid = c.conrelid
      JOIN pg_namespace n ON n.oid = t.relnamespace
      WHERE n.nspname = 'public' 
        AND t.relname = 'employee_registry'
        AND c.contype = 'p' 
        AND c.conkey = ARRAY[(
            SELECT a.attnum FROM pg_attribute a 
            WHERE a.attrelid = t.oid AND a.attname = 'employee_id'
        )]
  ) INTO v_has_pk;

  -- 1e. UNIQUE constraint: strictly on single column work_email
  SELECT EXISTS (
      SELECT 1 
      FROM pg_constraint c
      JOIN pg_class t ON t.oid = c.conrelid
      JOIN pg_namespace n ON n.oid = t.relnamespace
      WHERE n.nspname = 'public' 
        AND t.relname = 'employee_registry'
        AND c.contype = 'u' 
        AND c.conkey = ARRAY[(
            SELECT a.attnum FROM pg_attribute a 
            WHERE a.attrelid = t.oid AND a.attname = 'work_email'
        )]
  ) INTO v_has_email_uq;

  -- 1e. UNIQUE constraint: strictly on single column supabase_user_id
  SELECT EXISTS (
      SELECT 1 
      FROM pg_constraint c
      JOIN pg_class t ON t.oid = c.conrelid
      JOIN pg_namespace n ON n.oid = t.relnamespace
      WHERE n.nspname = 'public' 
        AND t.relname = 'employee_registry'
        AND c.contype = 'u' 
        AND c.conkey = ARRAY[(
            SELECT a.attnum FROM pg_attribute a 
            WHERE a.attrelid = t.oid AND a.attname = 'supabase_user_id'
        )]
  ) INTO v_has_uuid_uq;
  ```
- **Safety Guarantee:** Any composite key or constraint that includes extra columns is strictly rejected.

---

### 1.4 Status Index Deep Inspection (`idx_employee_registry_status`)
- **Previous Weakness:** Merely verified existence of the index name in `pg_indexes`.
- **Remediation Implemented:**
  Inspected `pg_index`, `pg_class`, `pg_namespace`, and `pg_am`:
  ```sql
  SELECT 
      i.indisvalid,
      i.indisready,
      am.amname,
      i.indnatts,
      (SELECT a.attname FROM pg_attribute a WHERE a.attrelid = t.oid AND a.attnum = (i.indkey::smallint[])[1]),
      pg_get_indexdef(idx.oid)
  INTO 
      v_idx_is_valid,
      v_idx_is_ready,
      v_idx_am,
      v_idx_natts,
      v_idx_col,
      v_idx_def
  FROM pg_index i
  JOIN pg_class idx ON idx.oid = i.indexrelid
  JOIN pg_class t ON t.oid = i.indrelid
  JOIN pg_namespace n ON n.oid = t.relnamespace
  JOIN pg_am am ON am.oid = idx.relam
  WHERE n.nspname = 'public' 
    AND t.relname = 'employee_registry' 
    AND idx.relname = 'idx_employee_registry_status';
  ```
- **Safety Guarantee:** Verifies that the index:
  1. Belongs to `public.employee_registry`.
  2. Is marked valid (`indisvalid = true`) and ready (`indisready = true`).
  3. Uses the `btree` access method.
  4. Indexes exactly one single column (`indnatts = 1`), which is `status`.
  5. Rejects any invalid index build or misleading index definition.

---

## 2. CATALOG CHECKS AND THEIR LIMITATIONS

| Catalog Object / Function | What It Validates | Limitations & Boundary Considerations | Fail-Closed Handling |
| :--- | :--- | :--- | :--- |
| `pg_constraint.conkey` | Exact single-attribute matching for PK, UNIQUE, and CHECK constraints. | Does not validate table-level multi-column foreign keys (not applicable here). | Compares exact array equality `conkey = ARRAY[(attnum)]`. Any length mismatch fails closed. |
| `pg_get_constraintdef()` | Deparsed text representation of the check constraint. | Format depends on PostgreSQL version deparsing formatting of `ScalarArrayOpExpr`. | Normalized whitespace and checked AST regex pattern. Any unrecognized format triggers explicit abort. |
| `pg_policies` | `cmd`, `roles`, `qual`, `with_check`. | Textual representation of expressions. | Used `IS DISTINCT FROM 'false'` after stripping whitespace and parentheses. NULL or non-false expressions abort. |
| `pg_index` & `pg_am` | Index validity, readiness, access method, and indexed column. | Functional expression indexes (e.g. `lower(status)`) would have `attnum = 0`. | Validates `indnatts = 1` and matches column `status` directly. Non-btree or invalid indexes abort. |

---

## 3. AUTOMATED TEST & VERIFICATION RESULTS

### 3.1 Static SQL Validator (`scratch/verify_step5_sql.py`)
- **Total lines:** 506
- **Transaction wrapping:** `BEGIN;` as first non-comment statement, `COMMIT;` as last non-comment statement.
- **Parentheses balance:** 148 pairs (100% balanced).
- **Dollar-quote blocks:** 4 `DO $$` and 4 `END $$;` blocks (100% balanced).
- **Destructive statements:** 0 occurrences of `DROP`, `TRUNCATE`, `CASCADE`, or `ALTER TABLE ... DROP`.
- **Schema qualification:** All table and migration statements explicitly qualified with `public.`.
- **Preflight checks:** All Step 5 assertions passed.

### 3.2 Backend Test Suites
**Execution:** `cmd /c "backend\.venv\Scripts\python.exe -m pytest tests/test_employee_registration.py -v && backend\.venv\Scripts\python.exe -m pytest tests/test_customer_api.py -v"`

- `tests/test_employee_registration.py`: **19/19 Passed** in 5.65s (100% pass rate).
- `tests/test_customer_api.py`: **13/13 Passed** in 2.77s (100% pass rate).

### 3.3 Frontend Test Suites
**Execution:** `cmd /c "cd frontend && npm test"`
- **Results:** 15 test suites, 46/46 tests passed in 230ms (100% pass rate).

---

## 4. CONFIRMATION OF BOUNDARY & COMPLIANCE

- **Zero Remote Connections:** No commands connected to remote Supabase.
- **Zero Remote DDL:** No remote SQL or DDL execution took place.
- **Zero Credential Exposure:** No service-role keys, tokens, or passwords were logged or exposed.
- **Machine Learning Invariants Preserved:** Locked pipeline `final_churn_rf_pipeline.joblib` (SHA-256 `24F1F0E3...`), threshold $\tau=0.50$, 43 Config D features, and 5 customer personas remain completely untouched.
- **Phase 8.4.6 Gate:** Development strictly stopped awaiting explicit instruction.

---

## 5. FINAL SAFETY VERDICT

> **VERDICT: APPROVED — PRE-EXECUTION APPROVAL GATE PASSED**  
> The migration file `backend/database/migrations/008_create_employee_registry.sql` is catalog-hardened, composite-proof, NULL-safe, duplicate-free, and verified. It is safe for execution via the Supabase Dashboard SQL Editor.
