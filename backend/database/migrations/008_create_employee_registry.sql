-- ==============================================================================
-- Migration: 008_create_employee_registry.sql (Final Production Release Candidate)
-- Description: Creates persistent employee registry for administrator-controlled onboarding.
-- Dialect: PostgreSQL / Supabase
-- Phase: 8.4.5.3 (Final Migration Review)
-- Status: FINAL CANDIDATE — FULLY HARDENED, VALIDATED & READY FOR MANUAL REMOTE EXECUTION
-- ==============================================================================

BEGIN;

-- ------------------------------------------------------------------------------
-- 1. Schema Integrity Preflight Guard (Strict Fail-Closed System Catalog Audit)
-- ------------------------------------------------------------------------------
-- If public.employee_registry exists, rigorously validate:
-- - All 12 columns by name
-- - Exact PostgreSQL data types (TIMESTAMPTZ for timestamps)
-- - NOT NULL constraints on employee_id, work_email, status
-- - Primary key constraint strictly on single column employee_id (rejects composite PK)
-- - Unique constraints strictly on single columns work_email and supabase_user_id
-- - Exactly one status CHECK constraint enforcing exact 5 enum values without permissive logic or arbitrary expressions
-- - Custom lookup index idx_employee_registry_status (ready, valid, non-unique, non-partial, non-expression B-tree mapping exactly to status)
-- - Row Level Security (RLS) enablement (pg_class.relrowsecurity)
-- - Complete client-denial policy definition via pg_policies (NULL-safe IS DISTINCT FROM 'false', exactly {anon, authenticated})
-- Strictly NO DROP, NO TRUNCATE, NO CASCADE, NO SILENT REPAIR.
DO $$
DECLARE
    v_missing_cols TEXT;
    v_type_mismatches TEXT;
    v_nullability_errors TEXT;
    v_has_pk BOOLEAN;
    v_has_email_uq BOOLEAN;
    v_has_uuid_uq BOOLEAN;
    v_status_attnum INT;
    v_status_check_count INT;
    v_status_check_oid OID;
    v_status_check_key_len INT;
    v_status_check_def TEXT;
    v_norm_check TEXT;
    v_match TEXT[];
    v_array_content TEXT;
    v_elements TEXT[];
    v_all_statuses TEXT[];
    v_distinct_statuses TEXT[];
    v_idx_is_valid BOOLEAN;
    v_idx_is_ready BOOLEAN;
    v_idx_is_unique BOOLEAN;
    v_idx_is_non_expr BOOLEAN;
    v_idx_is_non_partial BOOLEAN;
    v_idx_am TEXT;
    v_idx_natts INT;
    v_idx_nkeyatts INT;
    v_idx_col_name TEXT;
    v_tbl_col_name TEXT;
    v_rls_enabled BOOLEAN;
    v_policy_cmd TEXT;
    v_policy_roles NAME[];
    v_policy_qual TEXT;
    v_policy_with_check TEXT;
    v_norm_qual TEXT;
    v_norm_with_check TEXT;
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.tables 
        WHERE table_schema = 'public' AND table_name = 'employee_registry'
    ) THEN
        -- 1a. Validate all 12 columns exist
        SELECT string_agg(expected_col, ', ')
        INTO v_missing_cols
        FROM (
            VALUES 
                ('employee_id'), ('work_email'), ('full_name'), ('department'),
                ('supabase_user_id'), ('status'), ('created_at'), ('registered_at'),
                ('approved_at'), ('approved_by'), ('rejection_reason'), ('notes')
        ) AS exp(expected_col)
        WHERE NOT EXISTS (
            SELECT 1 FROM information_schema.columns c
            WHERE c.table_schema = 'public' 
              AND c.table_name = 'employee_registry' 
              AND c.column_name = exp.expected_col
        );

        IF v_missing_cols IS NOT NULL THEN
            RAISE EXCEPTION 'Schema integrity preflight failure: public.employee_registry exists but is missing required column(s): %. Aborting migration without schema modification.', v_missing_cols;
        END IF;

        -- 1b. Validate exact data types (TIMESTAMPTZ for timestamp columns)
        SELECT string_agg(c.column_name || ' (actual: ' || c.data_type || ')', ', ')
        INTO v_type_mismatches
        FROM information_schema.columns c
        WHERE c.table_schema = 'public' AND c.table_name = 'employee_registry'
          AND (
            (c.column_name IN ('employee_id', 'work_email', 'full_name', 'department', 'supabase_user_id', 'status', 'approved_by', 'rejection_reason', 'notes')
             AND c.data_type NOT IN ('text', 'character varying'))
            OR
            (c.column_name IN ('created_at', 'registered_at', 'approved_at')
             AND c.data_type != 'timestamp with time zone')
          );

        IF v_type_mismatches IS NOT NULL THEN
            RAISE EXCEPTION 'Schema integrity preflight failure: public.employee_registry column data type mismatch: %. Aborting migration.', v_type_mismatches;
        END IF;

        -- 1c. Validate NOT NULL constraints on employee_id, work_email, status
        SELECT string_agg(c.column_name, ', ')
        INTO v_nullability_errors
        FROM information_schema.columns c
        WHERE c.table_schema = 'public' AND c.table_name = 'employee_registry'
          AND c.column_name IN ('employee_id', 'work_email', 'status')
          AND c.is_nullable != 'NO';

        IF v_nullability_errors IS NOT NULL THEN
            RAISE EXCEPTION 'Schema integrity preflight failure: expected NOT NULL constraint missing on column(s): %. Aborting migration.', v_nullability_errors;
        END IF;

        -- 1d. Validate Primary Key constraint is strictly on employee_id (reject composite PK)
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

        IF NOT v_has_pk THEN
            RAISE EXCEPTION 'Schema integrity preflight failure: PRIMARY KEY constraint must be exactly on column employee_id (composite or missing PK rejected). Aborting migration.';
        END IF;

        -- 1e. Validate UNIQUE constraints are strictly on work_email and supabase_user_id (reject composite)
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

        IF NOT v_has_email_uq THEN
            RAISE EXCEPTION 'Schema integrity preflight failure: UNIQUE constraint must be exactly on column work_email (composite or missing UNIQUE rejected). Aborting migration.';
        END IF;

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

        IF NOT v_has_uuid_uq THEN
            RAISE EXCEPTION 'Schema integrity preflight failure: UNIQUE constraint must be exactly on column supabase_user_id (composite or missing UNIQUE rejected). Aborting migration.';
        END IF;

        -- 1f. Validate exact status CHECK constraint (catalog-native, single-column, strictly 5 enum values)
        -- Retrieve the exact attribute number of status on employee_registry
        SELECT a.attnum INTO v_status_attnum
        FROM pg_attribute a
        JOIN pg_class t ON t.oid = a.attrelid
        JOIN pg_namespace n ON n.oid = t.relnamespace
        WHERE n.nspname = 'public' 
          AND t.relname = 'employee_registry' 
          AND a.attname = 'status';

        IF v_status_attnum IS NULL THEN
            RAISE EXCEPTION 'Schema integrity preflight failure: column status not found in pg_attribute for public.employee_registry. Aborting migration.';
        END IF;

        -- Query A — Count all CHECK constraints referencing status (including multi-column / composite constraints)
        SELECT count(*)
        INTO v_status_check_count
        FROM pg_constraint c
        JOIN pg_class t ON t.oid = c.conrelid
        JOIN pg_namespace n ON n.oid = t.relnamespace
        WHERE n.nspname = 'public' 
          AND t.relname = 'employee_registry'
          AND c.contype = 'c'
          AND v_status_attnum = ANY(c.conkey);

        IF v_status_check_count = 0 THEN
            RAISE EXCEPTION 'Schema integrity preflight failure: no CHECK constraint referencing status column found on public.employee_registry. Aborting migration.';
        END IF;

        IF v_status_check_count > 1 THEN
            RAISE EXCEPTION 'Schema integrity preflight failure: multiple (% constraints) CHECK constraints referencing status column found on public.employee_registry. Expected exactly one status CHECK constraint. Aborting migration.', v_status_check_count;
        END IF;

        -- Query B — Retrieve the matching constraint OID and column count (executes only after confirming exactly one constraint exists)
        SELECT c.oid, array_length(c.conkey, 1)
        INTO v_status_check_oid, v_status_check_key_len
        FROM pg_constraint c
        JOIN pg_class t ON t.oid = c.conrelid
        JOIN pg_namespace n ON n.oid = t.relnamespace
        WHERE n.nspname = 'public' 
          AND t.relname = 'employee_registry'
          AND c.contype = 'c'
          AND v_status_attnum = ANY(c.conkey);

        -- Verify that the constraint's referenced-column set consists exclusively of the single status column
        IF v_status_check_key_len IS DISTINCT FROM 1 OR (
            SELECT c.conkey FROM pg_constraint c WHERE c.oid = v_status_check_oid
        ) IS DISTINCT FROM ARRAY[v_status_attnum::smallint] THEN
            RAISE EXCEPTION 'Schema integrity preflight failure: CHECK constraint on status column is composite or references additional columns. Expected constraint to reference exclusively the status column. Aborting migration.';
        END IF;

        SELECT pg_get_constraintdef(v_status_check_oid) INTO v_status_check_def;

        v_norm_check := regexp_replace(trim(v_status_check_def), '\s+', ' ', 'g');

        -- Reject permissive or injection-prone logical operators and keywords
        IF v_norm_check ~* '\b(OR|AND|NOT|TRUE|FALSE|IS\s+NULL|LIKE|ILIKE|CASE|WHEN|COALESCE|NULLIF)\b' THEN
            RAISE EXCEPTION 'Schema integrity preflight failure: CHECK constraint contains forbidden logical operator or permissive keyword. Found: %. Aborting.', v_status_check_def;
        END IF;

        -- Enforce strict AST structural pattern using scalar regexp_match()
        v_match := regexp_match(v_norm_check, '^CHECK \(\(\(?status\)?(?:::text)? = ANY \(ARRAY\[([^\]]+)\]\)\)\)$');
        IF v_match IS NULL OR v_match[1] IS NULL THEN
            RAISE EXCEPTION 'Schema integrity preflight failure: CHECK constraint does not match exact structural pattern "CHECK ((status = ANY (ARRAY[...])))". Found: %. Aborting.', v_status_check_def;
        END IF;

        -- Extract array content safely from scalar match capture group 1
        v_array_content := v_match[1];

        -- Parse array elements into array
        SELECT ARRAY(
            SELECT trim(elem) 
            FROM regexp_split_to_table(v_array_content, ',') AS elem
        ) INTO v_elements;

        -- Reject any non-literal or expression-based array elements
        IF EXISTS (
            SELECT 1 FROM unnest(v_elements) AS e 
            WHERE trim(e) !~ '^''[A-Z_]+''(::text)?$'
        ) THEN
            RAISE EXCEPTION 'Schema integrity preflight failure: status ARRAY contains invalid, non-literal, or expression-based element. Array content: %. Aborting.', v_array_content;
        END IF;

        -- Extract all status literals using scalar regexp_match() (preserving order and duplicates for counting)
        SELECT array_agg((regexp_match(trim(e), '^''([A-Z_]+)''(::text)?$'))[1] ORDER BY (regexp_match(trim(e), '^''([A-Z_]+)''(::text)?$'))[1])
        INTO v_all_statuses
        FROM unnest(v_elements) AS e;

        -- Extract distinct status literals using scalar regexp_match()
        SELECT array_agg(DISTINCT (regexp_match(trim(e), '^''([A-Z_]+)''(::text)?$'))[1] ORDER BY (regexp_match(trim(e), '^''([A-Z_]+)''(::text)?$'))[1])
        INTO v_distinct_statuses
        FROM unnest(v_elements) AS e;

        -- Reject duplicate status literals
        IF array_length(v_all_statuses, 1) != array_length(v_distinct_statuses, 1) THEN
            RAISE EXCEPTION 'Schema integrity preflight failure: CHECK constraint on status contains duplicate status literals. Found: %. Aborting.', v_array_content;
        END IF;

        -- Enforce exact count of 5 and exact expected enum set
        IF array_length(v_all_statuses, 1) != 5 OR v_distinct_statuses IS DISTINCT FROM ARRAY['APPROVED', 'INVITED', 'PENDING', 'REJECTED', 'SUSPENDED'] THEN
            RAISE EXCEPTION 'Schema integrity preflight failure: CHECK constraint on status does not enforce exactly the five permitted statuses (APPROVED, INVITED, PENDING, REJECTED, SUSPENDED). Found: %. Definition: %. Aborting.',
                coalesce(array_to_string(v_distinct_statuses, ', '), 'none'), v_status_check_def;
        END IF;

        -- 1g. Validate idx_employee_registry_status using pg_attribute on index relation (safe catalog-based extraction)
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
        JOIN pg_attribute tbl_att ON tbl_att.attrelid = t.oid AND tbl_att.attnum = ANY(i.indkey)
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

        IF v_idx_natts IS DISTINCT FROM 1 OR v_idx_nkeyatts IS DISTINCT FROM 1 THEN
            RAISE EXCEPTION 'Schema integrity preflight failure: index "idx_employee_registry_status" must index exactly one key attribute (found % attributes, % key attributes). Aborting migration.', v_idx_natts, v_idx_nkeyatts;
        END IF;

        -- Explicit index-to-table attribute mapping verification
        IF v_idx_col_name IS DISTINCT FROM 'status' 
           OR v_tbl_col_name IS DISTINCT FROM 'status' 
           OR v_idx_col_name IS DISTINCT FROM v_tbl_col_name THEN
            RAISE EXCEPTION 'Schema integrity preflight failure: index "idx_employee_registry_status" attribute mapping mismatch (index col: "%", table col: "%", expected: "status"). Aborting migration.', v_idx_col_name, v_tbl_col_name;
        END IF;

        -- 1h. Validate Row Level Security (RLS) is enabled
        SELECT c.relrowsecurity INTO v_rls_enabled
        FROM pg_class c
        JOIN pg_namespace n ON n.oid = c.relnamespace
        WHERE n.nspname = 'public' AND c.relname = 'employee_registry';

        IF NOT v_rls_enabled THEN
            RAISE EXCEPTION 'Schema integrity preflight failure: Row Level Security (RLS) is not enabled on public.employee_registry. Aborting migration.';
        END IF;

        -- 1i. Validate complete client-denial policy definition via pg_policies with NULL-safe checks
        SELECT 
            cmd,
            roles,
            qual,
            with_check
        INTO 
            v_policy_cmd,
            v_policy_roles,
            v_policy_qual,
            v_policy_with_check
        FROM pg_policies
        WHERE schemaname = 'public' 
          AND tablename = 'employee_registry'
          AND policyname = 'Deny direct client access to employee_registry';

        IF NOT FOUND THEN
            RAISE EXCEPTION 'Schema integrity preflight failure: policy "Deny direct client access to employee_registry" is missing on public.employee_registry. Aborting migration.';
        END IF;

        IF v_policy_cmd IS DISTINCT FROM 'ALL' THEN
            RAISE EXCEPTION 'Schema integrity preflight failure: policy command is "%" (expected "ALL"). Aborting migration.', v_policy_cmd;
        END IF;

        -- Require strictly and exactly the anon and authenticated roles
        IF v_policy_roles IS NULL 
           OR array_length(v_policy_roles, 1) != 2 
           OR NOT ('anon' = ANY(v_policy_roles) AND 'authenticated' = ANY(v_policy_roles)) THEN
            RAISE EXCEPTION 'Schema integrity preflight failure: policy roles must be exactly {anon, authenticated} (found: %). Aborting migration.', coalesce(array_to_string(v_policy_roles, ', '), 'NULL');
        END IF;

        v_norm_qual := trim(both ' ()' from v_policy_qual);
        v_norm_with_check := trim(both ' ()' from v_policy_with_check);

        IF v_norm_qual IS DISTINCT FROM 'false' THEN
            RAISE EXCEPTION 'Schema integrity preflight failure: policy USING expression is "%" (expected explicit "false"). Aborting migration.', v_policy_qual;
        END IF;

        IF v_norm_with_check IS DISTINCT FROM 'false' THEN
            RAISE EXCEPTION 'Schema integrity preflight failure: policy WITH CHECK expression is "%" (expected explicit "false"). Aborting migration.', v_policy_with_check;
        END IF;
    END IF;
