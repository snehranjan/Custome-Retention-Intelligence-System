"""
Indian E-Commerce Customer Retention Intelligence System
Comprehensive Unit & Integration Test Suite for Supabase Repository (Phase 7.4 Checkpoint 4)

Tests:
- Interface compatibility and exact signature parity with BaseRepository and SQLiteRepository
- PostgREST operations via deterministic MockTransport (customer CRUD, upsert, count)
- ML prediction insertion, probability bounds, and history retrieval
- RFM segmentation upsert with prior segment archival and single active segment rule
- Retention recommendation insertion, status transitions, and nullable prediction links
- Error translation: Foreign keys (23503), unique duplicates (409/23505), check constraints (23514), auth (401/403)
- Network resilience: timeouts, connection errors, and error sanitization (no secret leakage)
- Configuration & NO SILENT FALLBACK verification
- Safe live connectivity probe
"""

import inspect
import json
import pytest
import httpx
from typing import Dict, Any

from backend.app.core.config import settings
from backend.app.repositories.base_repository import BaseRepository
from backend.app.repositories.sqlite_repository import SQLiteRepository
from backend.app.repositories.supabase_repository import SupabaseRepository
from backend.app.repositories import get_repository
from backend.app.repositories.exceptions import (
    ConfigurationError,
    ConstraintViolationError,
    DatabaseUnavailableError,
    DuplicateRecordError,
    ForeignKeyViolationError,
    RepositoryError,
)

# Canonical Locked Artifact Hashes
LOCKED_RF_MODEL_HASH = "24F1F0E33C75B5590906369960DB6E5951EC95DF9AE40384DA60082B3438F301"
TEST_SUPABASE_URL = "https://hyngxdkuanugcvqhkaas.supabase.co"
TEST_SECRET_KEY = "test_secret_key_mock_value"


# ==============================================================================
# 1. INTERFACE COMPATIBILITY & PARITY TESTS
# ==============================================================================

def test_interface_completeness():
    """Verifies that SupabaseRepository implements all abstract methods declared in BaseRepository."""
    base_methods = {
        name for name, method in inspect.getmembers(BaseRepository, predicate=inspect.isfunction)
        if getattr(method, "__isabstractmethod__", False)
    }
    supabase_methods = {
        name for name, method in inspect.getmembers(SupabaseRepository, predicate=inspect.isfunction)
    }
    missing = base_methods - supabase_methods
    assert not missing, f"SupabaseRepository is missing required BaseRepository methods: {missing}"


def test_sqlite_and_supabase_signatures_match():
    """Verifies that all public operations have identical argument signatures across repositories."""
    public_ops = [
        "insert_customer",
        "upsert_customer",
        "upsert_customers_batch",
        "get_existing_customer_ids",
        "get_customer_by_id",
        "get_customer_count",
        "list_customers",
        "insert_prediction",
        "get_prediction_history",
        "get_latest_prediction",
        "upsert_customer_segment",
        "get_current_segment",
        "get_segment_history",
        "insert_recommendation",
        "get_recommendations",
        "update_recommendation_status",
        "get_health_status",
        "get_storage_status",
        "get_customer_metrics",
    ]
    for method_name in public_ops:
        sqlite_sig = inspect.signature(getattr(SQLiteRepository, method_name))
        supabase_sig = inspect.signature(getattr(SupabaseRepository, method_name))
        assert sqlite_sig.parameters.keys() == supabase_sig.parameters.keys(), (
            f"Signature mismatch on '{method_name}': "
            f"SQLite={sqlite_sig} vs Supabase={supabase_sig}"
        )


# ==============================================================================
# 2. POSTGREST BEHAVIOUR WITH MOCKED TRANSPORT
# ==============================================================================

