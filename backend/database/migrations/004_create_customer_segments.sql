-- ==============================================================================
-- Migration: 004_create_customer_segments.sql
-- Description: Creates the customer_segments table to store RFM K-Means clustering assignments.
-- Dialect: PostgreSQL / Supabase
-- ==============================================================================

CREATE TABLE IF NOT EXISTS customer_segments (
    segment_record_id VARCHAR(50) PRIMARY KEY,
    customer_id VARCHAR(50) NOT NULL REFERENCES customers(customer_id) ON DELETE CASCADE,
    cluster_id INTEGER NOT NULL CHECK (cluster_id IN (0, 1, 2, 3, 4)),
    segment_name VARCHAR(100) NOT NULL CHECK (segment_name IN (
        'Champions & High-Value Loyalists',
        'At-Risk / Lapsed Low-Value Customers',
        'Zero Delivered-Purchase Customers',
        'Steady Core Repeaters',
        'Recent Low-Ticket / New Promising Customers'
    )),
    recency_delivered_days NUMERIC(10, 2) NOT NULL CHECK (recency_delivered_days >= 0.0),
    hist_delivered_order_count INTEGER NOT NULL CHECK (hist_delivered_order_count >= 0),
    hist_delivered_order_value_inr NUMERIC(12, 2) NOT NULL CHECK (hist_delivered_order_value_inr >= 0.0),
    segmentation_model VARCHAR(100) NOT NULL DEFAULT 'KMeans_RFM_K5',
    is_current BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Partial unique index ensuring exactly one active segment per customer while retaining history
CREATE UNIQUE INDEX IF NOT EXISTS uq_current_customer_segment
    ON customer_segments (customer_id)
    WHERE is_current = TRUE;

COMMENT ON TABLE customer_segments IS 'RFM customer segmentation assignments using pre-fitted K-Means (K=5).';
COMMENT ON COLUMN customer_segments.recency_delivered_days IS 'Days since last delivered purchase (1117.0 for zero-delivered cohort).';