END $$;

-- ------------------------------------------------------------------------------
-- 2. Create public.employee_registry table with complete 12-column schema
-- ------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.employee_registry (
    employee_id TEXT PRIMARY KEY,
    work_email TEXT UNIQUE NOT NULL,
    full_name TEXT,
    department TEXT DEFAULT 'Customer Success',
    supabase_user_id TEXT UNIQUE,
    status TEXT NOT NULL DEFAULT 'INVITED' CHECK (status IN ('INVITED', 'PENDING', 'APPROVED', 'REJECTED', 'SUSPENDED')),
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    registered_at TIMESTAMPTZ,
    approved_at TIMESTAMPTZ,
    approved_by TEXT,
    rejection_reason TEXT,
    notes TEXT
);

-- ------------------------------------------------------------------------------
-- 3. Dedicated Custom Lookup Index for Fast Status Queries
-- ------------------------------------------------------------------------------
-- Note: Constraint indexes are automatically generated by PostgreSQL:
-- 1. employee_registry_pkey (PRIMARY KEY on employee_id)
-- 2. employee_registry_work_email_key (UNIQUE on work_email)
-- 3. employee_registry_supabase_user_id_key (UNIQUE on supabase_user_id)
-- To prevent redundant duplicate B-Tree indexes, explicit indexes on work_email
-- and supabase_user_id are omitted.
-- Only the custom non-unique filter index on status is created:
CREATE INDEX IF NOT EXISTS idx_employee_registry_status ON public.employee_registry(status);

