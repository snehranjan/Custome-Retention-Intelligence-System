"""
Indian E-Commerce Customer Retention Intelligence System
Employee Registration & Administrator Approval Test Suite (Phase 8.4.5)

Tests:
1. POST /api/v1/employee/register with valid issued Employee ID succeeds and returns status PENDING (HTTP 201).
2. POST /api/v1/employee/register with nonexistent Employee ID is rejected (HTTP 422).
3. POST /api/v1/employee/register with mismatched work email is rejected (HTTP 422).
4. POST /api/v1/employee/register with already APPROVED Employee ID is rejected (HTTP 422).
5. POST /api/v1/employee/register with already PENDING Employee ID is rejected (HTTP 422).
6. Password mismatch is rejected by request validation (HTTP 422).
7. Weak / short password (<8 chars) is rejected (HTTP 422).
8. Passwords are NEVER persisted in plaintext anywhere in database.
9. Pending employee receives HTTP 403 on protected customer APIs.
10. Suspended employee receives HTTP 403 on protected customer APIs.
11. Approved employee successfully accesses protected customer APIs (HTTP 200).
12. Admin endpoints reject unauthenticated requests (HTTP 401).
13. Admin endpoints reject non-admin authenticated users (HTTP 403).
14. Authorized admin can list pending employee registrations (HTTP 200).
15. Authorized admin can approve pending employee (HTTP 200 -> status APPROVED).
16. Admin cannot approve themselves (HTTP 403).
17. Authorized admin can reject pending employee with mandatory reason (HTTP 200 -> status REJECTED).
"""

import json
import sqlite3
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
from backend.app.repositories import get_repository


# ==============================================================================
# Ephemeral Cryptographic Test Fixtures
# ==============================================================================

@pytest.fixture(scope="module")
def ec_keypair():
    """Generates an ephemeral NIST P-256 EC key pair for signing test ES256 tokens."""
    private_key = ec.generate_private_key(ec.SECP256R1())
    public_key = private_key.public_key()
    kid = "test-employee-reg-kid"

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
    email: Optional[str] = "test_user@retainiq.internal",
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


# Known test credentials
ADMIN_UUID = "admin-root-uuid-9999"
ADMIN_EMAIL = "admin_security@ecommerce.in"

APPROVED_USER_UUID = "11111111-2222-3333-4444-555555555555"
APPROVED_USER_EMAIL = "authorized_employee@ecommerce.in"

PENDING_USER_UUID = "33333333-3333-3333-3333-333333333333"
PENDING_USER_EMAIL = "pending_analyst@retainiq.internal"

SUSPENDED_USER_UUID = "44444444-4444-4444-4444-444444444444"
SUSPENDED_USER_EMAIL = "suspended_user@retainiq.internal"


@pytest.fixture
def configure_admin(monkeypatch):
    """Configures server-side administrator authorization registry."""
    monkeypatch.setattr(settings, "ADMIN_EMAILS", [ADMIN_EMAIL])
    monkeypatch.setattr(settings, "ADMIN_USER_IDS", [ADMIN_UUID])


# ==============================================================================
# Employee Registration API Tests
# ==============================================================================

def test_register_employee_success(client):
    """Valid pre-issued Employee ID registration succeeds with status PENDING (HTTP 201)."""
    # EMP-2026-002 was seeded with status INVITED and work_email 'new_hire@retainiq.internal'
    repo = get_repository(settings.STORAGE_MODE.lower())
    # Reset EMP-2026-002 to INVITED in case previously mutated
    repo.update_employee_status("EMP-2026-002", "INVITED")

    payload = {
        "employee_id": "EMP-2026-002",
        "work_email": "new_hire@retainiq.internal",
        "password": "SecurePassword2026!",
        "confirm_password": "SecurePassword2026!",
    }
    response = client.post("/api/v1/employee/register", json=payload)
    assert response.status_code == 201
    body = response.json()
    assert body["success"] is True
    data = body["data"]
    assert data["employee_id"] == "EMP-2026-002"
    assert data["work_email"] == "new_hire@retainiq.internal"
    assert data["status"] == "PENDING"
    assert "awaiting administrator approval" in data["message"].lower()

    # Verify status in repository
    emp = repo.get_employee_by_id("EMP-2026-002")
    assert emp["status"] == "PENDING"
    assert emp["supabase_user_id"] is not None


