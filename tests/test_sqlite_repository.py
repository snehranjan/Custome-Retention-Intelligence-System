"""
Indian E-Commerce Customer Retention Intelligence System
Comprehensive Unit & Integration Test Suite for SQLite Repository (Phase 7.4 Checkpoint 3)

Tests:
- Database initialization, folder creation, migration, repeated initialization, and persistence
- Customer CRUD, upsert, count, duplicate rejection, and nullable city/state handling
- ML Prediction insertion, retrieval, foreign key checks, probability bounds, and history
- RFM Segmentation insertion, update, single active segment enforcement, and history
- Retention Recommendations insertion, filtering, status transitions, and nullable prediction link
- Reliability, transactional rollback, foreign keys, multi-instance concurrency, and persistence
"""

import os
import pytest
from typing import Dict, Any

from backend.app.repositories.sqlite_repository import SQLiteRepository
from backend.app.repositories.exceptions import (
    ConstraintViolationError,
    CustomerNotFoundError,
    DatabaseUnavailableError,
    DuplicateRecordError,
    ForeignKeyViolationError,
    RepositoryError,
)

# Canonical Locked Artifact Hashes
LOCKED_RF_MODEL_HASH = "24F1F0E33C75B5590906369960DB6E5951EC95DF9AE40384DA60082B3438F301"


@pytest.fixture
def repo(tmp_path) -> SQLiteRepository:
    """Fixture providing a fresh isolated SQLiteRepository backed by a temporary file."""
    db_file = str(tmp_path / "test_isolated.db")
    return SQLiteRepository(db_path=db_file)


# ==============================================================================
# 1. INITIALIZATION & PERSISTENCE TESTS
# ==============================================================================

def test_database_creation(tmp_path):
    """Verifies that SQLiteRepository initializes and creates the database file."""
    db_file = str(tmp_path / "test_init.db")
    assert not os.path.exists(db_file)
    repo = SQLiteRepository(db_path=db_file)
    assert os.path.exists(db_file)
    health = repo.get_health_status()
    assert health["status"] == "healthy"
    assert health["is_connected"] is True


def test_directory_creation(tmp_path):
    """Verifies that parent directories are recursively created if they do not exist."""
    nested_db = str(tmp_path / "nested" / "sub_folder" / "repo.db")
    assert not os.path.exists(os.path.dirname(nested_db))
    repo = SQLiteRepository(db_path=nested_db)
    assert os.path.exists(nested_db)
    assert repo.get_customer_count() == 0


def test_schema_migration_applied(tmp_path):
    """Verifies that schema migrations are recorded upon repository creation."""
    db_file = str(tmp_path / "test_migration.db")
    repo = SQLiteRepository(db_path=db_file)
    health = repo.get_health_status()
    assert "001_initial_schema" in health["applied_migrations"]


def test_repeated_initialization_safety(tmp_path):
    """Verifies that calling initialize() repeatedly is safe and never overwrites existing records."""
    db_file = str(tmp_path / "test_repeat.db")
    repo = SQLiteRepository(db_path=db_file)
    repo.insert_customer({
        "customer_id": "IND_CUST_TEST_01",
        "customer_name": "Test Customer",
        "signup_date": "2024-01-15",
        "churn": 0,
    })
    assert repo.get_customer_count() == 1

    # Re-initialize multiple times
    repo.initialize()
    repo.initialize()

    # Verify data is fully preserved
    assert repo.get_customer_count() == 1
    cust = repo.get_customer_by_id("IND_CUST_TEST_01")
    assert cust is not None
    assert cust["customer_name"] == "Test Customer"


def test_persistence_after_reopening(tmp_path):
    """Verifies that closing and reopening the repository across instances preserves data."""
    db_file = str(tmp_path / "test_reopen.db")
    
    # Session 1: Create and write
    repo1 = SQLiteRepository(db_path=db_file)
    repo1.insert_customer({
        "customer_id": "IND_CUST_PERSIST_01",
        "customer_name": "Persistent Customer",
        "signup_date": "2024-02-01",
        "churn": 1,
    })
    del repo1

    # Session 2: Fresh instance pointing to same file
    repo2 = SQLiteRepository(db_path=db_file)
    cust = repo2.get_customer_by_id("IND_CUST_PERSIST_01")
    assert cust is not None
    assert cust["churn"] == 1
    assert cust["customer_name"] == "Persistent Customer"


