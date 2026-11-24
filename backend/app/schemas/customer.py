"""
Indian E-Commerce Customer Retention Intelligence System
Customer Schemas (Phase 8.4.4 - Backend Customer Management API Bridge)

Provides strictly typed Pydantic models for:
- CustomerSummary: Directory list item representation
- CustomerListResponse: Paginated customer collection envelope
- CustomerDetail: Comprehensive customer profile with associated ML intelligence
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


class CustomerSummary(BaseModel):
    """Customer representation for directory listings with ML intelligence."""
    model_config = ConfigDict(extra="ignore")

    customer_id: str = Field(..., description="Unique customer identifier (e.g. IND_CUST_10001)")
    customer_name: str = Field(..., description="Customer full name")
    signup_date: str = Field(..., description="Registration date in YYYY-MM-DD format")
    city: Optional[str] = Field(None, description="Customer city name")
    state: Optional[str] = Field(None, description="Customer state name")
    churn: Optional[int] = Field(None, ge=0, le=1, description="Ground-truth churn label (0 = Retained, 1 = Churned)")
    created_at: Optional[str] = Field(None, description="Database record creation timestamp")
    updated_at: Optional[str] = Field(None, description="Database record update timestamp")
    # Joined intelligence fields (Phase 8.4.8)
    cluster_id: Optional[int] = Field(None, description="Customer persona cluster ID (0 to 4)")
    segment_name: Optional[str] = Field(None, description="Official business persona name")
    churn_probability: Optional[float] = Field(None, description="Model churn probability score")
    predicted_churn: Optional[int] = Field(None, description="Predicted class label (1 = Churn, 0 = Retained)")
    risk_tier: Optional[str] = Field(None, description="Risk tier: LOW, MODERATE, HIGH")
    recency_delivered_days: Optional[float] = Field(None, description="Days since last delivered order")
    hist_delivered_order_count: Optional[int] = Field(None, description="Total delivered historical orders")
    hist_delivered_order_value_inr: Optional[float] = Field(None, description="Total delivered monetary spend (INR)")



class CustomerListResponse(BaseModel):
    """Paginated response envelope for customer directory listings."""
    items: List[CustomerSummary] = Field(default_factory=list, description="Paginated customer records")
    total: int = Field(..., ge=0, description="Total matching customer count in storage")
    limit: int = Field(..., ge=1, le=100, description="Applied page limit")
    offset: int = Field(..., ge=0, description="Applied page offset")
    has_more: bool = Field(..., description="Whether additional records exist beyond current page")


class CustomerDetail(BaseModel):
    """Comprehensive customer profile with associated ML intelligence artifacts."""
    model_config = ConfigDict(extra="ignore")

    customer_id: str = Field(..., description="Unique customer identifier")
    customer_name: str = Field(..., description="Customer full name")
    signup_date: str = Field(..., description="Registration date in YYYY-MM-DD format")
    city: Optional[str] = Field(None, description="Customer city name")
    state: Optional[str] = Field(None, description="Customer state name")
    snapshot_date: Optional[str] = Field(None, description="Observation snapshot cutoff date (2025-12-31)")
    churn: Optional[int] = Field(None, ge=0, le=1, description="Ground-truth churn label (0 = Retained, 1 = Churned)")
    created_at: Optional[str] = Field(None, description="Database record creation timestamp")
    updated_at: Optional[str] = Field(None, description="Database record update timestamp")
    latest_prediction: Optional[Dict[str, Any]] = Field(None, description="Latest persisted churn prediction record, if any")
    current_segment: Optional[Dict[str, Any]] = Field(None, description="Current RFM customer persona segment, if any")
    recommendations: List[Dict[str, Any]] = Field(default_factory=list, description="Active retention recommendations, if any")
    features: Optional[Dict[str, Any]] = Field(None, description="Full behavioral features dictionary for prediction explanation")

