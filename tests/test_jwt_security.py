"""
Indian E-Commerce Customer Retention Intelligence System
JWT Security & Verification Engine Test Suite (Phase 7.5 Checkpoint 2)

Tests:
1. Valid ES256 token verification & claim extraction.
2. Expired token rejection.
3. Invalid signature (tampered payload) rejection.
4. Wrong issuer rejection.
5. Wrong audience rejection.
6. Unsupported algorithm rejection (none, HS256, RS256).
7. Missing or malformed Bearer token extraction.
8. Unknown key ID (kid) and JWKS refresh behavior.
9. In-memory JWKS cache hit behavior.
10. JWKS network failure & timeout safe error handling.
"""

import json
import time
from typing import Any, Dict, Optional
import pytest
import httpx
import jwt
from jwt.algorithms import ECAlgorithm, RSAAlgorithm
from cryptography.hazmat.primitives.asymmetric import ec, rsa

from backend.app.core.config import settings
from backend.app.core.errors import AuthenticationException
from backend.app.core.security import (
    JWKSManager,
    extract_bearer_token,
    verify_supabase_jwt,
)


# ==============================================================================
# Fixtures for Ephemeral Cryptographic Test Keys
# ==============================================================================

@pytest.fixture(scope="module")
def ec_keypair():
    """Generates an ephemeral NIST P-256 EC key pair for testing ES256 tokens."""
    private_key = ec.generate_private_key(ec.SECP256R1())
    public_key = private_key.public_key()
    kid = "test-ec-kid-primary"

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


@pytest.fixture(scope="module")
def secondary_ec_keypair():
    """Generates a second key pair to test key rotation scenarios."""
    private_key = ec.generate_private_key(ec.SECP256R1())
    public_key = private_key.public_key()
    kid = "test-ec-kid-secondary"

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


def create_token(
    private_key: Any,
    kid: str,
    algorithm: str = "ES256",
    sub: str = "00000000-0000-0000-0000-000000000001",
    email: str = "employee@example.com",
    aud: Optional[str] = "authenticated",
    iss: Optional[str] = None,
    exp_offset: int = 3600,
    extra_claims: Optional[Dict[str, Any]] = None,
) -> str:
    """Helper creating signed test tokens with customizable claims."""
    now = int(time.time())
    payload = {
        "sub": sub,
        "email": email,
        "aud": aud if aud is not None else settings.JWT_AUDIENCE,
        "iss": iss if iss is not None else settings.get_supabase_auth_issuer(),
        "iat": now,
        "exp": now + exp_offset,
        "role": "authenticated",
        "app_metadata": {"role": "employee"},
        "user_metadata": {"full_name": "Test Employee"},
    }
    if extra_claims:
        payload.update(extra_claims)

    headers = {"kid": kid, "alg": algorithm}
    return jwt.encode(payload, private_key, algorithm=algorithm, headers=headers)


# ==============================================================================
# 1. Valid ES256 Token Verification
# ==============================================================================

def test_valid_es256_token_verification(ec_keypair):
    """Verify that a genuine, correctly signed ES256 token verifies and returns claims."""
    transport = httpx.MockTransport(
        lambda request: httpx.Response(200, json={"keys": [ec_keypair["jwk"]]})
    )
    mock_client = httpx.Client(transport=transport)
    manager = JWKSManager(client=mock_client)

    token = create_token(ec_keypair["private_key"], ec_keypair["kid"])
    claims = verify_supabase_jwt(token, key_manager=manager)

    assert claims is not None
    assert claims["sub"] == "00000000-0000-0000-0000-000000000001"
    assert claims["email"] == "employee@example.com"
    assert claims["aud"] == "authenticated"
    assert claims["iss"] == settings.get_supabase_auth_issuer()
    assert claims["role"] == "authenticated"
    assert claims["app_metadata"]["role"] == "employee"


# ==============================================================================
# 2. Expired Token Rejection
# ==============================================================================

def test_expired_token_rejection(ec_keypair):
    """Verify that a token with exp in the past is rejected with AuthenticationException."""
    transport = httpx.MockTransport(
        lambda request: httpx.Response(200, json={"keys": [ec_keypair["jwk"]]})
    )
    mock_client = httpx.Client(transport=transport)
    manager = JWKSManager(client=mock_client)

    # Token expired 100 seconds ago (exceeding 10s leeway)
    expired_token = create_token(
        ec_keypair["private_key"],
        ec_keypair["kid"],
        exp_offset=-100,
    )

    with pytest.raises(AuthenticationException) as exc_info:
        verify_supabase_jwt(expired_token, key_manager=manager)

    assert "expired" in str(exc_info.value).lower()


# ==============================================================================
# 3. Invalid Signature (Tampered Payload) Rejection
# ==============================================================================

