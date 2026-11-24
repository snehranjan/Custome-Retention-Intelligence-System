"""
Indian E-Commerce Customer Retention Intelligence System
Employee Registration & Approval Service (Phase 8.4.5)

Implements:
- Server-side Employee ID validation against administrator-issued invitations
- Work email referential verification
- Secure server-side Supabase Auth user identity creation via Admin API
- Zero plaintext password storage
- Atomic employee registry state updates (status transition to PENDING)
- Administrator approval and rejection logic with self-approval prevention
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
import uuid
import httpx

from backend.app.core.config import settings
from backend.app.core.errors import (
    AppException,
    AuthorizationException,
    NotFoundException,
    ValidationException,
)
from backend.app.core.logging import logger
from backend.app.repositories import get_repository
from backend.app.schemas.employee import (
    AdminStatsResponse,
    EmployeeInvitationRequest,
    EmployeeProfileResponse,
    EmployeeRegistrationRequest,
    EmployeeRegistrationResponse,
    EmployeeResponse,
)
from backend.app.schemas.auth import AuthenticatedUser


class EmployeeRegistrationService:
    """Orchestrates secure employee registration and administrator review workflows."""

    @classmethod
    def _get_repo(cls):
        return get_repository(settings.STORAGE_MODE.lower())

    @classmethod
    def register_employee(cls, request: EmployeeRegistrationRequest) -> EmployeeRegistrationResponse:
        """
        Registers an employee using a pre-issued, administrator-managed Employee ID.
        Enforces:
        1. Employee ID must exist in employee_registry.
        2. Employee status must be 'INVITED' (unregistered).
        3. Work email must match pre-issued invitation record.
        4. Supabase identity created via secure server-side Admin API.
        5. Passwords never stored in registry.
        6. Status set to 'PENDING'.
        """
        repo = cls._get_repo()
        clean_emp_id = request.employee_id.strip().upper()
        clean_email = request.work_email.strip().lower()

        # 1. Inspect invitation record in employee_registry
        emp = repo.get_employee_by_id(clean_emp_id)
        if not emp:
            logger.warning("Registration rejected: Employee ID '%s' not found in registry.", clean_emp_id)
            raise ValidationException("Invalid Employee ID. Please verify your administrator-issued credentials.")

        current_status = str(emp.get("status", "")).upper()
        if current_status != "INVITED":
            if current_status in ("PENDING", "APPROVED"):
                logger.warning("Registration rejected: Employee ID '%s' already registered (status: %s).", clean_emp_id, current_status)
                raise ValidationException("This Employee ID has already been registered or is pending approval.")
            else:
                logger.warning("Registration rejected: Employee ID '%s' status is %s.", clean_emp_id, current_status)
                raise ValidationException(f"This Employee ID is inactive (status: {current_status}).")

        # 2. Check work email referential integrity
        invited_email = str(emp.get("work_email", "")).strip().lower()
        if invited_email != clean_email:
            logger.warning("Registration rejected: Email '%s' does not match invitation for '%s'.", clean_email, clean_emp_id)
            raise ValidationException("Work email does not match the invitation record for this Employee ID.")

        # 3. Provision or link Supabase Auth identity via server-side Admin API
        supabase_uid = cls._provision_supabase_identity(clean_email, request.password)

        # Pre-binding check: verify no conflicting employee already bound to this UUID
        existing_by_uid = repo.get_employee_by_supabase_user_id(supabase_uid)
        if existing_by_uid and existing_by_uid.get("employee_id") != clean_emp_id:
            logger.warning(
                "Registration rejected: Supabase Auth UUID '%s' already bound to employee '%s'",
                supabase_uid,
                existing_by_uid.get("employee_id"),
            )
            raise ValidationException(
                "This authentication account is already linked to an existing employee profile."
            )

        # Pre-binding check: if invitation record has a pre-assigned UUID, ensure it matches
        pre_assigned_uid = emp.get("supabase_user_id")
        if pre_assigned_uid and pre_assigned_uid != supabase_uid:
            logger.warning(
                "Registration rejected: Supabase Auth UUID '%s' does not match invitation pre-assigned UUID '%s'",
                supabase_uid,
                pre_assigned_uid,
            )
            raise ValidationException(
                "Authentication identity mismatch for pre-assigned employee invitation."
            )

        # 4. Update employee registry record to PENDING
        now_utc = datetime.now(timezone.utc).isoformat()
        try:
            repo.register_employee(
                employee_id=clean_emp_id,
                supabase_user_id=supabase_uid,
                work_email=clean_email,
            )
            logger.info("Employee registration successfully recorded for '%s' (%s) -> PENDING", clean_emp_id, clean_email)
        except Exception as e:
            logger.error("Failed to update employee registry for '%s': %s", clean_emp_id, str(e))
            raise AppException(message="Failed to persist employee registration. Please try again.")

        return EmployeeRegistrationResponse(
            employee_id=clean_emp_id,
            work_email=clean_email,
            status="PENDING",
            registered_at=now_utc,
            message="Employee registration submitted successfully. Your account is awaiting administrator approval.",
        )

    @classmethod
    def _provision_supabase_identity(cls, email: str, password: str) -> str:
        """
        Creates or retrieves Supabase Auth identity via server-only service-role Admin API.
        Never exposes secrets to client; handles network boundaries gracefully.
        Only treats HTTP 422 as existing account if error explicitly indicates pre-existing email.
        """
        secret_key = settings.get_supabase_secret_key()
        base_url = (settings.SUPABASE_URL or "").rstrip("/")

        if secret_key and base_url and not base_url.startswith("http://placeholder"):
            headers = {
                "apikey": secret_key,
                "Authorization": f"Bearer {secret_key}",
                "Content-Type": "application/json",
            }
            payload = {
                "email": email,
                "password": password,
                "email_confirm": True,
            }
            try:
                with httpx.Client(timeout=8.0) as client:
                    resp = client.post(f"{base_url}/auth/v1/admin/users", json=payload, headers=headers)
                    if resp.status_code in (200, 201):
                        data = resp.json()
                        return str(data.get("id"))
                    elif resp.status_code == 422:
                        resp_body = resp.text.lower()
                        # Verify the 422 is genuinely due to an already existing account
                        if "already" in resp_body or "registered" in resp_body or "exists" in resp_body:
                            # CRITICAL SECURITY CONTROL (Phase 8.4.5.3):
                            # Prevent account takeover: DO NOT silently overwrite or sync passwords via Admin API.
                            # The applicant MUST independently prove ownership of the existing Auth account by verifying credentials.
                            auth_resp = client.post(
                                f"{base_url}/auth/v1/token?grant_type=password",
                                json={"email": email, "password": password},
                                headers={"apikey": settings.SUPABASE_PUBLISHABLE_KEY or secret_key, "Content-Type": "application/json"},
                            )
                            if auth_resp.status_code == 200:
                                token_data = auth_resp.json()
                                user_obj = token_data.get("user", {})
                                verified_uid = str(user_obj.get("id"))
                                if verified_uid:
                                    logger.info("Existing Auth account verified via credential ownership for %s", email)
                                    return verified_uid
                            elif auth_resp.status_code == 400:
                                logger.warning("Account takeover blocked: applicant password does not match existing Auth account for %s", email)
                                raise ValidationException(
                                    "An account with this work email already exists in the identity system, "
                                    "but the password provided does not match. Please verify your password or contact your administrator."
                                )
                            else:
                                logger.warning("Supabase Auth password verification failed with status %s: %s", auth_resp.status_code, auth_resp.text)
                                raise ValidationException("Unable to verify identity with existing authentication account.")
                        else:
                            logger.warning("Supabase Auth rejected user creation with 422: %s", resp.text)
                            raise ValidationException("Account creation rejected by authentication provider.")
                    elif resp.status_code >= 400:
                        logger.warning("Supabase Auth returned error %s: %s", resp.status_code, resp.text)
                        raise ValidationException("Authentication provider error during account creation.")
            except ValidationException:
                raise
            except Exception as e:
                logger.warning("Supabase Admin API call bypassed (%s): generating isolated ID", str(e))

        # Deterministic UUID fallback for isolated test environments or offline execution
        return str(uuid.uuid5(uuid.NAMESPACE_DNS, f"retainiq_{email.lower()}"))

    @classmethod
    def list_pending_employees(cls, limit: int = 50, offset: int = 0) -> List[EmployeeResponse]:
        """Lists employees awaiting administrator approval."""
        repo = cls._get_repo()
        raw_list = repo.list_employees_by_status(status="PENDING", limit=limit, offset=offset)
        return [EmployeeResponse(**r) for r in raw_list]

    @classmethod
    def approve_employee(cls, employee_id: str, admin_id: str, notes: Optional[str] = None) -> EmployeeResponse:
        """
        Approves a pending employee registration.
        Enforces self-approval prevention and valid pending status.
        """
        repo = cls._get_repo()
        clean_id = employee_id.strip().upper()
        emp = repo.get_employee_by_id(clean_id)
        if not emp:
            raise NotFoundException(f"Employee record '{clean_id}' not found.")

        # Self-approval prevention
        if admin_id and emp.get("supabase_user_id") and admin_id == emp.get("supabase_user_id"):
            logger.warning("Security alert: Admin %s attempted to approve their own employee registration (%s)", admin_id, clean_id)
            raise AuthorizationException("Security policy violation: Administrators cannot approve their own employee registration.")

        current_status = str(emp.get("status", "")).upper()
        if current_status != "PENDING":
            raise ValidationException(f"Cannot approve employee with status '{current_status}'. Only PENDING accounts can be approved.")

        updated = repo.update_employee_status(employee_id=clean_id, status="APPROVED", admin_id=admin_id)
        logger.info("Employee '%s' APPROVED by admin %s", clean_id, admin_id)
        return EmployeeResponse(**updated)

    @classmethod
    def reject_employee(cls, employee_id: str, admin_id: str, reason: str) -> EmployeeResponse:
        """
        Rejects a pending employee registration with mandatory objective reason.
        """
        repo = cls._get_repo()
        clean_id = employee_id.strip().upper()
        emp = repo.get_employee_by_id(clean_id)
        if not emp:
            raise NotFoundException(f"Employee record '{clean_id}' not found.")

        current_status = str(emp.get("status", "")).upper()
        if current_status != "PENDING":
            raise ValidationException(f"Cannot reject employee with status '{current_status}'. Only PENDING accounts can be rejected.")

        updated = repo.update_employee_status(employee_id=clean_id, status="REJECTED", admin_id=admin_id, reason=reason)
        logger.info("Employee '%s' REJECTED by admin %s (reason: %s)", clean_id, admin_id, reason)
        return EmployeeResponse(**updated)

    @classmethod
    def get_admin_stats(cls) -> AdminStatsResponse:
        """Retrieves aggregated employee status metrics for the admin dashboard."""
        repo = cls._get_repo()
        stats = repo.get_employee_stats()
        return AdminStatsResponse(**stats)

    @classmethod
    def list_employees(
        cls,
        status: Optional[str] = None,
        search: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[EmployeeResponse]:
        """Lists employee registry records with optional status, search filter, and pagination."""
        repo = cls._get_repo()
        raw_list = repo.list_employees_by_status(status=status, search=search, limit=limit, offset=offset)
        return [EmployeeResponse(**r) for r in raw_list]

    @classmethod
    def get_employee(cls, employee_id: str) -> EmployeeResponse:
        """Retrieves an employee record by ID."""
        repo = cls._get_repo()
        clean_id = employee_id.strip().upper()
        emp = repo.get_employee_by_id(clean_id)
        if not emp:
            raise NotFoundException(f"Employee record '{clean_id}' not found.")
        return EmployeeResponse(**emp)

    @classmethod
    def create_invitation(cls, request: EmployeeInvitationRequest, admin_id: str) -> EmployeeResponse:
        """
        Creates a new employee invitation with status 'INVITED'.
        Enforces uniqueness of employee_id and work_email.
        """
        repo = cls._get_repo()
        clean_id = request.employee_id.strip().upper()
        clean_email = request.work_email.strip().lower()

        # Check existing employee_id
        existing_id = repo.get_employee_by_id(clean_id)
        if existing_id:
            logger.warning("Invitation creation blocked: Employee ID '%s' already exists in registry.", clean_id)
            raise ValidationException(f"Employee ID '{clean_id}' is already registered or invited.")

        # Check existing work_email
        existing_email = repo.get_employee_by_email(clean_email)
        if existing_email:
            logger.warning("Invitation creation blocked: Work email '%s' already exists in registry.", clean_email)
            raise ValidationException(f"Work email '{clean_email}' is already registered or invited.")

        payload = {
            "employee_id": clean_id,
            "work_email": clean_email,
            "full_name": request.full_name.strip() if request.full_name else None,
            "department": request.department.strip() if request.department else "Customer Success",
            "status": "INVITED",
            "notes": request.notes.strip() if request.notes else f"Invited by administrator ({admin_id})",
        }

        created = repo.create_employee_invitation(payload)
        logger.info("Employee invitation created for '%s' (%s) by admin %s", clean_id, clean_email, admin_id)
        return EmployeeResponse(**created)

    @classmethod
    def get_current_employee_profile(cls, current_user: AuthenticatedUser) -> EmployeeProfileResponse:
        """
        Retrieves the verified employee profile for the authenticated and authorized user.
        Queries employee_registry by supabase_user_id or work_email.
        """
        repo = cls._get_repo()
        clean_uid = (current_user.user_id or "").strip()
        clean_email = (current_user.email or "").strip().lower()

        emp = None
        if clean_uid:
            emp = repo.get_employee_by_supabase_user_id(clean_uid)
        if not emp and clean_email:
            emp = repo.get_employee_by_email(clean_email)

        if emp:
            return EmployeeProfileResponse(
                employee_id=emp.get("employee_id"),
                work_email=emp.get("work_email"),
                full_name=emp.get("full_name") or "Authorized Employee",
                department=emp.get("department") or "Customer Success",
                status=str(emp.get("status", "APPROVED")).upper(),
                registered_at=emp.get("registered_at"),
                approved_at=emp.get("approved_at"),
            )

        # Fallback for settings-based authorized employees (AUTHORIZED_EMPLOYEE_EMAILS / USER_IDS)
        return EmployeeProfileResponse(
            employee_id=f"EMP-{clean_uid[:8].upper()}" if clean_uid else "EMP-STAFF-001",
            work_email=clean_email or "employee@retainiq.internal",
            full_name="Authorized Staff Member",
            department="Customer Success",
            status="APPROVED",
            registered_at=None,
            approved_at=None,
        )

