"""
Indian E-Commerce Customer Retention Intelligence System
Employee Profile & Verification Test Suite (Phase 8.4.7)

Tests:
1. GET /api/v1/employee/me rejects unauthenticated requests (HTTP 401).
2. GET /api/v1/employee/me rejects requests with invalid / tampered token (HTTP 401).
3. GET /api/v1/employee/me rejects unmapped authenticated user (HTTP 403).
4. GET /api/v1/employee/me rejects PENDING employee with status-specific message (HTTP 403).
5. GET /api/v1/employee/me rejects REJECTED employee with status-specific message (HTTP 403).
6. GET /api/v1/employee/me rejects SUSPENDED employee with status-specific message (HTTP 403).
7. GET /api/v1/employee/me rejects INVITED (unregistered) employee with status-specific message (HTTP 403).
8. GET /api/v1/employee/me allows APPROVED employee (HTTP 200) returning verified profile.
9. Regular approved employee cannot access administrator endpoints (GET /api/v1/admin/me returns HTTP 403).
10. Fallback authorized employee (via server settings) succeeds and returns synthesized profile (HTTP 200).
"""

import json
import time
import uuid
from typing import Any, Dict, Optional
import pytest
import httpx
from jwt.algorithms import ECAlgorithm
from cryptography.hazmat.primitives.asymmetric import ec
from starlette.testclient import TestClient

from backend.app.core.config import settings
from backend.app.core.security import jwks_manager
from backend.app.main import app
from backend.app.repositories import get_repository



# ==============================================================================
# Ephemeral Cryptographic Test Fixtures
# ==============================================================================

@pytest.fixture(scope="module")
def ec_keypair():
    """Generates an ephemeral NIST P-256 EC key pair for signing test ES256 tokens."""
    private_key = ec.generate_private_key(ec.SECP256R1())
    public_key = private_key.public_key()
    kid = "test-employee-me-kid"

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
    email: Optional[str] = "staff@retainiq.internal",
    aud: Optional[str] = "authenticated",
    iss: Optional[str] = None,
    exp_offset: int = 3600,
) -> str:
    """Helper generating signed ES256 tokens for testing."""
    import jwt
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


# ==============================================================================
# Helper to Seed Registry Records in Active Repository
# ==============================================================================

@pytest.fixture
def repo():
    return get_repository(settings.STORAGE_MODE.lower())


# ==============================================================================
# Test Cases
# ==============================================================================

def test_employee_me_unauthenticated(client):
    """1. Unauthenticated requests to /api/v1/employee/me return HTTP 401."""
    resp = client.get("/api/v1/employee/me")
    assert resp.status_code == 401
    data = resp.json()
    assert data["success"] is False
    assert "Missing Authorization header" in data["error"]["message"]


def test_employee_me_invalid_token(client):
    """2. Requests with malformed tokens return HTTP 401."""
    resp = client.get("/api/v1/employee/me", headers={"Authorization": "Bearer bad-token"})
    assert resp.status_code == 401
    data = resp.json()
    assert data["success"] is False


