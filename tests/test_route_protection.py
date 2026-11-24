"""
Indian E-Commerce Customer Retention Intelligence System
Comprehensive Route Protection & Authentication Enforcement Test Suite (Phase 7.5 Checkpoint 4)

Tests:
1. Complete Protected Route Enumeration:
   - GET  /api/v1/auth/me
   - GET  /api/v1/ml/status
   - POST /api/v1/predictions/churn
   - POST /api/v1/segmentation/predict
   - POST /api/v1/retention/recommendations
   - POST /api/v1/customers/analyze
   - GET  /api/v1/database/health
   - GET  /api/v1/database/status
   - GET  /api/v1/database/customers/count
   - GET  /api/v1/database/import/status
2. Rejection of unauthenticated requests (HTTP 401 Unauthorized, missing token) across all 10 protected routes.
3. Rejection of malformed Bearer tokens (HTTP 401).
4. Rejection of expired tokens (HTTP 401).
5. Rejection of tampered signatures (HTTP 401).
6. Rejection of incorrect issuer and audience claims (HTTP 401).
7. Acceptance of authentic ES256 tokens on protected ML & Database routes (HTTP 200).
8. Intentionally public endpoints remain accessible without tokens:
   - GET /
   - GET /health
   - GET /api/v1/health
   - GET /api/v1/auth/health
9. Public endpoints do not expose sensitive configuration, model files/hashes, or customer data.
10. Execution order & boundary integrity:
    - Unauthenticated calls NEVER execute ML inference (ChurnPredictionService.predict is not called).
    - Unauthenticated calls NEVER execute customer analysis (CustomerAnalysisService.analyze_customer is not called).
    - Unauthenticated calls NEVER execute database repository queries (get_repository is not called).
11. Standardized error envelope contract strictly preserved for all 401 rejections.
12. Identity source anti-spoofing: spoofed client headers (e.g. X-User-Id) are strictly ignored.
"""

import json
import os
import time
from typing import Any, Dict, Optional
from unittest.mock import patch
import pandas as pd
import pytest
import httpx
import jwt
from jwt.algorithms import ECAlgorithm
from cryptography.hazmat.primitives.asymmetric import ec
from starlette.testclient import TestClient

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

from backend.app.core.config import settings
from backend.app.core.security import jwks_manager
from backend.app.main import app
from backend.app.services.churn_service import ChurnPredictionService
from backend.app.services.customer_analysis_service import CustomerAnalysisService
from backend.app.services.model_loader import ModelLoader


# ==============================================================================
# Fixtures & Ephemeral Key Setup
# ==============================================================================

@pytest.fixture(scope="module", autouse=True)
def load_models():
    """Ensure production ML model artifacts are loaded for inference tests."""
    ModelLoader.load_all()


@pytest.fixture(scope="module")
def client():
    """Provides a TestClient instance for testing the FastAPI application."""
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture(scope="module")
def ec_keypair():
    """Generates an ephemeral NIST P-256 EC key pair for deterministic token signing."""
    private_key = ec.generate_private_key(ec.SECP256R1())
    public_key = private_key.public_key()
    kid = "route-protection-test-kid-2026"

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
    """Mocks JWKS endpoint to return the ephemeral test public key."""
    transport = httpx.MockTransport(
        lambda request: httpx.Response(200, json={"keys": [ec_keypair["jwk"]]})
    )
    mock_client = httpx.Client(transport=transport)
    monkeypatch.setattr(jwks_manager, "_custom_client", mock_client)
    jwks_manager.clear_cache()
    yield
    jwks_manager.clear_cache()


def create_test_token(
    private_key: Any,
    kid: str,
    sub: str = "route-protection-user-uuid-1234",
    email: Optional[str] = "analyst@ecommerce.in",
    aud: Optional[str] = "authenticated",
    iss: Optional[str] = None,
    exp_offset: int = 3600,
) -> str:
    """Creates a cryptographically signed test ES256 JWT."""
    now = int(time.time())
    payload = {
        "sub": sub,
        "aud": aud if aud is not None else settings.JWT_AUDIENCE,
        "iss": iss if iss is not None else settings.get_supabase_auth_issuer(),
        "iat": now,
        "exp": now + exp_offset,
        "role": "authenticated",
    }
    if email is not None:
        payload["email"] = email

    headers = {"kid": kid, "alg": "ES256"}
    return jwt.encode(payload, private_key, algorithm="ES256", headers=headers)


@pytest.fixture
def valid_token(ec_keypair) -> str:
    """Returns a valid signed ES256 token."""
    return create_test_token(ec_keypair["private_key"], ec_keypair["kid"])