# ==============================================================================
# 2. CUSTOMER OPERATIONS TESTS
# ==============================================================================

def test_insert_and_retrieve_customer(repo: SQLiteRepository):
    """Verifies inserting a customer profile and retrieving it by string customer_id."""
    data = {
        "customer_id": "IND_CUST_10001",
        "customer_name": "Aarav Sharma",
        "signup_date": "2024-03-10",
        "city": "Bengaluru",
        "state": "Karnataka",
        "churn": 0,
    }
    inserted = repo.insert_customer(data)
    assert inserted["customer_id"] == "IND_CUST_10001"

    retrieved = repo.get_customer_by_id("IND_CUST_10001")
    assert retrieved is not None
    assert retrieved["customer_id"] == "IND_CUST_10001"
    assert retrieved["customer_name"] == "Aarav Sharma"
    assert retrieved["city"] == "Bengaluru"
    assert retrieved["state"] == "Karnataka"
    assert retrieved["churn"] == 0


def test_customer_upsert(repo: SQLiteRepository):
    """Verifies that upserting updates an existing customer profile cleanly."""
    initial = {
        "customer_id": "IND_CUST_10002",
        "customer_name": "Diya Patel",
        "signup_date": "2024-01-01",
        "city": "Ahmedabad",
        "state": "Gujarat",
        "churn": 0,
    }
    repo.insert_customer(initial)

    updated = {
        "customer_id": "IND_CUST_10002",
        "customer_name": "Diya Patel Updated",
        "signup_date": "2024-01-01",
        "city": "Gandhinagar",
        "state": "Gujarat",
        "churn": 1,
    }
    repo.upsert_customer(updated)

    record = repo.get_customer_by_id("IND_CUST_10002")
    assert record["customer_name"] == "Diya Patel Updated"
    assert record["city"] == "Gandhinagar"
    assert record["churn"] == 1
    assert repo.get_customer_count() == 1


def test_customer_count_and_pagination(repo: SQLiteRepository):
    """Verifies customer counting and paginated listing."""
    for i in range(5):
        repo.insert_customer({
            "customer_id": f"IND_CUST_{20000 + i}",
            "customer_name": f"Customer {i}",
            "signup_date": "2024-01-01",
            "churn": i % 2,
        })
    assert repo.get_customer_count() == 5

    page1 = repo.list_customers(limit=3, offset=0)
    assert len(page1) == 3
    assert page1[0]["customer_id"] == "IND_CUST_20000"

    page2 = repo.list_customers(limit=3, offset=3)
    assert len(page2) == 2
    assert page2[0]["customer_id"] == "IND_CUST_20003"


def test_customer_duplicate_handling(repo: SQLiteRepository):
    """Verifies that inserting a duplicate customer_id raises DuplicateRecordError."""
    data = {
        "customer_id": "IND_CUST_DUP_01",
        "customer_name": "First Insert",
        "signup_date": "2024-01-01",
        "churn": 0,
    }
    repo.insert_customer(data)

    with pytest.raises(DuplicateRecordError):
        repo.insert_customer(data)


def test_customer_nullable_city_state(repo: SQLiteRepository):
    """Verifies that customers with None/null city and state are supported (46 EDA nulls)."""
    data = {
        "customer_id": "IND_CUST_NULL_GEO",
        "customer_name": "Missing Geo Customer",
        "signup_date": "2024-01-01",
        "city": None,
        "state": None,
        "churn": 1,
    }
    repo.insert_customer(data)
    record = repo.get_customer_by_id("IND_CUST_NULL_GEO")
    assert record is not None
    assert record["city"] is None
    assert record["state"] is None


