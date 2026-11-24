"""
Indian E-Commerce Customer Retention Intelligence System
Comprehensive Unit & Integration Test Suite for ML Result Persistence (Phase 7.4 Checkpoint 6)

Tests:
1. Churn prediction persistence to customer_predictions
2. Correct probability and class mapping (tau=0.50, sum ~ 1.0)
3. Model checksum and locked pipeline metadata persistence
4. Prediction history preservation across multiple inferences
5. RFM customer segmentation persistence to customer_segments
6. Previous active segment archival (is_current=0) upon new assignment
7. Exactly one current active segment per customer invariant
8. Retention recommendation persistence to retention_recommendations
9. Duplicate recommendation prevention for existing pending actions
10. Foreign-key constraints and missing customer handling
11. Critical failure rule: inference succeeds when persistence fails
12. Target database unavailable handling
13. Strict enforcement of NO SILENT FALLBACK in Supabase mode
14. Repeated analysis idempotency
15. FastAPI endpoint /api/v1/customers/analyze with ?persist=true
16. Backward compatibility of /api/v1/customers/analyze without persistence
"""

import os
import pytest
from starlette.testclient import TestClient
from typing import Dict, Any

from backend.app.core.config import settings
from backend.app.core.dependencies import get_current_user
from backend.app.main import app
from backend.app.repositories import get_repository
from backend.app.repositories.sqlite_repository import SQLiteRepository
from backend.app.repositories.exceptions import (
    ConfigurationError,
    ConstraintViolationError,
    DatabaseUnavailableError,
    RepositoryError,
)
from backend.app.schemas.auth import AuthenticatedUser
from backend.app.schemas.ml import (
    CustomerAnalysisRequest,
    CustomerAnalysisResponse,
    RawCustomerFeatures,
)
from backend.app.services.customer_analysis_service import CustomerAnalysisService
from backend.app.services.ml_persistence_service import MLPersistenceService
from backend.app.services.model_loader import ModelLoader

# Canonical Artifact Hashes
LOCKED_RF_MODEL_HASH = "24F1F0E33C75B5590906369960DB6E5951EC95DF9AE40384DA60082B3438F301"


@pytest.fixture(autouse=True)
def override_auth():
    """Simulates an authenticated employee for ML persistence API tests."""
    app.dependency_overrides[get_current_user] = lambda: AuthenticatedUser(
        user_id="test-authorized-persistence-uuid",
        email="persistence_user@ecommerce.in",
    )
    yield
    app.dependency_overrides.pop(get_current_user, None)


@pytest.fixture(scope="module", autouse=True)
def load_models():
    """Ensure locked machine learning models are loaded."""
    ModelLoader.load_all()


@pytest.fixture
def isolated_repo(tmp_path) -> SQLiteRepository:
    """Fixture providing an isolated SQLite repository seeded with a test customer."""
    db_file = str(tmp_path / "test_persistence_isolated.db")
    repo = SQLiteRepository(db_path=db_file)
    # Seed canonical test customer
    repo.insert_customer({
        "customer_id": "IND_CUST_PERSIST_01",
        "customer_name": "Test Customer Alpha",
        "signup_date": "2024-01-15",
        "city": "Bengaluru",
        "state": "Karnataka",
        "churn": 0,
    })
    return repo