@pytest.fixture
def auth_headers(valid_token) -> Dict[str, str]:
    """Returns valid Authorization Bearer header dict."""
    return {"Authorization": f"Bearer {valid_token}"}


@pytest.fixture(scope="module")
def sample_feature_dict():
    """Provides a genuine 43-feature dictionary extracted from the independent cohort."""
    csv_path = os.path.join(PROJECT_ROOT, "data", "independent_test", "processed", "independent_features.csv")
    df = pd.read_csv(csv_path)
    cols = ChurnPredictionService.CONFIG_D_FEATURES
    row_dict = df[cols].iloc[0].to_dict()

    int_cols = {
        "has_historical_orders", "has_delivered_order", "hist_order_count",
        "hist_delivered_order_count", "hist_returned_order_count", "hist_cancelled_order_count",
        "orders_last_30_days", "orders_last_90_days", "orders_last_180_days",
        "delivered_orders_last_30_days", "delivered_orders_last_90_days", "delivered_orders_last_180_days",
        "hist_delivery_delay_missing_count", "hist_discounted_order_count", "hist_discount_missing_count",
        "hist_payment_missing_count", "hist_cod_order_count", "hist_upi_order_count",
        "has_orders_last_90_days", "has_orders_last_180_days", "cluster_id",
    }
    cleaned = {}
    for k, v in row_dict.items():
        if pd.isna(v):
            cleaned[k] = None
        elif k in int_cols:
            cleaned[k] = int(v)
        elif isinstance(v, (int, float)):
            cleaned[k] = float(v)
        else:
            cleaned[k] = str(v)
    return cleaned


@pytest.fixture
def sample_payloads(sample_feature_dict) -> Dict[str, Any]:
    """Provides representative valid payloads for POST endpoints."""
    return {
        "churn": sample_feature_dict,
        "segmentation": {
            "recency_delivered_days": 25.0,
            "hist_delivered_order_count": 5,
            "hist_delivered_order_value_inr": 7200.0,
        },
        "retention": sample_feature_dict,
        "analyze": {
            "customer_id": "IND_TEST_CUST_PROTECTION",
            "features": sample_feature_dict,
            "persist_results": False,
        },
    }


# ==============================================================================
# 1. Protected Route Inventory & Unauthenticated Rejection
# ==============================================================================

PROTECTED_ROUTES = [
    ("GET", "/api/v1/auth/me", None),
    ("GET", "/api/v1/ml/status", None),
    ("POST", "/api/v1/predictions/churn", "churn"),
    ("POST", "/api/v1/segmentation/predict", "segmentation"),
    ("POST", "/api/v1/retention/recommendations", "retention"),
    ("POST", "/api/v1/customers/analyze", "analyze"),
    ("GET", "/api/v1/database/health", None),
    ("GET", "/api/v1/database/status", None),
    ("GET", "/api/v1/database/customers/count", None),
    ("GET", "/api/v1/database/import/status", None),
]


@pytest.mark.parametrize("method, path, payload_key", PROTECTED_ROUTES)
def test_protected_routes_reject_missing_token(client, sample_payloads, method, path, payload_key):
    """Verifies that every protected endpoint rejects unauthenticated requests with HTTP 401."""
    payload = sample_payloads[payload_key] if payload_key else None

    if method == "GET":
        response = client.get(path)
    else:
        response = client.post(path, json=payload)

    assert response.status_code == 401, f"{method} {path} should return 401 when token is missing"
    body = response.json()
    assert body["success"] is False
    assert body["error"]["code"] == "UNAUTHORIZED"
    assert "missing authorization header" in body["error"]["message"].lower()
    assert body["meta"]["path"] == path


@pytest.mark.parametrize("method, path, payload_key", PROTECTED_ROUTES)
def test_protected_routes_reject_malformed_token(client, sample_payloads, method, path, payload_key):
    """Verifies that every protected endpoint rejects malformed tokens with HTTP 401."""
    payload = sample_payloads[payload_key] if payload_key else None
    headers = {"Authorization": "Bearer not-a-valid-jwt-token"}

    if method == "GET":
        response = client.get(path, headers=headers)
    else:
        response = client.post(path, json=payload, headers=headers)

    assert response.status_code == 401
    body = response.json()
    assert body["success"] is False
    assert body["error"]["code"] == "UNAUTHORIZED"