def test_customer_invalid_churn_check(repo: SQLiteRepository):
    """Verifies that churn values other than 0 or 1 fail check constraints."""
    with pytest.raises(ConstraintViolationError):
        repo.insert_customer({
            "customer_id": "IND_CUST_BAD_CHURN",
            "customer_name": "Bad Churn",
            "signup_date": "2024-01-01",
            "churn": 5,
        })


# ==============================================================================
# 3. ML PREDICTION TESTS
# ==============================================================================

def test_insert_prediction_and_history(repo: SQLiteRepository):
    """Verifies recording ML prediction results and fetching history."""
    repo.insert_customer({
        "customer_id": "IND_CUST_PRED_01",
        "customer_name": "Prediction Target",
        "signup_date": "2024-01-01",
        "churn": 0,
    })

    # Synthetic ML test fixture satisfying probability sum = 1.0, tau = 0.50
    pred_data = {
        "customer_id": "IND_CUST_PRED_01",
        "churn_probability": 0.65000,
        "retention_probability": 0.35000,
        "predicted_churn": 1,
        "decision_threshold": 0.50,
        "risk_tier": "MODERATE",
        "model_name": "RandomForestClassifier_ConfigD",
        "model_version": "1.0.0",
        "model_hash": LOCKED_RF_MODEL_HASH,
    }
    inserted = repo.insert_prediction(pred_data)
    assert inserted["predicted_churn"] == 1

    history = repo.get_prediction_history("IND_CUST_PRED_01")
    assert len(history) == 1
    assert history[0]["churn_probability"] == pytest.approx(0.65, abs=1e-4)
    assert history[0]["risk_tier"] == "MODERATE"
    assert history[0]["model_hash"] == LOCKED_RF_MODEL_HASH

    latest = repo.get_latest_prediction("IND_CUST_PRED_01")
    assert latest is not None
    assert latest["prediction_id"] == inserted["prediction_id"]


def test_prediction_foreign_key_violation(repo: SQLiteRepository):
    """Verifies that inserting a prediction for a non-existent customer raises ForeignKeyViolationError."""
    with pytest.raises(ForeignKeyViolationError):
        repo.insert_prediction({
            "customer_id": "IND_CUST_NONEXISTENT",
            "churn_probability": 0.40,
            "retention_probability": 0.60,
            "predicted_churn": 0,
            "decision_threshold": 0.50,
            "risk_tier": "LOW",
        })


def test_prediction_probability_constraints(repo: SQLiteRepository):
    """Verifies that probability bounds and sum constraints are strictly enforced."""
    repo.insert_customer({
        "customer_id": "IND_CUST_PRED_BOUNDS",
        "customer_name": "Bounds Target",
        "signup_date": "2024-01-01",
        "churn": 0,
    })

    # Case 1: Probability exceeds 1.0
    with pytest.raises(ConstraintViolationError):
        repo.insert_prediction({
            "customer_id": "IND_CUST_PRED_BOUNDS",
            "churn_probability": 1.20,
            "retention_probability": -0.20,
            "predicted_churn": 1,
            "decision_threshold": 0.50,
            "risk_tier": "HIGH",
        })

    # Case 2: Probability sum != 1.0
    with pytest.raises(ConstraintViolationError):
        repo.insert_prediction({
            "customer_id": "IND_CUST_PRED_BOUNDS",
            "churn_probability": 0.70,
            "retention_probability": 0.70,
            "predicted_churn": 1,
            "decision_threshold": 0.50,
            "risk_tier": "HIGH",
        })

    # Case 3: Altered decision threshold != 0.50
    with pytest.raises(ConstraintViolationError):
        repo.insert_prediction({
            "customer_id": "IND_CUST_PRED_BOUNDS",
            "churn_probability": 0.60,
            "retention_probability": 0.40,
            "predicted_churn": 1,
            "decision_threshold": 0.40,  # Locked at 0.50
            "risk_tier": "MODERATE",
        })


