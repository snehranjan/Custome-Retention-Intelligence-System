"""
Indian E-Commerce Customer Retention Intelligence System
Authentication Schemas (Phase 7.5 Checkpoint 3 - Security Corrected)

Provides minimal Pydantic models for authenticated user identity and auth health diagnostics.
Strictly adheres to the principle of least privilege and minimal disclosure.
"""

from datetime import datetime, timezone
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class AuthenticatedUser(BaseModel):
    """
    Minimal verified employee identity derived strictly from validated Supabase JWT claims.
    Contains only essential identity fields (user_id and optional validated email).
    Excludes user_metadata, app_metadata, role, and internal token metadata to adhere
    to the principle of minimal disclosure and prevent privilege leakage.
    """
    model_config = ConfigDict(extra="forbid")

    user_id: str = Field(..., description="Unique Supabase Auth UUID (sub claim)")
    email: Optional[str] = Field(None, description="Employee email address if present and validated")


class AuthHealthData(BaseModel):
    """Public non-sensitive authentication status."""
    status: str = Field("healthy", description="Authentication service configuration health")
    auth_provider: str = Field("supabase_auth", description="Active authentication provider")
    signing_algorithm: str = Field("ES256", description="Authoritative asymmetric signing algorithm")
    jwks_configured: bool = Field(True, description="Whether JWKS endpoint is configured")
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