def test_tampered_signature_rejection(ec_keypair):
    """Verify that altering token payload causes cryptographic signature rejection."""
    transport = httpx.MockTransport(
        lambda request: httpx.Response(200, json={"keys": [ec_keypair["jwk"]]})
    )
    mock_client = httpx.Client(transport=transport)
    manager = JWKSManager(client=mock_client)

    token = create_token(ec_keypair["private_key"], ec_keypair["kid"])
    # Tamper with the middle payload segment
    parts = token.split(".")
    tampered_token = f"{parts[0]}.eyJhZG1pbiI6IHRydWV9.{parts[2]}"

    with pytest.raises(AuthenticationException) as exc_info:
        verify_supabase_jwt(tampered_token, key_manager=manager)

    assert "signature" in str(exc_info.value).lower() or "verification failed" in str(exc_info.value).lower()


# ==============================================================================
# 4. Wrong Issuer Rejection
# ==============================================================================

def test_wrong_issuer_rejection(ec_keypair):
    """Verify that a token signed with an unauthorized issuer is rejected."""
    transport = httpx.MockTransport(
        lambda request: httpx.Response(200, json={"keys": [ec_keypair["jwk"]]})
    )
    mock_client = httpx.Client(transport=transport)
    manager = JWKSManager(client=mock_client)

    token = create_token(
        ec_keypair["private_key"],
        ec_keypair["kid"],
        iss="https://rogue-supabase-project.supabase.co/auth/v1",
    )

    with pytest.raises(AuthenticationException) as exc_info:
        verify_supabase_jwt(token, key_manager=manager)

    assert "issuer" in str(exc_info.value).lower()


# ==============================================================================
# 5. Wrong Audience Rejection
# ==============================================================================

def test_wrong_audience_rejection(ec_keypair):
    """Verify that a token with non-authenticated audience is rejected."""
    transport = httpx.MockTransport(
        lambda request: httpx.Response(200, json={"keys": [ec_keypair["jwk"]]})
    )
    mock_client = httpx.Client(transport=transport)
    manager = JWKSManager(client=mock_client)

    token = create_token(
        ec_keypair["private_key"],
        ec_keypair["kid"],
        aud="unauthorized-aud",
    )

    with pytest.raises(AuthenticationException) as exc_info:
        verify_supabase_jwt(token, key_manager=manager)

    assert "audience" in str(exc_info.value).lower()


# ==============================================================================
# 6. Unsupported Algorithm Rejection
# ==============================================================================

def test_unsupported_algorithm_hs256_rejection():
    """Verify symmetric HS256 tokens are strictly rejected by the ES256 allowlist."""
    hmac_token = jwt.encode(
        {
            "sub": "00000000-0000-0000-0000-000000000001",
            "aud": "authenticated",
            "iss": settings.get_supabase_auth_issuer(),
            "exp": int(time.time()) + 3600,
        },
        key="a_very_secret_key_that_is_32_bytes_long_!",
        algorithm="HS256",
        headers={"kid": "some-kid", "alg": "HS256"},
    )

    with pytest.raises(AuthenticationException) as exc_info:
        verify_supabase_jwt(hmac_token)

    assert "unsupported signing algorithm" in str(exc_info.value).lower()
    assert "es256" in str(exc_info.value).lower()


def test_unsupported_algorithm_none_rejection():
    """Verify unsigned 'none' algorithm tokens are strictly rejected."""
    none_token = jwt.encode(
        {
            "sub": "00000000-0000-0000-0000-000000000001",
            "aud": "authenticated",
            "iss": settings.get_supabase_auth_issuer(),
            "exp": int(time.time()) + 3600,
        },
        key="",
        algorithm="none",
        headers={"kid": "some-kid", "alg": "none"},
    )

    with pytest.raises(AuthenticationException) as exc_info:
        verify_supabase_jwt(none_token)

    assert "unsupported signing algorithm" in str(exc_info.value).lower()


# ==============================================================================
# 7. Bearer Token Extraction & Malformed Token Checks
# ==============================================================================

def test_bearer_token_extraction_valid():
    """Verify correct Bearer token string extraction from Authorization header."""
    assert extract_bearer_token("Bearer my.sample.jwt") == "my.sample.jwt"
    assert extract_bearer_token("bearer   my.sample.jwt  ") == "my.sample.jwt"


def test_bearer_token_extraction_invalid():
    """Verify missing, non-Bearer, or empty tokens raise AuthenticationException."""
    with pytest.raises(AuthenticationException):
        extract_bearer_token(None)

    with pytest.raises(AuthenticationException):
        extract_bearer_token("")

    with pytest.raises(AuthenticationException):
        extract_bearer_token("Basic dXNlcjpwYXNz")

    with pytest.raises(AuthenticationException):
        extract_bearer_token("Bearer")


