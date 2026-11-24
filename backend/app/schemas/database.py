"""
Indian E-Commerce Customer Retention Intelligence System
Database & Storage API Schemas (Phase 7.4 Checkpoint 7)

Provides strictly typed Pydantic models for database health checks,
storage status inspection, customer metrics, and administrative import status.
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class DatabaseHealthData(BaseModel):
    """Payload for database connectivity and health diagnostics."""
    status: str = Field(..., description="Overall health: 'healthy' or 'unavailable'")
    storage_mode: str = Field(..., description="Active configured storage mode: 'sqlite' or 'supabase'")
    backend: str = Field(..., description="Active backend implementation name")
    is_connected: bool = Field(..., description="Whether persistent database is reachable")
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    error: Optional[str] = Field(None, description="Sanitized error diagnostic if unavailable")


class DatabaseStatusData(BaseModel):
    """Payload for comprehensive database schema and storage status."""
    status: str = Field(..., description="Overall status: 'healthy' or 'unavailable'")
    storage_mode: str = Field(..., description="Configured storage mode: 'sqlite' or 'supabase'")
    backend: str = Field(..., description="Active storage driver backend")
    is_connected: bool = Field(..., description="Connection probe result")
    schema_ready: bool = Field(..., description="Whether required tables and migrations are present")
    applied_migrations: List[str] = Field(default_factory=list, description="List of recorded migrations")
    tables_available: List[str] = Field(default_factory=list, description="List of verified tables")
    table_counts: Dict[str, int] = Field(default_factory=dict, description="Row counts per table")
    database_version: Optional[str] = Field(None, description="Database engine version info")
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    error: Optional[str] = Field(None, description="Sanitized error if inspection failed")


class CustomerCountMetricsData(BaseModel):
    """Aggregated demographic and ground-truth counts from the customers table."""
    total_customers: int = Field(..., ge=0, description="Total customer records in database")
    churned_customers: int = Field(..., ge=0, description="Customers labeled churned (churn = 1)")
    retained_customers: int = Field(..., ge=0, description="Customers labeled retained (churn = 0)")
    null_city_count: int = Field(..., ge=0, description="Customers with missing city attribute")
    null_state_count: int = Field(..., ge=0, description="Customers with missing state attribute")
    reconciliation_valid: bool = Field(..., description="Whether churned + retained equals total_customers")
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class DatabaseImportStatusData(BaseModel):
    """Administrative status of baseline customer data population."""
    storage_mode: str = Field(..., description="Configured storage mode")
    baseline_records_expected: int = Field(7000, description="Expected baseline customer count from Phase 1")
    current_customer_count: int = Field(..., ge=0, description="Actual customers present in database")
    is_baseline_populated: bool = Field(..., description="True if database holds >= 7,000 customers")
    status: str = Field(..., description="Status summary: 'READY', 'INCOMPLETE', or 'UNAVAILABLE'")
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