@pytest.fixture
def valid_features_dict() -> Dict[str, Any]:
    """Authoritative 43-feature input dictionary."""
    return {
        "customer_tenure_days": 365.0,
        "has_historical_orders": 1,
        "recency_days": 25.0,
        "recency_delivered_days": 25.0,
        "has_delivered_order": 1,
        "hist_order_count": 6,
        "hist_delivered_order_count": 5,
        "hist_returned_order_count": 1,
        "hist_cancelled_order_count": 0,
        "hist_total_order_value_inr": 8500.0,
        "hist_delivered_order_value_inr": 7200.0,
        "hist_total_recorded_discount_inr": 450.0,
        "hist_average_order_value_inr": 1440.0,
        "orders_last_30_days": 1,
        "orders_last_90_days": 3,
        "orders_last_180_days": 5,
        "delivered_orders_last_30_days": 1,
        "delivered_orders_last_90_days": 3,
        "delivered_orders_last_180_days": 5,
        "hist_return_rate": 0.1667,
        "hist_cancellation_rate": 0.0,
        "hist_average_delivery_delay_days": 1.2,
        "hist_delivery_delay_missing_count": 0,
        "hist_delivery_delay_missing_rate": 0.0,
        "hist_average_discount_amount_inr": 90.0,
        "hist_discounted_order_count": 3,
        "hist_discount_missing_count": 0,
        "hist_discount_missing_rate": 0.0,
        "hist_payment_missing_count": 0,
        "hist_payment_missing_rate": 0.0,
        "hist_cod_order_count": 2,
        "hist_cod_usage_rate": 0.3333,
        "hist_upi_order_count": 3,
        "hist_upi_usage_rate": 0.50,
        "velocity_ratio_30_90": 1.0,
        "velocity_ratio_90_180": 1.2,
        "has_orders_last_90_days": 1,
        "has_orders_last_180_days": 1,
        "delay_friction_score": 0.2,
        "missing_friction_score": 0.0,
        "city": "Bengaluru",
        "state": "Karnataka",
        "cluster_id": 3,
    }


# ==============================================================================
# 1. CHURN PREDICTION PERSISTENCE TESTS
# ==============================================================================

def test_churn_prediction_persistence(isolated_repo, valid_features_dict):
    """Verifies that actual churn model outputs are persisted to customer_predictions."""
    req = CustomerAnalysisRequest(
        customer_id="IND_CUST_PERSIST_01",
        features=RawCustomerFeatures(**valid_features_dict),
        persist_results=True,
    )
    res = CustomerAnalysisService.analyze_customer(req, repository=isolated_repo)

    assert res.persistence_status is not None
    assert res.persistence_status.prediction_persisted is True
    assert res.persistence_status.prediction_id is not None
    assert res.persistence_status.error is None

    # Retrieve from repository
    pred = isolated_repo.get_latest_prediction("IND_CUST_PERSIST_01")
    assert pred is not None
    assert pred["prediction_id"] == res.persistence_status.prediction_id
    assert pred["customer_id"] == "IND_CUST_PERSIST_01"
    assert pred["churn_probability"] == pytest.approx(res.churn_prediction.churn_probability, abs=1e-4)
    assert pred["retention_probability"] == pytest.approx(res.churn_prediction.retention_probability, abs=1e-4)
    assert pred["predicted_churn"] == res.churn_prediction.predicted_class
    assert pred["decision_threshold"] == 0.50
    assert pred["model_hash"] == LOCKED_RF_MODEL_HASH


def test_probability_and_class_mapping(isolated_repo, valid_features_dict):
    """Verifies that persisted probabilities sum to ~1.0 and match the locked threshold."""
    req = CustomerAnalysisRequest(
        customer_id="IND_CUST_PERSIST_01",
        features=RawCustomerFeatures(**valid_features_dict),
        persist_results=True,
    )
    res = CustomerAnalysisService.analyze_customer(req, repository=isolated_repo)

    pred = isolated_repo.get_latest_prediction("IND_CUST_PERSIST_01")
    prob_sum = pred["churn_probability"] + pred["retention_probability"]
    assert prob_sum == pytest.approx(1.0, abs=0.001)

    expected_class = 1 if pred["churn_probability"] >= 0.50 else 0
    assert pred["predicted_churn"] == expected_class


def test_prediction_history_preservation(isolated_repo, valid_features_dict):
    """Verifies that multiple inferences append to history without overwriting prior records."""
    req = CustomerAnalysisRequest(
        customer_id="IND_CUST_PERSIST_01",
        features=RawCustomerFeatures(**valid_features_dict),
        persist_results=True,
    )
    # Execution 1
    CustomerAnalysisService.analyze_customer(req, repository=isolated_repo)
    # Execution 2
    CustomerAnalysisService.analyze_customer(req, repository=isolated_repo)

    history = isolated_repo.get_prediction_history("IND_CUST_PERSIST_01")
    assert len(history) == 2
    assert history[0]["prediction_id"] != history[1]["prediction_id"]


# ==============================================================================
# 2. RFM CUSTOMER SEGMENTATION PERSISTENCE TESTS
# ==============================================================================

