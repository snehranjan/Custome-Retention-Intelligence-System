-- ==============================================================================
-- Migration: 002_create_customers.sql
-- Description: Creates the customers table to store synthetic customer profiles.
-- Dialect: PostgreSQL / Supabase
-- ==============================================================================

CREATE TABLE IF NOT EXISTS customers (
    customer_id VARCHAR(50) PRIMARY KEY,
    customer_name VARCHAR(255) NOT NULL,
    signup_date DATE NOT NULL,
    city VARCHAR(100),
    state VARCHAR(100),
    snapshot_date DATE NOT NULL DEFAULT '2025-12-31',
    churn INTEGER NOT NULL CHECK (churn IN (0, 1)),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE customers IS 'Primary customer profile table storing demographics and ground-truth churn status.';
COMMENT ON COLUMN customers.customer_id IS 'Unique customer identifier (e.g. IND_CUST_10001).';
COMMENT ON COLUMN customers.city IS 'Customer city (nullable to reflect intentional EDA missingness).';
COMMENT ON COLUMN customers.state IS 'Customer state (nullable to reflect intentional EDA missingness).';
COMMENT ON COLUMN customers.churn IS 'Ground-truth churn label (0 = Retained, 1 = Churned).';