def test_multiple_predictions_history_ordering(repo: SQLiteRepository):
    """Verifies that multiple predictions for one customer are ordered newest first."""
    repo.insert_customer({
        "customer_id": "IND_CUST_MULTI_PRED",
        "customer_name": "Multi Pred Customer",
        "signup_date": "2024-01-01",
        "churn": 0,
    })

    repo.insert_prediction({
        "customer_id": "IND_CUST_MULTI_PRED",
        "churn_probability": 0.30,
        "retention_probability": 0.70,
        "predicted_churn": 0,
        "decision_threshold": 0.50,
        "risk_tier": "LOW",
        "prediction_timestamp": "2026-01-01T10:00:00Z",
    })

    repo.insert_prediction({
        "customer_id": "IND_CUST_MULTI_PRED",
        "churn_probability": 0.85,
        "retention_probability": 0.15,
        "predicted_churn": 1,
        "decision_threshold": 0.50,
        "risk_tier": "HIGH",
        "prediction_timestamp": "2026-02-01T10:00:00Z",
    })

    history = repo.get_prediction_history("IND_CUST_MULTI_PRED")
    assert len(history) == 2
    assert history[0]["prediction_timestamp"] == "2026-02-01T10:00:00Z"
    assert history[0]["risk_tier"] == "HIGH"
    assert history[1]["risk_tier"] == "LOW"


# ==============================================================================
# 4. RFM SEGMENTATION TESTS
# ==============================================================================

def test_segment_upsert_and_active_retrieval(repo: SQLiteRepository):
    """Verifies segment assignment and retrieval of the current active persona."""
    repo.insert_customer({
        "customer_id": "IND_CUST_SEG_01",
        "customer_name": "Segment Target",
        "signup_date": "2024-01-01",
        "churn": 0,
    })

    segment_data = {
        "customer_id": "IND_CUST_SEG_01",
        "cluster_id": 0,
        "segment_name": "Champions & High-Value Loyalists",
        "recency_delivered_days": 12.5,
        "hist_delivered_order_count": 8,
        "hist_delivered_order_value_inr": 18500.0,
        "is_current": 1,
    }
    repo.upsert_customer_segment(segment_data)

    current = repo.get_current_segment("IND_CUST_SEG_01")
    assert current is not None
    assert current["cluster_id"] == 0
    assert current["segment_name"] == "Champions & High-Value Loyalists"
    assert current["is_current"] == 1


def test_segment_history_preservation_and_single_active(repo: SQLiteRepository):
    """
    Verifies that updating a customer's segment archives prior records (is_current=0)
    and enforces exactly one active segment per customer.
    """
    repo.insert_customer({
        "customer_id": "IND_CUST_SEG_HIST",
        "customer_name": "Segment Transition Customer",
        "signup_date": "2024-01-01",
        "churn": 0,
    })

    # Initial segment: Cluster 4
    repo.upsert_customer_segment({
        "customer_id": "IND_CUST_SEG_HIST",
        "cluster_id": 4,
        "segment_name": "Recent Low-Ticket / New Promising Customers",
        "recency_delivered_days": 15.0,
        "hist_delivered_order_count": 1,
        "hist_delivered_order_value_inr": 850.0,
        "is_current": 1,
    })

    # Updated segment: Cluster 3 (Customer grew into steady repeater)
    repo.upsert_customer_segment({
        "customer_id": "IND_CUST_SEG_HIST",
        "cluster_id": 3,
        "segment_name": "Steady Core Repeaters",
        "recency_delivered_days": 28.0,
        "hist_delivered_order_count": 4,
        "hist_delivered_order_value_inr": 4200.0,
        "is_current": 1,
    })

    # Active segment must be Cluster 3
    current = repo.get_current_segment("IND_CUST_SEG_HIST")
    assert current["cluster_id"] == 3
    assert current["segment_name"] == "Steady Core Repeaters"

    # History must contain both records
    history = repo.get_segment_history("IND_CUST_SEG_HIST")
    assert len(history) == 2
    active_records = [r for r in history if r["is_current"] == 1]
    archived_records = [r for r in history if r["is_current"] == 0]
    assert len(active_records) == 1
    assert len(archived_records) == 1
    assert archived_records[0]["cluster_id"] == 4


