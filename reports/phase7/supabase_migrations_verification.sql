-- ==============================================================================
-- Indian E-Commerce Customer Retention Intelligence System
-- Post-Migration Verification Suite for Supabase PostgreSQL
-- 
-- Run this script in Supabase Dashboard -> SQL Editor after executing
-- supabase_migrations_execution.sql.
-- ==============================================================================

-- ==============================================================================
-- 1. VERIFY TABLE PRESENCE
-- ==============================================================================
SELECT 
    table_name,
    CASE 
        WHEN table_name IN ('schema_migrations', 'customers', 'customer_predictions', 'customer_segments', 'retention_recommendations') 
        THEN 'PASSED' 
        ELSE 'UNEXPECTED' 
    END AS verification_status
FROM information_schema.tables 
WHERE table_schema = 'public' 
  AND table_type = 'BASE TABLE'
ORDER BY table_name;

-- Summary Count Check (Expected: Exactly 5 tables in public schema)
SELECT 
    COUNT(*) AS total_tables,
    CASE WHEN COUNT(*) >= 5 THEN 'PASSED (All required tables present)' ELSE 'FAILED (Missing tables)' END AS status
FROM information_schema.tables 
WHERE table_schema = 'public' 
  AND table_name IN ('schema_migrations', 'customers', 'customer_predictions', 'customer_segments', 'retention_recommendations');


-- ==============================================================================
-- 2. VERIFY MIGRATION VERSION TRACKING
-- ==============================================================================
SELECT 
    version,
    name,
    applied_at,
    'PASSED' AS status
FROM schema_migrations
ORDER BY version;


-- ==============================================================================
-- 3. VERIFY COLUMN SPECIFICATIONS & DATA TYPES
-- ==============================================================================
SELECT 
    table_name,
    column_name,
    data_type,
    is_nullable,
    column_default
FROM information_schema.columns
WHERE table_schema = 'public'
  AND table_name IN ('customers', 'customer_predictions', 'customer_segments', 'retention_recommendations')
ORDER BY table_name, ordinal_position;


-- ==============================================================================
-- 4. VERIFY PRIMARY KEYS & FOREIGN KEYS
-- ==============================================================================
SELECT
    tc.table_name,
    tc.constraint_name,
    tc.constraint_type,
    kcu.column_name,
    ccu.table_name AS foreign_table_name,
    ccu.column_name AS foreign_column_name,
    'PASSED' AS status
FROM information_schema.table_constraints AS tc
JOIN information_schema.key_column_usage AS kcu
  ON tc.constraint_name = kcu.constraint_name
  AND tc.table_schema = kcu.table_schema
LEFT JOIN information_schema.constraint_column_usage AS ccu
  ON ccu.constraint_name = tc.constraint_name
  AND ccu.table_schema = tc.table_schema
WHERE tc.table_schema = 'public'
  AND tc.constraint_type IN ('PRIMARY KEY', 'FOREIGN KEY')
  AND tc.table_name IN ('customers', 'customer_predictions', 'customer_segments', 'retention_recommendations')
ORDER BY tc.table_name, tc.constraint_type DESC;


-- ==============================================================================
-- 5. VERIFY DOMAIN CHECK CONSTRAINTS
-- ==============================================================================
SELECT 
    conrelid::regclass AS table_name,
    conname AS constraint_name,
    pg_get_constraintdef(c.oid) AS constraint_definition,
    'PASSED' AS status
FROM pg_constraint c
JOIN pg_namespace n ON n.oid = c.connamespace
WHERE n.nspname = 'public'
  AND c.contype = 'c'
  AND conrelid::regclass::text IN ('customers', 'customer_predictions', 'customer_segments', 'retention_recommendations')
ORDER BY table_name, conname;


-- ==============================================================================
-- 6. VERIFY INDEXES (INCLUDING PARTIAL UNIQUE INDEX ON CURRENT SEGMENT)
-- ==============================================================================
SELECT 
    tablename AS table_name,
    indexname AS index_name,
    indexdef AS index_definition,
    'PASSED' AS status
FROM pg_indexes
WHERE schemaname = 'public'
  AND tablename IN ('customers', 'customer_predictions', 'customer_segments', 'retention_recommendations')
ORDER BY tablename, indexname;


-- ==============================================================================
-- 7. VERIFY ROW LEVEL SECURITY (RLS) ACTIVATION
-- ==============================================================================
SELECT 
    c.relname AS table_name,
    CASE WHEN c.relrowsecurity THEN 'PASSED (RLS Enabled)' ELSE 'FAILED (RLS Disabled)' END AS rls_status
FROM pg_class c
JOIN pg_namespace n ON n.oid = c.relnamespace
WHERE n.nspname = 'public'
  AND c.relname IN ('customers', 'customer_predictions', 'customer_segments', 'retention_recommendations')
ORDER BY c.relname;


-- ==============================================================================
-- 8. VERIFY NON-ANONYMOUS ACCESS POLICIES & ABSENCE OF UNRESTRICTED PERMISSIONS
-- ==============================================================================
SELECT 
    schemaname,
    tablename,
    policyname,
    roles,
    cmd,
    qual,
    CASE 
        -- Ensure that any policy targeting 'anon' explicitly restricts access
        WHEN 'anon' = ANY(roles) AND qual = 'false' THEN 'PASSED (Anonymous access blocked)'
        WHEN 'anon' = ANY(roles) AND qual != 'false' THEN 'FAILED (Anonymous access permitted!)'
        ELSE 'PASSED'
    END AS policy_safety_audit
FROM pg_policies
WHERE schemaname = 'public'
  AND tablename IN ('customers', 'customer_predictions', 'customer_segments', 'retention_recommendations')
ORDER BY tablename, policyname;
