"""
Indian E-Commerce Customer Retention Intelligence System
Authentication Routes (Phase 7.5 Checkpoint 3 - Security Corrected)

Endpoints:
- GET /api/v1/auth/health: Non-sensitive auth provider diagnostics (Public)
- GET /api/v1/auth/me: Retrieve verified minimal employee identity (Protected)
"""

from fastapi import APIRouter, Depends, status

from backend.app.core.config import settings
from backend.app.core.dependencies import get_current_user
from backend.app.schemas.auth import AuthenticatedUser, AuthHealthData
from backend.app.schemas.common import ApiResponse

router = APIRouter(tags=["Authentication"])


@router.get(
    "/health",
    response_model=ApiResponse[AuthHealthData],
    status_code=status.HTTP_200_OK,
    summary="Authentication Integration Health Check",
    description="Public endpoint confirming that Supabase Auth integration is configured and active without exposing credentials.",
)
async def get_auth_health() -> ApiResponse[AuthHealthData]:
    """Public non-sensitive auth health check."""
    return ApiResponse[AuthHealthData](
        success=True,
        data=AuthHealthData(
            status="healthy",
            auth_provider="supabase_auth",
            signing_algorithm="ES256",
            jwks_configured=bool(settings.get_supabase_jwks_url()),
        ),
    )


@router.get(
    "/me",
    response_model=ApiResponse[AuthenticatedUser],
    status_code=status.HTTP_200_OK,
    summary="Get Authenticated Employee Profile",
    description="Returns verified minimal identity (user_id and optional email) for the currently authenticated employee.",
)
async def get_current_user_profile(
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> ApiResponse[AuthenticatedUser]:
    """Returns the minimal verified identity extracted from the Supabase JWT access token."""
    return ApiResponse[AuthenticatedUser](
        success=True,
        data=current_user,
    )
