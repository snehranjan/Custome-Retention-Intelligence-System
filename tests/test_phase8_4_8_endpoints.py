"""
Indian E-Commerce Customer Retention Intelligence System
Phase 8.4.8 Backend Endpoints Test Suite
(Customer Retention Explorer & Advanced Analytics)

Covers:
1. GET /api/v1/customers: Advanced filtering (segment, risk tier, city, state), search, and sorting.
2. GET /api/v1/customers/{customer_id}: Profile retrieval with 43 behavioral features and ML artifacts.
3. POST /api/v1/customers/{customer_id}/predict: Live Random Forest inference and probability boundaries.
4. GET /api/v1/analytics/overview: Master KPI counts, distributions, and dataset metadata.
5. GET /api/v1/analytics/model-performance: Authoritative N=1,500 test metrics, confusion matrix, disclosures.
6. GET /api/v1/analytics/segments: 5 official persona profiles and churn distributions.
7. GET /api/v1/recommendations: Filterable recommendations by priority, segment, risk tier, and search.
8. Fail-closed security: 401 Unauthorized for unauthenticated, 403 Forbidden for unapproved.
"""

import json
import time
from typing import Any, Dict, Optional
import pytest
import httpx
import jwt
from jwt.algorithms import ECAlgorithm
from cryptography.hazmat.primitives.asymmetric import ec
from starlette.testclient import TestClient

from backend.app.core.config import settings
from backend.app.core.security import jwks_manager
from backend.app.main import app


# ==============================================================================
# Ephemeral Cryptographic Test Fixtures
# ==============================================================================

@pytest.fixture(scope="module")
def ec_keypair():
    """Generates an ephemeral NIST P-256 EC key pair for signing test ES256 tokens."""
    private_key = ec.generate_private_key(ec.SECP256R1())
    public_key = private_key.public_key()
    kid = "test-phase848-kid"

    jwk_dict = json.loads(ECAlgorithm.to_jwk(public_key))
    jwk_dict["kid"] = kid
    jwk_dict["alg"] = "ES256"
    jwk_dict["use"] = "sig"

    return {
        "private_key": private_key,
        "public_key": public_key,
        "kid": kid,
        "jwk": jwk_dict,
    }


@pytest.fixture(autouse=True)
def mock_jwks(ec_keypair, monkeypatch):
    """Configures jwks_manager to serve the test EC public key via MockTransport."""
    transport = httpx.MockTransport(
        lambda request: httpx.Response(200, json={"keys": [ec_keypair["jwk"]]})
    )
    mock_client = httpx.Client(transport=transport)
    monkeypatch.setattr(jwks_manager, "_custom_client", mock_client)
    jwks_manager.clear_cache()
    yield


@pytest.fixture(scope="module")
def client():
    """Provides a TestClient instance for testing the FastAPI application."""
    with TestClient(app) as test_client:
        yield test_client


def create_token(
    private_key: Any,
    kid: str,
    sub: str = "11111111-2222-3333-4444-555555555555",
    email: Optional[str] = "authorized_employee@ecommerce.in",
    exp_offset: int = 3600,
) -> str:
    """Helper generating signed ES256 tokens for testing."""
    now = int(time.time())
    payload = {
        "sub": sub,
        "aud": settings.JWT_AUDIENCE,
        "iss": settings.get_supabase_auth_issuer(),
        "iat": now,
        "exp": now + exp_offset,
        "role": "authenticated",
    }
    if email:
        payload["email"] = email

    headers = {
        "kid": kid,
        "alg": "ES256",
        "typ": "JWT",
    }
    return jwt.encode(payload, private_key, algorithm="ES256", headers=headers)


APPROVED_EMAIL = "analyst@retainiq.internal"
APPROVED_UUID = "8a07da14-a872-4a13-a579-ddc164b10631"

UNAPPROVED_EMAIL = "unapproved_applicant@gmail.com"
UNAPPROVED_UUID = "99999999-8888-7777-6666-555555555555"


@pytest.fixture
def auth_headers(ec_keypair, monkeypatch):
    monkeypatch.setattr(settings, "AUTHORIZED_EMPLOYEE_EMAILS", [APPROVED_EMAIL])
    monkeypatch.setattr(settings, "AUTHORIZED_EMPLOYEE_USER_IDS", [APPROVED_UUID])
    token = create_token(ec_keypair["private_key"], ec_keypair["kid"], sub=APPROVED_UUID, email=APPROVED_EMAIL)
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def unapproved_headers(ec_keypair, monkeypatch):
    monkeypatch.setattr(settings, "AUTHORIZED_EMPLOYEE_EMAILS", [APPROVED_EMAIL])
    monkeypatch.setattr(settings, "AUTHORIZED_EMPLOYEE_USER_IDS", [APPROVED_UUID])
    token = create_token(ec_keypair["private_key"], ec_keypair["kid"], sub=UNAPPROVED_UUID, email=UNAPPROVED_EMAIL)
    return {"Authorization": f"Bearer {token}"}


