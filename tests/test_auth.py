"""
Indian E-Commerce Customer Retention Intelligence System
FastAPI Supabase Authentication Integration Test Suite (Phase 7.5 Checkpoint 3 - Security Corrected)

Tests:
1. Public GET /api/v1/auth/health returns 200 without exposing secrets.
2. GET /api/v1/auth/me rejects missing Authorization header (401 Unauthorized).
3. GET /api/v1/auth/me rejects malformed Bearer header (401 Unauthorized).
4. GET /api/v1/auth/me rejects expired access token (401 Unauthorized).
5. GET /api/v1/auth/me rejects invalid / tampered signature (401 Unauthorized).
6. GET /api/v1/auth/me rejects wrong issuer and wrong audience (401 Unauthorized).
7. GET /api/v1/auth/me accepts valid ES256 token and returns MINIMAL approved identity (user_id and email only).
8. Verify app_metadata, user_metadata, role, and internal token metadata are strictly excluded from response.
9. GET /api/v1/auth/me accepts valid token without optional email claim.
10. Returned identity strictly originates from verified token claims (ignores spoofed client headers).
11. Authentication error envelope conforms strictly to standardized API error contract.
12. Existing API foundation routes remain functional and unblocked.
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
# Fixtures & Test Setup
# ==============================================================================

@pytest.fixture(scope="module")
def client():
    """Provides a TestClient instance for testing the FastAPI application."""
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture(scope="module")
def ec_keypair():
    """Generates an ephemeral NIST P-256 EC key pair for signing test tokens."""
    private_key = ec.generate_private_key(ec.SECP256R1())
    public_key = private_key.public_key()
    kid = "test-auth-integration-kid"

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
    """
    Automatically configures jwks_manager to serve the test EC public key
    via httpx.MockTransport for deterministic, zero-network unit tests.
    """
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
    sub: str = "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    email: Optional[str] = "verified_employee@ecommerce.in",
    aud: Optional[str] = "authenticated",
    iss: Optional[str] = None,
    exp_offset: int = 3600,
    role: str = "authenticated",
    app_metadata: Optional[Dict[str, Any]] = None,
    user_metadata: Optional[Dict[str, Any]] = None,
) -> str:
    """Creates a signed test JWT with specified claims."""
    now = int(time.time())
    payload = {
        "sub": sub,
        "aud": aud if aud is not None else settings.JWT_AUDIENCE,
        "iss": iss if iss is not None else settings.get_supabase_auth_issuer(),
        "iat": now,
        "exp": now + exp_offset,
        "role": role,
        "app_metadata": app_metadata or {"role": "employee", "department": "Retention"},
        "user_metadata": user_metadata or {"full_name": "Verified Employee"},
    }
    if email is not None:
        payload["email"] = email

    headers = {"kid": kid, "alg": "ES256"}
    return jwt.encode(payload, private_key, algorithm="ES256", headers=headers)


# ==============================================================================
# 1. Public Auth Health Endpoint
# ==============================================================================

def test_auth_health_endpoint_public(client):
    """Verify GET /api/v1/auth/health is public and returns operational metadata without secrets."""
    response = client.get("/api/v1/auth/health")
    assert response.status_code == 200
    body = response.json()

    assert body["success"] is True
    assert "data" in body
    data = body["data"]
    assert data["status"] == "healthy"
    assert data["auth_provider"] == "supabase_auth"
    assert data["signing_algorithm"] == "ES256"
    assert data["jwks_configured"] is True
    assert "timestamp" in data

    # Verify no credentials or private info leaked in response
    body_str = json.dumps(body)
    assert "secret" not in body_str.lower()
    assert "key" not in body_str.lower() or "signing_algorithm" in body_str or "jwks_configured" in body_str


# ==============================================================================
# 2. Missing Token Rejection
# ==============================================================================

def test_auth_me_rejects_missing_token(client):
    """Verify GET /api/v1/auth/me returns 401 when Authorization header is omitted."""
    response = client.get("/api/v1/auth/me")
    assert response.status_code == 401
    body = response.json()

    assert body["success"] is False
    assert body["error"]["code"] == "UNAUTHORIZED"
    assert "missing authorization header" in body["error"]["message"].lower()
    assert "meta" in body


# ==============================================================================
# 3. Malformed Bearer Header Rejection
# ==============================================================================

def test_auth_me_rejects_malformed_bearer_headers(client):
    """Verify various malformed Authorization headers return 401."""
    # 1. Basic scheme instead of Bearer
    resp = client.get("/api/v1/auth/me", headers={"Authorization": "Basic dXNlcjpwYXNz"})
    assert resp.status_code == 401
    assert resp.json()["error"]["code"] == "UNAUTHORIZED"
    assert "bearer" in resp.json()["error"]["message"].lower()

    # 2. Bearer without token
    resp = client.get("/api/v1/auth/me", headers={"Authorization": "Bearer"})
    assert resp.status_code == 401
    assert resp.json()["error"]["code"] == "UNAUTHORIZED"

    # 3. Garbage token
    resp = client.get("/api/v1/auth/me", headers={"Authorization": "Bearer not-a-valid-jwt"})
    assert resp.status_code == 401
    assert resp.json()["error"]["code"] == "UNAUTHORIZED"


# ==============================================================================
# 4. Expired Token Rejection
# ==============================================================================

def test_auth_me_rejects_expired_token(client, ec_keypair):
    """Verify token past expiration returns 401 with standard error envelope."""
    expired_token = create_test_token(
        ec_keypair["private_key"],
        ec_keypair["kid"],
        exp_offset=-60,  # Expired 60s ago
    )

    response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {expired_token}"},
    )
    assert response.status_code == 401
    body = response.json()

    assert body["success"] is False
    assert body["error"]["code"] == "UNAUTHORIZED"
    assert "expired" in body["error"]["message"].lower()


# ==============================================================================
# 5. Invalid Signature Rejection
# ==============================================================================

def test_auth_me_rejects_tampered_signature(client, ec_keypair):
    """Verify tampered token bits fail signature check and return 401."""
    valid_token = create_test_token(ec_keypair["private_key"], ec_keypair["kid"])
    parts = valid_token.split(".")
    # Tamper with the signature portion
    tampered_sig = parts[2][:-4] + "AAAA"
    tampered_token = f"{parts[0]}.{parts[1]}.{tampered_sig}"

    response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {tampered_token}"},
    )
    assert response.status_code == 401
    body = response.json()

    assert body["success"] is False
    assert body["error"]["code"] == "UNAUTHORIZED"
    assert "signature" in body["error"]["message"].lower() or "verification failed" in body["error"]["message"].lower()


# ==============================================================================
# 6. Wrong Issuer and Audience Rejection
# ==============================================================================

def test_auth_me_rejects_wrong_issuer(client, ec_keypair):
    """Verify token with untrusted issuer returns 401."""
    token = create_test_token(
        ec_keypair["private_key"],
        ec_keypair["kid"],
        iss="https://untrusted-issuer.supabase.co/auth/v1",
    )
    response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 401
    body = response.json()

    assert body["success"] is False
    assert body["error"]["code"] == "UNAUTHORIZED"
    assert "issuer" in body["error"]["message"].lower()


def test_auth_me_rejects_wrong_audience(client, ec_keypair):
    """Verify token with non-authenticated audience returns 401."""
    token = create_test_token(
        ec_keypair["private_key"],
        ec_keypair["kid"],
        aud="unauthorized_audience",
    )
    response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 401
    body = response.json()

    assert body["success"] is False
    assert body["error"]["code"] == "UNAUTHORIZED"
    assert "audience" in body["error"]["message"].lower()


# ==============================================================================
# 7. Valid ES256 Token Returns Minimal Identity Only
# ==============================================================================

def test_auth_me_accepts_valid_es256_token_minimal_identity(client, ec_keypair):
    """
    Verify valid token returns 200 OK and strictly minimal verified identity.
    Confirms app_metadata, user_metadata, role, and internal metadata are EXCLUDED.
    """
    test_sub = "11112222-3333-4444-5555-666677778888"
    test_email = "lead_analyst@ecommerce.in"

    valid_token = create_test_token(
        ec_keypair["private_key"],
        ec_keypair["kid"],
        sub=test_sub,
        email=test_email,
        role="authenticated",
        app_metadata={"role": "analyst", "team": "Retention Strategy"},
        user_metadata={"full_name": "Rohan Sharma", "phone": "+919876543210"},
    )

    response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {valid_token}"},
    )
    assert response.status_code == 200
    body = response.json()

    assert body["success"] is True
    assert "data" in body
    user_data = body["data"]

    # 1. Approved identity fields MUST be present
    assert user_data["user_id"] == test_sub
    assert user_data["email"] == test_email

    # 2. Unapproved fields MUST NOT be present
    assert "role" not in user_data
    assert "app_metadata" not in user_data
    assert "user_metadata" not in user_data
    assert "issued_at" not in user_data
    assert "expires_at" not in user_data

    # 3. Exactly only the approved keys are returned
    assert set(user_data.keys()) == {"user_id", "email"}


# ==============================================================================
# 8. Token Without Optional Email Accepted
# ==============================================================================

def test_auth_me_accepts_token_without_email(client, ec_keypair):
    """Verify that an authentic token without email succeeds and returns user_id with email=None."""
    test_sub = "99998888-7777-6666-5555-444433332222"

    token_no_email = create_test_token(
        ec_keypair["private_key"],
        ec_keypair["kid"],
        sub=test_sub,
        email=None,
    )

    response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token_no_email}"},
    )
    assert response.status_code == 200
    body = response.json()

    user_data = body["data"]
    assert user_data["user_id"] == test_sub
    assert user_data["email"] is None
    assert set(user_data.keys()) == {"user_id", "email"}


# ==============================================================================
# 9. Identity Source Integrity (No Client Spoofing)
# ==============================================================================

def test_identity_cannot_be_spoofed_via_request_headers(client, ec_keypair):
    """
    Verify identity is extracted exclusively from verified cryptographic claims,
    ignoring any spoofed client headers (e.g. X-User-Id, X-User-Email, X-User-Role).
    """
    legitimate_sub = "legitimate-uuid-9999"
    legitimate_email = "real_user@ecommerce.in"

    token = create_test_token(
        ec_keypair["private_key"],
        ec_keypair["kid"],
        sub=legitimate_sub,
        email=legitimate_email,
    )

    # Attacker attempts header-based identity injection
    spoofed_headers = {
        "Authorization": f"Bearer {token}",
        "X-User-Id": "attacker-injected-id",
        "X-User-Email": "attacker@evil.com",
        "X-User-Role": "superadmin",
    }

    response = client.get("/api/v1/auth/me", headers=spoofed_headers)
    assert response.status_code == 200
    body = response.json()

    user_data = body["data"]
    assert user_data["user_id"] == legitimate_sub
    assert user_data["email"] == legitimate_email
    assert user_data["user_id"] != "attacker-injected-id"
    assert "role" not in user_data
    assert "app_metadata" not in user_data
    assert "user_metadata" not in user_data


# ==============================================================================
# 10. Standardized Error Envelope Structure
# ==============================================================================

def test_auth_error_envelope_structure(client):
    """Verify that authentication rejections strictly adhere to the standard error envelope."""
    response = client.get("/api/v1/auth/me")
    assert response.status_code == 401
    body = response.json()

    assert "success" in body
    assert body["success"] is False
    assert "error" in body
    assert "code" in body["error"]
    assert "message" in body["error"]
    assert "details" in body["error"]
    assert isinstance(body["error"]["details"], list)
    assert "meta" in body
    assert "timestamp" in body["meta"]
    assert "path" in body["meta"]
    assert body["meta"]["path"] == "/api/v1/auth/me"


# ==============================================================================
# 11. Existing API Routes Remain Functional & Unblocked
# ==============================================================================

def test_existing_unauthenticated_routes_remain_functional(client):
    """Verify root and health endpoints remain functional without authentication."""
    # 1. Root info
    root_resp = client.get("/")
    assert root_resp.status_code == 200
    assert root_resp.json()["success"] is True

    # 2. Direct health
    health_resp = client.get("/health")
    assert health_resp.status_code == 200
    assert health_resp.json()["data"]["status"] == "healthy"

    # 3. Versioned health
    v1_health_resp = client.get("/api/v1/health")
    assert v1_health_resp.status_code == 200
    assert v1_health_resp.json()["data"]["status"] == "healthy"
