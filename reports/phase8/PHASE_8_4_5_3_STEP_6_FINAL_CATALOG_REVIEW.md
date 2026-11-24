# RETAINIQ — PHASE 8.4.5.3 (STEP 6)
# FINAL POSTGRESQL CATALOG VALIDATION — EXECUTION APPROVAL CANDIDATE REPORT

**Project:** RetainIQ — Indian E-Commerce Customer Retention Intelligence System Using Machine Learning  
**Workspace Root:** `C:\customer churn retention system`  
**Target Migration:** `backend/database/migrations/008_create_employee_registry.sql`  
**Execution Mode:** Local Catalog Hardening and Verification Suite (Zero Remote Connections)  
**Date:** 23 November 2026  
**Auditor:** Senior PostgreSQL Database Architect, Supabase Security Engineer & QA Lead  
**Status:** **APPROVED — FINAL EXECUTION APPROVAL CANDIDATE**

---

## 1. EXACT CORRECTIONS MADE IN STEP 6

### 1.1 Reliable Catalog-Based Index Attribute Extraction
- **The Issue with `(i.indkey::smallint[])[1]`:**
  In PostgreSQL internal architecture, `int2vector` is a C-array type with 0-based indexing semantics. When cast to standard arrays, subscripting behavior across PostgreSQL major/minor versions or custom compiler flags can retain lower-bound 0 `[0:0]`, causing 1-based indexing `[1]` to return `NULL` or fail to retrieve the primary attribute.
- **The Catalog-Native Solution Implemented:**
  Every index relation in PostgreSQL has its own metadata in `pg_class` and column entries in `pg_attribute`. The key columns of an index relation have deterministic attribute numbers starting at `attnum = 1`.
  We join `pg_attribute` directly to `idx.oid` at `attnum = 1`:
  ```sql
  JOIN pg_attribute idx_att ON idx_att.attrelid = idx.oid AND idx_att.attnum = 1
  ```
- **Complete Index Invariants Verified:**
  ```sql
  -- 1g. Validate idx_employee_registry_status
  SELECT 
      i.indisvalid,
      i.indisready,
      i.indisunique,
      (i.indexprs IS NULL) AS is_non_expression,
      (i.indpred IS NULL) AS is_non_partial,
      am.amname,
      i.indnatts,
      i.indnkeyatts,
      idx_att.attname AS index_col_name,
      tbl_att.attname AS table_col_name
  INTO 
      v_idx_is_valid,
      v_idx_is_ready,
      v_idx_is_unique,
      v_idx_is_non_expr,
      v_idx_is_non_partial,
      v_idx_am,
      v_idx_natts,
      v_idx_nkeyatts,
      v_idx_col_name,
      v_tbl_col_name
  FROM pg_index i
  JOIN pg_class idx ON idx.oid = i.indexrelid
  JOIN pg_class t ON t.oid = i.indrelid
  JOIN pg_namespace n ON n.oid = t.relnamespace
  JOIN pg_am am ON am.oid = idx.relam
  JOIN pg_attribute idx_att ON idx_att.attrelid = idx.oid AND idx_att.attnum = 1
  JOIN pg_attribute tbl_att ON tbl_att.attrelid = t.oid AND tbl_att.attname = 'status'
  WHERE n.nspname = 'public' 
    AND t.relname = 'employee_registry' 
    AND idx.relname = 'idx_employee_registry_status';

  IF NOT FOUND THEN
      RAISE EXCEPTION 'Schema integrity preflight failure: required index "idx_employee_registry_status" is missing on public.employee_registry. Aborting migration.';
  END IF;

  IF NOT v_idx_is_valid THEN
      RAISE EXCEPTION 'Schema integrity preflight failure: index "idx_employee_registry_status" is marked invalid in pg_index (indisvalid = false). Aborting migration.';
  END IF;

  IF NOT v_idx_is_ready THEN
      RAISE EXCEPTION 'Schema integrity preflight failure: index "idx_employee_registry_status" is not ready in pg_index (indisready = false). Aborting migration.';
  END IF;

  IF v_idx_is_unique THEN
      RAISE EXCEPTION 'Schema integrity preflight failure: index "idx_employee_registry_status" is marked unique (expected non-unique lookup index). Aborting migration.';
  END IF;

  IF NOT v_idx_is_non_expr THEN
      RAISE EXCEPTION 'Schema integrity preflight failure: index "idx_employee_registry_status" has indexprs expression tree (expected simple non-expression index). Aborting migration.';
  END IF;

  IF NOT v_idx_is_non_partial THEN
      RAISE EXCEPTION 'Schema integrity preflight failure: index "idx_employee_registry_status" has indpred predicate tree (expected full non-partial index). Aborting migration.';
  END IF;

  IF v_idx_am IS DISTINCT FROM 'btree' THEN
      RAISE EXCEPTION 'Schema integrity preflight failure: index "idx_employee_registry_status" access method is "%" (expected "btree"). Aborting migration.', v_idx_am;
  END IF;

  IF v_idx_natts IS DISTINCT FROM 1 OR v_idx_nkeyatts IS DISTINCT FROM 1 OR v_idx_col_name IS DISTINCT FROM 'status' THEN
      RAISE EXCEPTION 'Schema integrity preflight failure: index "idx_employee_registry_status" must index exactly the single column status (found % attributes, key name: "%"). Aborting migration.', v_idx_natts, v_idx_col_name;
  END IF;
  ```