@pytest.mark.parametrize("method, path, payload_key", PROTECTED_ROUTES)
def test_protected_routes_reject_expired_token(client, ec_keypair, sample_payloads, method, path, payload_key):
    """Verifies that every protected endpoint rejects expired tokens with HTTP 401."""
    expired_token = create_test_token(ec_keypair["private_key"], ec_keypair["kid"], exp_offset=-120)
    headers = {"Authorization": f"Bearer {expired_token}"}
    payload = sample_payloads[payload_key] if payload_key else None

    if method == "GET":
        response = client.get(path, headers=headers)
    else:
        response = client.post(path, json=payload, headers=headers)

    assert response.status_code == 401
    body = response.json()
    assert body["success"] is False
    assert body["error"]["code"] == "UNAUTHORIZED"
    assert "expired" in body["error"]["message"].lower()


@pytest.mark.parametrize("method, path, payload_key", PROTECTED_ROUTES)
def test_protected_routes_reject_tampered_signature(client, valid_token, sample_payloads, method, path, payload_key):
    """Verifies that every protected endpoint rejects tampered signatures with HTTP 401."""
    parts = valid_token.split(".")
    tampered_sig = parts[2][:-4] + "ZZZZ"
    tampered_token = f"{parts[0]}.{parts[1]}.{tampered_sig}"
    headers = {"Authorization": f"Bearer {tampered_token}"}
    payload = sample_payloads[payload_key] if payload_key else None

    if method == "GET":
        response = client.get(path, headers=headers)
    else:
        response = client.post(path, json=payload, headers=headers)

    assert response.status_code == 401
    body = response.json()
    assert body["success"] is False
    assert body["error"]["code"] == "UNAUTHORIZED"


# ==============================================================================
# 2. Rejection of Invalid Issuer and Audience Claims
# ==============================================================================

def test_protected_route_rejects_wrong_issuer(client, ec_keypair):
    """Verifies that an authentic token from an untrusted issuer is rejected."""
    token = create_test_token(
        ec_keypair["private_key"],
        ec_keypair["kid"],
        iss="https://malicious-counterfeit-issuer.supabase.co/auth/v1",
    )
    headers = {"Authorization": f"Bearer {token}"}
    response = client.get("/api/v1/ml/status", headers=headers)
    assert response.status_code == 401
    assert "issuer" in response.json()["error"]["message"].lower()


def test_protected_route_rejects_wrong_audience(client, ec_keypair):
    """Verifies that a token with non-authenticated audience is rejected."""
    token = create_test_token(
        ec_keypair["private_key"],
        ec_keypair["kid"],
        aud="anon_public_visitor",
    )
    headers = {"Authorization": f"Bearer {token}"}
    response = client.get("/api/v1/database/health", headers=headers)
    assert response.status_code == 401
    assert "audience" in response.json()["error"]["message"].lower()


# ==============================================================================
# 3. Acceptance of Valid Authentic ES256 Tokens (Authorized Access)
# ==============================================================================

def test_authorized_ml_status(client, auth_headers):
    """Verifies that GET /api/v1/ml/status succeeds with a valid token."""
    response = client.get("/api/v1/ml/status", headers=auth_headers)
    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["data"]["rf_pipeline_loaded"] is True
    assert body["data"]["decision_threshold"] == 0.50


def test_authorized_churn_prediction(client, auth_headers, sample_payloads):
    """Verifies that POST /api/v1/predictions/churn succeeds with a valid token."""
    response = client.post("/api/v1/predictions/churn", json=sample_payloads["churn"], headers=auth_headers)
    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert "churn_probability" in body["data"]
    assert "predicted_class" in body["data"]
    assert body["data"]["decision_threshold"] == 0.50


def test_authorized_segmentation(client, auth_headers, sample_payloads):
    """Verifies that POST /api/v1/segmentation/predict succeeds with a valid token."""
    response = client.post("/api/v1/segmentation/predict", json=sample_payloads["segmentation"], headers=auth_headers)
    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert "cluster_id" in body["data"]
    assert "persona_name" in body["data"]


def test_authorized_retention_recommendations(client, auth_headers, sample_payloads):
    """Verifies that POST /api/v1/retention/recommendations succeeds with a valid token."""
    response = client.post("/api/v1/retention/recommendations", json=sample_payloads["retention"], headers=auth_headers)
    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert "recommendations" in body["data"]


def test_authorized_customer_analysis(client, auth_headers, sample_payloads):
    """Verifies that POST /api/v1/customers/analyze succeeds with a valid token."""
    response = client.post("/api/v1/customers/analyze", json=sample_payloads["analyze"], headers=auth_headers)
    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert "churn_prediction" in body["data"]
    assert "segmentation" in body["data"]
    assert "retention_recommendations" in body["data"]


