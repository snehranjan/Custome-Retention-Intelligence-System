"""
Indian E-Commerce Customer Retention Intelligence System
Employee Registration & Profile Routes (Phase 8.4.5 & Phase 8.4.7)

Endpoints:
- POST /api/v1/employee/register: Register using pre-issued Employee ID and work email
- GET /api/v1/employee/me: Get verified employee profile (requires APPROVED status)
"""

from fastapi import APIRouter, Depends, status

from backend.app.core.dependencies import require_authorized_employee
from backend.app.schemas.auth import AuthenticatedUser
from backend.app.schemas.common import ApiResponse
from backend.app.schemas.employee import (
    EmployeeProfileResponse,
    EmployeeRegistrationRequest,
    EmployeeRegistrationResponse,
)
from backend.app.services.employee_service import EmployeeRegistrationService

router = APIRouter(tags=["Employee Operations"])


@router.get(
    "/me",
    response_model=ApiResponse[EmployeeProfileResponse],
    status_code=status.HTTP_200_OK,
    summary="Get Verified Employee Profile",
    description=(
        "Retrieves the verified employee profile for the authenticated employee session. "
        "Enforces the ADMIN-CONTROLLED EMPLOYEE ACCOUNTS policy: only accounts with status APPROVED "
        "can access this endpoint. Non-approved accounts receive HTTP 403 Forbidden."
    ),
    dependencies=[Depends(require_authorized_employee)],
)
async def get_my_employee_profile(
    current_user: AuthenticatedUser = Depends(require_authorized_employee),
) -> ApiResponse[EmployeeProfileResponse]:
    """Retrieves verified employee profile for the active session."""
    profile = EmployeeRegistrationService.get_current_employee_profile(current_user)
    return ApiResponse[EmployeeProfileResponse](
        success=True,
        data=profile,
    )


@router.post(
    "/register",
    response_model=ApiResponse[EmployeeRegistrationResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Register Employee Account",
    description=(
        "Registers an enterprise employee account using an administrator-issued Employee ID "
        "and work email. New accounts are assigned status PENDING until administrator approval."
    ),
)
async def register_employee(
    request: EmployeeRegistrationRequest,
) -> ApiResponse[EmployeeRegistrationResponse]:
    """Validates Employee ID and registers employee account awaiting administrator approval."""
    result = EmployeeRegistrationService.register_employee(request)
    return ApiResponse[EmployeeRegistrationResponse](
        success=True,
        data=result,
    )