def test_segment_constraints(repo: SQLiteRepository):
    """Verifies that invalid cluster IDs or non-official persona names are rejected."""
    repo.insert_customer({
        "customer_id": "IND_CUST_BAD_SEG",
        "customer_name": "Bad Seg Customer",
        "signup_date": "2024-01-01",
        "churn": 0,
    })

    # Invalid cluster ID (5)
    with pytest.raises(ConstraintViolationError):
        repo.upsert_customer_segment({
            "customer_id": "IND_CUST_BAD_SEG",
            "cluster_id": 5,
            "segment_name": "Champions & High-Value Loyalists",
            "recency_delivered_days": 10.0,
            "hist_delivered_order_count": 2,
            "hist_delivered_order_value_inr": 1000.0,
        })

    # Invalid persona name
    with pytest.raises(ConstraintViolationError):
        repo.upsert_customer_segment({
            "customer_id": "IND_CUST_BAD_SEG",
            "cluster_id": 0,
            "segment_name": "Non-Existent Unapproved Persona",
            "recency_delivered_days": 10.0,
            "hist_delivered_order_count": 2,
            "hist_delivered_order_value_inr": 1000.0,
        })


# ==============================================================================
# 5. RETENTION RECOMMENDATIONS TESTS
# ==============================================================================

def test_insert_and_get_recommendations(repo: SQLiteRepository):
    """Verifies creating and querying retention recommendations."""
    repo.insert_customer({
        "customer_id": "IND_CUST_REC_01",
        "customer_name": "Recommendation Target",
        "signup_date": "2024-01-01",
        "churn": 1,
    })

    rec_data = {
        "customer_id": "IND_CUST_REC_01",
        "recommendation_category": "Delivery SLA Recovery",
        "recommendation_title": "Expedited Delivery Voucher",
        "recommendation_description": "Provide free priority shipping on next 2 orders.",
        "evidence": "Customer experienced 4.2 day average delivery delay.",
        "priority": "HIGH",
        "recommendation_status": "PENDING",
    }
    inserted = repo.insert_recommendation(rec_data)
    assert inserted["priority"] == "HIGH"

    recs = repo.get_recommendations("IND_CUST_REC_01")
    assert len(recs) == 1
    assert recs[0]["recommendation_title"] == "Expedited Delivery Voucher"
    assert recs[0]["prediction_id"] is None


def test_recommendation_status_update(repo: SQLiteRepository):
    """Verifies updating the status of a recommendation."""
    repo.insert_customer({
        "customer_id": "IND_CUST_REC_02",
        "customer_name": "Status Update Target",
        "signup_date": "2024-01-01",
        "churn": 0,
    })

    rec = repo.insert_recommendation({
        "customer_id": "IND_CUST_REC_02",
        "recommendation_category": "Loyalty",
        "recommendation_title": "VIP Cashback Incentive",
        "priority": "MEDIUM",
        "recommendation_status": "PENDING",
    })

    # Update to APPLIED
    updated = repo.update_recommendation_status(rec["recommendation_id"], "APPLIED")
    assert updated is not None
    assert updated["recommendation_status"] == "APPLIED"

    # Query filtered by status
    pending = repo.get_recommendations("IND_CUST_REC_02", status="PENDING")
    applied = repo.get_recommendations("IND_CUST_REC_02", status="APPLIED")
    assert len(pending) == 0
    assert len(applied) == 1

    # Invalid status raises ConstraintViolationError
    with pytest.raises(ConstraintViolationError):
        repo.update_recommendation_status(rec["recommendation_id"], "INVALID_STATUS")