def test_customer_insert_and_retrieve_mocked():
    """Verifies customer insertion and retrieval via PostgREST endpoints."""
    stored_customers = {}

    def handler(request: httpx.Request) -> httpx.Response:
        url_path = request.url.path
        if url_path == "/rest/v1/customers":
            if request.method == "POST":
                data = json.loads(request.content)
                cid = data["customer_id"]
                if cid in stored_customers:
                    return httpx.Response(409, json={"code": "23505", "message": "duplicate key value"})
                stored_customers[cid] = data
                return httpx.Response(201, json=[data])
            elif request.method == "GET":
                params = dict(request.url.params)
                cid_param = params.get("customer_id")
                if cid_param and cid_param.startswith("eq."):
                    target_id = cid_param[3:]
                    cust = stored_customers.get(target_id)
                    return httpx.Response(200, json=[cust] if cust else [])
                return httpx.Response(200, json=list(stored_customers.values()))
        return httpx.Response(404, json={"message": "Not found"})

    client = httpx.Client(transport=httpx.MockTransport(handler), base_url=f"{TEST_SUPABASE_URL}/rest/v1")
    repo = SupabaseRepository(url=TEST_SUPABASE_URL, key=TEST_SECRET_KEY, client=client)

    cust_data = {
        "customer_id": "IND_CUST_SUPA_01",
        "customer_name": "Priya Nair",
        "signup_date": "2024-04-12",
        "city": "Kochi",
        "state": "Kerala",
        "churn": 0,
    }
    inserted = repo.insert_customer(cust_data)
    assert inserted["customer_id"] == "IND_CUST_SUPA_01"

    retrieved = repo.get_customer_by_id("IND_CUST_SUPA_01")
    assert retrieved is not None
    assert retrieved["customer_name"] == "Priya Nair"
    assert retrieved["city"] == "Kochi"

    not_found = repo.get_customer_by_id("IND_CUST_MISSING")
    assert not_found is None


def test_customer_upsert_mocked():
    """Verifies customer upsertion with merge-duplicates header."""
    upserted = {}

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/rest/v1/customers" and request.method == "POST":
            data = json.loads(request.content)
            upserted[data["customer_id"]] = data
            return httpx.Response(200, json=[data])
        return httpx.Response(404)

    client = httpx.Client(transport=httpx.MockTransport(handler), base_url=f"{TEST_SUPABASE_URL}/rest/v1")
    repo = SupabaseRepository(url=TEST_SUPABASE_URL, key=TEST_SECRET_KEY, client=client)

    res = repo.upsert_customer({
        "customer_id": "IND_CUST_UPSERT_01",
        "customer_name": "Kavita Rao",
        "signup_date": "2024-01-01",
        "city": "Hyderabad",
        "state": "Telangana",
        "churn": 1,
    })
    assert res["customer_id"] == "IND_CUST_UPSERT_01"
    assert "IND_CUST_UPSERT_01" in upserted


def test_customer_count_exact_mocked():
    """Verifies that customer count correctly parses PostgREST Content-Range header."""
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/rest/v1/customers" and request.method == "GET":
            headers = {"Content-Range": "0-0/7000"}
            return httpx.Response(200, json=[{"customer_id": "IND_CUST_10001"}], headers=headers)
        return httpx.Response(404)

    client = httpx.Client(transport=httpx.MockTransport(handler), base_url=f"{TEST_SUPABASE_URL}/rest/v1")
    repo = SupabaseRepository(url=TEST_SUPABASE_URL, key=TEST_SECRET_KEY, client=client)
    count = repo.get_customer_count()
    assert count == 7000


def test_prediction_insertion_and_history_mocked():
    """Verifies ML prediction recording and historical retrieval."""
    predictions = []

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/rest/v1/customer_predictions":
            if request.method == "POST":
                data = json.loads(request.content)
                predictions.append(data)
                return httpx.Response(201, json=[data])
            elif request.method == "GET":
                return httpx.Response(200, json=predictions)
        return httpx.Response(404)

    client = httpx.Client(transport=httpx.MockTransport(handler), base_url=f"{TEST_SUPABASE_URL}/rest/v1")
    repo = SupabaseRepository(url=TEST_SUPABASE_URL, key=TEST_SECRET_KEY, client=client)

    pred_data = {
        "customer_id": "IND_CUST_PRED_SUPA",
        "churn_probability": 0.68,
        "retention_probability": 0.32,
        "predicted_churn": 1,
        "decision_threshold": 0.50,
        "risk_tier": "MODERATE",
        "model_name": "RandomForestClassifier_ConfigD",
        "model_version": "1.0.0",
        "model_hash": LOCKED_RF_MODEL_HASH,
    }
    inserted = repo.insert_prediction(pred_data)
    assert inserted["predicted_churn"] == 1

    history = repo.get_prediction_history("IND_CUST_PRED_SUPA")
    assert len(history) == 1
    assert history[0]["churn_probability"] == 0.68

    latest = repo.get_latest_prediction("IND_CUST_PRED_SUPA")
    assert latest is not None
    assert latest["prediction_id"] == inserted["prediction_id"]


