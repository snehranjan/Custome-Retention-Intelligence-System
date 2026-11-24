-- ==============================================================================
-- Migration: 006_create_indexes_and_constraints.sql
-- Description: Creates performance indexes and operational constraints.
-- Dialect: PostgreSQL / Supabase
-- ==============================================================================

-- Customer Indexes
CREATE INDEX IF NOT EXISTS idx_customers_churn ON customers(churn);
CREATE INDEX IF NOT EXISTS idx_customers_city_state ON customers(city, state);
CREATE INDEX IF NOT EXISTS idx_customers_signup_date ON customers(signup_date);

-- Prediction Indexes
CREATE INDEX IF NOT EXISTS idx_predictions_customer_timestamp ON customer_predictions(customer_id, prediction_timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_predictions_risk_tier ON customer_predictions(risk_tier);
CREATE INDEX IF NOT EXISTS idx_predictions_predicted_churn ON customer_predictions(predicted_churn);

-- Segmentation Indexes
CREATE INDEX IF NOT EXISTS idx_segments_customer_id ON customer_segments(customer_id);
CREATE INDEX IF NOT EXISTS idx_segments_cluster_id ON customer_segments(cluster_id);
CREATE INDEX IF NOT EXISTS idx_segments_is_current ON customer_segments(is_current);

-- Retention Recommendation Indexes
CREATE INDEX IF NOT EXISTS idx_recs_customer_id ON retention_recommendations(customer_id);
CREATE INDEX IF NOT EXISTS idx_recs_prediction_id ON retention_recommendations(prediction_id);
CREATE INDEX IF NOT EXISTS idx_recs_priority_status ON retention_recommendations(priority, recommendation_status);
CREATE INDEX IF NOT EXISTS idx_recs_category ON retention_recommendations(recommendation_category);
