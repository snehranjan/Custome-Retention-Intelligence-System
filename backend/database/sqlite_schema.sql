-- ==============================================================================
-- Indian E-Commerce Customer Retention Intelligence System
-- Complete Relational DDL Schema (SQLite Compatible Dialect)
-- File: backend/database/sqlite_schema.sql
-- ==============================================================================

PRAGMA foreign_keys = ON;

-- 1. Schema Migrations Tracking Table
CREATE TABLE IF NOT EXISTS schema_migrations (
    version TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    applied_at TEXT DEFAULT (datetime('now', 'utc'))
);

-- 2. Customers Table
CREATE TABLE IF NOT EXISTS customers (
    customer_id TEXT PRIMARY KEY,
    customer_name TEXT NOT NULL,
    signup_date TEXT NOT NULL,
    city TEXT,
    state TEXT,
    snapshot_date TEXT NOT NULL DEFAULT '2025-12-31',
    churn INTEGER NOT NULL CHECK (churn IN (0, 1)),
    created_at TEXT DEFAULT (datetime('now', 'utc')),
    updated_at TEXT DEFAULT (datetime('now', 'utc'))
);

-- 3. Customer Predictions History Table
CREATE TABLE IF NOT EXISTS customer_predictions (
    prediction_id TEXT PRIMARY KEY,
    customer_id TEXT NOT NULL,
    churn_probability REAL NOT NULL CHECK (churn_probability >= 0.0 AND churn_probability <= 1.0),
    retention_probability REAL NOT NULL CHECK (retention_probability >= 0.0 AND retention_probability <= 1.0),
    predicted_churn INTEGER NOT NULL CHECK (predicted_churn IN (0, 1)),
    decision_threshold REAL NOT NULL DEFAULT 0.50 CHECK (decision_threshold = 0.50),
    risk_tier TEXT NOT NULL CHECK (risk_tier IN ('HIGH', 'MODERATE', 'LOW')),
    model_name TEXT NOT NULL DEFAULT 'RandomForestClassifier_ConfigD',
    model_version TEXT NOT NULL DEFAULT '1.0.0',
    model_hash TEXT NOT NULL DEFAULT '24F1F0E33C75B5590906369960DB6E5951EC95DF9AE40384DA60082B3438F301',
    prediction_timestamp TEXT DEFAULT (datetime('now', 'utc')),
    created_at TEXT DEFAULT (datetime('now', 'utc')),
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id) ON DELETE CASCADE,
    CHECK (abs(churn_probability + retention_probability - 1.0) <= 0.001)
);

-- 4. Customer Segments Table
CREATE TABLE IF NOT EXISTS customer_segments (
    segment_record_id TEXT PRIMARY KEY,
    customer_id TEXT NOT NULL,
    cluster_id INTEGER NOT NULL CHECK (cluster_id IN (0, 1, 2, 3, 4)),
    segment_name TEXT NOT NULL CHECK (segment_name IN (
        'Champions & High-Value Loyalists',
        'At-Risk / Lapsed Low-Value Customers',
        'Zero Delivered-Purchase Customers',
        'Steady Core Repeaters',
        'Recent Low-Ticket / New Promising Customers'
    )),
    recency_delivered_days REAL NOT NULL CHECK (recency_delivered_days >= 0.0),
    hist_delivered_order_count INTEGER NOT NULL CHECK (hist_delivered_order_count >= 0),
    hist_delivered_order_value_inr REAL NOT NULL CHECK (hist_delivered_order_value_inr >= 0.0),
    segmentation_model TEXT NOT NULL DEFAULT 'KMeans_RFM_K5',
    is_current INTEGER NOT NULL DEFAULT 1 CHECK (is_current IN (0, 1)),
    created_at TEXT DEFAULT (datetime('now', 'utc')),
    updated_at TEXT DEFAULT (datetime('now', 'utc')),
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id) ON DELETE CASCADE
);

