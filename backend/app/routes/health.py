"""
Indian E-Commerce Customer Retention Intelligence System
Health Check & Readiness Endpoints
"""

from datetime import datetime, timezone
from fastapi import APIRouter, status
from backend.app.core.config import settings
from backend.app.schemas.common import ApiResponse, HealthStatusData
from backend.app.services.ml_boundary import MLServiceBoundary

router = APIRouter(tags=["System Health"])


@router.get(
    "/health",
    response_model=ApiResponse[HealthStatusData],
    status_code=status.HTTP_200_OK,
    summary="Application Health Status",
    description="Returns current system operational status, environment, version, and ML artifact readiness.",
)
async def get_health_status() -> ApiResponse[HealthStatusData]:
    """Provides operational health metrics for monitoring and viva demonstrations."""
    ml_ready = MLServiceBoundary.are_artifacts_ready()
    return ApiResponse[HealthStatusData](
        success=True,
        data=HealthStatusData(
            status="healthy" if ml_ready else "degraded",
            environment=settings.ENVIRONMENT,
            version=settings.VERSION,
            api_prefix=settings.API_V1_STR,
            ml_artifacts_ready=ml_ready,
            timestamp=datetime.now(timezone.utc).isoformat(),
        ),
    )
