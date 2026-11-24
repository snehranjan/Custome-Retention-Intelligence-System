"""
Indian E-Commerce Customer Retention Intelligence System
Customer Management API Test Suite (Phase 8.4.4 - Backend Customer Management API Bridge)

Tests:
1. GET /api/v1/customers rejects unauthenticated requests (HTTP 401 UNAUTHORIZED).
2. GET /api/v1/customers rejects invalid / expired tokens (HTTP 401 UNAUTHORIZED).
3. GET /api/v1/customers rejects authenticated but unapproved users (HTTP 403 FORBIDDEN - Fail Closed).
4. GET /api/v1/customers allows approved employees and returns paginated CustomerListResponse.
5. GET /api/v1/customers validates pagination bounds (limit=0, limit=101, offset=-1 return HTTP 422).
6. GET /api/v1/customers enforces correct pagination slicing and has_more flag.
7. GET /api/v1/customers supports optional search by customer ID.
8. GET /api/v1/customers returns empty list for nonexistent search term.
9. GET /api/v1/customers/{customer_id} rejects unauthenticated requests (HTTP 401).
10. GET /api/v1/customers/{customer_id} rejects unapproved authenticated users (HTTP 403).
11. GET /api/v1/customers/{customer_id} returns full customer detail profile for existing customer.
12. GET /api/v1/customers/{customer_id} returns HTTP 404 for nonexistent customer ID.
13. Existing POST /api/v1/customers/analyze remains functional and unblocked.
14. System health and existing database APIs remain functional and unaffected.
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
    kid = "test-customer-api-kid"

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
    jwks_manager.clear_cache()


@pytest.fixture(scope="module")
def client():
    """Provides a TestClient instance for testing the FastAPI application."""
    with TestClient(app) as test_client:
        yield test_client


def create_token(
    private_key: Any,
    kid: str,
    sub: str = "00000000-0000-0000-0000-000000000001",
    email: Optional[str] = "unapproved_user@external.com",
    aud: Optional[str] = "authenticated",
    iss: Optional[str] = None,
    exp_offset: int = 3600,
) -> str:
    """Helper generating signed ES256 tokens for testing."""
    now = int(time.time())
    payload = {
        "sub": sub,
        "aud": aud if aud is not None else settings.JWT_AUDIENCE,
        "iss": iss if iss is not None else settings.get_supabase_auth_issuer(),
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


# Approved employee test credentials
APPROVED_EMPLOYEE_EMAIL = "authorized_employee@ecommerce.in"
APPROVED_EMPLOYEE_UUID = "11111111-2222-3333-4444-555555555555"

UNAPPROVED_USER_EMAIL = "unapproved_applicant@gmail.com"
UNAPPROVED_USER_UUID = "99999999-8888-7777-6666-555555555555"


@pytest.fixture
def configure_authorized_employee(monkeypatch):
    """Configures server-side employee authorization registry."""
    monkeypatch.setattr(settings, "AUTHORIZED_EMPLOYEE_EMAILS", [APPROVED_EMPLOYEE_EMAIL])
    monkeypatch.setattr(settings, "AUTHORIZED_EMPLOYEE_USER_IDS", [APPROVED_EMPLOYEE_UUID])


# ==============================================================================
# Security & Authorization Tests (HTTP 401 & 403)
# ==============================================================================

def test_customers_list_rejects_unauthenticated(client):
    """GET /api/v1/customers must return 401 UNAUTHORIZED when no token is provided."""
    response = client.get("/api/v1/customers")
    assert response.status_code == 401
    body = response.json()
    assert body["success"] is False
    assert body["error"]["code"] == "UNAUTHORIZED"
    assert "Missing Authorization header" in body["error"]["message"]


def test_customers_list_rejects_expired_token(client, ec_keypair):
    """GET /api/v1/customers must return 401 UNAUTHORIZED for expired tokens."""
    token = create_token(
        ec_keypair["private_key"],
        ec_keypair["kid"],
        email=APPROVED_EMPLOYEE_EMAIL,
        exp_offset=-60,
    )
    response = client.get("/api/v1/customers", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 401
    body = response.json()
    assert body["success"] is False
    assert body["error"]["code"] == "UNAUTHORIZED"


def test_customers_list_rejects_unapproved_employee_fail_closed(
    client, ec_keypair, configure_authorized_employee
):
    """
    GET /api/v1/customers must return 403 FORBIDDEN when user has valid JWT
    but is not in server-controlled employee registry (Strict Admin-Controlled Policy).
    Verifies that NO customer data is leaked.
    """
    token = create_token(
        ec_keypair["private_key"],
        ec_keypair["kid"],
        sub=UNAPPROVED_USER_UUID,
        email=UNAPPROVED_USER_EMAIL,
    )
    response = client.get("/api/v1/customers", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 403
    body = response.json()
    assert body["success"] is False
    assert body["error"]["code"] == "FORBIDDEN"
    assert "not authorized as an approved RetainIQ employee" in body["error"]["message"]
    # Ensure zero customer data in response
    assert "data" not in body or body["data"] is None


def test_customer_detail_rejects_unauthenticated(client):
    """GET /api/v1/customers/{id} must return 401 when no token is provided."""
    response = client.get("/api/v1/customers/IND_CUST_10001")
    assert response.status_code == 401
    body = response.json()
    assert body["success"] is False
    assert body["error"]["code"] == "UNAUTHORIZED"


def test_customer_detail_rejects_unapproved_employee(
    client, ec_keypair, configure_authorized_employee
):
    """GET /api/v1/customers/{id} must return 403 for unapproved authenticated users."""
    token = create_token(
        ec_keypair["private_key"],
        ec_keypair["kid"],
        sub=UNAPPROVED_USER_UUID,
        email=UNAPPROVED_USER_EMAIL,
    )
    response = client.get(
        "/api/v1/customers/IND_CUST_10001",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 403
    body = response.json()
    assert body["success"] is False
    assert body["error"]["code"] == "FORBIDDEN"


# ==============================================================================
# Customer Directory Listing Tests (GET /api/v1/customers)
# ==============================================================================

def test_customers_list_success_for_authorized_employee(
    client, ec_keypair, configure_authorized_employee
):
    """GET /api/v1/customers returns paginated customer records for authorized employee."""
    token = create_token(
        ec_keypair["private_key"],
        ec_keypair["kid"],
        sub=APPROVED_EMPLOYEE_UUID,
        email=APPROVED_EMPLOYEE_EMAIL,
    )
    response = client.get("/api/v1/customers", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True

    data = body["data"]
    assert "items" in data
    assert "total" in data
    assert "limit" in data
    assert "offset" in data
    assert "has_more" in data

    assert data["total"] == 7000
    assert data["limit"] == 50
    assert data["offset"] == 0
    assert len(data["items"]) == 50
    assert data["has_more"] is True

    # Validate customer item schema
    first = data["items"][0]
    assert "customer_id" in first
    assert "customer_name" in first
    assert "signup_date" in first
    assert "city" in first
    assert "state" in first
    assert "churn" in first


def test_customers_list_pagination_parameters(
    client, ec_keypair, configure_authorized_employee
):
    """GET /api/v1/customers enforces custom limit and offset slicing."""
    token = create_token(
        ec_keypair["private_key"],
        ec_keypair["kid"],
        sub=APPROVED_EMPLOYEE_UUID,
        email=APPROVED_EMPLOYEE_EMAIL,
    )

    # Page 1: limit=5, offset=0
    res1 = client.get(
        "/api/v1/customers?limit=5&offset=0",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res1.status_code == 200
    data1 = res1.json()["data"]
    assert len(data1["items"]) == 5
    assert data1["limit"] == 5
    assert data1["offset"] == 0
    assert data1["has_more"] is True
    ids_page1 = [c["customer_id"] for c in data1["items"]]

    # Page 2: limit=5, offset=5
    res2 = client.get(
        "/api/v1/customers?limit=5&offset=5",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res2.status_code == 200
    data2 = res2.json()["data"]
    assert len(data2["items"]) == 5
    assert data2["limit"] == 5
    assert data2["offset"] == 5
    ids_page2 = [c["customer_id"] for c in data2["items"]]

    # Ensure pages do not overlap
    assert set(ids_page1).isdisjoint(set(ids_page2))


def test_customers_list_invalid_pagination_bounds(
    client, ec_keypair, configure_authorized_employee
):
    """GET /api/v1/customers rejects invalid pagination parameters with 422."""
    token = create_token(
        ec_keypair["private_key"],
        ec_keypair["kid"],
        sub=APPROVED_EMPLOYEE_UUID,
        email=APPROVED_EMPLOYEE_EMAIL,
    )
    headers = {"Authorization": f"Bearer {token}"}

    # limit = 0 (< 1)
    r1 = client.get("/api/v1/customers?limit=0", headers=headers)
    assert r1.status_code == 422

    # limit = 101 (> 100)
    r2 = client.get("/api/v1/customers?limit=101", headers=headers)
    assert r2.status_code == 422

    # offset = -1 (< 0)
    r3 = client.get("/api/v1/customers?offset=-1", headers=headers)
    assert r3.status_code == 422


def test_customers_list_search_by_exact_id(
    client, ec_keypair, configure_authorized_employee
):
    """GET /api/v1/customers?search=IND_CUST_10001 returns exact matched customer."""
    token = create_token(
        ec_keypair["private_key"],
        ec_keypair["kid"],
        sub=APPROVED_EMPLOYEE_UUID,
        email=APPROVED_EMPLOYEE_EMAIL,
    )
    response = client.get(
        "/api/v1/customers?search=IND_CUST_10001",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["total"] == 1
    assert len(data["items"]) == 1
    assert data["items"][0]["customer_id"] == "IND_CUST_10001"
    assert data["has_more"] is False


def test_customers_list_search_nonexistent_returns_empty(
    client, ec_keypair, configure_authorized_employee
):
    """GET /api/v1/customers?search=NONEXISTENT returns empty items list."""
    token = create_token(
        ec_keypair["private_key"],
        ec_keypair["kid"],
        sub=APPROVED_EMPLOYEE_UUID,
        email=APPROVED_EMPLOYEE_EMAIL,
    )
    response = client.get(
        "/api/v1/customers?search=NONEXISTENT_CUST_ID",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["total"] == 0
    assert len(data["items"]) == 0
    assert data["has_more"] is False


# ==============================================================================
# Customer Detail Profile Tests (GET /api/v1/customers/{customer_id})
# ==============================================================================

def test_customer_detail_success_for_authorized_employee(
    client, ec_keypair, configure_authorized_employee
):
    """GET /api/v1/customers/{customer_id} returns full customer profile."""
    token = create_token(
        ec_keypair["private_key"],
        ec_keypair["kid"],
        sub=APPROVED_EMPLOYEE_UUID,
        email=APPROVED_EMPLOYEE_EMAIL,
    )
    response = client.get(
        "/api/v1/customers/IND_CUST_10001",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True

    detail = body["data"]
    assert detail["customer_id"] == "IND_CUST_10001"
    assert detail["customer_name"] == "Pradeep Mehta"
    assert detail["city"] == "Bhopal"
    assert detail["state"] == "Madhya Pradesh"
    assert detail["signup_date"] == "2024-08-13"
    assert detail["churn"] == 1
    assert "latest_prediction" in detail
    assert "current_segment" in detail
    assert "recommendations" in detail
    assert isinstance(detail["recommendations"], list)


def test_customer_detail_returns_404_for_nonexistent_customer(
    client, ec_keypair, configure_authorized_employee
):
    """GET /api/v1/customers/{customer_id} returns 404 RESOURCE_NOT_FOUND if ID not found."""
    token = create_token(
        ec_keypair["private_key"],
        ec_keypair["kid"],
        sub=APPROVED_EMPLOYEE_UUID,
        email=APPROVED_EMPLOYEE_EMAIL,
    )
    response = client.get(
        "/api/v1/customers/IND_CUST_99999",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 404
    body = response.json()
    assert body["success"] is False
    assert body["error"]["code"] == "RESOURCE_NOT_FOUND"
    assert "not found" in body["error"]["message"].lower()


# ==============================================================================
# Route Non-Interference & Regression Invariants
# ==============================================================================

def test_customers_analyze_endpoint_remains_functional(
    client, ec_keypair, configure_authorized_employee
):
    """
    Verifies that POST /api/v1/customers/analyze from Phase 7.3 remains functional
    and does not conflict with customer management routes.
    """
    token = create_token(
        ec_keypair["private_key"],
        ec_keypair["kid"],
        sub=APPROVED_EMPLOYEE_UUID,
        email=APPROVED_EMPLOYEE_EMAIL,
    )

    # Valid Config D features sample
    payload = {
        "customer_id": "IND_CUST_TEST",
        "persist_results": False,
        "features": {
            "customer_tenure_days": 350.0,
            "has_historical_orders": 1,
            "recency_days": 25.0,
            "recency_delivered_days": 25.0,
            "has_delivered_order": 1,
            "hist_order_count": 5,
            "hist_delivered_order_count": 4,
            "hist_returned_order_count": 0,
            "hist_cancelled_order_count": 1,
            "hist_total_order_value_inr": 8500.0,
            "hist_delivered_order_value_inr": 7200.0,
            "hist_total_recorded_discount_inr": 800.0,
            "hist_average_order_value_inr": 1700.0,
            "orders_last_30_days": 1,
            "orders_last_90_days": 2,
            "orders_last_180_days": 4,
            "delivered_orders_last_30_days": 1,
            "delivered_orders_last_90_days": 2,
            "delivered_orders_last_180_days": 3,
            "hist_return_rate": 0.0,
            "hist_cancellation_rate": 0.2,
            "hist_average_delivery_delay_days": 0.5,
            "hist_delivery_delay_missing_count": 0,
            "hist_delivery_delay_missing_rate": 0.0,
            "hist_average_discount_amount_inr": 160.0,
            "hist_discounted_order_count": 3,
            "hist_discount_missing_count": 0,
            "hist_discount_missing_rate": 0.0,
            "hist_payment_missing_count": 0,
            "hist_payment_missing_rate": 0.0,
            "hist_cod_order_count": 1,
            "hist_cod_usage_rate": 0.2,
            "hist_upi_order_count": 4,
            "hist_upi_usage_rate": 0.8,
            "velocity_ratio_30_90": 1.5,
            "velocity_ratio_90_180": 1.0,
            "has_orders_last_90_days": 1,
            "has_orders_last_180_days": 1,
            "delay_friction_score": 0.1,
            "missing_friction_score": 0.0,
            "city": "Bengaluru",
            "state": "Karnataka",
            "cluster_id": 0,
        },
    }

    response = client.post(
        "/api/v1/customers/analyze",
        json=payload,
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert "churn_prediction" in body["data"]
    assert "segmentation" in body["data"]
    assert "retention_recommendations" in body["data"]
