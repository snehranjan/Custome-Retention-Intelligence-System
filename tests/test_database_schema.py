"""
Indian E-Commerce Customer Retention Intelligence System
Database Schema & Migration Validation Suite (Phase 7.4 Checkpoint 2)

Tests:
1. Schema table creation & object presence
2. Primary keys and data types
3. Foreign key constraints & referential integrity
4. Unique constraints & partial unique indexes (active segment per customer)
5. Domain CHECK constraints (churn bounds [0, 1], prob sum, cluster IDs 0-4, persona names, priorities)
6. Nullable fields (city, state, prediction_id)
7. Performance index creation
8. Migration version tracking & idempotency
"""

import os
import sqlite3
import tempfile
import pytest

from backend.database.sqlite_migrator import SQLiteMigrator, MIGRATION_VERSION, MIGRATION_008_VERSION


@pytest.fixture
def temp_db():
    """Provides an isolated temporary SQLite database for clean testing."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        db_path = os.path.join(tmp_dir, "test_schema.db")
        SQLiteMigrator.apply_migrations(db_path)
        yield db_path


# ==============================================================================
# SECTION 1: Table & Migration Presence Tests
# ==============================================================================

def test_migration_tracking_and_idempotency(temp_db):
    """Verify schema_migrations table tracks applied version and prevents duplicate execution."""
    applied = SQLiteMigrator.get_applied_migrations(temp_db)
    assert len(applied) == 2
    versions = [m[0] for m in applied]
    assert MIGRATION_VERSION in versions
    assert MIGRATION_008_VERSION in versions

    # Repeated application must be idempotent and return False
    second_run = SQLiteMigrator.apply_migrations(temp_db)
    assert second_run is False
    applied_after = SQLiteMigrator.get_applied_migrations(temp_db)
    assert len(applied_after) == 2


def test_table_presence(temp_db):
    """Verify all 5 relational tables exist in the database."""
    tables = SQLiteMigrator.get_table_names(temp_db)
    expected_tables = {
        "schema_migrations",
        "customers",
        "customer_predictions",
        "customer_segments",
        "retention_recommendations",
    }
    assert expected_tables.issubset(set(tables))


# ==============================================================================
# SECTION 2: Primary Keys & Column Structure
# ==============================================================================

def test_primary_keys(temp_db):
    """Verify primary keys are correctly defined on all tables."""
    conn = sqlite3.connect(temp_db)
    cursor = conn.cursor()

    pk_expectations = {
        "customers": "customer_id",
        "customer_predictions": "prediction_id",
        "customer_segments": "segment_record_id",
        "retention_recommendations": "recommendation_id",
        "schema_migrations": "version",
    }

    for table, expected_pk in pk_expectations.items():
        cursor.execute(f"PRAGMA table_info({table});")
        cols = cursor.fetchall()
        # pk flag is column index 5 in PRAGMA table_info
        pk_cols = [c[1] for c in cols if c[5] > 0]
        assert pk_cols == [expected_pk], f"Table {table} expected PK {expected_pk}, got {pk_cols}"

    conn.close()


# ==============================================================================
# SECTION 3: Foreign Key Integrity Tests
# ==============================================================================

def test_foreign_key_enforcement(temp_db):
    """Verify that foreign keys prevent orphaned child records."""
    conn = sqlite3.connect(temp_db)
    conn.execute("PRAGMA foreign_keys = ON;")
    cursor = conn.cursor()

    # Attempt inserting prediction for non-existent customer
    with pytest.raises(sqlite3.IntegrityError):
        cursor.execute("""
            INSERT INTO customer_predictions (
                prediction_id, customer_id, churn_probability, retention_probability,
                predicted_churn, decision_threshold, risk_tier
            ) VALUES ('pred_orphan', 'IND_CUST_NONEXISTENT', 0.65, 0.35, 1, 0.50, 'MODERATE');
        """)

    # Attempt inserting segment for non-existent customer
    with pytest.raises(sqlite3.IntegrityError):
        cursor.execute("""
            INSERT INTO customer_segments (
                segment_record_id, customer_id, cluster_id, segment_name,
                recency_delivered_days, hist_delivered_order_count, hist_delivered_order_value_inr
            ) VALUES ('seg_orphan', 'IND_CUST_NONEXISTENT', 3, 'Steady Core Repeaters', 45.0, 8, 12000.0);
        """)

    # Attempt inserting recommendation with invalid prediction_id
    # First insert valid customer
    cursor.execute("""
        INSERT INTO customers (customer_id, customer_name, signup_date, churn)
        VALUES ('IND_CUST_VALID_01', 'Test Customer', '2024-01-15', 0);
    """)

    with pytest.raises(sqlite3.IntegrityError):
        cursor.execute("""
            INSERT INTO retention_recommendations (
                recommendation_id, customer_id, prediction_id, recommendation_category,
                recommendation_title, recommendation_description, evidence, priority
            ) VALUES (
                'rec_orphan_pred', 'IND_CUST_VALID_01', 'pred_nonexistent',
                'Loyalty Rewards', 'Title', 'Desc', 'Evidence', 'HIGH'
            );
        """)

    conn.close()


def test_nullable_foreign_key_in_recommendations(temp_db):
    """Verify recommendation can be created without prediction_id (nullable FK)."""
    conn = sqlite3.connect(temp_db)
    conn.execute("PRAGMA foreign_keys = ON;")
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO customers (customer_id, customer_name, signup_date, churn)
        VALUES ('IND_CUST_VALID_02', 'Test Customer 2', '2024-02-15', 0);
    """)
    cursor.execute("""
        INSERT INTO retention_recommendations (
            recommendation_id, customer_id, prediction_id, recommendation_category,
            recommendation_title, recommendation_description, evidence, priority
        ) VALUES (
            'rec_null_pred', 'IND_CUST_VALID_02', NULL,
            'Customer Care', 'General Care', 'Standard check-in', 'Tenure 400d', 'LOW'
        );
    """)
    conn.commit()

    cursor.execute("SELECT recommendation_id, prediction_id FROM retention_recommendations WHERE recommendation_id = 'rec_null_pred';")
    row = cursor.fetchone()
    assert row[0] == "rec_null_pred"
    assert row[1] is None

    conn.close()


