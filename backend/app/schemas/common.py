"""
Indian E-Commerce Customer Retention Intelligence System
Standardized API Response and Error Envelope Schemas
"""

from datetime import datetime, timezone
from typing import Any, Generic, List, Optional, TypeVar
from pydantic import BaseModel, Field

DataT = TypeVar("DataT")


class ResponseMeta(BaseModel):
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    version: str = "1.0.0"
    path: Optional[str] = None


class ErrorDetail(BaseModel):
    code: str
    message: str
    details: List[Any] = Field(default_factory=list)


class ApiResponse(BaseModel, Generic[DataT]):
    """Standard success API envelope."""
    success: bool = True
    data: DataT
    meta: ResponseMeta = Field(default_factory=ResponseMeta)


class ErrorResponse(BaseModel):
    """Standard error API envelope."""
    success: bool = False
    error: ErrorDetail
    meta: ResponseMeta = Field(default_factory=ResponseMeta)


class HealthStatusData(BaseModel):
    status: str = "healthy"
    environment: str
    version: str
    api_prefix: str
    ml_artifacts_ready: bool
    timestamp: str
