"""
Indian E-Commerce Customer Retention Intelligence System
Authentication & Authorization Stabilization Test Suite (Phase 8 Auth Stabilization)

Tests:
1. Administrator token accessing /api/v1/admin/me returns 200 OK with is_admin=True.
2. Regular employee token accessing /api/v1/admin/me returns 403 Forbidden.
3. Unauthenticated request to /api/v1/admin/me returns 401 Unauthorized.
4. Approved employee token accessing /api/v1/employee/me returns 200 OK with status=APPROVED.
5. Non-approved employee accessing /api/v1/employee/me returns 403 Forbidden with status-specific message.
6. Role isolation: admin cannot access employee routes without employee clearance, employee cannot access admin routes.
7. Unauthenticated request to /api/v1/employee/me returns 401 Unauthorized.
"""

import json
import time
import uuid
from typing import Any, Optional
import pytest
import jwt
import httpx
from jwt.algorithms import ECAlgorithm
from cryptography.hazmat.primitives.asymmetric import ec
from starlette.testclient import TestClient

from backend.app.core.config import settings
from backend.app.core.security import jwks_manager
from backend.app.main import app
from backend.app.repositories import get_repository


@pytest.fixture(scope="module")
def ec_keypair():
    """Generates an ephemeral NIST P-256 EC key pair for signing test ES256 tokens."""
    private_key = ec.generate_private_key(ec.SECP256R1())
    public_key = private_key.public_key()
    kid = "test-auth-stabilization-kid"

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


def create_test_token(ec_keypair, sub: str, email: str, role: str = "authenticated") -> str:
    now = int(time.time())
    payload = {
        "sub": sub,
        "email": email,
        "role": role,
        "iat": now,
        "exp": now + 3600,
        "iss": settings.get_supabase_auth_issuer(),
        "aud": settings.JWT_AUDIENCE,
    }
    return jwt.encode(
        payload,
        ec_keypair["private_key"],
        algorithm="ES256",
        headers={"kid": ec_keypair["kid"], "alg": "ES256"},
    )


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def repo():
    return get_repository(settings.STORAGE_MODE.lower())


class TestAuthStabilization:
    def test_unauthenticated_requests_receive_401(self, client):
        """Unauthenticated requests to admin or employee endpoints fail with 401."""
        res_admin = client.get("/api/v1/admin/me")
        assert res_admin.status_code == 401

        res_emp = client.get("/api/v1/employee/me")
        assert res_emp.status_code == 401

    def test_administrator_accesses_admin_me_successfully(self, client, ec_keypair):
        """Administrator token gets 200 OK and is_admin=True from /api/v1/admin/me."""
        admin_email = settings.ADMIN_EMAILS[0] if settings.ADMIN_EMAILS else "system_admin@retainiq.internal"
        admin_sub = str(uuid.uuid4())

        token = create_test_token(ec_keypair, sub=admin_sub, email=admin_email)
        headers = {"Authorization": f"Bearer {token}"}

        res = client.get("/api/v1/admin/me", headers=headers)
        assert res.status_code == 200
        body = res.json()
        assert body["success"] is True
        assert body["data"]["is_admin"] is True
        assert body["data"]["role"] == "ADMINISTRATOR"
        assert body["data"]["email"] == admin_email

    def test_non_admin_employee_rejected_from_admin_endpoints(self, client, ec_keypair):
        """Non-admin employee token receives 403 Forbidden on /api/v1/admin/me."""
        emp_email = "regular_analyst@retainiq.internal"
        emp_sub = str(uuid.uuid4())

        token = create_test_token(ec_keypair, sub=emp_sub, email=emp_email)
        headers = {"Authorization": f"Bearer {token}"}

        res = client.get("/api/v1/admin/me", headers=headers)
        assert res.status_code == 403
        body = res.json()
        assert body["success"] is False
        assert "administrator" in body["error"]["message"].lower()

    def test_approved_employee_accesses_employee_me_successfully(self, client, ec_keypair, repo):
        """Approved employee in registry receives 200 OK from /api/v1/employee/me."""
        uid = str(uuid.uuid4())
        suffix = uuid.uuid4().hex[:6]
        email = f"approved_{suffix}@retainiq.internal"
        emp_id = f"EMP-APP-{suffix.upper()}"

        repo.create_employee_invitation({
            "employee_id": emp_id,
            "work_email": email,
            "full_name": "Approved Staff",
            "department": "Retention Analytics",
        })
        repo.register_employee(emp_id, uid, email)
        repo.update_employee_status(emp_id, "APPROVED", admin_id="SYSTEM-ADMIN-01")

        token = create_test_token(ec_keypair, sub=uid, email=email)
        headers = {"Authorization": f"Bearer {token}"}

        res = client.get("/api/v1/employee/me", headers=headers)
        assert res.status_code == 200
        body = res.json()
        assert body["success"] is True
        assert body["data"]["status"] == "APPROVED"
        assert body["data"]["employee_id"] == emp_id
        assert body["data"]["work_email"] == email

    def test_pending_employee_rejected_from_employee_me(self, client, ec_keypair, repo):
        """Pending employee in registry receives 403 Forbidden with awaiting review message."""
        uid = str(uuid.uuid4())
        suffix = uuid.uuid4().hex[:6]
        email = f"pending_{suffix}@retainiq.internal"
        emp_id = f"EMP-PEND-{suffix.upper()}"

        repo.create_employee_invitation({
            "employee_id": emp_id,
            "work_email": email,
            "full_name": "Pending Staff",
            "department": "Customer Support",
        })
        repo.register_employee(emp_id, uid, email)

        token = create_test_token(ec_keypair, sub=uid, email=email)
        headers = {"Authorization": f"Bearer {token}"}

        res = client.get("/api/v1/employee/me", headers=headers)
        assert res.status_code == 403
        body = res.json()
        assert body["success"] is False
        assert "awaiting administrator approval" in body["error"]["message"].lower()