# ==============================================================================
# SECTION 4: Unique Constraints & Partial Unique Indexes
# ==============================================================================

def test_duplicate_customer_id_rejected(temp_db):
    """Verify duplicate customer_id insertion raises IntegrityError."""
    conn = sqlite3.connect(temp_db)
    cursor = conn.cursor()

    cursor.execute("INSERT INTO customers (customer_id, customer_name, signup_date, churn) VALUES ('CUST_UQ_1', 'Name 1', '2024-01-01', 0);")
    conn.commit()

    with pytest.raises(sqlite3.IntegrityError):
        cursor.execute("INSERT INTO customers (customer_id, customer_name, signup_date, churn) VALUES ('CUST_UQ_1', 'Name 2', '2024-01-02', 1);")

    conn.close()


def test_partial_unique_index_active_segment(temp_db):
    """Verify partial unique index allows multiple historical segments but only ONE active segment."""
    conn = sqlite3.connect(temp_db)
    cursor = conn.cursor()

    cursor.execute("INSERT INTO customers (customer_id, customer_name, signup_date, churn) VALUES ('CUST_SEG_1', 'Segment User', '2024-01-01', 0);")

    # 1. Insert first active segment (is_current = 1) -> SUCCEEDS
    cursor.execute("""
        INSERT INTO customer_segments (
            segment_record_id, customer_id, cluster_id, segment_name,
            recency_delivered_days, hist_delivered_order_count, hist_delivered_order_value_inr, is_current
        ) VALUES ('seg_001', 'CUST_SEG_1', 4, 'Recent Low-Ticket / New Promising Customers', 20.0, 3, 4500.0, 1);
    """)
    conn.commit()

    # 2. Insert second active segment for same customer -> MUST FAIL
    with pytest.raises(sqlite3.IntegrityError):
        cursor.execute("""
            INSERT INTO customer_segments (
                segment_record_id, customer_id, cluster_id, segment_name,
                recency_delivered_days, hist_delivered_order_count, hist_delivered_order_value_inr, is_current
            ) VALUES ('seg_002', 'CUST_SEG_1', 3, 'Steady Core Repeaters', 15.0, 6, 9500.0, 1);
        """)

    # 3. Mark old segment historical (is_current = 0) and insert new active segment -> SUCCEEDS
    cursor.execute("UPDATE customer_segments SET is_current = 0 WHERE segment_record_id = 'seg_001';")
    cursor.execute("""
        INSERT INTO customer_segments (
            segment_record_id, customer_id, cluster_id, segment_name,
            recency_delivered_days, hist_delivered_order_count, hist_delivered_order_value_inr, is_current
        ) VALUES ('seg_002', 'CUST_SEG_1', 3, 'Steady Core Repeaters', 15.0, 6, 9500.0, 1);
    """)
    conn.commit()

    # Verify both records exist
    cursor.execute("SELECT segment_record_id, is_current FROM customer_segments WHERE customer_id = 'CUST_SEG_1' ORDER BY segment_record_id;")
    records = cursor.fetchall()
    assert len(records) == 2
    assert records[0] == ("seg_001", 0)
    assert records[1] == ("seg_002", 1)

    conn.close()


