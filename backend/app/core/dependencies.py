"""
Indian E-Commerce Customer Retention Intelligence System
FastAPI Security & Authentication Dependencies (Phase 7.5 Checkpoint 3 - Security Corrected)

Provides reusable FastAPI dependencies for extracting and verifying Supabase JWTs.
Returns minimal verified identity strictly adhering to the principle of minimal disclosure.
"""

from typing import Optional
from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from backend.app.core.config import settings
from backend.app.core.errors import AuthenticationException, AuthorizationException
from backend.app.core.logging import logger
from backend.app.core.security import extract_bearer_token, verify_supabase_jwt
from backend.app.repositories import get_repository
from backend.app.schemas.auth import AuthenticatedUser

# HTTPBearer with auto_error=False allows us to intercept missing/invalid headers
# and raise custom AuthenticationException to produce our uniform error envelope.
bearer_security = HTTPBearer(auto_error=False)


async def get_current_user(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_security),
) -> AuthenticatedUser:
    """
    FastAPI dependency that validates the Bearer token in the Authorization header.
    Returns the minimal verified AuthenticatedUser identity model (user_id and optional email).
    Raises AuthenticationException (HTTP 401) on any authentication failure.
    """
    # 1. Check if Authorization header is present
    auth_header = request.headers.get("Authorization")
    if not auth_header:
        raise AuthenticationException("Missing Authorization header.")

    # 2. Extract bearer token (validates scheme and non-empty token string)
    token = extract_bearer_token(auth_header)

    # 3. Cryptographically verify JWT against Supabase JWKS
    claims = verify_supabase_jwt(token)

    # 4. Safely extract and validate optional email string
    raw_email = claims.get("email")
    email = str(raw_email).strip() if (isinstance(raw_email, str) and raw_email.strip()) else None

    # 5. Construct minimal AuthenticatedUser model (user_id and optional email only)
    return AuthenticatedUser(
        user_id=claims["sub"],
        email=email,
    )


async def require_authorized_employee(
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> AuthenticatedUser:
    """
    FastAPI authorization dependency enforcing the ADMIN-CONTROLLED EMPLOYEE ACCOUNTS policy (Phase 8.4.5).
    Evaluates:
    1. Persistent employee_registry in active repository:
       - status == 'APPROVED': Access granted.
       - status == 'PENDING': HTTP 403 (registration awaiting administrator approval).
       - status == 'REJECTED': HTTP 403 (registration rejected).
       - status == 'SUSPENDED': HTTP 403 (account suspended).
       - status == 'INVITED': HTTP 403 (registration incomplete).
    2. Server-controlled fallback settings (AUTHORIZED_EMPLOYEE_EMAILS / AUTHORIZED_EMPLOYEE_USER_IDS):
       - If matched: Access granted.
       - If not matched: HTTP 403 (account not authorized).

    Invariants:
    - Fails closed by default.
    - Zero client spoofing: ignores user_metadata and request headers.
    """
    user_email = (current_user.email or "").strip().lower()
    user_id = (current_user.user_id or "").strip()

    # 1. Check persistent employee registry
    try:
        repo = get_repository(settings.STORAGE_MODE.lower())
        emp = None
        if user_id:
            emp = repo.get_employee_by_supabase_user_id(user_id)
        if not emp and user_email:
            emp = repo.get_employee_by_email(user_email)

        if emp:
            bound_uid = emp.get("supabase_user_id")
            # Enforce cryptographic identity binding: prevent account takeover via email matching
            if bound_uid and user_id and bound_uid != user_id:
                logger.warning(
                    "Identity mismatch blocked: token sub '%s' does not match bound employee '%s' (emp_id: %s)",
                    user_id,
                    bound_uid,
                    emp.get("employee_id"),
                )
                raise AuthorizationException("Access denied: Authentication identity does not match employee record.")

            # Unbound employee accounts (supabase_user_id IS NULL) have not completed verified registration
            if not bound_uid:
                logger.warning(
                    "Unbound employee access blocked: emp_id %s has no verified supabase_user_id",
                    emp.get("employee_id"),
                )
                raise AuthorizationException("Access denied: Employee identity has not completed registration linking.")

            status = str(emp.get("status", "")).upper()
            if status == "APPROVED":
                return current_user
            elif status == "PENDING":
                logger.warning("Employee access blocked: user %s (%s) registration is PENDING", user_id, user_email)
                raise AuthorizationException("Access denied: Employee registration is awaiting administrator approval.")
            elif status == "REJECTED":
                logger.warning("Employee access blocked: user %s (%s) registration is REJECTED", user_id, user_email)
                raise AuthorizationException("Access denied: Employee registration was rejected by administrator.")
            elif status == "SUSPENDED":
                logger.warning("Employee access blocked: user %s (%s) account is SUSPENDED", user_id, user_email)
                raise AuthorizationException("Access denied: Employee account has been suspended by administrator.")
            else:
                logger.warning("Employee access blocked: user %s (%s) status is %s", user_id, user_email, status)
                raise AuthorizationException("Access denied: Employee registration is not completed or approved.")
    except AuthorizationException:
        raise
    except Exception as e:
        logger.warning("Error checking employee registry: %s", str(e))

    # 2. Server-controlled settings fallback (Phase 8.4.4 backward compatibility)
    allowed_emails = [e.strip().lower() for e in settings.AUTHORIZED_EMPLOYEE_EMAILS if e.strip()]
    allowed_user_ids = [u.strip() for u in settings.AUTHORIZED_EMPLOYEE_USER_IDS if u.strip()]

    is_authorized = (
        (user_email and user_email in allowed_emails)
        or (user_id and user_id in allowed_user_ids)
    )

    if not is_authorized:
        logger.warning(
            "Access denied: user %s (%s) is authenticated but not an authorized employee.",
            user_id,
            user_email or "no email",
        )
        raise AuthorizationException(
            "Access denied: Account is authenticated but not authorized as an approved RetainIQ employee."
        )

    return current_user


async def require_admin_user(
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> AuthenticatedUser:
    """
    FastAPI authorization dependency for administrator-only operations (Phase 8.4.5).
    Strictly fail-closed: requires user_id or email to be present in server-side
    settings.ADMIN_USER_IDS or settings.ADMIN_EMAILS.
    Raises AuthorizationException (HTTP 403) on any non-admin access attempt.
    """
    user_email = (current_user.email or "").strip().lower()
    user_id = (current_user.user_id or "").strip()

    admin_emails = [e.strip().lower() for e in settings.ADMIN_EMAILS if e.strip()]
    admin_user_ids = [u.strip() for u in settings.ADMIN_USER_IDS if u.strip()]

    is_admin = (
        (user_email and user_email in admin_emails)
        or (user_id and user_id in admin_user_ids)
    )

    if not is_admin:
        logger.warning(
            "Access denied: user %s (%s) attempted administrator operation without admin privileges.",
            user_id,
            user_email or "no email",
        )
        raise AuthorizationException(
            "Access denied: Administrator privileges are required to perform this operation."
        )

    return current_user