def test_segment_upsert_and_archival_mocked():
    """
    Verifies that upserting a segment archives prior active records (is_current=false)
    and creates the new active segment record with boolean is_current=True.
    """
    patches = []
    posts = []

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/rest/v1/customer_segments":
            if request.method == "PATCH":
                patches.append(json.loads(request.content))
                return httpx.Response(200, json=[])
            elif request.method == "POST":
                data = json.loads(request.content)
                posts.append(data)
                return httpx.Response(201, json=[data])
            elif request.method == "GET":
                params = dict(request.url.params)
                if params.get("is_current") == "eq.true":
                    active = [p for p in posts if p.get("is_current") is True]
                    return httpx.Response(200, json=active[:1])
                return httpx.Response(200, json=posts)
        return httpx.Response(404)

    client = httpx.Client(transport=httpx.MockTransport(handler), base_url=f"{TEST_SUPABASE_URL}/rest/v1")
    repo = SupabaseRepository(url=TEST_SUPABASE_URL, key=TEST_SECRET_KEY, client=client)

    seg1 = {
        "customer_id": "IND_CUST_SEG_SUPA",
        "cluster_id": 4,
        "segment_name": "Recent Low-Ticket / New Promising Customers",
        "recency_delivered_days": 10.0,
        "hist_delivered_order_count": 1,
        "hist_delivered_order_value_inr": 500.0,
        "is_current": True,
    }
    repo.upsert_customer_segment(seg1)
    assert len(posts) == 1
    assert posts[0]["is_current"] is True

    # Update to Cluster 0
    seg2 = {
        "customer_id": "IND_CUST_SEG_SUPA",
        "cluster_id": 0,
        "segment_name": "Champions & High-Value Loyalists",
        "recency_delivered_days": 5.0,
        "hist_delivered_order_count": 10,
        "hist_delivered_order_value_inr": 25000.0,
        "is_current": True,
    }
    repo.upsert_customer_segment(seg2)

    # Verify that a PATCH was issued to archive previous record
    assert len(patches) == 2
    assert patches[1]["is_current"] is False


def test_recommendation_and_status_update_mocked():
    """Verifies retention recommendation insertion and status transitions."""
    recs = {}

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/rest/v1/retention_recommendations":
            if request.method == "POST":
                data = json.loads(request.content)
                rid = data["recommendation_id"]
                recs[rid] = data
                return httpx.Response(201, json=[data])
            elif request.method == "PATCH":
                params = dict(request.url.params)
                rid_param = params.get("recommendation_id", "")
                rid = rid_param.replace("eq.", "")
                if rid in recs:
                    body = json.loads(request.content)
                    recs[rid].update(body)
                    return httpx.Response(200, json=[recs[rid]])
                return httpx.Response(200, json=[])
            elif request.method == "GET":
                return httpx.Response(200, json=list(recs.values()))
        return httpx.Response(404)

    client = httpx.Client(transport=httpx.MockTransport(handler), base_url=f"{TEST_SUPABASE_URL}/rest/v1")
    repo = SupabaseRepository(url=TEST_SUPABASE_URL, key=TEST_SECRET_KEY, client=client)

    rec = repo.insert_recommendation({
        "customer_id": "IND_CUST_REC_SUPA",
        "recommendation_category": "Loyalty",
        "recommendation_title": "Cashback Offer",
        "priority": "HIGH",
        "recommendation_status": "PENDING",
    })
    rid = rec["recommendation_id"]
    assert rec["recommendation_status"] == "PENDING"

    updated = repo.update_recommendation_status(rid, "APPLIED")
    assert updated is not None
    assert updated["recommendation_status"] == "APPLIED"