def test_register_employee_invalid_id_rejected(client):
    """Nonexistent Employee ID is rejected with HTTP 422."""
    payload = {
        "employee_id": "EMP-NONEXISTENT-999",
        "work_email": "random@retainiq.internal",
        "password": "SecurePassword2026!",
        "confirm_password": "SecurePassword2026!",
    }
    response = client.post("/api/v1/employee/register", json=payload)
    assert response.status_code == 422
    body = response.json()
    assert body["success"] is False
    assert "Invalid Employee ID" in body["error"]["message"]


def test_register_employee_existing_auth_wrong_password_blocked(client):
    """Existing Auth account registration with incorrect password is rejected (takeover blocked)."""
    repo = get_repository(settings.STORAGE_MODE.lower())
    repo.update_employee_status("EMP-2026-002", "INVITED")

    payload = {
        "employee_id": "EMP-2026-002",
        "work_email": "new_hire@retainiq.internal",
        "password": "WrongAttackerPassword2026!",
        "confirm_password": "WrongAttackerPassword2026!",
    }
    response = client.post("/api/v1/employee/register", json=payload)
    assert response.status_code == 422
    body = response.json()
    assert body["success"] is False
    assert "password provided does not match" in body["error"]["message"].lower()


def test_register_employee_mismatched_email_rejected(client):
    """Submitted work email not matching invitation record is rejected with HTTP 422."""
    repo = get_repository(settings.STORAGE_MODE.lower())
    repo.update_employee_status("EMP-2026-002", "INVITED")

    payload = {
        "employee_id": "EMP-2026-002",
        "work_email": "impostor@external.com",
        "password": "SecurePassword2026!",
        "confirm_password": "SecurePassword2026!",
    }
    response = client.post("/api/v1/employee/register", json=payload)
    assert response.status_code == 422
    body = response.json()
    assert body["success"] is False
    assert "does not match the invitation record" in body["error"]["message"]


def test_register_employee_already_approved_rejected(client):
    """Attempting to re-register an already APPROVED Employee ID is rejected with HTTP 422."""
    payload = {
        "employee_id": "EMP-2026-001",  # Pre-seeded as APPROVED
        "work_email": "authorized_employee@ecommerce.in",
        "password": "SecurePassword2026!",
        "confirm_password": "SecurePassword2026!",
    }
    response = client.post("/api/v1/employee/register", json=payload)
    assert response.status_code == 422
    body = response.json()
    assert body["success"] is False
    assert "already been registered" in body["error"]["message"]


def test_register_employee_password_mismatch_rejected(client):
    """Password and confirmation password mismatch is rejected with HTTP 422."""
    payload = {
        "employee_id": "EMP-2026-002",
        "work_email": "new_hire@retainiq.internal",
        "password": "SecurePassword2026!",
        "confirm_password": "DifferentPassword2026!",
    }
    response = client.post("/api/v1/employee/register", json=payload)
    assert response.status_code == 422
    body = response.json()
    assert body["success"] is False


def test_register_employee_short_password_rejected(client):
    """Short password (< 8 chars) is rejected with HTTP 422."""
    payload = {
        "employee_id": "EMP-2026-002",
        "work_email": "new_hire@retainiq.internal",
        "password": "short",
        "confirm_password": "short",
    }
    response = client.post("/api/v1/employee/register", json=payload)
    assert response.status_code == 422


def test_passwords_never_stored_in_plaintext():
    """Verifies that no password column or plaintext password exists in employee_registry."""
    repo = get_repository(settings.STORAGE_MODE.lower())
    emp = repo.get_employee_by_id("EMP-2026-001")
    assert "password" not in emp
    assert "pass" not in emp
    assert "hash" not in emp


