"""
Indian E-Commerce Customer Retention Intelligence System
Database & Storage Management Routes (Phase 7.4 Checkpoint 7)

Endpoints:
- GET /api/v1/database/health: Live connectivity probe
- GET /api/v1/database/status: Storage schema, migration, and table diagnostics
- GET /api/v1/database/customers/count: Live aggregate customer counts and reconciliation
- GET /api/v1/database/import/status: Read-only population audit status
"""

from datetime import datetime, timezone
from typing import Optional
from fastapi import APIRouter, Depends, Response, status

from backend.app.core.config import settings
from backend.app.core.dependencies import get_current_user
from backend.app.core.logging import logger
from backend.app.repositories import get_repository
from backend.app.schemas.common import ApiResponse
from backend.app.schemas.database import (
    CustomerCountMetricsData,
    DatabaseHealthData,
    DatabaseImportStatusData,
    DatabaseStatusData,
)

router = APIRouter(
    prefix="/database",
    tags=["Database & Storage Management"],
    dependencies=[Depends(get_current_user)],
)


def _sanitize_error_message(err: Optional[str]) -> Optional[str]:
    """Sanitizes raw repository error strings, preventing leakage of paths, keys, or internal details."""
    if not err:
        return None
    err_str = str(err)
    sensitive_markers = ("\\", "/", "key", "secret", "password", "token", "cred", "private")
    if any(marker in err_str.lower() for marker in sensitive_markers):
        return "Storage backend connection error or misconfiguration"
    return err_str


@router.get(
    "/health",
    response_model=ApiResponse[DatabaseHealthData],
    summary="Database Connectivity & Health Check",
    description="Probes active database storage (SQLite or Supabase) and returns connectivity health.",
)
async def get_database_health(response: Response) -> ApiResponse[DatabaseHealthData]:
    """Live connectivity check against the active repository."""
    storage_mode = settings.STORAGE_MODE.lower()
    try:
        repo = get_repository(storage_mode)
        health = repo.get_health_status()
        is_conn = health.get("is_connected", False)

        if not is_conn:
            response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE

        return ApiResponse[DatabaseHealthData](
            success=is_conn,
            data=DatabaseHealthData(
                status=health.get("status", "unavailable"),
                storage_mode=storage_mode,
                backend=health.get("backend", storage_mode),
                is_connected=is_conn,
                error=_sanitize_error_message(health.get("error")),
                timestamp=datetime.now(timezone.utc).isoformat(),
            ),
        )
    except Exception as e:
        logger.error("Database health check error: %s", str(e))
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return ApiResponse[DatabaseHealthData](
            success=False,
            data=DatabaseHealthData(
                status="unavailable",
                storage_mode=storage_mode,
                backend=storage_mode,
                is_connected=False,
                error="Storage backend is unreachable or misconfigured",
                timestamp=datetime.now(timezone.utc).isoformat(),
            ),
        )


@router.get(
    "/status",
    response_model=ApiResponse[DatabaseStatusData],
    summary="Database Schema & Storage Diagnostics",
    description="Returns detailed schema migration readiness, table presence, and record counts.",
)
async def get_database_status(response: Response) -> ApiResponse[DatabaseStatusData]:
    """Returns comprehensive storage diagnostic metadata and table counts."""
    storage_mode = settings.STORAGE_MODE.lower()
    try:
        repo = get_repository(storage_mode)
        storage_status = repo.get_storage_status()
        is_conn = storage_status.get("is_connected", False)

        if not is_conn:
            response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE

        return ApiResponse[DatabaseStatusData](
            success=is_conn,
            data=DatabaseStatusData(
                status=storage_status.get("status", "unavailable"),
                storage_mode=storage_mode,
                backend=storage_status.get("backend", storage_mode),
                is_connected=is_conn,
                schema_ready=storage_status.get("schema_ready", False),
                applied_migrations=storage_status.get("applied_migrations", []),
                tables_available=storage_status.get("tables_available", []),
                table_counts=storage_status.get("table_counts", {}),
                database_version=storage_status.get("database_version"),
                error=_sanitize_error_message(storage_status.get("error")),
                timestamp=datetime.now(timezone.utc).isoformat(),
            ),
        )
    except Exception as e:
        logger.error("Database status check error: %s", str(e))
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return ApiResponse[DatabaseStatusData](
            success=False,
            data=DatabaseStatusData(
                status="unavailable",
                storage_mode=storage_mode,
                backend=storage_mode,
                is_connected=False,
                schema_ready=False,
                applied_migrations=[],
                tables_available=[],
                table_counts={},
                error="Storage backend inspection failed",
                timestamp=datetime.now(timezone.utc).isoformat(),
            ),
        )


@router.get(
    "/customers/count",
    response_model=ApiResponse[CustomerCountMetricsData],
    summary="Customer Population & Demographic Counts",
    description="Returns verified customer counts, churn distribution, and null city/state metrics via live database query.",
)
async def get_customer_counts() -> ApiResponse[CustomerCountMetricsData]:
    """Queries live customer aggregate metrics directly from storage."""
    storage_mode = settings.STORAGE_MODE.lower()
    repo = get_repository(storage_mode)
    metrics = repo.get_customer_metrics()

    total = metrics.get("total_customers", 0)
    churned = metrics.get("churned_customers", 0)
    retained = metrics.get("retained_customers", 0)
    reconciliation_valid = (churned + retained == total)

    return ApiResponse[CustomerCountMetricsData](
        success=True,
        data=CustomerCountMetricsData(
            total_customers=total,
            churned_customers=churned,
            retained_customers=retained,
            null_city_count=metrics.get("null_city_count", 0),
            null_state_count=metrics.get("null_state_count", 0),
            reconciliation_valid=reconciliation_valid,
            timestamp=datetime.now(timezone.utc).isoformat(),
        ),
    )


@router.get(
    "/import/status",
    response_model=ApiResponse[DatabaseImportStatusData],
    summary="Customer Baseline Import Readiness Status",
    description="Reports whether the 7,000 synthetic customer records from data/raw/customers.csv are populated.",
)
async def get_import_status() -> ApiResponse[DatabaseImportStatusData]:
    """Read-only audit status of baseline customer data population."""
    storage_mode = settings.STORAGE_MODE.lower()
    repo = get_repository(storage_mode)
    health = repo.get_health_status()

    if not health.get("is_connected", False):
        return ApiResponse[DatabaseImportStatusData](
            success=False,
            data=DatabaseImportStatusData(
                storage_mode=storage_mode,
                baseline_records_expected=7000,
                current_customer_count=0,
                is_baseline_populated=False,
                status="UNAVAILABLE",
                timestamp=datetime.now(timezone.utc).isoformat(),
            ),
        )

    count = repo.get_customer_count()
    is_populated = count >= 7000
    status_label = "READY" if is_populated else "INCOMPLETE"

    return ApiResponse[DatabaseImportStatusData](
        success=True,
        data=DatabaseImportStatusData(
            storage_mode=storage_mode,
            baseline_records_expected=7000,
            current_customer_count=count,
            is_baseline_populated=is_populated,
            status=status_label,
            timestamp=datetime.now(timezone.utc).isoformat(),
        ),
    )