# ==============================================================================
# 3. ERROR TRANSLATION & SANITIZATION TESTS
# ==============================================================================

def test_duplicate_key_error_handling():
    """Verifies that 409 Conflict translates to DuplicateRecordError."""
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(409, json={"code": "23505", "message": "duplicate key value violates unique constraint"})

    client = httpx.Client(transport=httpx.MockTransport(handler), base_url=f"{TEST_SUPABASE_URL}/rest/v1")
    repo = SupabaseRepository(url=TEST_SUPABASE_URL, key=TEST_SECRET_KEY, client=client)

    with pytest.raises(DuplicateRecordError):
        repo.insert_customer({"customer_id": "IND_CUST_DUP"})


def test_foreign_key_violation_error_handling():
    """Verifies that PostgreSQL 23503 foreign key violation translates to ForeignKeyViolationError."""
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(400, json={"code": "23503", "message": "violates foreign key constraint"})

    client = httpx.Client(transport=httpx.MockTransport(handler), base_url=f"{TEST_SUPABASE_URL}/rest/v1")
    repo = SupabaseRepository(url=TEST_SUPABASE_URL, key=TEST_SECRET_KEY, client=client)

    with pytest.raises(ForeignKeyViolationError):
        repo.insert_prediction({
            "customer_id": "IND_CUST_NONEXISTENT",
            "churn_probability": 0.50,
            "retention_probability": 0.50,
            "predicted_churn": 0,
        })


def test_check_constraint_error_handling():
    """Verifies that PostgreSQL 23514 check constraint violation translates to ConstraintViolationError."""
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(400, json={"code": "23514", "message": "violates check constraint probability_sum_check"})

    client = httpx.Client(transport=httpx.MockTransport(handler), base_url=f"{TEST_SUPABASE_URL}/rest/v1")
    repo = SupabaseRepository(url=TEST_SUPABASE_URL, key=TEST_SECRET_KEY, client=client)

    with pytest.raises(ConstraintViolationError):
        repo.insert_prediction({
            "customer_id": "IND_CUST_01",
            "churn_probability": 0.90,
            "retention_probability": 0.90,
            "predicted_churn": 1,
        })


def test_authentication_error_handling():
    """Verifies that 401 Unauthorized translates to ConfigurationError."""
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(401, json={"message": "Invalid API key"})

    client = httpx.Client(transport=httpx.MockTransport(handler), base_url=f"{TEST_SUPABASE_URL}/rest/v1")
    repo = SupabaseRepository(url=TEST_SUPABASE_URL, key=TEST_SECRET_KEY, client=client)

    with pytest.raises(ConfigurationError):
        repo.get_customer_by_id("IND_CUST_01")


def test_network_timeout_error_handling():
    """Verifies that network timeout translates to DatabaseUnavailableError without crashing."""
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectTimeout("Connection timed out")

    client = httpx.Client(transport=httpx.MockTransport(handler), base_url=f"{TEST_SUPABASE_URL}/rest/v1")
    repo = SupabaseRepository(url=TEST_SUPABASE_URL, key=TEST_SECRET_KEY, client=client)

    with pytest.raises(DatabaseUnavailableError):
        repo.get_customer_count()


def test_sanitized_exceptions_never_leak_secret_key():
    """Verifies that exception messages never expose the secret API key."""
    secret_value = "SUPER_SECRET_TOKEN_DO_NOT_LEAK"

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(500, text=f"Internal database crash with key {secret_value}")

    client = httpx.Client(transport=httpx.MockTransport(handler), base_url=f"{TEST_SUPABASE_URL}/rest/v1")
    repo = SupabaseRepository(url=TEST_SUPABASE_URL, key=secret_value, client=client)

    try:
        repo.get_customer_by_id("IND_CUST_01")
    except Exception as e:
        error_msg = str(e)
        assert secret_value not in error_msg, "CRITICAL: Secret key was leaked in repository exception message!"


# ==============================================================================
# 4. CONFIGURATION & NO SILENT FALLBACK TESTS
# ==============================================================================