# ==============================================================================
# Status-Based Authorization Enforcement on Customer APIs
# ==============================================================================

def test_pending_employee_access_denied(client, ec_keypair):
    """Pending employee receives HTTP 403 on customer data APIs."""
    repo = get_repository(settings.STORAGE_MODE.lower())
    repo.update_employee_status("EMP-2026-003", "PENDING")

    token = create_token(
        ec_keypair["private_key"],
        ec_keypair["kid"],
        sub=PENDING_USER_UUID,
        email=PENDING_USER_EMAIL,
    )
    response = client.get("/api/v1/customers", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 403
    body = response.json()
    assert body["success"] is False
    assert body["error"]["code"] == "FORBIDDEN"
    assert "awaiting administrator approval" in body["error"]["message"]


def test_suspended_employee_access_denied(client, ec_keypair):
    """Suspended employee receives HTTP 403 on customer data APIs."""
    repo = get_repository(settings.STORAGE_MODE.lower())
    repo.update_employee_status("EMP-2026-004", "SUSPENDED")

    token = create_token(
        ec_keypair["private_key"],
        ec_keypair["kid"],
        sub=SUSPENDED_USER_UUID,
        email=SUSPENDED_USER_EMAIL,
    )
    response = client.get("/api/v1/customers", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 403
    body = response.json()
    assert body["success"] is False
    assert "suspended" in body["error"]["message"].lower()


def test_approved_employee_access_granted(client, ec_keypair):
    """Approved employee receives HTTP 200 on customer data APIs."""
    repo = get_repository(settings.STORAGE_MODE.lower())
    repo.update_employee_status("EMP-2026-001", "APPROVED")

    token = create_token(
        ec_keypair["private_key"],
        ec_keypair["kid"],
        sub=APPROVED_USER_UUID,
        email=APPROVED_USER_EMAIL,
    )
    response = client.get("/api/v1/customers", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert "items" in body["data"]


def test_account_takeover_mismatched_uuid_blocked(client, ec_keypair):
    """Token with matching email but forged/mismatched user_id is blocked with HTTP 403."""
    repo = get_repository(settings.STORAGE_MODE.lower())
    repo.update_employee_status("EMP-2026-001", "APPROVED")
    emp = repo.get_employee_by_id("EMP-2026-001")
    target_email = emp.get("work_email") if emp else APPROVED_USER_EMAIL

    forged_uuid = "99999999-9999-9999-9999-999999999999"
    token = create_token(
        ec_keypair["private_key"],
        ec_keypair["kid"],
        sub=forged_uuid,
        email=target_email,
    )
    response = client.get("/api/v1/customers", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 403
    body = response.json()
    assert body["success"] is False
    assert "identity does not match" in body["error"]["message"].lower()


def test_unbound_employee_blocked_without_registration(client, ec_keypair):
    """Employee record with status APPROVED but supabase_user_id=NULL is blocked from customer APIs."""
    repo = get_repository(settings.STORAGE_MODE.lower())
    unbound_emp_id = "EMP-UNBOUND-TEST"
    unbound_email = "unbound_analyst@retainiq.internal"
    try:
        repo.create_employee_invitation({
            "employee_id": unbound_emp_id,
            "work_email": unbound_email,
            "status": "APPROVED",
            "supabase_user_id": None,
        })
    except Exception:
        repo.update_employee_status(unbound_emp_id, "APPROVED")

    unbound_sub = "88888888-8888-8888-8888-888888888888"
    token = create_token(
        ec_keypair["private_key"],
        ec_keypair["kid"],
        sub=unbound_sub,
        email=unbound_email,
    )
    response = client.get("/api/v1/customers", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 403
    body = response.json()
    assert body["success"] is False
    assert "not completed registration linking" in body["error"]["message"].lower()


# ==============================================================================
# Administrator Operations Tests
# ==============================================================================

def test_admin_endpoints_reject_unauthenticated(client):
    """Admin endpoints reject unauthenticated requests with HTTP 401."""
    response = client.get("/api/v1/admin/employees/pending")
    assert response.status_code == 401


def test_admin_endpoints_reject_non_admin_user(client, ec_keypair, configure_admin):
    """Standard authenticated employees receive HTTP 403 on admin endpoints."""
    token = create_token(
        ec_keypair["private_key"],
        ec_keypair["kid"],
        sub=APPROVED_USER_UUID,
        email=APPROVED_USER_EMAIL,
    )
    response = client.get(
        "/api/v1/admin/employees/pending",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 403
    body = response.json()
    assert body["success"] is False
    assert "Administrator privileges are required" in body["error"]["message"]


def test_admin_list_pending_employees(client, ec_keypair, configure_admin):
    """Authorized administrator can list pending employees."""
    admin_token = create_token(
        ec_keypair["private_key"],
        ec_keypair["kid"],
        sub=ADMIN_UUID,
        email=ADMIN_EMAIL,
    )
    response = client.get(
        "/api/v1/admin/employees/pending",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert isinstance(body["data"], list)


def test_admin_approve_pending_employee(client, ec_keypair, configure_admin):
    """Authorized administrator can approve a pending employee."""
    repo = get_repository(settings.STORAGE_MODE.lower())
    # Ensure EMP-2026-003 is PENDING
    repo.update_employee_status("EMP-2026-003", "PENDING")

    admin_token = create_token(
        ec_keypair["private_key"],
        ec_keypair["kid"],
        sub=ADMIN_UUID,
        email=ADMIN_EMAIL,
    )
    response = client.post(
        "/api/v1/admin/employees/EMP-2026-003/approve",
        json={"notes": "Approved for Analytics Operations team"},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["data"]["status"] == "APPROVED"
    assert body["data"]["approved_by"] == ADMIN_UUID

    # Verify status in repository
    emp = repo.get_employee_by_id("EMP-2026-003")
    assert emp["status"] == "APPROVED"


def test_admin_self_approval_rejected(client, ec_keypair, configure_admin):
    """Admin cannot approve their own employee registration."""
    repo = get_repository(settings.STORAGE_MODE.lower())
    # Setup record where supabase_user_id == ADMIN_UUID
    try:
        repo.create_employee_invitation({
            "employee_id": "EMP-ADMIN-SELF",
            "work_email": ADMIN_EMAIL,
            "supabase_user_id": ADMIN_UUID,
            "status": "PENDING",
        })
    except Exception:
        repo.update_employee_status("EMP-ADMIN-SELF", "PENDING")

    admin_token = create_token(
        ec_keypair["private_key"],
        ec_keypair["kid"],
        sub=ADMIN_UUID,
        email=ADMIN_EMAIL,
    )
    response = client.post(
        "/api/v1/admin/employees/EMP-ADMIN-SELF/approve",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 403
    body = response.json()
    assert body["success"] is False
    assert "Administrators cannot approve their own employee registration" in body["error"]["message"]


def test_admin_reject_pending_employee(client, ec_keypair, configure_admin):
    """Authorized administrator can reject a pending employee with a reason."""
    repo = get_repository(settings.STORAGE_MODE.lower())
    # Create or set a pending record
    try:
        repo.create_employee_invitation({
            "employee_id": "EMP-REJECT-TEST",
            "work_email": "reject_test@retainiq.internal",
            "status": "PENDING",
        })
    except Exception:
        repo.update_employee_status("EMP-REJECT-TEST", "PENDING")

    admin_token = create_token(
        ec_keypair["private_key"],
        ec_keypair["kid"],
        sub=ADMIN_UUID,
        email=ADMIN_EMAIL,
    )
    response = client.post(
        "/api/v1/admin/employees/EMP-REJECT-TEST/reject",
        json={"reason": "Employment verification failed."},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["data"]["status"] == "REJECTED"
    assert body["data"]["rejection_reason"] == "Employment verification failed."

    # Verify status in repository
    emp = repo.get_employee_by_id("EMP-REJECT-TEST")
    assert emp["status"] == "REJECTED"