def test_recommendation_with_prediction_foreign_key(repo: SQLiteRepository):
    """Verifies recommendation linked to an existing prediction, and FK check on missing prediction."""
    repo.insert_customer({
        "customer_id": "IND_CUST_REC_FK",
        "customer_name": "Prediction Link Customer",
        "signup_date": "2024-01-01",
        "churn": 0,
    })

    pred = repo.insert_prediction({
        "customer_id": "IND_CUST_REC_FK",
        "churn_probability": 0.72,
        "retention_probability": 0.28,
        "predicted_churn": 1,
        "decision_threshold": 0.50,
        "risk_tier": "HIGH",
    })

    # Linked successfully
    rec = repo.insert_recommendation({
        "customer_id": "IND_CUST_REC_FK",
        "prediction_id": pred["prediction_id"],
        "recommendation_category": "Early Intervention",
        "recommendation_title": "High Risk Immediate Retention Outreach",
        "priority": "HIGH",
    })
    assert rec["prediction_id"] == pred["prediction_id"]

    # Linking to non-existent prediction fails foreign key check
    with pytest.raises(ForeignKeyViolationError):
        repo.insert_recommendation({
            "customer_id": "IND_CUST_REC_FK",
            "prediction_id": "PRED_NONEXISTENT_999",
            "recommendation_category": "Test",
            "recommendation_title": "Will Fail",
            "priority": "LOW",
        })


# ==============================================================================
# 6. RELIABILITY, CONCURRENCY & TRANSACTION ROLLBACK TESTS
# ==============================================================================

def test_foreign_keys_enabled_every_connection(repo: SQLiteRepository):
    """Verifies that PRAGMA foreign_keys = ON is active on every connection."""
    with repo._get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("PRAGMA foreign_keys;")
        assert cursor.fetchone()[0] == 1


def test_transaction_rollback_on_failure(repo: SQLiteRepository):
    """Verifies that a failure during an operation rolls back atomically."""
    repo.insert_customer({
        "customer_id": "IND_CUST_ROLLBACK",
        "customer_name": "Rollback Test",
        "signup_date": "2024-01-01",
        "churn": 0,
    })
    initial_count = repo.get_customer_count()

    # Attempt inserting an invalid record that violates check constraint
    with pytest.raises(ConstraintViolationError):
        repo.insert_customer({
            "customer_id": "IND_CUST_INVALID_CHURN",
            "customer_name": "Should Not Be Committed",
            "signup_date": "2024-01-01",
            "churn": 99,  # Check constraint violation
        })

    # Verify no partial write occurred
    assert repo.get_customer_count() == initial_count
    assert repo.get_customer_by_id("IND_CUST_INVALID_CHURN") is None


def test_concurrent_access_multiple_instances(tmp_path):
    """Verifies safe multi-instance read/write concurrency on the same SQLite database file."""
    db_file = str(tmp_path / "shared_concurrent.db")
    
    repo_a = SQLiteRepository(db_path=db_file)
    repo_b = SQLiteRepository(db_path=db_file)

    # Instance A writes
    repo_a.insert_customer({
        "customer_id": "IND_CUST_CONC_A",
        "customer_name": "Customer Written by Instance A",
        "signup_date": "2024-01-01",
        "churn": 0,
    })

    # Instance B writes
    repo_b.insert_customer({
        "customer_id": "IND_CUST_CONC_B",
        "customer_name": "Customer Written by Instance B",
        "signup_date": "2024-01-02",
        "churn": 1,
    })

    # Both instances can read each other's data
    assert repo_a.get_customer_by_id("IND_CUST_CONC_B") is not None
    assert repo_b.get_customer_by_id("IND_CUST_CONC_A") is not None
    assert repo_a.get_customer_count() == 2
    assert repo_b.get_customer_count() == 2


def test_invalid_customer_id_handling(repo: SQLiteRepository):
    """Verifies that None or empty customer_id strings raise ConstraintViolationError."""
    with pytest.raises(ConstraintViolationError):
        repo.insert_customer({
            "customer_id": "",
            "customer_name": "Empty ID",
            "signup_date": "2024-01-01",
            "churn": 0,
        })

    with pytest.raises(ConstraintViolationError):
        repo.insert_customer({
            "customer_id": None,
            "customer_name": "None ID",
            "signup_date": "2024-01-01",
            "churn": 0,
        })