-- ------------------------------------------------------------------------------
-- 4. Enable Row Level Security (RLS)
-- ------------------------------------------------------------------------------
ALTER TABLE public.employee_registry ENABLE ROW LEVEL SECURITY;

-- ------------------------------------------------------------------------------
-- 5. Restrict all public and client access via PostgREST
-- ------------------------------------------------------------------------------
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_policies 
        WHERE schemaname = 'public' 
          AND tablename = 'employee_registry'
          AND policyname = 'Deny direct client access to employee_registry'
          AND cmd = 'ALL'
    ) THEN
        CREATE POLICY "Deny direct client access to employee_registry" ON public.employee_registry
            FOR ALL TO anon, authenticated USING (false) WITH CHECK (false);
    END IF;
END $$;

-- ------------------------------------------------------------------------------
-- 6. Defense-in-depth table-level privilege revocation & grants
-- ------------------------------------------------------------------------------
REVOKE ALL ON public.employee_registry FROM anon, authenticated, public;
GRANT ALL ON public.employee_registry TO service_role;

-- ------------------------------------------------------------------------------
-- 7. Bidirectional Safe Seed Validation & Insertion
-- ------------------------------------------------------------------------------
-- Strictly validates complete expected seed records bidirectionally:
-- - EMP-2026-001 <-> authorized_employee@ecommerce.in (INVITED, UUID: NULL)
-- - EMP-2026-002 <-> new_hire@retainiq.internal <-> UUID 15dc86fa-14ce-4b50-9dbf-5eb9f97dd05a (INVITED)
-- Aborts if existing records have ANY unexpected email, ID, status or UUID.
-- Preserves matching records without mutation.
DO $$
DECLARE
    r_id1 RECORD;
    r_email1 RECORD;
    r_id2 RECORD;
    r_email2 RECORD;
    r_uuid2 RECORD;
    v_target_uuid CONSTANT TEXT := '15dc86fa-14ce-4b50-9dbf-5eb9f97dd05a';
