-- ==============================================================================
-- Migration: 001_create_schema_migrations.sql
-- Description: Creates the schema_migrations version tracking table.
-- Dialect: PostgreSQL / Supabase
-- ==============================================================================

CREATE TABLE IF NOT EXISTS schema_migrations (
    version VARCHAR(50) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    applied_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE schema_migrations IS 'Tracks versioned database migrations applied to the database.';