# ==============================================================================
# 1. Security & Fail-Closed Invariants
# ==============================================================================

def test_endpoints_require_authentication(client):
    """All Phase 8.4.8 endpoints reject missing auth header with 401."""
    assert client.get("/api/v1/analytics/overview").status_code == 401
    assert client.get("/api/v1/analytics/model-performance").status_code == 401
    assert client.get("/api/v1/analytics/segments").status_code == 401
    assert client.get("/api/v1/recommendations").status_code == 401
    assert client.post("/api/v1/customers/IND_CUST_10001/predict").status_code == 401


def test_endpoints_reject_unapproved_employee(client, unapproved_headers):
    """All Phase 8.4.8 endpoints reject valid JWT with unapproved employee status (403)."""
    assert client.get("/api/v1/analytics/overview", headers=unapproved_headers).status_code == 403
    assert client.get("/api/v1/analytics/model-performance", headers=unapproved_headers).status_code == 403
    assert client.get("/api/v1/analytics/segments", headers=unapproved_headers).status_code == 403
    assert client.get("/api/v1/recommendations", headers=unapproved_headers).status_code == 403
    assert client.post("/api/v1/customers/IND_CUST_10001/predict", headers=unapproved_headers).status_code == 403


# ==============================================================================
# 2. Customer Explorer Advanced Filtering & Sorting
# ==============================================================================

def test_customers_list_with_segment_filter(client, auth_headers):
    """Filter customers by segment 0."""
    res = client.get("/api/v1/customers?segment=0&limit=10", headers=auth_headers)
    assert res.status_code == 200
    data = res.json()["data"]
    assert data["total"] == 1569
    for item in data["items"]:
        assert item["cluster_id"] == 0
        assert item["segment_name"] == "Champions & High-Value Loyalists"


def test_customers_list_with_risk_tier_filter(client, auth_headers):
    """Filter customers by HIGH risk tier."""
    res = client.get("/api/v1/customers?risk_tier=HIGH&limit=10", headers=auth_headers)
    assert res.status_code == 200
    data = res.json()["data"]
    assert data["total"] == 1210
    for item in data["items"]:
        assert item["risk_tier"] == "HIGH"
        assert item["churn_probability"] >= 0.70


def test_customers_list_sorting_by_probability(client, auth_headers):
    """Sort customers by churn probability descending."""
    res = client.get("/api/v1/customers?sort_by=churn_probability&sort_dir=DESC&limit=10", headers=auth_headers)
    assert res.status_code == 200
    items = res.json()["data"]["items"]
    assert len(items) == 10
    probs = [i["churn_probability"] for i in items]
    assert probs == sorted(probs, reverse=True)


def test_customers_search_by_id_or_name(client, auth_headers):
    """Search customers by ID pattern."""
    res = client.get("/api/v1/customers?search=IND_CUST_10001", headers=auth_headers)
    assert res.status_code == 200
    data = res.json()["data"]
    assert data["total"] >= 1
    assert any(i["customer_id"] == "IND_CUST_10001" for i in data["items"])


# ==============================================================================
# 3. Customer Profile & 43 Behavioral Features
# ==============================================================================

def test_customer_detail_with_features(client, auth_headers):
    """Retrieves full profile with 43 features for IND_CUST_10001."""
    res = client.get("/api/v1/customers/IND_CUST_10001", headers=auth_headers)
    assert res.status_code == 200
    data = res.json()["data"]
    assert data["customer_id"] == "IND_CUST_10001"
    assert data["features"] is not None
    assert len(data["features"]) == 43
    # Check specific momentum & categorical features
    assert "velocity_ratio_30_90" in data["features"]
    assert "delay_friction_score" in data["features"]
    assert "missing_friction_score" in data["features"]
    assert "city" in data["features"]
    assert "state" in data["features"]
    assert "cluster_id" in data["features"]
    assert data["latest_prediction"] is not None
    assert data["current_segment"] is not None


def test_customer_detail_not_found(client, auth_headers):
    """Nonexistent customer returns 404."""
    res = client.get("/api/v1/customers/IND_CUST_NONEXISTENT", headers=auth_headers)
    assert res.status_code == 404


# ==============================================================================
# 4. Live Churn Prediction Inference
# ==============================================================================

def test_live_prediction_inference(client, auth_headers):
    """Executes live inference on IND_CUST_10001 and validates decision rules."""
    res = client.post("/api/v1/customers/IND_CUST_10001/predict", headers=auth_headers)
    assert res.status_code == 200
    pred = res.json()["data"]
    assert 0.0 <= pred["churn_probability"] <= 1.0
    assert 0.0 <= pred["retention_probability"] <= 1.0
    assert abs((pred["churn_probability"] + pred["retention_probability"]) - 1.0) < 0.01
    assert pred["decision_threshold"] == 0.50
    assert pred["predicted_class"] in [0, 1]
    assert pred["risk_tier"] in ["LOW", "MODERATE", "HIGH"]

    # Verify risk tier boundaries
    p = pred["churn_probability"]
    if p >= 0.70:
        assert pred["risk_tier"] == "HIGH"
    elif p >= 0.50:
        assert pred["risk_tier"] == "MODERATE"
    else:
        assert pred["risk_tier"] == "LOW"