def test_segment_persistence_and_archival(isolated_repo, valid_features_dict):
    """
    Verifies that assigning a new persona archives the prior segment (is_current=0)
    and enforces exactly one active segment per customer.
    """
    # 1. Initial analysis (yields Steady Core Repeaters or similar)
    req1 = CustomerAnalysisRequest(
        customer_id="IND_CUST_PERSIST_01",
        features=RawCustomerFeatures(**valid_features_dict),
        persist_results=True,
    )
    res1 = CustomerAnalysisService.analyze_customer(req1, repository=isolated_repo)
    assert res1.persistence_status.segment_persisted is True

    curr1 = isolated_repo.get_current_segment("IND_CUST_PERSIST_01")
    assert curr1 is not None
    assert curr1["is_current"] == 1

    # 2. Second analysis with high spend features (yields Champions)
    champ_features = dict(valid_features_dict)
    champ_features["hist_delivered_order_value_inr"] = 35000.0
    champ_features["hist_delivered_order_count"] = 15
    champ_features["recency_delivered_days"] = 5.0

    req2 = CustomerAnalysisRequest(
        customer_id="IND_CUST_PERSIST_01",
        features=RawCustomerFeatures(**champ_features),
        persist_results=True,
    )
    res2 = CustomerAnalysisService.analyze_customer(req2, repository=isolated_repo)
    assert res2.persistence_status.segment_persisted is True

    # Active segment must be updated
    curr2 = isolated_repo.get_current_segment("IND_CUST_PERSIST_01")
    assert curr2["is_current"] == 1
    assert curr2["segment_record_id"] != curr1["segment_record_id"]

    # History must preserve both records with exactly one active
    history = isolated_repo.get_segment_history("IND_CUST_PERSIST_01")
    assert len(history) == 2
    active_segments = [s for s in history if s["is_current"] == 1]
    archived_segments = [s for s in history if s["is_current"] == 0]
    assert len(active_segments) == 1
    assert len(archived_segments) == 1


# ==============================================================================
# 3. RETENTION RECOMMENDATIONS PERSISTENCE & DEDUPLICATION TESTS
# ==============================================================================

def test_retention_recommendations_persistence_and_deduplication(isolated_repo, valid_features_dict):
    """
    Verifies that rule-based recommendations are stored, linked to prediction_id,
    and deduplicated across repeated evaluations.
    """
    req = CustomerAnalysisRequest(
        customer_id="IND_CUST_PERSIST_01",
        features=RawCustomerFeatures(**valid_features_dict),
        persist_results=True,
    )
    # Execution 1
    res1 = CustomerAnalysisService.analyze_customer(req, repository=isolated_repo)
    assert res1.persistence_status.recommendations_persisted is True
    initial_rec_count = len(res1.persistence_status.recommendation_ids)
    assert initial_rec_count > 0

    recs_in_db = isolated_repo.get_recommendations("IND_CUST_PERSIST_01", status="PENDING")
    assert len(recs_in_db) == initial_rec_count
    assert recs_in_db[0]["prediction_id"] == res1.persistence_status.prediction_id

    # Execution 2: Repeated analysis of same customer should not spam duplicate pending recommendations
    res2 = CustomerAnalysisService.analyze_customer(req, repository=isolated_repo)
    assert res2.persistence_status.recommendations_persisted is True
    # Duplicate pending recommendations were cleanly bypassed
    assert len(res2.persistence_status.recommendation_ids) == 0

    # Total pending recommendations in DB remains unchanged
    recs_after = isolated_repo.get_recommendations("IND_CUST_PERSIST_01", status="PENDING")
    assert len(recs_after) == initial_rec_count


# ==============================================================================
# 4. FAILURE ISOLATION & CRITICAL FAILURE RULE TESTS
# ==============================================================================

def test_foreign_key_missing_customer_handling(isolated_repo, valid_features_dict):
    """
    CRITICAL FAILURE RULE:
    When an un-seeded customer_id is analyzed with persist=True,
    ML inference MUST succeed, while persistence_status accurately reports the error.
    """
    req = CustomerAnalysisRequest(
        customer_id="IND_CUST_UNKNOWN_9999",
        features=RawCustomerFeatures(**valid_features_dict),
        persist_results=True,
    )
    res = CustomerAnalysisService.analyze_customer(req, repository=isolated_repo)

    # 1. Genuine ML inference succeeded
    assert res.churn_prediction.churn_probability is not None
    assert res.segmentation.cluster_id is not None
    assert res.retention_recommendations.total_recommendations > 0

    # 2. Persistence status accurately reports failure
    assert res.persistence_status is not None
    assert res.persistence_status.prediction_persisted is False
    assert "does not exist in the database" in res.persistence_status.error


