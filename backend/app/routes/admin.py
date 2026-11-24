"""
Indian E-Commerce Customer Retention Intelligence System
Administrator Employee Review & Directory Routes (Phase 8.4.5 & Phase 8.4.6)

Endpoints:
- GET /api/v1/admin/me: Verify administrator privileges and retrieve identity
- GET /api/v1/admin/stats: Real-time aggregated employee registry metrics
- GET /api/v1/admin/employees: Employee directory with status filtering and search
- GET /api/v1/admin/employees/pending: List employee registrations awaiting approval
- GET /api/v1/admin/employees/{employee_id}: Inspect single employee record details
- POST /api/v1/admin/employees/invite: Pre-authorize / invite an employee (status INVITED)
- POST /api/v1/admin/employees/{employee_id}/approve: Approve pending employee registration
- POST /api/v1/admin/employees/{employee_id}/reject: Reject pending employee registration

Security:
- All routes strictly protected by require_admin_user dependency.
- Fails closed: non-administrator accounts receive HTTP 403 FORBIDDEN.
- Self-approval by administrators is strictly prohibited.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, Path, Query, status

from backend.app.core.dependencies import require_admin_user
from backend.app.schemas.auth import AuthenticatedUser
from backend.app.schemas.common import ApiResponse
from backend.app.schemas.employee import (
    AdminProfileResponse,
    AdminStatsResponse,
    EmployeeApprovalRequest,
    EmployeeInvitationRequest,
    EmployeeRejectionRequest,
    EmployeeResponse,
)
from backend.app.services.employee_service import EmployeeRegistrationService

router = APIRouter(
    prefix="/admin",
    tags=["Administrator Operations"],
    dependencies=[Depends(require_admin_user)],
)


@router.get(
    "/me",
    response_model=ApiResponse[AdminProfileResponse],
    status_code=status.HTTP_200_OK,
    summary="Verify Administrator Privileges",
    description="Validates that the current authenticated user has active administrator privileges.",
)
async def get_admin_profile(
    current_admin: AuthenticatedUser = Depends(require_admin_user),
) -> ApiResponse[AdminProfileResponse]:
    """Returns administrator identity confirmation."""
    return ApiResponse[AdminProfileResponse](
        success=True,
        data=AdminProfileResponse(
            user_id=current_admin.user_id,
            email=current_admin.email,
            is_admin=True,
            role="ADMINISTRATOR",
        ),
    )


@router.get(
    "/stats",
    response_model=ApiResponse[AdminStatsResponse],
    status_code=status.HTTP_200_OK,
    summary="Get Employee Access Statistics",
    description="Returns real backend-derived employee registry statistics (total, pending, approved, rejected, suspended, invited).",
)
async def get_admin_stats(
    current_admin: AuthenticatedUser = Depends(require_admin_user),
) -> ApiResponse[AdminStatsResponse]:
    """Retrieves employee registry aggregate statistics."""
    stats = EmployeeRegistrationService.get_admin_stats()
    return ApiResponse[AdminStatsResponse](
        success=True,
        data=stats,
    )


@router.get(
    "/employees",
    response_model=ApiResponse[List[EmployeeResponse]],
    status_code=status.HTTP_200_OK,
    summary="List Employee Registry Directory",
    description="Returns employee registry records with optional status filtering, search term query, and pagination.",
)
async def list_employees(
    status_filter: Optional[str] = Query(default=None, alias="status", description="Filter by status (e.g. ALL, PENDING, APPROVED, REJECTED, SUSPENDED, INVITED)"),
    search: Optional[str] = Query(default=None, max_length=128, description="Search by employee ID, email, or full name"),
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    current_admin: AuthenticatedUser = Depends(require_admin_user),
) -> ApiResponse[List[EmployeeResponse]]:
    """Lists employee registry records."""
    employees = EmployeeRegistrationService.list_employees(
        status=status_filter,
        search=search,
        limit=limit,
        offset=offset,
    )
    return ApiResponse[List[EmployeeResponse]](
        success=True,
        data=employees,
    )


@router.get(
    "/employees/pending",
    response_model=ApiResponse[List[EmployeeResponse]],
    status_code=status.HTTP_200_OK,
    summary="List Pending Employee Registrations",
    description="Returns all employee registrations awaiting administrator approval. Requires administrator privileges.",
)
async def list_pending_employees(
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    current_admin: AuthenticatedUser = Depends(require_admin_user),
) -> ApiResponse[List[EmployeeResponse]]:
    """Lists pending employee registrations."""
    pending_list = EmployeeRegistrationService.list_pending_employees(limit=limit, offset=offset)
    return ApiResponse[List[EmployeeResponse]](
        success=True,
        data=pending_list,
    )


@router.get(
    "/employees/{employee_id}",
    response_model=ApiResponse[EmployeeResponse],
    status_code=status.HTTP_200_OK,
    summary="Inspect Employee Details",
    description="Retrieves complete employee registry record including onboarding and approval metadata.",
)
async def get_employee_details(
    employee_id: str = Path(..., min_length=3, max_length=32),
    current_admin: AuthenticatedUser = Depends(require_admin_user),
) -> ApiResponse[EmployeeResponse]:
    """Inspects a single employee registry record."""
    employee = EmployeeRegistrationService.get_employee(employee_id=employee_id)
    return ApiResponse[EmployeeResponse](
        success=True,
        data=employee,
    )


@router.post(
    "/employees/invite",
    response_model=ApiResponse[EmployeeResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Pre-Authorize / Invite Employee",
    description="Creates an administrator-authorized employee invitation in the registry with status 'INVITED'.",
)
async def invite_employee(
    request: EmployeeInvitationRequest,
    current_admin: AuthenticatedUser = Depends(require_admin_user),
) -> ApiResponse[EmployeeResponse]:
    """Creates a new employee invitation."""
    result = EmployeeRegistrationService.create_invitation(
        request=request,
        admin_id=current_admin.user_id,
    )
    return ApiResponse[EmployeeResponse](
        success=True,
        data=result,
    )


@router.post(
    "/employees/{employee_id}/approve",
    response_model=ApiResponse[EmployeeResponse],
    status_code=status.HTTP_200_OK,
    summary="Approve Employee Registration",
    description="Approves a pending employee registration, granting customer intelligence portal access.",
)
async def approve_employee(
    employee_id: str = Path(..., min_length=3, max_length=32),
    request: EmployeeApprovalRequest = EmployeeApprovalRequest(),
    current_admin: AuthenticatedUser = Depends(require_admin_user),
) -> ApiResponse[EmployeeResponse]:
    """Approves a pending employee account."""
    result = EmployeeRegistrationService.approve_employee(
        employee_id=employee_id,
        admin_id=current_admin.user_id,
        notes=request.notes,
    )
    return ApiResponse[EmployeeResponse](
        success=True,
        data=result,
    )


@router.post(
    "/employees/{employee_id}/reject",
    response_model=ApiResponse[EmployeeResponse],
    status_code=status.HTTP_200_OK,
    summary="Reject Employee Registration",
    description="Rejects a pending employee registration with mandatory objective reason.",
)
async def reject_employee(
    request: EmployeeRejectionRequest,
    employee_id: str = Path(..., min_length=3, max_length=32),
    current_admin: AuthenticatedUser = Depends(require_admin_user),
) -> ApiResponse[EmployeeResponse]:
    """Rejects a pending employee account."""
    result = EmployeeRegistrationService.reject_employee(
        employee_id=employee_id,
        admin_id=current_admin.user_id,
        reason=request.reason,
    )
    return ApiResponse[EmployeeResponse](
        success=True,
        data=result,
    )