# ==============================================================================
# SECTION 5: Domain CHECK Constraints Tests
# ==============================================================================

def test_customer_churn_check_constraint(temp_db):
    """Verify customers.churn must be 0 or 1."""
    conn = sqlite3.connect(temp_db)
    cursor = conn.cursor()

    with pytest.raises(sqlite3.IntegrityError):
        cursor.execute("INSERT INTO customers (customer_id, customer_name, signup_date, churn) VALUES ('CUST_INV_CHURN', 'User', '2024-01-01', 2);")

    conn.close()


def test_prediction_probability_bounds_and_sum(temp_db):
    """Verify prediction probabilities must be in [0, 1] and sum to 1.0."""
    conn = sqlite3.connect(temp_db)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO customers (customer_id, customer_name, signup_date, churn) VALUES ('CUST_PRED_CHK', 'User', '2024-01-01', 0);")

    # 1. Negative probability fails
    with pytest.raises(sqlite3.IntegrityError):
        cursor.execute("""
            INSERT INTO customer_predictions (
                prediction_id, customer_id, churn_probability, retention_probability,
                predicted_churn, decision_threshold, risk_tier
            ) VALUES ('p1', 'CUST_PRED_CHK', -0.10, 1.10, 0, 0.50, 'LOW');
        """)

    # 2. Probability > 1.0 fails
    with pytest.raises(sqlite3.IntegrityError):
        cursor.execute("""
            INSERT INTO customer_predictions (
                prediction_id, customer_id, churn_probability, retention_probability,
                predicted_churn, decision_threshold, risk_tier
            ) VALUES ('p2', 'CUST_PRED_CHK', 1.50, -0.50, 1, 0.50, 'HIGH');
        """)

    # 3. Probability sum mismatch (> 0.001 error) fails
    with pytest.raises(sqlite3.IntegrityError):
        cursor.execute("""
            INSERT INTO customer_predictions (
                prediction_id, customer_id, churn_probability, retention_probability,
                predicted_churn, decision_threshold, risk_tier
            ) VALUES ('p3', 'CUST_PRED_CHK', 0.80, 0.80, 1, 0.50, 'HIGH');
        """)

    # 4. Decision threshold != 0.50 fails
    with pytest.raises(sqlite3.IntegrityError):
        cursor.execute("""
            INSERT INTO customer_predictions (
                prediction_id, customer_id, churn_probability, retention_probability,
                predicted_churn, decision_threshold, risk_tier
            ) VALUES ('p4', 'CUST_PRED_CHK', 0.40, 0.60, 0, 0.46, 'LOW');
        """)

    # 5. Valid prediction succeeds
    cursor.execute("""
        INSERT INTO customer_predictions (
            prediction_id, customer_id, churn_probability, retention_probability,
            predicted_churn, decision_threshold, risk_tier
        ) VALUES ('p5', 'CUST_PRED_CHK', 0.3756, 0.6244, 0, 0.50, 'LOW');
    """)
    conn.commit()

    conn.close()


