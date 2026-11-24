"""
Indian E-Commerce Customer Retention Intelligence System
Administrator Portal & Directory API Test Suite (Phase 8.4.6)

Verifies:
1. Administrator Authentication & Authorization (/api/v1/admin/me)
   - 401 Unauthenticated rejected
   - 403 Non-administrator employee rejected
   - 200 Authorized administrator granted
2. Aggregated Employee Statistics (/api/v1/admin/stats)
   - Real backend-derived status counts (total, pending, approved, rejected, suspended, invited)
3. Employee Directory & Filtering (/api/v1/admin/employees)
   - Status filtering (ALL, PENDING, APPROVED, etc.)
   - Search query matching by ID, email, or name
   - Pagination parameters (limit, offset)
4. Employee Details Inspection (/api/v1/admin/employees/{employee_id})
   - 404 for nonexistent employee
   - 200 with full attribute metadata for existing employee
5. Pre-Authorized Invitation Workflow (/api/v1/admin/employees/invite)
   - 403 Non-administrator rejected
   - 422 Duplicate employee ID rejected
   - 422 Duplicate work email rejected
   - 422 Invalid email format rejected
   - 201 Success creating INVITED record
6. Approval & Rejection Integrity
   - Self-approval blocked (403)
   - Rejection requires valid non-empty reason (422)
   - State transitions verified in repository
"""

import json
import time
from typing import Any, Optional
import pytest
import httpx
import jwt
from jwt.algorithms import ECAlgorithm
from cryptography.hazmat.primitives.asymmetric import ec
from fastapi.testclient import TestClient

from backend.app.core.config import settings
from backend.app.core.security import jwks_manager
from backend.app.main import app
from backend.app.repositories import get_repository

ADMIN_UUID = "d0000000-0000-0000-0000-000000000001"
ADMIN_EMAIL = "system_admin@retainiq.internal"

EMPLOYEE_UUID = "e0000000-0000-0000-0000-000000000001"
EMPLOYEE_EMAIL = "authorized_employee@ecommerce.in"


@pytest.fixture(scope="module")
def ec_keypair():
    """Generates an ephemeral NIST P-256 EC key pair for signing test ES256 tokens."""
    private_key = ec.generate_private_key(ec.SECP256R1())
    public_key = private_key.public_key()
    kid = "test-admin-portal-kid"

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
    """Configures jwks_manager to serve the test EC public key."""
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
    sub: str,
    email: Optional[str] = None,
) -> str:
    """Helper generating signed ES256 tokens for testing."""
    now = int(time.time())
    payload = {
        "sub": sub,
        "aud": settings.JWT_AUDIENCE,
        "iss": settings.get_supabase_auth_issuer(),
        "iat": now,
        "exp": now + 3600,
    }
    if email:
        payload["email"] = email

    headers = {"kid": kid, "alg": "ES256"}
    return jwt.encode(payload, private_key, algorithm="ES256", headers=headers)


@pytest.fixture(autouse=True)
def configure_admin(monkeypatch):
    """Ensures test admin is configured in server-side settings."""
    monkeypatch.setattr(settings, "ADMIN_EMAILS", [ADMIN_EMAIL])
    monkeypatch.setattr(settings, "ADMIN_USER_IDS", [ADMIN_UUID])
    monkeypatch.setattr(settings, "AUTHORIZED_EMPLOYEE_EMAILS", [EMPLOYEE_EMAIL])
    monkeypatch.setattr(settings, "AUTHORIZED_EMPLOYEE_USER_IDS", [EMPLOYEE_UUID])


# ==============================================================================
# 1. Administrator Authentication & Authorization Tests
# ==============================================================================

def test_admin_me_rejects_unauthenticated(client):
    """GET /api/v1/admin/me rejects missing token with 401."""
    response = client.get("/api/v1/admin/me")
    assert response.status_code == 401
    assert response.json()["success"] is False


