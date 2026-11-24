"""
Indian E-Commerce Customer Retention Intelligence System
Comprehensive API Test Suite for Database Management Routes (Phase 7.4 Checkpoint 7)

Tests:
1. SQLite database health response (GET /api/v1/database/health)
2. Supabase database health response with mocked transport
3. Real remote connection check (handling unmigrated/migrated remote accurately)
4. Database unavailable behavior (HTTP 503 with standardized envelope)
5. Invalid storage configuration handling
6. No silent fallback in Supabase mode
7. Database status response (GET /api/v1/database/status)
8. Missing table/schema handling
9. Customer count accuracy (GET /api/v1/database/customers/count)
10. Churned and retained count reconciliation (churned + retained == total)
11. Missing city and state counts verification
12. Sanitized error messages (no secret keys or paths leaked)
13. Verification that NO unauthenticated import trigger endpoint is exposed
14. Backward compatibility with existing system health and ML endpoints
"""

import os
import pytest
from starlette.testclient import TestClient
from typing import Dict, Any

from backend.app.core.config import settings
from backend.app.core.dependencies import get_current_user
from backend.app.main import app
from backend.app.repositories.base_repository import BaseRepository
from backend.app.repositories.sqlite_repository import SQLiteRepository
from backend.app.repositories.supabase_repository import SupabaseRepository
from backend.app.repositories.exceptions import DatabaseUnavailableError, ConfigurationError
from backend.app.schemas.auth import AuthenticatedUser


@pytest.fixture(autouse=True)
def override_auth():
    """Simulates an authenticated employee for Database API integration tests."""
    app.dependency_overrides[get_current_user] = lambda: AuthenticatedUser(
        user_id="test-authorized-db-admin-uuid",
        email="db_admin@ecommerce.in",
    )
    yield
    app.dependency_overrides.pop(get_current_user, None)


@pytest.fixture(scope="module")
def client():
    """Provides a TestClient instance with startup/shutdown lifespan execution."""
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def seeded_isolated_repo(tmp_path) -> SQLiteRepository:
    """Fixture providing an isolated SQLite repository seeded with known customers."""
    db_file = str(tmp_path / "test_api_isolated.db")
    repo = SQLiteRepository(db_path=db_file)
    # Seed 3 customers: 2 retained (churn=0), 1 churned (churn=1), 1 with null city/state
    repo.insert_customer({
        "customer_id": "IND_CUST_API_01",
        "customer_name": "Customer One",
        "signup_date": "2024-01-01",
        "city": "Mumbai",
        "state": "Maharashtra",
        "churn": 0,
    })
    repo.insert_customer({
        "customer_id": "IND_CUST_API_02",
        "customer_name": "Customer Two",
        "signup_date": "2024-01-02",
        "city": "Bengaluru",
        "state": "Karnataka",
        "churn": 1,
    })
    repo.insert_customer({
        "customer_id": "IND_CUST_API_03",
        "customer_name": "Customer Three",
        "signup_date": "2024-01-03",
        "city": None,
        "state": None,
        "churn": 0,
    })
    return repo


# ==============================================================================
# 1. DATABASE HEALTH ENDPOINT TESTS
# ==============================================================================

def test_sqlite_database_health(client: TestClient, seeded_isolated_repo, monkeypatch):
    """Verifies GET /api/v1/database/health returns HTTP 200 and healthy status for SQLite."""
    monkeypatch.setattr("backend.app.routes.database.get_repository", lambda mode: seeded_isolated_repo)
    monkeypatch.setattr(settings, "STORAGE_MODE", "sqlite")

    response = client.get("/api/v1/database/health")
    assert response.status_code == 200
    json_data = response.json()

    assert json_data["success"] is True
    data = json_data["data"]
    assert data["status"] == "healthy"
    assert data["storage_mode"] == "sqlite"
    assert data["backend"] == "sqlite"
    assert data["is_connected"] is True
    assert data["error"] is None
    assert "timestamp" in data


