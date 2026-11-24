"""
Indian E-Commerce Customer Retention Intelligence System
Employee Registration & Administrator Schemas (Phase 8.4.5)

Provides strictly typed Pydantic models for:
- EmployeeRegistrationRequest: Employee ID registration payload
- EmployeeRegistrationResponse: Safe confirmation payload
- EmployeeResponse: Full employee registry model
- EmployeeApprovalRequest / EmployeeRejectionRequest: Admin operation payloads
"""

import re
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class EmployeeRegistrationRequest(BaseModel):
    """Payload for registering an administrator-issued Employee ID."""
    model_config = ConfigDict(extra="forbid")

    employee_id: str = Field(..., min_length=3, max_length=32, description="Pre-issued Employee ID (e.g. EMP-2026-002)")
    work_email: str = Field(..., min_length=5, max_length=128, description="Enterprise work email address")
    password: str = Field(..., min_length=8, max_length=128, description="Account password")
    confirm_password: str = Field(..., min_length=8, max_length=128, description="Password confirmation")

    @field_validator("employee_id")
    @classmethod
    def clean_employee_id(cls, v: str) -> str:
        cleaned = v.strip().upper()
        if not cleaned or len(cleaned) < 3:
            raise ValueError("Employee ID must be at least 3 non-whitespace characters.")
        if not re.match(r"^[A-Z0-9_\-]+$", cleaned):
            raise ValueError("Employee ID may only contain alphanumeric characters, hyphens, and underscores.")
        return cleaned

    @field_validator("work_email")
    @classmethod
    def clean_work_email(cls, v: str) -> str:
        cleaned = v.strip().lower()
        email_regex = r"^[^\s@]+@[^\s@]+\.[^\s@]+$"
        if not re.match(email_regex, cleaned):
            raise ValueError("Invalid work email address format.")
        return cleaned

    @field_validator("password")
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters in length.")
        return v

    @model_validator(mode="after")
    def verify_passwords_match(self) -> "EmployeeRegistrationRequest":
        if self.password != self.confirm_password:
            raise ValueError("Password and confirmation password do not match.")
        return self


class EmployeeRegistrationResponse(BaseModel):
    """Safe response returned to applicant after registration submission."""
    model_config = ConfigDict(extra="ignore")

    employee_id: str = Field(..., description="Registered Employee ID")
    work_email: str = Field(..., description="Registered work email")
    status: str = Field("PENDING", description="Current employee status (PENDING administrator approval)")
    registered_at: str = Field(..., description="Registration timestamp")
    message: str = Field(
        "Employee registration submitted successfully. Your account is awaiting administrator approval.",
        description="User-facing status message",
    )


class EmployeeResponse(BaseModel):
    """Detailed employee registry record for administrative inspection."""
    model_config = ConfigDict(extra="ignore")

    employee_id: str
    work_email: str
    full_name: Optional[str] = None
    department: Optional[str] = None
    supabase_user_id: Optional[str] = None
    status: str
    created_at: Optional[str] = None
    registered_at: Optional[str] = None
    approved_at: Optional[str] = None
    approved_by: Optional[str] = None
    rejection_reason: Optional[str] = None
    notes: Optional[str] = None


class EmployeeApprovalRequest(BaseModel):
    """Optional payload when an administrator approves an employee."""
    model_config = ConfigDict(extra="forbid")
    notes: Optional[str] = Field(None, max_length=256, description="Optional administrative approval notes")


class EmployeeRejectionRequest(BaseModel):
    """Mandatory payload when an administrator rejects an employee registration."""
    model_config = ConfigDict(extra="forbid")
    reason: str = Field(..., min_length=3, max_length=256, description="Objective reason for registration rejection")


class EmployeeInvitationRequest(BaseModel):
    """Payload for administrator pre-authorizing / inviting an employee."""
    model_config = ConfigDict(extra="forbid")

    employee_id: str = Field(..., min_length=3, max_length=32, description="Unique Employee ID (e.g. EMP-2026-004)")
    work_email: str = Field(..., min_length=5, max_length=128, description="Enterprise work email address")
    full_name: Optional[str] = Field(None, max_length=128, description="Employee full name")
    department: Optional[str] = Field("Customer Success", max_length=64, description="Assigned department")
    notes: Optional[str] = Field(None, max_length=256, description="Optional administrative notes")

    @field_validator("employee_id")
    @classmethod
    def clean_employee_id(cls, v: str) -> str:
        cleaned = v.strip().upper()
        if not cleaned or len(cleaned) < 3:
            raise ValueError("Employee ID must be at least 3 non-whitespace characters.")
        if not re.match(r"^[A-Z0-9_\-]+$", cleaned):
            raise ValueError("Employee ID may only contain alphanumeric characters, hyphens, and underscores.")
        return cleaned

    @field_validator("work_email")
    @classmethod
    def clean_work_email(cls, v: str) -> str:
        cleaned = v.strip().lower()
        email_regex = r"^[^\s@]+@[^\s@]+\.[^\s@]+$"
        if not re.match(email_regex, cleaned):
            raise ValueError("Invalid work email address format.")
        return cleaned


class AdminStatsResponse(BaseModel):
    """Aggregated employee registry statistics."""
    model_config = ConfigDict(extra="ignore")

    total: int = Field(0, description="Total registered or invited employee records")
    pending: int = Field(0, description="Employees awaiting approval")
    approved: int = Field(0, description="Approved employees with active access")
    rejected: int = Field(0, description="Rejected employee applications")
    suspended: int = Field(0, description="Suspended employee accounts")
    invited: int = Field(0, description="Pre-authorized invitations awaiting applicant registration")


class AdminProfileResponse(BaseModel):
    """Administrator verification and profile payload."""
    model_config = ConfigDict(extra="ignore")

    user_id: str = Field(..., description="Administrator subject identifier")
    email: Optional[str] = Field(None, description="Administrator email address")
    is_admin: bool = Field(True, description="Confirmed administrator privilege flag")
    role: str = Field("ADMINISTRATOR", description="Access role identifier")


class EmployeeProfileResponse(BaseModel):
    """Verified employee profile payload returned to authorized employee."""
    model_config = ConfigDict(extra="ignore")

    employee_id: str = Field(..., description="Unique employee identifier (e.g. EMP-2026-001)")
    work_email: str = Field(..., description="Enterprise work email address")
    full_name: Optional[str] = Field(None, description="Employee full name")
    department: Optional[str] = Field("Customer Success", description="Department or business unit")
    status: str = Field("APPROVED", description="Authorization status (strictly APPROVED)")
    registered_at: Optional[str] = Field(None, description="Registration timestamp")
    approved_at: Optional[str] = Field(None, description="Administrator approval timestamp")