def test_segment_cluster_and_persona_check_constraints(temp_db):
    """Verify customer_segments enforces cluster_id in [0, 4] and exact official persona names."""
    conn = sqlite3.connect(temp_db)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO customers (customer_id, customer_name, signup_date, churn) VALUES ('CUST_SEG_CHK', 'User', '2024-01-01', 0);")

    # 1. Invalid cluster_id (5) fails
    with pytest.raises(sqlite3.IntegrityError):
        cursor.execute("""
            INSERT INTO customer_segments (
                segment_record_id, customer_id, cluster_id, segment_name,
                recency_delivered_days, hist_delivered_order_count, hist_delivered_order_value_inr
            ) VALUES ('s1', 'CUST_SEG_CHK', 5, 'Champions & High-Value Loyalists', 10.0, 5, 5000.0);
        """)

    # 2. Fabricated persona name fails
    with pytest.raises(sqlite3.IntegrityError):
        cursor.execute("""
            INSERT INTO customer_segments (
                segment_record_id, customer_id, cluster_id, segment_name,
                recency_delivered_days, hist_delivered_order_count, hist_delivered_order_value_inr
            ) VALUES ('s2', 'CUST_SEG_CHK', 0, 'Super VIP Ultra Buyers', 10.0, 5, 5000.0);
        """)

    # 3. All 5 official persona names succeed
    official_personas = [
        (0, "Champions & High-Value Loyalists"),
        (1, "At-Risk / Lapsed Low-Value Customers"),
        (2, "Zero Delivered-Purchase Customers"),
        (3, "Steady Core Repeaters"),
        (4, "Recent Low-Ticket / New Promising Customers"),
    ]
    for cid, pname in official_personas:
        # Use different customer or is_current=0 to avoid partial unique violation
        cursor.execute(f"""
            INSERT INTO customer_segments (
                segment_record_id, customer_id, cluster_id, segment_name,
                recency_delivered_days, hist_delivered_order_count, hist_delivered_order_value_inr, is_current
            ) VALUES ('s_test_{cid}', 'CUST_SEG_CHK', {cid}, '{pname}', 25.0, 4, 6000.0, 0);
        """)
    conn.commit()

    conn.close()


def test_recommendation_priority_and_status_check(temp_db):
    """Verify retention_recommendations enforces priority and status enums."""
    conn = sqlite3.connect(temp_db)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO customers (customer_id, customer_name, signup_date, churn) VALUES ('CUST_REC_CHK', 'User', '2024-01-01', 0);")

    # 1. Invalid priority fails
    with pytest.raises(sqlite3.IntegrityError):
        cursor.execute("""
            INSERT INTO retention_recommendations (
                recommendation_id, customer_id, recommendation_category,
                recommendation_title, recommendation_description, evidence, priority
            ) VALUES ('r1', 'CUST_REC_CHK', 'Loyalty', 'Title', 'Desc', 'Evidence', 'URGENT');
        """)

    # 2. Invalid status fails
    with pytest.raises(sqlite3.IntegrityError):
        cursor.execute("""
            INSERT INTO retention_recommendations (
                recommendation_id, customer_id, recommendation_category,
                recommendation_title, recommendation_description, evidence, priority, recommendation_status
            ) VALUES ('r2', 'CUST_REC_CHK', 'Loyalty', 'Title', 'Desc', 'Evidence', 'HIGH', 'CANCELLED');
        """)

    conn.close()


# ==============================================================================
# SECTION 6: Nullable Fields Verification
# ==============================================================================

def test_customers_nullable_city_state(temp_db):
    """Verify customers table permits NULL city and state for intentional EDA missingness."""
    conn = sqlite3.connect(temp_db)
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO customers (customer_id, customer_name, signup_date, city, state, churn)
        VALUES ('IND_CUST_NULL_CS', 'Nameless City Customer', '2024-05-10', NULL, NULL, 1);
    """)
    conn.commit()

    cursor.execute("SELECT city, state FROM customers WHERE customer_id = 'IND_CUST_NULL_CS';")
    row = cursor.fetchone()
    assert row[0] is None
    assert row[1] is None

    conn.close()


# ==============================================================================
# SECTION 7: Performance Index Verification
# ==============================================================================

def test_performance_indexes_created(temp_db):
    """Verify all defined performance indexes exist in sqlite_master."""
    conn = sqlite3.connect(temp_db)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type = 'index';")
    index_names = {row[0] for row in cursor.fetchall()}

    expected_indexes = {
        "idx_customers_churn",
        "idx_customers_city_state",
        "idx_customers_signup_date",
        "idx_predictions_customer_timestamp",
        "idx_predictions_risk_tier",
        "idx_predictions_predicted_churn",
        "idx_segments_customer_id",
        "idx_segments_cluster_id",
        "idx_segments_is_current",
        "idx_recs_customer_id",
        "idx_recs_prediction_id",
        "idx_recs_priority_status",
        "idx_recs_category",
        "uq_current_customer_segment",
    }

    missing_indexes = expected_indexes - index_names
    assert len(missing_indexes) == 0, f"Missing indexes: {missing_indexes}"

    conn.close()