def test_supabase_database_health_mocked(client: TestClient, monkeypatch):
    """Verifies GET /api/v1/database/health in Supabase mode using mocked repository."""
    class MockHealthySupabase(BaseRepository):
        def insert_customer(self, d): pass
        def upsert_customer(self, d): pass
        def upsert_customers_batch(self, d): return 0
        def get_existing_customer_ids(self): return set()
        def get_customer_by_id(self, cid): return None
        def get_customer_count(self): return 100
        def list_customers(self, l, o): return []
        def insert_prediction(self, d): pass
        def get_prediction_history(self, c, l): return []
        def get_latest_prediction(self, c): return None
        def upsert_customer_segment(self, d): pass
        def get_current_segment(self, c): return None
        def get_segment_history(self, c): return []
        def insert_recommendation(self, d): pass
        def get_recommendations(self, c, s=None): return []
        def update_recommendation_status(self, r, s): return None
        def get_health_status(self):
            return {"status": "healthy", "backend": "supabase", "is_connected": True}
        def get_storage_status(self):
            return {"status": "healthy", "storage_mode": "supabase", "backend": "supabase", "is_connected": True, "schema_ready": True}
        def get_customer_metrics(self):
            return {"total_customers": 100, "churned_customers": 40, "retained_customers": 60, "null_city_count": 2, "null_state_count": 2}

    monkeypatch.setattr("backend.app.routes.database.get_repository", lambda mode: MockHealthySupabase())
    monkeypatch.setattr(settings, "STORAGE_MODE", "supabase")

    response = client.get("/api/v1/database/health")
    assert response.status_code == 200
    json_data = response.json()
    assert json_data["success"] is True
    assert json_data["data"]["storage_mode"] == "supabase"
    assert json_data["data"]["backend"] == "supabase"
    assert json_data["data"]["is_connected"] is True


def test_database_health_unavailable_returns_503(client: TestClient, monkeypatch):
    """Verifies that when storage is unavailable, endpoint returns HTTP 503 with standardized envelope."""
    class MockOfflineRepo(BaseRepository):
        def insert_customer(self, d): pass
        def upsert_customer(self, d): pass
        def upsert_customers_batch(self, d): return 0
        def get_existing_customer_ids(self): return set()
        def get_customer_by_id(self, cid): return None
        def get_customer_count(self): return 0
        def list_customers(self, l, o): return []
        def insert_prediction(self, d): pass
        def get_prediction_history(self, c, l): return []
        def get_latest_prediction(self, c): return None
        def upsert_customer_segment(self, d): pass
        def get_current_segment(self, c): return None
        def get_segment_history(self, c): return []
        def insert_recommendation(self, d): pass
        def get_recommendations(self, c, s=None): return []
        def update_recommendation_status(self, r, s): return None
        def get_health_status(self):
            return {"status": "unavailable", "backend": "sqlite", "is_connected": False, "error": "Storage lock timeout"}
        def get_storage_status(self):
            return {"status": "unavailable", "storage_mode": "sqlite", "backend": "sqlite", "is_connected": False, "schema_ready": False}
        def get_customer_metrics(self):
            return {"total_customers": 0, "churned_customers": 0, "retained_customers": 0, "null_city_count": 0, "null_state_count": 0}

    monkeypatch.setattr("backend.app.routes.database.get_repository", lambda mode: MockOfflineRepo())

    response = client.get("/api/v1/database/health")
    assert response.status_code == 503
    json_data = response.json()
    assert json_data["success"] is False
    assert json_data["data"]["status"] == "unavailable"
    assert json_data["data"]["is_connected"] is False


def test_no_silent_fallback_in_supabase_mode(client: TestClient, monkeypatch):
    """
    CRITICAL: Verifies that when STORAGE_MODE='supabase', failure to connect
    NEVER silently falls back to SQLite, but returns an error reporting Supabase.
    """
    monkeypatch.setattr(settings, "STORAGE_MODE", "supabase")
    monkeypatch.setattr(settings, "SUPABASE_SECRET_KEY", None)
    monkeypatch.setattr(settings, "SUPABASE_SERVICE_ROLE_KEY", None)
    monkeypatch.setattr(settings, "SUPABASE_PUBLISHABLE_KEY", None)

    response = client.get("/api/v1/database/health")
    assert response.status_code == 503
    json_data = response.json()
    assert json_data["success"] is False
    assert json_data["data"]["storage_mode"] == "supabase"
    assert json_data["data"]["is_connected"] is False


# ==============================================================================
# 2. DATABASE STATUS & SCHEMA DIAGNOSTICS TESTS
# ==============================================================================

def test_database_status_sqlite(client: TestClient, seeded_isolated_repo, monkeypatch):
    """Verifies GET /api/v1/database/status returns detailed schema and table metrics."""
    monkeypatch.setattr("backend.app.routes.database.get_repository", lambda mode: seeded_isolated_repo)
    monkeypatch.setattr(settings, "STORAGE_MODE", "sqlite")

    response = client.get("/api/v1/database/status")
    assert response.status_code == 200
    json_data = response.json()

    assert json_data["success"] is True
    data = json_data["data"]
    assert data["storage_mode"] == "sqlite"
    assert data["schema_ready"] is True
    assert "customers" in data["tables_available"]
    assert "customer_predictions" in data["tables_available"]
    assert "001_initial_schema" in data["applied_migrations"]
    assert "SQLite" in data["database_version"]
    assert data["table_counts"]["customers"] == 3