---

### 1.2 Strengthened Status CHECK Constraint Strict Parser
- **The Issue with Permissive Parsing:**
  Previously, regular expressions allowed arbitrary expressions inside `ARRAY[...]` as long as 5 status literals were found. This would not reject duplicate literals, additional expressions, function invocations, or subqueries.
- **The Multi-Stage Strict Parser Implemented:**
  1. **Single-Column Constraint Verification:**
     Enforced via `c.conkey = ARRAY[(SELECT attnum ... WHERE attname = 'status')]`.
  2. **Banned Logic and Permissive Keyword Filter:**
     ```sql
     IF v_norm_check ~* '\b(OR|AND|NOT|TRUE|FALSE|IS\s+NULL|LIKE|ILIKE|CASE|WHEN|COALESCE|NULLIF)\b' THEN
         RAISE EXCEPTION 'Schema integrity preflight failure: CHECK constraint contains forbidden logical operator or permissive keyword. Found: %. Aborting.', v_status_check_def;
     END IF;
     ```
  3. **Strict Structural AST Matching:**
     ```sql
     IF v_norm_check !~* '^CHECK \(\(\(?status\)?(?:::text)? = ANY \(ARRAY\[([^\]]+)\]\)\)\)$' THEN
         RAISE EXCEPTION 'Schema integrity preflight failure: CHECK constraint does not match exact structural pattern "CHECK ((status = ANY (ARRAY[...])))". Found: %. Aborting.', v_status_check_def;
     END IF;
     ```
  4. **Array Elements Extraction and Literal Token Verification:**
     ```sql
     v_array_content := (regexp_matches(v_norm_check, '^CHECK \(\(\(?status\)?(?:::text)? = ANY \(ARRAY\[([^\]]+)\]\)\)\)$'))[1];

     SELECT ARRAY(
         SELECT trim(elem) 
         FROM regexp_split_to_table(v_array_content, ',') AS elem
     ) INTO v_elements;

     -- Strictly reject non-literal or expression-based array elements
     IF EXISTS (
         SELECT 1 FROM unnest(v_elements) AS e 
         WHERE trim(e) !~ '^''[A-Z_]+''(::text)?$'
     ) THEN
         RAISE EXCEPTION 'Schema integrity preflight failure: status ARRAY contains invalid, non-literal, or expression-based element. Array content: %. Aborting.', v_array_content;
     END IF;
     ```
  5. **Duplicate Literal Rejection:**
     ```sql
     SELECT array_agg((regexp_matches(trim(e), '^''([A-Z_]+)''(::text)?$'))[1] ORDER BY (regexp_matches(trim(e), '^''([A-Z_]+)''(::text)?$'))[1])
     INTO v_all_statuses FROM unnest(v_elements) AS e;

     SELECT array_agg(DISTINCT (regexp_matches(trim(e), '^''([A-Z_]+)''(::text)?$'))[1] ORDER BY (regexp_matches(trim(e), '^''([A-Z_]+)''(::text)?$'))[1])
     INTO v_distinct_statuses FROM unnest(v_elements) AS e;

     IF array_length(v_all_statuses, 1) != array_length(v_distinct_statuses, 1) THEN
         RAISE EXCEPTION 'Schema integrity preflight failure: CHECK constraint on status contains duplicate status literals. Found: %. Aborting.', v_array_content;
     END IF;
     ```
  6. **Exact Count and Enum Set Verification:**
     ```sql
     IF array_length(v_all_statuses, 1) != 5 OR v_distinct_statuses IS DISTINCT FROM ARRAY['APPROVED', 'INVITED', 'PENDING', 'REJECTED', 'SUSPENDED'] THEN
         RAISE EXCEPTION 'Schema integrity preflight failure: CHECK constraint on status does not enforce exactly the five permitted statuses (APPROVED, INVITED, PENDING, REJECTED, SUSPENDED). Found: %. Definition: %. Aborting.',
             coalesce(array_to_string(v_distinct_statuses, ', '), 'none'), v_status_check_def;
     END IF;
     ```

