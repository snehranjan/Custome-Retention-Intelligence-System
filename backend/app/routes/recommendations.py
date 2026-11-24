"""
Indian E-Commerce Customer Retention Intelligence System
Retention Recommendations Routes (Phase 8.4.8 - Customer Retention Explorer & Advanced Analytics)

Endpoints:
- GET /api/v1/recommendations: Paginated and filterable customer retention recommendations

Security:
- Protected by require_authorized_employee dependency.
- Rejects unauthenticated requests with HTTP 401 UNAUTHORIZED.
- Rejects authenticated but unapproved accounts with HTTP 403 FORBIDDEN.
"""

from typing import Optional
from fastapi import APIRouter, Depends, Query, status

from backend.app.core.config import settings
from backend.app.core.dependencies import require_authorized_employee
from backend.app.repositories import get_repository
from backend.app.schemas.auth import AuthenticatedUser
from backend.app.schemas.common import ApiResponse
from backend.app.schemas.analytics import (
    RecommendationItemDetail,
    RecommendationListResponse,
)

router = APIRouter(
    prefix="/recommendations",
    tags=["Retention Recommendations"],
    dependencies=[Depends(require_authorized_employee)],
)


@router.get(
    "",
    response_model=ApiResponse[RecommendationListResponse],
    status_code=status.HTTP_200_OK,
    summary="List Retention Recommendations (Paginated & Filterable)",
    description=(
        "Retrieves a prioritized collection of retention recommendations filtered by "
        "segment, priority tier (HIGH, MEDIUM, LOW), category, risk tier, or search query. "
        "Requires authorized employee permissions."
    ),
)
async def list_recommendations(
    limit: int = Query(default=50, ge=1, le=100, description="Page size (1 to 100 records)"),
    offset: int = Query(default=0, ge=0, description="Page offset (>= 0)"),
    segment: Optional[int] = Query(default=None, ge=0, le=4, description="Filter by cluster ID (0 to 4)"),
    priority: Optional[str] = Query(default=None, pattern="^(HIGH|MEDIUM|LOW|high|medium|low)$", description="Filter by priority"),
    category: Optional[str] = Query(default=None, description="Filter by recommendation category"),
    risk_tier: Optional[str] = Query(default=None, pattern="^(LOW|MODERATE|HIGH|low|moderate|high)$", description="Filter by risk tier"),
    search: Optional[str] = Query(default=None, max_length=100, description="Search by customer ID, name, or recommendation title"),
    current_employee: AuthenticatedUser = Depends(require_authorized_employee),
) -> ApiResponse[RecommendationListResponse]:
    """Returns paginated recommendation items with linked customer and segment context."""
    storage_mode = settings.STORAGE_MODE.lower()
    repo = get_repository(storage_mode)

    try:
        raw_items, total = repo.query_recommendations(
            limit=limit,
            offset=offset,
            segment=segment,
            priority=priority,
            category=category,
            risk_tier=risk_tier,
            search=search,
        )
    except NotImplementedError:
        raw_items = []
        total = 0

    items = [RecommendationItemDetail(**r) for r in raw_items]
    has_more = (offset + len(items)) < total

    return ApiResponse[RecommendationListResponse](
        success=True,
        data=RecommendationListResponse(
            items=items,
            total=total,
            limit=limit,
            offset=offset,
            has_more=has_more,
        ),
    )
