"""
Indian E-Commerce Customer Retention Intelligence System
Supabase JWT Verification Engine (Phase 7.5 Checkpoint 2)

Provides:
- Cryptographic verification of Supabase Auth access tokens
- Public-key retrieval and in-memory TTL caching from Supabase JWKS
- Strict ES256 algorithm enforcement (ECDSA with NIST P-256 curve)
- Issuer, audience, expiration, and required claim validation
- Safe key rotation handling (unknown kid refresh)
- Safe error handling without token or secret credential leakage
"""

import threading
import time
from typing import Any, Dict, List, Optional

import httpx
import jwt
from jwt import PyJWK

from backend.app.core.config import settings
from backend.app.core.errors import AuthenticationException
from backend.app.core.logging import logger


class JWKSManager:
    """
    Manages fetching, caching, and key-rotation lookup of Supabase Auth public keys
    published at the project's JWKS endpoint (.well-known/jwks.json).
    """

    def __init__(
        self,
        jwks_url: Optional[str] = None,
        ttl_seconds: Optional[int] = None,
        timeout: float = 5.0,
        client: Optional[httpx.Client] = None,
    ):
        self.jwks_url = jwks_url or settings.get_supabase_jwks_url()
        self.ttl_seconds = ttl_seconds if ttl_seconds is not None else settings.JWKS_CACHE_TTL_SECONDS
        self.timeout = timeout
        self._custom_client = client
        self._cached_keys: Dict[str, PyJWK] = {}
        self._last_refresh_time: float = 0.0
        self._lock = threading.Lock()

    def _get_http_client(self) -> httpx.Client:
        """Returns injected client or a fresh bounded client session."""
        if self._custom_client is not None:
            return self._custom_client
        return httpx.Client(timeout=self.timeout)

    def fetch_jwks(self) -> Dict[str, PyJWK]:
        """
        Fetches the active public JWK set from the Supabase JWKS endpoint.
        Parses keys into PyJWK instances and updates the in-memory cache.
        """
        logger.debug("Fetching Supabase JWKS from: %s", self.jwks_url)
        try:
            client = self._get_http_client()
            # If client was injected, do not close in context manager
            if self._custom_client is not None:
                resp = client.get(self.jwks_url)
            else:
                with client as c:
                    resp = c.get(self.jwks_url)

            if resp.status_code != 200:
                logger.error("Supabase JWKS endpoint returned HTTP %d", resp.status_code)
                raise AuthenticationException(
                    "Authentication service temporarily unavailable (JWKS HTTP error)."
                )

            data = resp.json()
            raw_keys = data.get("keys", [])
            new_cache: Dict[str, PyJWK] = {}

            for k in raw_keys:
                kid = k.get("kid")
                if kid and isinstance(kid, str):
                    try:
                        new_cache[kid] = PyJWK(k)
                    except Exception as parse_err:
                        logger.warning("Failed to parse JWK with kid '%s': %s", kid, str(parse_err))

            with self._lock:
                self._cached_keys = new_cache
                self._last_refresh_time = time.time()

            logger.info("Successfully cached %d Supabase signing keys from JWKS", len(new_cache))
            return new_cache

        except (httpx.ConnectTimeout, httpx.ReadTimeout, httpx.WriteTimeout) as timeout_err:
            logger.error("Timeout fetching Supabase JWKS: %s", str(timeout_err))
            raise AuthenticationException(
                "Authentication service timeout while contacting identity provider."
            )
        except (httpx.ConnectError, httpx.NetworkError) as net_err:
            logger.error("Network error fetching Supabase JWKS: %s", str(net_err))
            raise AuthenticationException(
                "Authentication service is unreachable. Please verify network connectivity."
            )
        except AuthenticationException:
            raise
        except Exception as e:
            logger.error("Unexpected error fetching Supabase JWKS: %s", str(e))
            raise AuthenticationException(
                "Authentication service error while verifying token credentials."
            )

    def get_signing_key(self, kid: str) -> PyJWK:
        """
        Retrieves the public signing key matching the given key ID (kid).
        Handles legitimate key rotation: if kid is unknown, triggers one fresh fetch.
        """
        if not kid or not isinstance(kid, str) or not kid.strip():
            raise AuthenticationException("Token header missing required 'kid' (Key ID).")

        now = time.time()
        needs_initial_or_ttl_refresh = (
            not self._cached_keys or (now - self._last_refresh_time > self.ttl_seconds)
        )

        if needs_initial_or_ttl_refresh:
            self.fetch_jwks()

        # Check in current cache
        with self._lock:
            key = self._cached_keys.get(kid)

        if key is not None:
            return key

        # If kid was not found and we haven't refreshed within cooldown (10s), refresh once
        # to support legitimate Supabase key rotation
        if (time.time() - self._last_refresh_time) > 10.0:
            logger.info("Key ID '%s' not found in cache. Triggering JWKS refresh for key rotation.", kid)
            self.fetch_jwks()

            with self._lock:
                key = self._cached_keys.get(kid)

            if key is not None:
                return key

        logger.warning("Key ID '%s' was not found in Supabase JWKS after refresh.", kid)
        raise AuthenticationException(
            "Invalid or unknown token signing key ID. The token may be from another project or expired."
        )

    def clear_cache(self) -> None:
        """Clears cached keys and resets last refresh timestamp (primarily for tests)."""
        with self._lock:
            self._cached_keys.clear()
            self._last_refresh_time = 0.0