-- Partial unique index ensuring only one active segment assignment per customer
CREATE UNIQUE INDEX IF NOT EXISTS uq_current_customer_segment
    ON customer_segments (customer_id)
    WHERE is_current = 1;

-- 5. Retention Recommendations Table
CREATE TABLE IF NOT EXISTS retention_recommendations (
    recommendation_id TEXT PRIMARY KEY,
    customer_id TEXT NOT NULL,
    prediction_id TEXT,
    recommendation_category TEXT NOT NULL,
    recommendation_title TEXT NOT NULL,
    recommendation_description TEXT NOT NULL,
    evidence TEXT NOT NULL,
    priority TEXT NOT NULL CHECK (priority IN ('HIGH', 'MEDIUM', 'LOW')),
    recommendation_status TEXT NOT NULL DEFAULT 'PENDING' CHECK (recommendation_status IN ('PENDING', 'IN_PROGRESS', 'APPLIED', 'DISMISSED', 'EXPIRED')),
    generated_at TEXT DEFAULT (datetime('now', 'utc')),
    created_at TEXT DEFAULT (datetime('now', 'utc')),
    updated_at TEXT DEFAULT (datetime('now', 'utc')),
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id) ON DELETE CASCADE,
    FOREIGN KEY (prediction_id) REFERENCES customer_predictions(prediction_id) ON DELETE SET NULL
);

-- 6. Performance Indexes
CREATE INDEX IF NOT EXISTS idx_customers_churn ON customers(churn);
CREATE INDEX IF NOT EXISTS idx_customers_city_state ON customers(city, state);
CREATE INDEX IF NOT EXISTS idx_customers_signup_date ON customers(signup_date);

CREATE INDEX IF NOT EXISTS idx_predictions_customer_timestamp ON customer_predictions(customer_id, prediction_timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_predictions_risk_tier ON customer_predictions(risk_tier);
CREATE INDEX IF NOT EXISTS idx_predictions_predicted_churn ON customer_predictions(predicted_churn);

CREATE INDEX IF NOT EXISTS idx_segments_customer_id ON customer_segments(customer_id);
CREATE INDEX IF NOT EXISTS idx_segments_cluster_id ON customer_segments(cluster_id);
CREATE INDEX IF NOT EXISTS idx_segments_is_current ON customer_segments(is_current);

CREATE INDEX IF NOT EXISTS idx_recs_customer_id ON retention_recommendations(customer_id);
CREATE INDEX IF NOT EXISTS idx_recs_prediction_id ON retention_recommendations(prediction_id);
CREATE INDEX IF NOT EXISTS idx_recs_priority_status ON retention_recommendations(priority, recommendation_status);
CREATE INDEX IF NOT EXISTS idx_recs_category ON retention_recommendations(recommendation_category);

-- 7. Employee Registry Table (Phase 8.4.5)
CREATE TABLE IF NOT EXISTS employee_registry (
    employee_id TEXT PRIMARY KEY,
    work_email TEXT UNIQUE NOT NULL,
    full_name TEXT,
    department TEXT DEFAULT 'Customer Success',
    supabase_user_id TEXT UNIQUE,
    status TEXT NOT NULL DEFAULT 'INVITED' CHECK (status IN ('INVITED', 'PENDING', 'APPROVED', 'REJECTED', 'SUSPENDED')),
    created_at TEXT DEFAULT (datetime('now', 'utc')),
    registered_at TEXT,
    approved_at TEXT,
    approved_by TEXT,
    rejection_reason TEXT,
    notes TEXT
);

CREATE INDEX IF NOT EXISTS idx_employee_registry_work_email ON employee_registry(work_email);
CREATE INDEX IF NOT EXISTS idx_employee_registry_supabase_user_id ON employee_registry(supabase_user_id);
CREATE INDEX IF NOT EXISTS idx_employee_registry_status ON employee_registry(status);
