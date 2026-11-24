"""
Indian E-Commerce Customer Retention Intelligence System
Analytics & Intelligence Routes (Phase 8.4.8 - Customer Retention Explorer & Advanced Analytics)

Endpoints:
- GET /api/v1/analytics/overview: Master KPI summary, churn distributions, and segment metrics
- GET /api/v1/analytics/model-performance: Authoritative evaluation metrics (N=1,500) and confusion matrix
- GET /api/v1/analytics/segments: 5 official persona profiles with customer metrics & retention strategies

Security:
- All routes strictly protected by require_authorized_employee dependency.
- Rejects unauthenticated requests with HTTP 401 UNAUTHORIZED.
- Rejects authenticated but unapproved accounts with HTTP 403 FORBIDDEN.
"""

from typing import List
from fastapi import APIRouter, Depends, status

from backend.app.core.config import settings
from backend.app.core.dependencies import require_authorized_employee
from backend.app.repositories import get_repository
from backend.app.schemas.auth import AuthenticatedUser
from backend.app.schemas.common import ApiResponse
from backend.app.schemas.analytics import (
    ClassDistributions,
    ConfusionMatrixData,
    EvaluationMetrics,
    ModelPerformanceData,
    OverviewAnalyticsData,
    SegmentMetricItem,
)

router = APIRouter(
    prefix="/analytics",
    tags=["Analytics & Intelligence"],
    dependencies=[Depends(require_authorized_employee)],
)


@router.get(
    "/overview",
    response_model=ApiResponse[OverviewAnalyticsData],
    status_code=status.HTTP_200_OK,
    summary="Get Overview Analytics & KPIs",
    description=(
        "Retrieves master executive dashboard KPIs (7,000 customers, observed churn rate 45.81%, "
        "predicted at-risk rate 47.94%), risk tier distributions, and geographic summaries."
    ),
)
async def get_overview_analytics(
    current_employee: AuthenticatedUser = Depends(require_authorized_employee),
) -> ApiResponse[OverviewAnalyticsData]:
    """Returns authoritative cohort metrics and distribution breakdowns."""
    storage_mode = settings.STORAGE_MODE.lower()
    repo = get_repository(storage_mode)

    data = repo.get_overview_analytics()
    return ApiResponse[OverviewAnalyticsData](
        success=True,
        data=OverviewAnalyticsData(**data),
    )


@router.get(
    "/model-performance",
    response_model=ApiResponse[ModelPerformanceData],
    status_code=status.HTTP_200_OK,
    summary="Get Model Performance & Evaluation Metrics",
    description=(
        "Retrieves authoritative model evaluation scorecard on the independent synthetic test cohort "
        "(N = 1,500) with locked decision boundary (tau = 0.50), confusion matrix, and full disclosures."
    ),
)
async def get_model_performance(
    current_employee: AuthenticatedUser = Depends(require_authorized_employee),
) -> ApiResponse[ModelPerformanceData]:
    """Returns the frozen Phase 5.1 test cohort evaluation metrics and model provenance."""
    performance_data = ModelPerformanceData(
        evaluation_cohort="Phase 5.1 Independent Synthetic Test Cohort",
        sample_size=1500,
        locked_decision_threshold=0.50,
        model_name="RandomForestClassifier_ConfigD",
        model_sha256="24F1F0E33C75B5590906369960DB6E5951EC95DF9AE40384DA60082B3438F301",
        features_count=43,
        hyperparameters={
            "n_estimators": 150,
            "max_depth": 8,
            "min_samples_split": 2,
            "min_samples_leaf": 5,
            "criterion": "gini",
            "class_weight": "balanced",
            "random_state": 42,
        },
        metrics=EvaluationMetrics(
            accuracy=0.6893,
            precision=0.6422,
            recall=0.6900,
            specificity=0.6888,
            balanced_accuracy=0.6894,
            f1_score=0.6652,
            roc_auc=0.7651,
            average_precision=0.7308,
            brier_score=0.1970,
        ),
        confusion_matrix=ConfusionMatrixData(
            true_negatives=571,
            false_positives=258,
            false_negatives=208,
            true_positives=463,
        ),
        class_distributions=ClassDistributions(
            actual_retained=829,
            actual_churned=671,
            actual_churn_rate=0.4473,
            predicted_retained=779,
            predicted_churned=721,
            predicted_churn_rate=0.4807,
        ),
        methodology_disclosure=(
            "Model evaluated on an independent, held-out test cohort of 1,500 synthetic customer records "
            "partitioned chronologically to prevent lookahead bias. The model operates under locked decision "
            "threshold tau = 0.50."
        ),
        calibration_disclosure=(
            "Predictions reflect raw uncalibrated Random Forest voting probabilities. The threshold tau = 0.50 "
            "is mathematically locked based on empirical utility analysis during Phase 5.1."
        ),
    )

    return ApiResponse[ModelPerformanceData](
        success=True,
        data=performance_data,
    )


@router.get(
    "/segments",
    response_model=ApiResponse[List[SegmentMetricItem]],
    status_code=status.HTTP_200_OK,
    summary="Get 5 Customer Segmentation Profiles",
    description=(
        "Retrieves customer population and churn distribution across all 5 official personas "
        "(Clusters 0 through 4) with recommended operational strategies."
    ),
)
async def get_segment_profiles(
    current_employee: AuthenticatedUser = Depends(require_authorized_employee),
) -> ApiResponse[List[SegmentMetricItem]]:
    """Returns the 5 official segmentation clusters with population counts and churn rates."""
    storage_mode = settings.STORAGE_MODE.lower()
    repo = get_repository(storage_mode)

    overview = repo.get_overview_analytics()
    segment_data = overview.get("segment_distribution", [])
    items = [SegmentMetricItem(**s) for s in segment_data]

    return ApiResponse[List[SegmentMetricItem]](
        success=True,
        data=items,
    )