BEGIN
    -- 7a. Bidirectional Validation for EMP-2026-001
    -- Query by ID
    SELECT * INTO r_id1 FROM public.employee_registry WHERE employee_id = 'EMP-2026-001';
    IF FOUND THEN
        IF LOWER(TRIM(r_id1.work_email)) != 'authorized_employee@ecommerce.in' THEN
            RAISE EXCEPTION 'Seed conflict: EMP-2026-001 has unexpected email "%" (expected "authorized_employee@ecommerce.in"). Aborting.', r_id1.work_email;
        END IF;
        IF r_id1.status != 'INVITED' THEN
            RAISE EXCEPTION 'Seed conflict: EMP-2026-001 has unexpected status "%" (expected "INVITED"). Aborting.', r_id1.status;
        END IF;
        IF r_id1.supabase_user_id IS NOT NULL THEN
            RAISE EXCEPTION 'Seed conflict: EMP-2026-001 has unexpected supabase_user_id "%" (expected NULL). Aborting.', r_id1.supabase_user_id;
        END IF;
    END IF;

    -- Query by Email
    SELECT * INTO r_email1 FROM public.employee_registry WHERE LOWER(TRIM(work_email)) = 'authorized_employee@ecommerce.in';
    IF FOUND THEN
        IF r_email1.employee_id != 'EMP-2026-001' THEN
            RAISE EXCEPTION 'Seed conflict: authorized_employee@ecommerce.in is mapped to unexpected employee_id "%" (expected "EMP-2026-001"). Aborting.', r_email1.employee_id;
        END IF;
        IF r_email1.status != 'INVITED' THEN
            RAISE EXCEPTION 'Seed conflict: authorized_employee@ecommerce.in has unexpected status "%" (expected "INVITED"). Aborting.', r_email1.status;
        END IF;
        IF r_email1.supabase_user_id IS NOT NULL THEN
            RAISE EXCEPTION 'Seed conflict: authorized_employee@ecommerce.in has unexpected supabase_user_id "%" (expected NULL). Aborting.', r_email1.supabase_user_id;
        END IF;
    END IF;

    -- 7b. Bidirectional Validation for EMP-2026-002
    -- Query by ID
    SELECT * INTO r_id2 FROM public.employee_registry WHERE employee_id = 'EMP-2026-002';
    IF FOUND THEN
        IF LOWER(TRIM(r_id2.work_email)) != 'new_hire@retainiq.internal' THEN
            RAISE EXCEPTION 'Seed conflict: EMP-2026-002 has unexpected email "%" (expected "new_hire@retainiq.internal"). Aborting.', r_id2.work_email;
        END IF;
        IF r_id2.status != 'INVITED' THEN
            RAISE EXCEPTION 'Seed conflict: EMP-2026-002 has unexpected status "%" (expected "INVITED"). Aborting.', r_id2.status;
        END IF;
        IF r_id2.supabase_user_id IS NULL OR r_id2.supabase_user_id != v_target_uuid THEN
            RAISE EXCEPTION 'Seed conflict: EMP-2026-002 has unexpected supabase_user_id "%" (expected "%"). Aborting.', r_id2.supabase_user_id, v_target_uuid;
        END IF;
    END IF;

    -- Query by Email
    SELECT * INTO r_email2 FROM public.employee_registry WHERE LOWER(TRIM(work_email)) = 'new_hire@retainiq.internal';
    IF FOUND THEN
        IF r_email2.employee_id != 'EMP-2026-002' THEN
            RAISE EXCEPTION 'Seed conflict: new_hire@retainiq.internal is mapped to unexpected employee_id "%" (expected "EMP-2026-002"). Aborting.', r_email2.employee_id;
        END IF;
        IF r_email2.status != 'INVITED' THEN
            RAISE EXCEPTION 'Seed conflict: new_hire@retainiq.internal has unexpected status "%" (expected "INVITED"). Aborting.', r_email2.status;
        END IF;
        IF r_email2.supabase_user_id IS NULL OR r_email2.supabase_user_id != v_target_uuid THEN
            RAISE EXCEPTION 'Seed conflict: new_hire@retainiq.internal has unexpected supabase_user_id "%" (expected "%"). Aborting.', r_email2.supabase_user_id, v_target_uuid;
        END IF;
    END IF;

    -- Query by UUID
    SELECT * INTO r_uuid2 FROM public.employee_registry WHERE supabase_user_id = v_target_uuid;
    IF FOUND THEN
        IF r_uuid2.employee_id != 'EMP-2026-002' THEN
            RAISE EXCEPTION 'Seed conflict: UUID "%" is mapped to unexpected employee_id "%" (expected "EMP-2026-002"). Aborting.', v_target_uuid, r_uuid2.employee_id;
        END IF;
        IF LOWER(TRIM(r_uuid2.work_email)) != 'new_hire@retainiq.internal' THEN
            RAISE EXCEPTION 'Seed conflict: UUID "%" is mapped to unexpected email "%" (expected "new_hire@retainiq.internal"). Aborting.', v_target_uuid, r_uuid2.work_email;
        END IF;
        IF r_uuid2.status != 'INVITED' THEN
            RAISE EXCEPTION 'Seed conflict: UUID "%" has unexpected status "%" (expected "INVITED"). Aborting.', v_target_uuid, r_uuid2.status;
        END IF;
    END IF;

    -- 7c. Idempotent Non-Conflicting Insertion
    IF NOT EXISTS (SELECT 1 FROM public.employee_registry WHERE employee_id = 'EMP-2026-001') THEN
        INSERT INTO public.employee_registry (
            employee_id, work_email, full_name, department, status, supabase_user_id, created_at, notes
        ) VALUES (
            'EMP-2026-001',
            'authorized_employee@ecommerce.in',
            'Lead Retention Operations Analyst',
            'Customer Success',
            'INVITED',
            NULL,
            CURRENT_TIMESTAMP,
            'Administrator-issued invitation for foundational operations employee'
        );
    END IF;

    IF NOT EXISTS (SELECT 1 FROM public.employee_registry WHERE employee_id = 'EMP-2026-002') THEN
        INSERT INTO public.employee_registry (
            employee_id, work_email, full_name, department, status, supabase_user_id, created_at, notes
        ) VALUES (
            'EMP-2026-002',
            'new_hire@retainiq.internal',
            'Junior Retention Analyst',
            'Customer Success',
            'INVITED',
            v_target_uuid,
            CURRENT_TIMESTAMP,
            'Administrator-issued invitation linked to verified Supabase Auth account'
        );
    END IF;
END $$;

-- ------------------------------------------------------------------------------
-- 8. Strengthened Migration Tracking
-- ------------------------------------------------------------------------------
-- If absent, inserts expected record with confirmed schema (version, name, applied_at).
-- If present with exact matching name, leaves it unchanged.
-- If present with conflicting name, raises an exception and aborts.
DO $$
DECLARE
    v_existing_name TEXT;
    v_expected_version CONSTANT TEXT := '008_create_employee_registry';
    v_expected_name CONSTANT TEXT := 'Creates persistent employee registry for administrator-controlled onboarding';
BEGIN
    SELECT name INTO v_existing_name
    FROM public.schema_migrations
    WHERE version = v_expected_version;

    IF FOUND THEN
        IF v_existing_name != v_expected_name THEN
            RAISE EXCEPTION 'Migration tracking conflict: version "%" is already recorded with unexpected name "%" (expected "%"). Aborting.',
                v_expected_version, v_existing_name, v_expected_name;
        END IF;
    ELSE
        INSERT INTO public.schema_migrations (version, name, applied_at)
        VALUES (v_expected_version, v_expected_name, CURRENT_TIMESTAMP);
    END IF;
END $$;

COMMIT;