# Default global JWKS manager singleton
jwks_manager = JWKSManager()


def extract_bearer_token(auth_header: Optional[str]) -> str:
    """
    Extracts and validates the raw token from an HTTP Authorization header.
    Rejects missing, malformed, or non-Bearer authorization schemes.
    """
    if not auth_header or not auth_header.strip():
        raise AuthenticationException("Missing Authorization header.")

    parts = auth_header.strip().split()
    if len(parts) != 2:
        raise AuthenticationException(
            "Invalid Authorization header format. Expected 'Bearer <token>'."
        )

    scheme, token = parts
    if scheme.lower() != "bearer":
        raise AuthenticationException(
            f"Unsupported authorization scheme '{scheme}'. 'Bearer' scheme is required."
        )

    if not token.strip():
        raise AuthenticationException("Empty Bearer token provided.")

    return token.strip()


def verify_supabase_jwt(
    token: str,
    key_manager: Optional[JWKSManager] = None,
) -> Dict[str, Any]:
    """
    Cryptographically verifies a Supabase Auth access token using public keys from JWKS.

    Verification Invariants:
    1. Header structure & valid kid extraction.
    2. Strict ES256 algorithm enforcement (rejects HS256, RS256, 'none', etc.).
    3. Cryptographic signature check against matching EC public key.
    4. Issuer validation against dynamic Supabase Auth URL.
    5. Audience validation against 'authenticated'.
    6. Expiration and temporal bounds validation (with configured leeway).
    7. Valid non-empty subject ('sub') claim.

    Returns:
        Verified claims dictionary.
    Raises:
        AuthenticationException: If any verification invariant fails.
    """
    if not token or not isinstance(token, str) or not token.strip():
        raise AuthenticationException("Token must be a non-empty string.")

    # 1. Parse unverified header to extract kid and alg
    try:
        header = jwt.get_unverified_header(token)
    except (jwt.DecodeError, ValueError) as err:
        logger.warning("Malformed JWT header decoding failed: %s", str(err))
        raise AuthenticationException("Malformed or unparseable JWT header.")

    alg = header.get("alg")
    kid = header.get("kid")

    # 2. Strict algorithm allowlist check
    if not alg or alg not in settings.JWT_ALGORITHMS:
        logger.warning("Rejected token with disallowed signing algorithm: %s", alg)
        raise AuthenticationException(
            f"Unsupported signing algorithm '{alg}'. Only {settings.JWT_ALGORITHMS} are permitted."
        )

    # 3. Retrieve public signing key
    active_manager = key_manager or jwks_manager
    py_jwk = active_manager.get_signing_key(kid)

    # 4. Cryptographic signature verification and claim validation
    expected_issuer = settings.get_supabase_auth_issuer()
    expected_audience = settings.JWT_AUDIENCE
    leeway = settings.JWT_LEEWAY_SECONDS

    try:
        claims = jwt.decode(
            token,
            py_jwk.key,
            algorithms=settings.JWT_ALGORITHMS,  # Strictly ["ES256"]
            audience=expected_audience,
            issuer=expected_issuer,
            leeway=leeway,
            options={
                "verify_signature": True,
                "verify_exp": True,
                "verify_iss": True,
                "verify_aud": True,
                "require": ["exp", "iss", "aud", "sub"],
            },
        )
    except jwt.ExpiredSignatureError:
        raise AuthenticationException("Token has expired. Please sign in again.")
    except jwt.InvalidAudienceError:
        raise AuthenticationException(
            f"Invalid token audience. Expected audience '{expected_audience}'."
        )
    except jwt.InvalidIssuerError:
        raise AuthenticationException(
            f"Invalid token issuer. Expected issuer '{expected_issuer}'."
        )
    except jwt.InvalidSignatureError:
        raise AuthenticationException("Invalid token signature. Token may have been tampered with.")
    except jwt.MissingRequiredClaimError as miss_err:
        raise AuthenticationException(
            f"Token is missing required claim: {miss_err.claim}."
        )
    except jwt.ImmatureSignatureError:
        raise AuthenticationException("Token is not yet valid (nbf claim).")
    except jwt.InvalidAlgorithmError:
        raise AuthenticationException(
            f"Invalid token algorithm. Allowed: {settings.JWT_ALGORITHMS}."
        )
    except jwt.DecodeError as dec_err:
        raise AuthenticationException(f"Token decoding failed: {str(dec_err)}.")
    except jwt.PyJWTError as jwt_err:
        logger.warning("PyJWT verification failed: %s", type(jwt_err).__name__)
        raise AuthenticationException("Token cryptographic verification failed.")

    # 5. Validate subject claim
    sub = claims.get("sub")
    if not sub or not isinstance(sub, str) or not sub.strip():
        raise AuthenticationException("Token contains invalid or empty subject ('sub') claim.")

    return claims