def test_authorized_database_health(client, auth_headers):
    """Verifies that GET /api/v1/database/health succeeds with a valid token."""
    response = client.get("/api/v1/database/health", headers=auth_headers)
    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert "backend" in body["data"]


def test_authorized_database_status(client, auth_headers):
    """Verifies that GET /api/v1/database/status succeeds with a valid token."""
    response = client.get("/api/v1/database/status", headers=auth_headers)
    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert "tables_available" in body["data"]


def test_authorized_database_customer_counts(client, auth_headers):
    """Verifies that GET /api/v1/database/customers/count succeeds with a valid token."""
    response = client.get("/api/v1/database/customers/count", headers=auth_headers)
    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["data"]["reconciliation_valid"] is True


def test_authorized_database_import_status(client, auth_headers):
    """Verifies that GET /api/v1/database/import/status succeeds with a valid token."""
    response = client.get("/api/v1/database/import/status", headers=auth_headers)
    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["data"]["baseline_records_expected"] == 7000


# ==============================================================================
# 4. Intentionally Public Endpoints Remain Accessible Without Authentication
# ==============================================================================

PUBLIC_ROUTES = [
    ("/", "API Root Information"),
    ("/health", "Application Health Status"),
    ("/api/v1/health", "Application Health Status"),
    ("/api/v1/auth/health", "Authentication Integration Health Check"),
]


@pytest.mark.parametrize("path, expected_summary", PUBLIC_ROUTES)
def test_public_routes_accessible_without_token(client, path, expected_summary):
    """Verifies that public endpoints return HTTP 200 when called without any Authorization header."""
    response = client.get(path)
    assert response.status_code == 200, f"Public path {path} must be accessible without token"
    body = response.json()
    assert body["success"] is True


def test_public_routes_do_not_leak_sensitive_information(client):
    """Verifies that public endpoints do not expose file paths, hashes, secrets, or customer data."""
    for path, _ in PUBLIC_ROUTES:
        response = client.get(path)
        body_text = response.text.lower()
        assert "secret" not in body_text
        assert "password" not in body_text
        assert "private_key" not in body_text
        assert "customer_tenure" not in body_text
        assert "rf_model_sha256" not in body_text


# ==============================================================================
# 5. Security Boundary & Execution Order Verification
# ==============================================================================

def test_unauthorized_request_does_not_invoke_churn_service(client, sample_payloads):
    """
    CRITICAL SECURITY CHECK:
    Verifies that unauthenticated requests to /api/v1/predictions/churn are blocked
    at the dependency layer BEFORE ChurnPredictionService.predict is invoked.
    """
    with patch.object(ChurnPredictionService, "predict") as mock_predict:
        response = client.post("/api/v1/predictions/churn", json=sample_payloads["churn"])
        assert response.status_code == 401
        mock_predict.assert_not_called()


def test_unauthorized_request_does_not_invoke_customer_analysis_service(client, sample_payloads):
    """
    CRITICAL SECURITY CHECK:
    Verifies that unauthenticated requests to /api/v1/customers/analyze are blocked
    BEFORE CustomerAnalysisService.analyze_customer is invoked.
    """
    with patch.object(CustomerAnalysisService, "analyze_customer") as mock_analyze:
        response = client.post("/api/v1/customers/analyze", json=sample_payloads["analyze"])
        assert response.status_code == 401
        mock_analyze.assert_not_called()


def test_unauthorized_request_does_not_invoke_database_repository(client):
    """
    CRITICAL SECURITY CHECK:
    Verifies that unauthenticated requests to /api/v1/database/health are blocked
    BEFORE get_repository is invoked, preventing unauthenticated DB access.
    """
    with patch("backend.app.routes.database.get_repository") as mock_get_repo:
        response = client.get("/api/v1/database/health")
        assert response.status_code == 401
        mock_get_repo.assert_not_called()


# ==============================================================================
# 6. Anti-Spoofing & Client Header Immunity
# ==============================================================================

def test_client_headers_cannot_bypass_authentication(client):
    """
    Verifies that client-supplied identity or admin headers (e.g. X-User-Id, X-Role)
    cannot bypass authentication on protected routes.
    """
    spoofed_headers = {
        "X-User-Id": "injected-admin-uuid",
        "X-User-Email": "admin@ecommerce.in",
        "X-User-Role": "superadmin",
        "X-Authenticated": "true",
    }
    response = client.get("/api/v1/ml/status", headers=spoofed_headers)
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "UNAUTHORIZED"