def test_live_prediction_not_found(client, auth_headers):
    """Live prediction for nonexistent customer returns 404."""
    res = client.post("/api/v1/customers/IND_CUST_NONEXISTENT/predict", headers=auth_headers)
    assert res.status_code == 404


# ==============================================================================
# 5. Overview Analytics & KPIs
# ==============================================================================

def test_overview_analytics(client, auth_headers):
    """Validates master KPIs and population distributions."""
    res = client.get("/api/v1/analytics/overview", headers=auth_headers)
    assert res.status_code == 200
    data = res.json()["data"]

    # Exact KPI checks
    kpis = data["kpis"]
    assert kpis["total_customers"] == 7000
    assert kpis["observed_churned"] == 3207
    assert kpis["observed_retained"] == 3793
    assert kpis["observed_churn_rate"] == 0.4581
    assert kpis["predicted_at_risk"] == 3356
    assert kpis["predicted_retained"] == 3644
    assert kpis["predicted_at_risk_rate"] == 0.4794

    # Segment counts
    segments = data["segment_distribution"]
    assert len(segments) == 5
    seg_counts = {s["cluster_id"]: s["customer_count"] for s in segments}
    assert seg_counts[0] == 1569
    assert seg_counts[1] == 1723
    assert seg_counts[2] == 484
    assert seg_counts[3] == 2000
    assert seg_counts[4] == 1224

    # Risk tier counts
    risk_tiers = {r["tier"]: r["count"] for r in data["predicted_risk_distribution"]}
    assert risk_tiers["LOW"] == 3644
    assert risk_tiers["MODERATE"] == 2146
    assert risk_tiers["HIGH"] == 1210

    # Model metadata SHA-256
    assert data["model_metadata"]["model_sha256"] == "24F1F0E33C75B5590906369960DB6E5951EC95DF9AE40384DA60082B3438F301"


# ==============================================================================
# 6. Model Performance & Evaluation Metrics (N=1,500)
# ==============================================================================

def test_model_performance(client, auth_headers):
    """Validates independent evaluation test cohort metrics."""
    res = client.get("/api/v1/analytics/model-performance", headers=auth_headers)
    assert res.status_code == 200
    data = res.json()["data"]

    assert data["sample_size"] == 1500
    assert data["locked_decision_threshold"] == 0.50
    assert data["model_sha256"] == "24F1F0E33C75B5590906369960DB6E5951EC95DF9AE40384DA60082B3438F301"

    metrics = data["metrics"]
    assert metrics["accuracy"] == 0.6893
    assert metrics["precision"] == 0.6422
    assert metrics["recall"] == 0.6900
    assert metrics["specificity"] == 0.6888
    assert metrics["balanced_accuracy"] == 0.6894
    assert metrics["f1_score"] == 0.6652
    assert metrics["roc_auc"] == 0.7651
    assert metrics["average_precision"] == 0.7308
    assert metrics["brier_score"] == 0.1970

    cm = data["confusion_matrix"]
    assert cm["true_negatives"] == 571
    assert cm["false_positives"] == 258
    assert cm["false_negatives"] == 208
    assert cm["true_positives"] == 463


# ==============================================================================
# 7. Customer Segmentation Profiles
# ==============================================================================

def test_segment_profiles(client, auth_headers):
    """Validates 5 official personas endpoint."""
    res = client.get("/api/v1/analytics/segments", headers=auth_headers)
    assert res.status_code == 200
    segments = res.json()["data"]
    assert len(segments) == 5
    for s in segments:
        assert s["persona_description"]
        assert s["recommended_strategy"]
        assert s["customer_count"] > 0


# ==============================================================================
# 8. Retention Recommendations
# ==============================================================================

def test_recommendations_list_and_filters(client, auth_headers):
    """Validates recommendations listing and filtering."""
    res = client.get("/api/v1/recommendations?limit=20", headers=auth_headers)
    assert res.status_code == 200
    data = res.json()["data"]
    assert data["total"] == 16580
    assert len(data["items"]) == 20

    # Filter by HIGH priority
    res_high = client.get("/api/v1/recommendations?priority=HIGH&limit=10", headers=auth_headers)
    assert res_high.status_code == 200
    items_high = res_high.json()["data"]["items"]
    assert all(i["priority"] == "HIGH" for i in items_high)

    # Filter by segment 1
    res_seg = client.get("/api/v1/recommendations?segment=1&limit=10", headers=auth_headers)
    assert res_seg.status_code == 200
    items_seg = res_seg.json()["data"]["items"]
    assert all(i["cluster_id"] == 1 for i in items_seg)