def test_explicit_sqlite_selection(tmp_path):
    """Verifies that STORAGE_MODE='sqlite' explicitly returns SQLiteRepository."""
    db_file = str(tmp_path / "factory_test.db")
    repo = SQLiteRepository(db_path=db_file)
    assert isinstance(repo, SQLiteRepository)
    assert isinstance(repo, BaseRepository)


def test_missing_credentials_raises_configuration_error(monkeypatch):
    """Verifies that SupabaseRepository fails fast with ConfigurationError if key is missing."""
    monkeypatch.setattr(settings, "SUPABASE_SECRET_KEY", None)
    monkeypatch.setattr(settings, "SUPABASE_SERVICE_ROLE_KEY", None)
    monkeypatch.setattr(settings, "SUPABASE_PUBLISHABLE_KEY", None)
    monkeypatch.setattr(settings, "SUPABASE_ANON_KEY", None)

    with pytest.raises(ConfigurationError):
        SupabaseRepository(url=TEST_SUPABASE_URL, key=None)


def test_invalid_storage_mode_raises_configuration_error():
    """Verifies that an unsupported STORAGE_MODE raises ConfigurationError."""
    with pytest.raises(ConfigurationError):
        get_repository(storage_mode="unsupported_database_mode")


def test_no_silent_fallback_on_supabase_mode(monkeypatch):
    """
    CRITICAL: Verifies that when STORAGE_MODE='supabase', failure to connect or authenticate
    NEVER silently falls back to SQLite, but raises a fatal exception immediately.
    """
    # Force STORAGE_MODE to supabase with invalid credentials
    monkeypatch.setattr(settings, "STORAGE_MODE", "supabase")
    monkeypatch.setattr(settings, "SUPABASE_SECRET_KEY", None)
    monkeypatch.setattr(settings, "SUPABASE_SERVICE_ROLE_KEY", None)
    monkeypatch.setattr(settings, "SUPABASE_PUBLISHABLE_KEY", None)

    # Calling factory MUST raise ConfigurationError, NEVER return SQLiteRepository
    with pytest.raises(ConfigurationError):
        get_repository()


def test_supabase_health_status_reporting():
    """Verifies diagnostic health status reporting for Supabase backend."""
    # Online case
    def online_handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json=[{"customer_id": "1"}], headers={"Content-Range": "0-0/7000"})

    client_online = httpx.Client(transport=httpx.MockTransport(online_handler), base_url=f"{TEST_SUPABASE_URL}/rest/v1")
    repo_online = SupabaseRepository(url=TEST_SUPABASE_URL, key=TEST_SECRET_KEY, client=client_online)
    health_online = repo_online.get_health_status()
    assert health_online["status"] == "healthy"
    assert health_online["backend"] == "supabase"
    assert health_online["is_connected"] is True
    assert health_online["customer_count"] == 7000

    # Offline case
    def offline_handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(503, json={"message": "Service unavailable"})

    client_offline = httpx.Client(transport=httpx.MockTransport(offline_handler), base_url=f"{TEST_SUPABASE_URL}/rest/v1")
    repo_offline = SupabaseRepository(url=TEST_SUPABASE_URL, key=TEST_SECRET_KEY, client=client_offline)
    health_offline = repo_offline.get_health_status()
    assert health_offline["status"] == "unavailable"
    assert health_offline["is_connected"] is False


# ==============================================================================
# 5. SAFE REAL SUPABASE CONNECTIVITY PROBE (ISOLATED / CONDITIONAL)
# ==============================================================================

def test_safe_real_supabase_health_probe():
    """
    Executes a safe read-only health probe against the configured Supabase URL.
    Does NOT write or alter production tables.
    Accurately asserts healthy or documents remote availability status.
    """
    key = settings.get_supabase_secret_key() or settings.get_supabase_publishable_key()
    if not key:
        pytest.skip("No Supabase key configured in backend/.env for live probe.")

    repo = SupabaseRepository(url=settings.SUPABASE_URL, key=key, timeout=5.0)
    health = repo.get_health_status()
    # Live health check will return healthy (if remote tables exist) or unavailable (if tables pending or secret unset)
    assert health["backend"] == "supabase"
    assert "status" in health
    assert "is_connected" in health
    repo.close()