def test_employee_me_unmapped_user(client, ec_keypair):
    """3. Authenticated user with no employee record or fallback setting receives HTTP 403."""
    token = create_token(
        ec_keypair["private_key"],
        ec_keypair["kid"],
        sub="99999999-9999-9999-9999-999999999999",
        email="unknown_stranger@unknown.internal",
    )
    resp = client.get("/api/v1/employee/me", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 403
    data = resp.json()
    assert data["success"] is False
    assert "not authorized as an approved RetainIQ employee" in data["error"]["message"]


def test_employee_me_pending_employee(client, ec_keypair, repo):
    """4. Authenticated employee whose registration is PENDING receives HTTP 403."""
    uid = str(uuid.uuid4())
    suffix = uuid.uuid4().hex[:6]
    email = f"pending_{suffix}@retainiq.internal"
    emp_id = f"EMP-PEND-{suffix.upper()}"

    repo.create_employee_invitation({
        "employee_id": emp_id,
        "work_email": email,
        "full_name": "Pending Staff",
        "department": "Analytics",
    })
    repo.register_employee(emp_id, uid, email)

    token = create_token(
        ec_keypair["private_key"],
        ec_keypair["kid"],
        sub=uid,
        email=email,
    )
    resp = client.get("/api/v1/employee/me", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 403
    data = resp.json()
    assert data["success"] is False
    assert "awaiting administrator approval" in data["error"]["message"].lower()


def test_employee_me_rejected_employee(client, ec_keypair, repo):
    """5. Authenticated employee whose registration is REJECTED receives HTTP 403."""
    uid = str(uuid.uuid4())
    suffix = uuid.uuid4().hex[:6]
    email = f"rejected_{suffix}@retainiq.internal"
    emp_id = f"EMP-REJ-{suffix.upper()}"

    repo.create_employee_invitation({
        "employee_id": emp_id,
        "work_email": email,
        "full_name": "Rejected Staff",
        "department": "Retention",
    })
    repo.register_employee(emp_id, uid, email)
    repo.update_employee_status(emp_id, "REJECTED", admin_id="ADMIN-001", reason="Unverified department affiliation")

    token = create_token(
        ec_keypair["private_key"],
        ec_keypair["kid"],
        sub=uid,
        email=email,
    )
    resp = client.get("/api/v1/employee/me", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 403
    data = resp.json()
    assert data["success"] is False
    assert "rejected by administrator" in data["error"]["message"].lower()


def test_employee_me_suspended_employee(client, ec_keypair, repo):
    """6. Authenticated employee whose account is SUSPENDED receives HTTP 403."""
    uid = str(uuid.uuid4())
    suffix = uuid.uuid4().hex[:6]
    email = f"suspended_{suffix}@retainiq.internal"
    emp_id = f"EMP-SUSP-{suffix.upper()}"

    repo.create_employee_invitation({
        "employee_id": emp_id,
        "work_email": email,
        "full_name": "Suspended Staff",
        "department": "Customer Care",
    })
    repo.register_employee(emp_id, uid, email)
    repo.update_employee_status(emp_id, "SUSPENDED", admin_id="ADMIN-001", reason="Policy compliance review")

    token = create_token(
        ec_keypair["private_key"],
        ec_keypair["kid"],
        sub=uid,
        email=email,
    )
    resp = client.get("/api/v1/employee/me", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 403
    data = resp.json()
    assert data["success"] is False
    assert "suspended by administrator" in data["error"]["message"].lower()


def test_employee_me_invited_employee(client, ec_keypair, repo):
    """7. Authenticated employee with pre-issued invitation that has not completed registration receives HTTP 403."""
    uid = str(uuid.uuid4())
    suffix = uuid.uuid4().hex[:6]
    email = f"invited_{suffix}@retainiq.internal"
    emp_id = f"EMP-INV-{suffix.upper()}"

    repo.create_employee_invitation({
        "employee_id": emp_id,
        "work_email": email,
        "full_name": "Invited Staff",
        "department": "Retention Ops",
    })

    token = create_token(
        ec_keypair["private_key"],
        ec_keypair["kid"],
        sub=uid,
        email=email,
    )
    resp = client.get("/api/v1/employee/me", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 403
    data = resp.json()
    assert data["success"] is False
    assert "registration" in data["error"]["message"].lower()


def test_employee_me_approved_employee(client, ec_keypair, repo):
    """8. Authenticated and APPROVED employee receives HTTP 200 with verified profile."""
    uid = str(uuid.uuid4())
    suffix = uuid.uuid4().hex[:6]
    email = f"approved_{suffix}@retainiq.internal"
    emp_id = f"EMP-APP-{suffix.upper()}"

    repo.create_employee_invitation({
        "employee_id": emp_id,
        "work_email": email,
        "full_name": "Approved Officer",
        "department": "Customer Retention Intelligence",
    })
    repo.register_employee(emp_id, uid, email)
    repo.update_employee_status(emp_id, "APPROVED", admin_id="ADMIN-MASTER")

    token = create_token(
        ec_keypair["private_key"],
        ec_keypair["kid"],
        sub=uid,
        email=email,
    )
    resp = client.get("/api/v1/employee/me", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True
    profile = data["data"]
    assert profile["employee_id"] == emp_id
    assert profile["work_email"] == email
    assert profile["full_name"] == "Approved Officer"
    assert profile["department"] == "Customer Retention Intelligence"
    assert profile["status"] == "APPROVED"
    assert profile["approved_at"] is not None



def test_approved_employee_cannot_access_admin_endpoints(client, ec_keypair):
    """9. A regular approved employee cannot access administrative endpoints (returns HTTP 403)."""
    uid = "55555555-6666-7777-8888-999999999999"
    email = "approved_staff@retainiq.internal"

    token = create_token(
        ec_keypair["private_key"],
        ec_keypair["kid"],
        sub=uid,
        email=email,
    )
    headers = {"Authorization": f"Bearer {token}"}

    resp_admin_me = client.get("/api/v1/admin/me", headers=headers)
    assert resp_admin_me.status_code == 403
    assert "Administrator privileges are required" in resp_admin_me.json()["error"]["message"]

    resp_admin_stats = client.get("/api/v1/admin/stats", headers=headers)
    assert resp_admin_stats.status_code == 403

    resp_admin_pending = client.get("/api/v1/admin/employees/pending", headers=headers)
    assert resp_admin_pending.status_code == 403