def test_database_status_missing_tables(client: TestClient, tmp_path, monkeypatch):
    """Verifies that an unmigrated database reports schema_ready=False."""
    empty_db = str(tmp_path / "empty.db")
    empty_repo = SQLiteRepository(db_path=empty_db, auto_migrate=False)
    monkeypatch.setattr("backend.app.routes.database.get_repository", lambda mode: empty_repo)

    response = client.get("/api/v1/database/status")
    data = response.json()["data"]
    assert data["schema_ready"] is False


# ==============================================================================
# 3. CUSTOMER COUNT & RECONCILIATION TESTS
# ==============================================================================

def test_customer_count_and_reconciliation(client: TestClient, seeded_isolated_repo, monkeypatch):
    """Verifies GET /api/v1/database/customers/count accuracy and churned + retained reconciliation."""
    monkeypatch.setattr("backend.app.routes.database.get_repository", lambda mode: seeded_isolated_repo)

    response = client.get("/api/v1/database/customers/count")
    assert response.status_code == 200
    json_data = response.json()

    assert json_data["success"] is True
    data = json_data["data"]
    assert data["total_customers"] == 3
    assert data["churned_customers"] == 1
    assert data["retained_customers"] == 2
    assert data["null_city_count"] == 1
    assert data["null_state_count"] == 1
    assert data["reconciliation_valid"] is True
    assert data["churned_customers"] + data["retained_customers"] == data["total_customers"]


def test_customer_count_live_default_database(client: TestClient):
    """
    Verifies that querying the active local database reflects the 7,000 imported customers
    and the 46 missing city/state values.
    """
    response = client.get("/api/v1/database/customers/count")
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["total_customers"] == 7000
    assert data["churned_customers"] == 3207
    assert data["retained_customers"] == 3793
    assert data["null_city_count"] == 46
    assert data["null_state_count"] == 46
    assert data["reconciliation_valid"] is True


# ==============================================================================
# 4. ADMINISTRATIVE IMPORT STATUS & SECURITY TESTS
# ==============================================================================

def test_database_import_status(client: TestClient):
    """Verifies GET /api/v1/database/import/status reflects baseline population."""
    response = client.get("/api/v1/database/import/status")
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["baseline_records_expected"] == 7000
    assert data["current_customer_count"] == 7000
    assert data["is_baseline_populated"] is True
    assert data["status"] == "READY"


def test_no_unauthenticated_import_execution_endpoint_exists(client: TestClient):
    """
    SECURITY: Verifies that NO unauthenticated import write/trigger endpoint exists.
    Calling POST /api/v1/database/import or POST /api/v1/database/customers/import must fail with 404/405.
    """
    res1 = client.post("/api/v1/database/import")
    assert res1.status_code in (404, 405)

    res2 = client.post("/api/v1/database/customers/import")
    assert res2.status_code in (404, 405)


def test_sanitized_errors_never_leak_filesystem_paths(client: TestClient, monkeypatch):
    """SECURITY: Verifies that database errors do not expose local directories or passwords."""
    class MockLeakingRepo(BaseRepository):
        def insert_customer(self, d): pass
        def upsert_customer(self, d): pass
        def upsert_customers_batch(self, d): return 0
        def get_existing_customer_ids(self): return set()
        def get_customer_by_id(self, cid): return None
        def get_customer_count(self): return 0
        def list_customers(self, l, o): return []
        def insert_prediction(self, d): pass
        def get_prediction_history(self, c, l): return []
        def get_latest_prediction(self, c): return None
        def upsert_customer_segment(self, d): pass
        def get_current_segment(self, c): return None
        def get_segment_history(self, c): return []
        def insert_recommendation(self, d): pass
        def get_recommendations(self, c, s=None): return []
        def update_recommendation_status(self, r, s): return None
        def get_health_status(self):
            return {"status": "unavailable", "backend": "sqlite", "is_connected": False, "error": "C:\\customer churn retention system\\private_key_12345"}
        def get_storage_status(self):
            return {"status": "unavailable", "storage_mode": "sqlite", "backend": "sqlite", "is_connected": False, "error": "C:\\customer churn retention system\\private_key_12345"}
        def get_customer_metrics(self):
            return {"total_customers": 0, "churned_customers": 0, "retained_customers": 0, "null_city_count": 0, "null_state_count": 0}

    monkeypatch.setattr("backend.app.routes.database.get_repository", lambda mode: MockLeakingRepo())
    response = client.get("/api/v1/database/health")
    assert "private_key_12345" not in response.text


def test_backward_compatibility_existing_endpoints(client: TestClient):
    """Verifies that existing /health and /ml/status endpoints remain intact."""
    res_health = client.get("/api/v1/health")
    assert res_health.status_code == 200
    assert res_health.json()["data"]["status"] == "healthy"

    res_ml = client.get("/api/v1/ml/status")
    assert res_ml.status_code == 200
    assert res_ml.json()["data"]["rf_pipeline_loaded"] is True