def test_missing_customer_id_with_persist_flag(isolated_repo, valid_features_dict):
    """Verifies that requesting persistence without a customer_id reports clear status."""
    req = CustomerAnalysisRequest(
        customer_id=None,
        features=RawCustomerFeatures(**valid_features_dict),
        persist_results=True,
    )
    res = CustomerAnalysisService.analyze_customer(req, repository=isolated_repo)

    assert res.churn_prediction is not None
    assert res.persistence_status is not None
    assert res.persistence_status.prediction_persisted is False
    assert "customer_id must be provided" in res.persistence_status.error


def test_inference_success_with_simulated_db_crash(isolated_repo, valid_features_dict, monkeypatch):
    """
    Verifies that a mid-flight database error is caught, reported in persistence_status.error,
    and does NOT crash the inference response.
    """
    def mock_insert_prediction(*args, **kwargs):
        raise RepositoryError("Simulated storage write error")

    monkeypatch.setattr(isolated_repo, "insert_prediction", mock_insert_prediction)

    req = CustomerAnalysisRequest(
        customer_id="IND_CUST_PERSIST_01",
        features=RawCustomerFeatures(**valid_features_dict),
        persist_results=True,
    )
    res = CustomerAnalysisService.analyze_customer(req, repository=isolated_repo)

    # Inference intact
    assert res.churn_prediction is not None
    # Persistence failure accurately reported
    assert res.persistence_status.prediction_persisted is False
    assert "Simulated storage write error" in res.persistence_status.error


def test_no_silent_fallback_in_supabase_mode(monkeypatch, valid_features_dict):
    """
    Verifies that under STORAGE_MODE='supabase', missing credentials cause an immediate
    fatal exception and do NOT silently write to local SQLite.
    """
    monkeypatch.setattr(settings, "STORAGE_MODE", "supabase")
    monkeypatch.setattr(settings, "SUPABASE_SECRET_KEY", None)
    monkeypatch.setattr(settings, "SUPABASE_SERVICE_ROLE_KEY", None)
    monkeypatch.setattr(settings, "SUPABASE_PUBLISHABLE_KEY", None)

    req = CustomerAnalysisRequest(
        customer_id="IND_CUST_PERSIST_01",
        features=RawCustomerFeatures(**valid_features_dict),
        persist_results=True,
    )
    with pytest.raises(ConfigurationError):
        CustomerAnalysisService.analyze_customer(req)


# ==============================================================================
# 5. FASTAPI ROUTE INTEGRATION TESTS
# ==============================================================================

def test_api_customers_analyze_with_persist_param(isolated_repo, valid_features_dict, monkeypatch):
    """Verifies that POST /api/v1/customers/analyze?persist=true persists results."""
    monkeypatch.setattr("backend.app.services.ml_persistence_service.get_repository", lambda: isolated_repo)
    with TestClient(app) as client:
        payload = {
            "customer_id": "IND_CUST_PERSIST_01",
            "features": valid_features_dict,
            "persist_results": False,  # Will be overridden by ?persist=true query param
        }
        response = client.post("/api/v1/customers/analyze?persist=true", json=payload)
        assert response.status_code == 200

        data = response.json()["data"]
        assert data["persistence_status"] is not None
        assert data["persistence_status"]["prediction_persisted"] is True
        assert data["persistence_status"]["segment_persisted"] is True


def test_api_customers_analyze_without_persist_backward_compatibility(valid_features_dict):
    """Verifies backward compatibility: without persist flag, persistence_status is None."""
    with TestClient(app) as client:
        payload = {
            "customer_id": "IND_CUST_PERSIST_01",
            "features": valid_features_dict,
        }
        response = client.post("/api/v1/customers/analyze", json=payload)
        assert response.status_code == 200

        data = response.json()["data"]
        assert data["persistence_status"] is None

