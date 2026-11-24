-- ==============================================================================
-- Rollback Script: rollback_008_employee_registry.sql
-- Description: Completely and safely reverts migration 008_create_employee_registry.
-- Dialect: PostgreSQL / Supabase
-- Phase: 8.4.5.2.1
-- Invariant: Uses RESTRICT (never CASCADE) to prevent accidental deletion of future dependencies.
-- ==============================================================================

BEGIN;

-- 1. Drop employee_registry table safely (fails if future dependent objects exist)
DROP TABLE IF EXISTS employee_registry RESTRICT;

-- 2. Remove migration tracking record
DELETE FROM schema_migrations WHERE version = '008_create_employee_registry';

COMMIT;