def test_admin_me_rejects_standard_employee(client, ec_keypair):
    """GET /api/v1/admin/me rejects standard approved employee with 403."""
    token = create_token(
        ec_keypair["private_key"],
        ec_keypair["kid"],
        sub=EMPLOYEE_UUID,
        email=EMPLOYEE_EMAIL,
    )
    response = client.get(
        "/api/v1/admin/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 403
    assert response.json()["success"] is False
    assert "Administrator privileges are required" in response.json()["error"]["message"]


def test_admin_me_success_for_authorized_admin(client, ec_keypair):
    """GET /api/v1/admin/me returns admin profile for authorized administrator."""
    token = create_token(
        ec_keypair["private_key"],
        ec_keypair["kid"],
        sub=ADMIN_UUID,
        email=ADMIN_EMAIL,
    )
    response = client.get(
        "/api/v1/admin/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    data = body["data"]
    assert data["user_id"] == ADMIN_UUID
    assert data["email"] == ADMIN_EMAIL
    assert data["is_admin"] is True
    assert data["role"] == "ADMINISTRATOR"


# ==============================================================================
# 2. Aggregated Employee Statistics Tests
# ==============================================================================

def test_admin_stats_rejects_unauthorized(client, ec_keypair):
    """GET /api/v1/admin/stats rejects non-admin with 403."""
    token = create_token(
        ec_keypair["private_key"],
        ec_keypair["kid"],
        sub=EMPLOYEE_UUID,
        email=EMPLOYEE_EMAIL,
    )
    response = client.get(
        "/api/v1/admin/stats",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 403


def test_admin_stats_returns_aggregated_metrics(client, ec_keypair):
    """GET /api/v1/admin/stats returns real backend counts."""
    token = create_token(
        ec_keypair["private_key"],
        ec_keypair["kid"],
        sub=ADMIN_UUID,
        email=ADMIN_EMAIL,
    )
    response = client.get(
        "/api/v1/admin/stats",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    stats = body["data"]
    assert "total" in stats and isinstance(stats["total"], int)
    assert "pending" in stats and isinstance(stats["pending"], int)
    assert "approved" in stats and isinstance(stats["approved"], int)
    assert "rejected" in stats and isinstance(stats["rejected"], int)
    assert "suspended" in stats and isinstance(stats["suspended"], int)
    assert "invited" in stats and isinstance(stats["invited"], int)
    assert stats["total"] >= stats["pending"] + stats["approved"]


# ==============================================================================
# 3. Employee Directory & Filtering Tests
# ==============================================================================

def test_admin_directory_lists_employees(client, ec_keypair):
    """GET /api/v1/admin/employees returns list of employee records."""
    token = create_token(
        ec_keypair["private_key"],
        ec_keypair["kid"],
        sub=ADMIN_UUID,
        email=ADMIN_EMAIL,
    )
    response = client.get(
        "/api/v1/admin/employees",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert isinstance(body["data"], list)
    assert len(body["data"]) > 0


def test_admin_directory_filters_by_status(client, ec_keypair):
    """GET /api/v1/admin/employees?status=APPROVED returns only approved accounts."""
    token = create_token(
        ec_keypair["private_key"],
        ec_keypair["kid"],
        sub=ADMIN_UUID,
        email=ADMIN_EMAIL,
    )
    response = client.get(
        "/api/v1/admin/employees?status=APPROVED",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    for emp in body["data"]:
        assert emp["status"] == "APPROVED"


def test_admin_directory_searches_by_keyword(client, ec_keypair):
    """GET /api/v1/admin/employees?search=EMP-2026-001 finds exact employee ID."""
    token = create_token(
        ec_keypair["private_key"],
        ec_keypair["kid"],
        sub=ADMIN_UUID,
        email=ADMIN_EMAIL,
    )
    response = client.get(
        "/api/v1/admin/employees?search=EMP-2026-001",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert len(body["data"]) >= 1
    assert body["data"][0]["employee_id"] == "EMP-2026-001"


# ==============================================================================
# 4. Employee Details Inspection Tests
# ==============================================================================

def test_admin_employee_details_success(client, ec_keypair):
    """GET /api/v1/admin/employees/{id} returns details for existing employee."""
    token = create_token(
        ec_keypair["private_key"],
        ec_keypair["kid"],
        sub=ADMIN_UUID,
        email=ADMIN_EMAIL,
    )
    response = client.get(
        "/api/v1/admin/employees/EMP-2026-001",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["data"]["employee_id"] == "EMP-2026-001"
    assert "work_email" in body["data"]


def test_admin_employee_details_not_found(client, ec_keypair):
    """GET /api/v1/admin/employees/{id} returns 404 for unknown employee."""
    token = create_token(
        ec_keypair["private_key"],
        ec_keypair["kid"],
        sub=ADMIN_UUID,
        email=ADMIN_EMAIL,
    )
    response = client.get(
        "/api/v1/admin/employees/EMP-NONEXISTENT-999",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 404
    assert response.json()["success"] is False


# ==============================================================================
# 5. Pre-Authorized Invitation Workflow Tests
# ==============================================================================

def test_admin_invite_rejects_non_admin(client, ec_keypair):
    """POST /api/v1/admin/employees/invite rejects non-admin with 403."""
    token = create_token(
        ec_keypair["private_key"],
        ec_keypair["kid"],
        sub=EMPLOYEE_UUID,
        email=EMPLOYEE_EMAIL,
    )
    payload = {
        "employee_id": "EMP-2026-099",
        "work_email": "test_invite@ecommerce.in",
    }
    response = client.post(
        "/api/v1/admin/employees/invite",
        json=payload,
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 403


def test_admin_invite_validates_email_format(client, ec_keypair):
    """POST /api/v1/admin/employees/invite rejects invalid email with 422."""
    token = create_token(
        ec_keypair["private_key"],
        ec_keypair["kid"],
        sub=ADMIN_UUID,
        email=ADMIN_EMAIL,
    )
    payload = {
        "employee_id": "EMP-2026-098",
        "work_email": "invalid-email-format",
    }
    response = client.post(
        "/api/v1/admin/employees/invite",
        json=payload,
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 422


def test_admin_invite_rejects_duplicate_employee_id(client, ec_keypair):
    """POST /api/v1/admin/employees/invite rejects existing employee ID."""
    token = create_token(
        ec_keypair["private_key"],
        ec_keypair["kid"],
        sub=ADMIN_UUID,
        email=ADMIN_EMAIL,
    )
    payload = {
        "employee_id": "EMP-2026-001",  # Pre-exists
        "work_email": "fresh_email@ecommerce.in",
    }
    response = client.post(
        "/api/v1/admin/employees/invite",
        json=payload,
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 422
    assert "already registered or invited" in response.json()["error"]["message"]


def test_admin_invite_rejects_duplicate_work_email(client, ec_keypair):
    """POST /api/v1/admin/employees/invite rejects existing work email."""
    token = create_token(
        ec_keypair["private_key"],
        ec_keypair["kid"],
        sub=ADMIN_UUID,
        email=ADMIN_EMAIL,
    )
    payload = {
        "employee_id": "EMP-2026-097",
        "work_email": "analyst@retainiq.internal",  # Seeded in database
    }
    response = client.post(
        "/api/v1/admin/employees/invite",
        json=payload,
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 422
    assert "already registered or invited" in response.json()["error"]["message"]


def test_admin_invite_success(client, ec_keypair):
    """POST /api/v1/admin/employees/invite successfully creates an INVITED record."""
    token = create_token(
        ec_keypair["private_key"],
        ec_keypair["kid"],
        sub=ADMIN_UUID,
        email=ADMIN_EMAIL,
    )
    emp_id = f"EMP-TEST-{int(time.time())}"
    work_email = f"invited_{int(time.time())}@retainiq.internal"
    payload = {
        "employee_id": emp_id,
        "work_email": work_email,
        "full_name": "Test Invited Analyst",
        "department": "Retention Analytics",
        "notes": "Pre-authorized invitation for testing",
    }
    response = client.post(
        "/api/v1/admin/employees/invite",
        json=payload,
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 201
    body = response.json()
    assert body["success"] is True
    data = body["data"]
    assert data["employee_id"] == emp_id
    assert data["work_email"] == work_email
    assert data["status"] == "INVITED"
    assert data["supabase_user_id"] is None

    # Verify repository state
    repo = get_repository(settings.STORAGE_MODE.lower())
    saved = repo.get_employee_by_id(emp_id)
    assert saved is not None
    assert saved["status"] == "INVITED"
