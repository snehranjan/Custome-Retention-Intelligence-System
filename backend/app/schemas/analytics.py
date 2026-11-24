"""
Indian E-Commerce Customer Retention Intelligence System
Analytics & Intelligence Schemas (Phase 8.4.8)

Provides strictly typed Pydantic models for:
- OverviewAnalyticsResponse: Master KPI summary, churn distributions, and segment metrics
- ModelPerformanceResponse: Independent evaluation test cohort metrics (N=1,500)
- SegmentProfileItem: 5 official persona profiles with customer metrics & retention strategies
- RecommendationItemDetail: Enriched retention action with customer context
- RecommendationListResponse: Paginated recommendation collection
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


class DistributionItem(BaseModel):
    model_config = ConfigDict(extra="ignore")
    label: str
    count: int
    percentage: float
    color: Optional[str] = None


class RiskTierItem(BaseModel):
    model_config = ConfigDict(extra="ignore")
    tier: str
    label: str
    count: int
    percentage: float
    range: str
    color: Optional[str] = None


class SegmentMetricItem(BaseModel):
    model_config = ConfigDict(extra="ignore")
    cluster_id: int
    segment_name: str
    customer_count: int
    share_percentage: float
    observed_churn_count: int
    observed_churn_rate: float
    predicted_churn_count: int
    predicted_churn_rate: float
    avg_monetary_inr: float
    avg_recency_days: float
    avg_delivered_orders: float
    persona_description: str
    recommended_strategy: str


class GeographicItem(BaseModel):
    model_config = ConfigDict(extra="ignore")
    name: str
    total_customers: int
    churned_customers: int
    churn_rate: float


class OverviewKpis(BaseModel):
    model_config = ConfigDict(extra="ignore")
    total_customers: int = 7000
    observed_churned: int = 3207
    observed_retained: int = 3793
    observed_churn_rate: float = 0.4581
    predicted_at_risk: int = 3356
    predicted_retained: int = 3644
    predicted_at_risk_rate: float = 0.4794


class OverviewAnalyticsData(BaseModel):
    model_config = ConfigDict(extra="ignore")
    kpis: OverviewKpis
    observed_churn_distribution: List[DistributionItem]
    predicted_risk_distribution: List[RiskTierItem]
    segment_distribution: List[SegmentMetricItem]
    state_distribution: List[GeographicItem]
    city_distribution: List[GeographicItem]
    dataset_metadata: Dict[str, Any]
    model_metadata: Dict[str, Any]


class ConfusionMatrixData(BaseModel):
    model_config = ConfigDict(extra="ignore")
    true_negatives: int = 571
    false_positives: int = 258
    false_negatives: int = 208
    true_positives: int = 463


class EvaluationMetrics(BaseModel):
    model_config = ConfigDict(extra="ignore")
    accuracy: float = 0.6893
    precision: float = 0.6422
    recall: float = 0.6900
    specificity: float = 0.6888
    balanced_accuracy: float = 0.6894
    f1_score: float = 0.6652
    roc_auc: float = 0.7651
    average_precision: float = 0.7308
    brier_score: float = 0.1970


class ClassDistributions(BaseModel):
    model_config = ConfigDict(extra="ignore")
    actual_retained: int = 829
    actual_churned: int = 671
    actual_churn_rate: float = 0.4473
    predicted_retained: int = 779
    predicted_churned: int = 721
    predicted_churn_rate: float = 0.4807


class ModelPerformanceData(BaseModel):
    model_config = ConfigDict(extra="ignore")
    evaluation_cohort: str = "Phase 5.1 Independent Synthetic Test Cohort"
    sample_size: int = 1500
    locked_decision_threshold: float = 0.50
    model_name: str = "RandomForestClassifier_ConfigD"
    model_sha256: str = "24F1F0E33C75B5590906369960DB6E5951EC95DF9AE40384DA60082B3438F301"
    features_count: int = 43
    hyperparameters: Dict[str, Any]
    metrics: EvaluationMetrics
    confusion_matrix: ConfusionMatrixData
    class_distributions: ClassDistributions
    methodology_disclosure: str
    calibration_disclosure: str


class RecommendationItemDetail(BaseModel):
    model_config = ConfigDict(extra="ignore")
    recommendation_id: str
    customer_id: str
    customer_name: Optional[str] = None
    cluster_id: Optional[int] = None
    segment_name: Optional[str] = None
    churn_probability: Optional[float] = None
    risk_tier: Optional[str] = None
    category: str
    suggested_action: str
    reason: str
    evidence: str
    priority: str
    status: str = "PENDING"
    suggested_channel: str
    generated_at: str


class RecommendationListResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")
    items: List[RecommendationItemDetail] = Field(default_factory=list)
    total: int = Field(..., ge=0)
    limit: int = Field(..., ge=1, le=100)
    offset: int = Field(..., ge=0)
    has_more: bool = Field(...)