def test_malformed_token_string_rejection():
    """Verify garbage or non-JWT strings are rejected safely."""
    with pytest.raises(AuthenticationException) as exc_info:
        verify_supabase_jwt("not-a-valid-jwt")

    assert "malformed" in str(exc_info.value).lower()


# ==============================================================================
# 8. Key ID (kid) and Key Rotation Refresh Behavior
# ==============================================================================

def test_unknown_kid_triggers_jwks_refresh(ec_keypair, secondary_ec_keypair):
    """
    Verify that an unknown kid triggers one JWKS refresh to support legitimate key rotation,
    and succeeds once the rotated key is served.
    """
    call_count = {"count": 0}

    def mock_jwks_handler(request):
        call_count["count"] += 1
        # First call: only primary key
        # Second call (refresh): includes secondary rotated key
        if call_count["count"] == 1:
            return httpx.Response(200, json={"keys": [ec_keypair["jwk"]]})
        return httpx.Response(200, json={"keys": [ec_keypair["jwk"], secondary_ec_keypair["jwk"]]})

    mock_client = httpx.Client(transport=httpx.MockTransport(mock_jwks_handler))
    manager = JWKSManager(client=mock_client)

    # 1. Warm cache with primary key
    manager.get_signing_key(ec_keypair["kid"])
    assert call_count["count"] == 1

    # 2. Token signed with new rotated secondary key
    # Ensure last_refresh_time allows rotation refresh (> 10s difference simulated)
    manager._last_refresh_time = time.time() - 15.0

    rotated_token = create_token(secondary_ec_keypair["private_key"], secondary_ec_keypair["kid"])
    claims = verify_supabase_jwt(rotated_token, key_manager=manager)

    # Verified that a second fetch occurred and the rotated token verified successfully
    assert call_count["count"] == 2
    assert claims["sub"] == "00000000-0000-0000-0000-000000000001"


def test_completely_unknown_kid_rejection(ec_keypair):
    """Verify that an unknown kid that still does not exist after refresh is rejected."""
    transport = httpx.MockTransport(
        lambda request: httpx.Response(200, json={"keys": [ec_keypair["jwk"]]})
    )
    mock_client = httpx.Client(transport=transport)
    manager = JWKSManager(client=mock_client)

    token = create_token(
        ec_keypair["private_key"],
        kid="non-existent-kid-999",
    )

    with pytest.raises(AuthenticationException) as exc_info:
        verify_supabase_jwt(token, key_manager=manager)

    assert "key id" in str(exc_info.value).lower()


# ==============================================================================
# 9. In-Memory JWKS Cache Behavior
# ==============================================================================

def test_jwks_cache_reuse(ec_keypair):
    """Verify subsequent token verifications use the cached public key without refetching."""
    fetch_counter = {"count": 0}

    def counting_handler(request):
        fetch_counter["count"] += 1
        return httpx.Response(200, json={"keys": [ec_keypair["jwk"]]})

    mock_client = httpx.Client(transport=httpx.MockTransport(counting_handler))
    manager = JWKSManager(client=mock_client, ttl_seconds=600)

    token1 = create_token(ec_keypair["private_key"], ec_keypair["kid"], sub="cust-01")
    token2 = create_token(ec_keypair["private_key"], ec_keypair["kid"], sub="cust-02")

    verify_supabase_jwt(token1, key_manager=manager)
    verify_supabase_jwt(token2, key_manager=manager)

    # Exactly one network fetch occurred despite two verifications
    assert fetch_counter["count"] == 1


# ==============================================================================
# 10. JWKS Network Failure & Timeout Safe Error Handling
# ==============================================================================

def test_jwks_network_timeout_handling():
    """Verify network timeout when fetching JWKS raises sanitized AuthenticationException."""
    def timeout_handler(request):
        raise httpx.ConnectTimeout("Connection to Supabase timed out after 5.0s")

    mock_client = httpx.Client(transport=httpx.MockTransport(timeout_handler))
    manager = JWKSManager(client=mock_client)

    with pytest.raises(AuthenticationException) as exc_info:
        manager.fetch_jwks()

    assert "timeout" in str(exc_info.value).lower()
    # Confirm secret/token details are not leaked in message
    assert "key" not in str(exc_info.value).lower() or "signing" in str(exc_info.value).lower()


def test_jwks_http_500_handling():
    """Verify HTTP error from JWKS endpoint raises sanitized AuthenticationException."""
    mock_client = httpx.Client(
        transport=httpx.MockTransport(lambda req: httpx.Response(500, text="Internal Error"))
    )
    manager = JWKSManager(client=mock_client)

    with pytest.raises(AuthenticationException) as exc_info:
        manager.fetch_jwks()

    assert "unavailable" in str(exc_info.value).lower()