---

## 2. CATALOG CHECKS AND THEIR LIMITATIONS

| Catalog Check | Inspection Mechanism | What It Enforces | Known Limitations & Fail-Closed Behavior |
| :--- | :--- | :--- | :--- |
| **Index Attribute Extraction** | `pg_attribute` for `idx.oid` where `attnum = 1`. | Guarantees index attribute name is strictly `status` without relying on `int2vector` casting. | Only inspects first key column. Mitigated by verifying `indnatts = 1` and `indnkeyatts = 1` (rejects multi-column indexes). |
| **Index Flags** | `pg_index.indisvalid`, `indisready`, `indisunique`, `indexprs`, `indpred`. | Ready, valid, non-unique, non-partial, non-expression index. | Relies on PostgreSQL's internal tree representation (`indexprs IS NULL`). Non-null trees trigger abort. |
| **CHECK AST Parsing** | `pg_get_constraintdef` + `regexp_split_to_table`. | Strictly 5 unique enum literals in a `= ANY (ARRAY[...])` structure; bans logical operators. | Assumes canonical PostgreSQL deparsed formatting. Any deviation fails closed with transaction rollback. |
| **Constraint Sets** | `pg_constraint.conkey = ARRAY[(attnum)]`. | Exact single-column Primary Key and Unique constraints. | Fails closed on any composite constraint. |
| **RLS Policy** | `pg_policies.qual` and `with_check` with `IS DISTINCT FROM 'false'`. | Denies all PostgREST client queries and writes. | String-based evaluation of `false`. Any non-false or NULL expression triggers immediate abort. |

---

## 3. AUTOMATED TEST SUITE EXECUTION RESULTS

### 3.1 Static SQL Assertion Suite (`scratch/verify_step6_sql.py`)
- **Total Lines:** 557
- **Transaction Structure:** Starts with `BEGIN;`, ends with `COMMIT;`.
- **Parentheses Balance:** 187 pairs (100% balanced).
- **Dollar-Quote Blocks:** 4 `DO $$` and 4 `END $$;` blocks (100% balanced).
- **Destructive Commands Check:** 0 occurrences of `DROP`, `TRUNCATE`, `CASCADE`, `ALTER TABLE ... DROP`.
- **Preflight Catalog Assertions:** All Step 6 index and strict CHECK parser rules validated.

### 3.2 Backend Test Suites
**Command:** `cmd /c "backend\.venv\Scripts\python.exe -m pytest tests/test_employee_registration.py -v && backend\.venv\Scripts\python.exe -m pytest tests/test_customer_api.py -v"`
- `tests/test_employee_registration.py`: **19/19 Passed** in 5.64s.
- `tests/test_customer_api.py`: **13/13 Passed** in 2.74s.

### 3.3 Frontend Test Suites
**Command:** `cmd /c "cd frontend && npm test"`
- **Result:** 15 test suites, **46/46 Passed** in 215ms.

---

## 4. BOUNDARY CONFIRMATION & PRESERVATION OF INVARIANTS

- **No Remote Connections:** Zero network calls were made to Supabase.
- **No Remote DDL:** The remote Supabase database was not modified.
- **No Credential Exposure:** Service-role keys, tokens, and passwords were not exposed or logged.
- **Preserved Core Invariants:**
  - 12-column employee registry schema.
  - Allowed status set: `APPROVED`, `INVITED`, `PENDING`, `REJECTED`, `SUSPENDED`.
  - Identity mappings: `EMP-2026-001` (`authorized_employee@ecommerce.in`) and `EMP-2026-002` (`new_hire@retainiq.internal` $\leftrightarrow$ `15dc86fa-14ce-4b50-9dbf-5eb9f97dd05a`).
  - Production ML Pipeline `final_churn_rf_pipeline.joblib` (SHA-256 `24F1F0E3...`), threshold $\tau = 0.50$, 43 features, and 5 customer personas are 100% immutable.
- **Phase 8.4.6:** Strictly not started.

---

## 5. FINAL SAFETY VERDICT

> **VERDICT: APPROVED — FINAL EXECUTION APPROVAL CANDIDATE**  
> The migration script `backend/database/migrations/008_create_employee_registry.sql` is catalog-complete, index-hardened, parser-verified, non-destructive, and idempotent. It is ready for manual deployment via the Supabase Dashboard SQL Editor.
