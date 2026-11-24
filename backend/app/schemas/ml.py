"""
Indian E-Commerce Customer Retention Intelligence System
Pydantic Schemas for ML Inference, Segmentation, and Recommendations (Phase 7.3)
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator
import math


class RawCustomerFeatures(BaseModel):
    """
    Authoritative 43-feature input contract for Random Forest Configuration D.
    Enforces strict typing, rejects unexpected fields, and accepts valid optional nulls.
    """
    model_config = ConfigDict(extra="forbid")

    # 40 Numerical Features
    customer_tenure_days: float = Field(..., ge=0, description="Days since customer registration")
    has_historical_orders: int = Field(..., ge=0, le=1, description="Binary flag: 1 if customer has placed any order")
    recency_days: Optional[float] = Field(None, ge=0, description="Days since last order placed; None for zero-order accounts")
    recency_delivered_days: Optional[float] = Field(None, ge=0, description="Days since last fulfilled order; None if 0 delivered orders")
    has_delivered_order: int = Field(..., ge=0, le=1, description="Binary flag: 1 if customer has >=1 delivered order")
    hist_order_count: int = Field(..., ge=0, description="Total historical orders placed")
    hist_delivered_order_count: int = Field(..., ge=0, description="Total delivered historical orders")
    hist_returned_order_count: int = Field(..., ge=0, description="Total returned orders")
    hist_cancelled_order_count: int = Field(..., ge=0, description="Total cancelled orders")
    hist_total_order_value_inr: float = Field(..., ge=0, description="Gross value of all historical orders (INR)")
    hist_delivered_order_value_inr: float = Field(..., ge=0, description="Net value of all delivered orders (INR)")
    hist_total_recorded_discount_inr: float = Field(..., ge=0, description="Total discount amounts recorded (INR)")
    hist_average_order_value_inr: float = Field(..., ge=0, description="Average gross order value (INR)")
    orders_last_30_days: int = Field(..., ge=0, description="Gross orders in final 30 days of observation")
    orders_last_90_days: int = Field(..., ge=0, description="Gross orders in final 90 days of observation")
    orders_last_180_days: int = Field(..., ge=0, description="Gross orders in final 180 days of observation")
    delivered_orders_last_30_days: int = Field(..., ge=0, description="Delivered orders in final 30 days")
    delivered_orders_last_90_days: int = Field(..., ge=0, description="Delivered orders in final 90 days")
    delivered_orders_last_180_days: int = Field(..., ge=0, description="Delivered orders in final 180 days")
    hist_return_rate: Optional[float] = Field(None, ge=0.0, le=1.0, description="Ratio of returned orders to total orders")
    hist_cancellation_rate: Optional[float] = Field(None, ge=0.0, le=1.0, description="Ratio of cancelled orders to total orders")
    hist_average_delivery_delay_days: Optional[float] = Field(None, description="Average delivery SLA delay in days")
    hist_delivery_delay_missing_count: int = Field(..., ge=0, description="Count of orders with missing delivery delay data")
    hist_delivery_delay_missing_rate: float = Field(..., ge=0.0, le=1.0, description="Fraction of orders missing delay data")
    hist_average_discount_amount_inr: float = Field(..., ge=0.0, description="Average discount applied per order (INR)")
    hist_discounted_order_count: int = Field(..., ge=0, description="Number of orders where discount was applied")
    hist_discount_missing_count: int = Field(..., ge=0, description="Orders with missing discount data")
    hist_discount_missing_rate: float = Field(..., ge=0.0, le=1.0, description="Fraction of orders with missing discount data")
    hist_payment_missing_count: int = Field(..., ge=0, description="Orders with unrecorded payment method")
    hist_payment_missing_rate: float = Field(..., ge=0.0, le=1.0, description="Fraction of orders missing payment method")
    hist_cod_order_count: int = Field(..., ge=0, description="Orders placed via Cash on Delivery")
    hist_cod_usage_rate: float = Field(..., ge=0.0, le=1.0, description="Fraction of orders paid via COD")
    hist_upi_order_count: int = Field(..., ge=0, description="Orders placed via UPI")
    hist_upi_usage_rate: float = Field(..., ge=0.0, le=1.0, description="Fraction of orders paid via UPI")
    velocity_ratio_30_90: Optional[float] = Field(None, ge=0.0, description="Order momentum ratio: orders_last_30_days / (orders_last_90_days / 3)")
    velocity_ratio_90_180: Optional[float] = Field(None, ge=0.0, description="Order momentum ratio: orders_last_90_days / (orders_last_180_days / 2)")
    has_orders_last_90_days: int = Field(..., ge=0, le=1, description="Binary flag: 1 if orders_last_90_days > 0")
    has_orders_last_180_days: int = Field(..., ge=0, le=1, description="Binary flag: 1 if orders_last_180_days > 0")
    delay_friction_score: Optional[float] = Field(None, ge=0.0, description="Operational friction metric combining delay and cancellation")
    missing_friction_score: float = Field(..., ge=0.0, description="Data logging friction metric combining missing delivery and payment fields")

    # 3 Categorical Features
    city: str = Field(..., min_length=1, description="Customer Indian city name")
    state: str = Field(..., min_length=1, description="Customer Indian state name")
    cluster_id: int = Field(..., ge=0, le=4, description="Customer RFM segment cluster (0, 1, 2, 3, or 4)")

    @field_validator(
        "customer_tenure_days",
        "recency_days",
        "recency_delivered_days",
        "hist_total_order_value_inr",
        "hist_delivered_order_value_inr",
        "hist_total_recorded_discount_inr",
        "hist_average_order_value_inr",
        "hist_return_rate",
        "hist_cancellation_rate",
        "hist_average_delivery_delay_days",
        "hist_average_discount_amount_inr",
        "velocity_ratio_30_90",
        "velocity_ratio_90_180",
        "delay_friction_score",
        "missing_friction_score",
        mode="before",
    )
    @classmethod
    def reject_infinite_values(cls, v: Any) -> Any:
        if v is not None and isinstance(v, (int, float)):
            if math.isinf(v) or (isinstance(v, float) and math.isnan(v)):
                raise ValueError("Infinite or non-finite float values are not allowed in input features")
        return v


class ChurnPredictionResponse(BaseModel):
    churn_probability: float = Field(..., ge=0.0, le=1.0, description="Calibrated probability of customer churning")
    retention_probability: float = Field(..., ge=0.0, le=1.0, description="Calibrated probability of customer being retained")
    predicted_class: int = Field(..., ge=0, le=1, description="Binary prediction: 1 = Churn, 0 = Retained")
    decision_threshold: float = Field(0.50, description="Locked decision boundary tau")
    prediction_label: str = Field(..., description="Human-readable prediction: 'Churn' or 'Retained'")
    risk_tier: str = Field(..., description="Risk tier: 'HIGH' (p>=0.70), 'MODERATE' (0.50<=p<0.70), or 'LOW' (p<0.50)")


class SegmentationInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    recency_delivered_days: Optional[float] = Field(None, ge=0, description="Days since last delivered purchase; None for zero-delivered")
    hist_delivered_order_count: int = Field(..., ge=0, description="Total historical delivered orders")
    hist_delivered_order_value_inr: float = Field(..., ge=0, description="Total delivered monetary spend (INR)")

    @field_validator("recency_delivered_days", "hist_delivered_order_value_inr", mode="before")
    @classmethod
    def reject_infinite_segmentation(cls, v: Any) -> Any:
        if v is not None and isinstance(v, (int, float)):
            if math.isinf(v) or (isinstance(v, float) and math.isnan(v)):
                raise ValueError("Infinite or NaN values are not allowed in segmentation inputs")
        return v


class SegmentationResponse(BaseModel):
    cluster_id: int = Field(..., ge=0, le=4, description="Assigned K-Means cluster (0 to 4)")
    persona_name: str = Field(..., description="Official business persona name")
    behavioral_profile: str = Field(..., description="Description of purchasing behavior and frequency")


class RetentionRecommendationItem(BaseModel):
    category: str = Field(..., description="Recommendation category (e.g. Loyalty Rewards, Delivery Experience)")
    suggested_action: str = Field(..., description="Concrete, actionable retention intervention")
    reason: str = Field(..., description="Objective explanation grounded in customer behavior")
    evidence: str = Field(..., description="Specific metrics and signals supporting the action")
    priority: str = Field(..., description="Intervention priority: 'HIGH', 'MEDIUM', or 'LOW'")


class RetentionRecommendationsResponse(BaseModel):
    recommendations: List[RetentionRecommendationItem]
    total_recommendations: int
    top_priority: Optional[str] = None


class PersistenceStatus(BaseModel):
    """Detailed persistence audit status for an analyzed customer."""
    prediction_persisted: bool = False
    segment_persisted: bool = False
    recommendations_persisted: bool = False
    prediction_id: Optional[str] = None
    segment_id: Optional[str] = None
    recommendation_ids: List[str] = Field(default_factory=list)
    persisted_at: Optional[str] = None
    backend: Optional[str] = None
    error: Optional[str] = None


class CustomerAnalysisRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    customer_id: Optional[str] = Field(None, description="Optional customer identifier")
    features: RawCustomerFeatures
    persist_results: bool = Field(False, description="Whether to persist results to active storage")


class CustomerAnalysisResponse(BaseModel):
    customer_id: Optional[str] = None
    churn_prediction: ChurnPredictionResponse
    segmentation: SegmentationResponse
    retention_recommendations: RetentionRecommendationsResponse
    persistence_status: Optional[PersistenceStatus] = None
    analysis_timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class MLStatusResponse(BaseModel):
    rf_pipeline_loaded: bool
    rf_model_sha256: str
    rf_model_path: str
    decision_threshold: float
    raw_feature_count: int
    segmentation_loaded: bool
    segmentation_scaler_sha256: str
    segmentation_kmeans_sha256: str
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
