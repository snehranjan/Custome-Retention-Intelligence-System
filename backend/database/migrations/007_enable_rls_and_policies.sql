-- ==============================================================================
-- Migration: 007_enable_rls_and_policies.sql
-- Description: Enables Row Level Security (RLS) and defines non-anonymous access policies.
-- Dialect: PostgreSQL / Supabase
-- ==============================================================================

-- 1. Enable Row Level Security on all core application tables
ALTER TABLE customers ENABLE ROW LEVEL SECURITY;
ALTER TABLE customer_predictions ENABLE ROW LEVEL SECURITY;
ALTER TABLE customer_segments ENABLE ROW LEVEL SECURITY;
ALTER TABLE retention_recommendations ENABLE ROW LEVEL SECURITY;

-- 2. Restrict public anonymous access
-- Explicitly deny unauthenticated anonymous access across all operations
DO $$
BEGIN
    -- customers
    IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE policyname = 'Deny anonymous access to customers' AND tablename = 'customers') THEN
        CREATE POLICY "Deny anonymous access to customers" ON customers
            FOR ALL TO anon USING (false);
    END IF;

    -- customer_predictions
    IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE policyname = 'Deny anonymous access to customer_predictions' AND tablename = 'customer_predictions') THEN
        CREATE POLICY "Deny anonymous access to customer_predictions" ON customer_predictions
            FOR ALL TO anon USING (false);
    END IF;

    -- customer_segments
    IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE policyname = 'Deny anonymous access to customer_segments' AND tablename = 'customer_segments') THEN
        CREATE POLICY "Deny anonymous access to customer_segments" ON customer_segments
            FOR ALL TO anon USING (false);
    END IF;

    -- retention_recommendations
    IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE policyname = 'Deny anonymous access to retention_recommendations' AND tablename = 'retention_recommendations') THEN
        CREATE POLICY "Deny anonymous access to retention_recommendations" ON retention_recommendations
            FOR ALL TO anon USING (false);
    END IF;
END $$;

-- 3. Documented Security Notice:
-- In Supabase, requests authenticated with the service_role secret key bypass RLS natively.
-- Authenticated employee user-level policies will be introduced in Phase 7.5 upon
-- integration of Supabase Auth / JWT verification.
