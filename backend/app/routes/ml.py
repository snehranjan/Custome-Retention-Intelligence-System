"""
Indian E-Commerce Customer Retention Intelligence System
Machine Learning & Analytics Routes (Phase 7.3)

Endpoints:
- GET  /api/v1/ml/status
- POST /api/v1/predictions/churn
- POST /api/v1/segmentation/predict
- POST /api/v1/retention/recommendations
- POST /api/v1/customers/analyze
"""

from datetime import datetime, timezone
from fastapi import APIRouter, Depends, status
from backend.app.core.config import settings
from backend.app.core.dependencies import get_current_user
from backend.app.schemas.common import ApiResponse
from backend.app.schemas.ml import (
    ChurnPredictionResponse,
    CustomerAnalysisRequest,
    CustomerAnalysisResponse,
    MLStatusResponse,
    RawCustomerFeatures,
    RetentionRecommendationsResponse,
    SegmentationInput,
    SegmentationResponse,
)
from backend.app.services.churn_service import ChurnPredictionService
from backend.app.services.customer_analysis_service import CustomerAnalysisService
from backend.app.services.model_loader import ModelLoader
from backend.app.services.retention_service import RetentionRecommendationEngine
from backend.app.services.segmentation_service import CustomerSegmentationService

router = APIRouter(
    tags=["Machine Learning & Analytics"],
    dependencies=[Depends(get_current_user)],
)


@router.get(
    "/ml/status",
    response_model=ApiResponse[MLStatusResponse],
    status_code=status.HTTP_200_OK,
    summary="Machine Learning Model & Artifact Status",
    description="Returns loading status, cryptographic SHA-256 hashes, and parameter metadata for all ML models.",
)
async def get_ml_status() -> ApiResponse[MLStatusResponse]:
    status_data = ModelLoader.get_status()
    meta = status_data.get("metadata", {})
    return ApiResponse[MLStatusResponse](
        success=True,
        data=MLStatusResponse(
            rf_pipeline_loaded=ModelLoader.is_loaded(),
            rf_model_sha256=meta.get("rf_model_sha256", settings.LOCKED_RF_MODEL_SHA256),
            rf_model_path=meta.get("rf_model_path", settings.LOCKED_RF_MODEL_PATH),
            decision_threshold=settings.LOCKED_DECISION_THRESHOLD,
            raw_feature_count=len(ChurnPredictionService.CONFIG_D_FEATURES),
            segmentation_loaded=ModelLoader.is_loaded(),
            segmentation_scaler_sha256=meta.get("scaler_sha256", settings.SEGMENTATION_SCALER_SHA256),
            segmentation_kmeans_sha256=meta.get("kmeans_sha256", settings.SEGMENTATION_KMEANS_SHA256),
            timestamp=datetime.now(timezone.utc).isoformat(),
        ),
    )


@router.post(
    "/predictions/churn",
    response_model=ApiResponse[ChurnPredictionResponse],
    status_code=status.HTTP_200_OK,
    summary="Predict Customer Churn Probability",
    description="Calculates calibrated churn probability using the locked Random Forest pipeline and locked tau=0.50 threshold.",
)
async def predict_churn(features: RawCustomerFeatures) -> ApiResponse[ChurnPredictionResponse]:
    prediction = ChurnPredictionService.predict(features)
    return ApiResponse[ChurnPredictionResponse](
        success=True,
        data=prediction,
    )


@router.post(
    "/segmentation/predict",
    response_model=ApiResponse[SegmentationResponse],
    status_code=status.HTTP_200_OK,
    summary="Assign RFM Customer Persona",
    description="Assigns customer to one of the 5 official personas using pre-fitted Scaler and K-Means clustering.",
)
async def predict_segment(rfm_input: SegmentationInput) -> ApiResponse[SegmentationResponse]:
    segment = CustomerSegmentationService.predict_segment(rfm_input)
    return ApiResponse[SegmentationResponse](
        success=True,
        data=segment,
    )


@router.post(
    "/retention/recommendations",
    response_model=ApiResponse[RetentionRecommendationsResponse],
    status_code=status.HTTP_200_OK,
    summary="Generate Rule-Based Retention Recommendations",
    description="Evaluates customer friction, RFM persona, and churn metrics to produce explainable retention interventions.",
)
async def get_retention_recommendations(features: RawCustomerFeatures) -> ApiResponse[RetentionRecommendationsResponse]:
    churn_pred = ChurnPredictionService.predict(features)
    seg_input = SegmentationInput(
        recency_delivered_days=features.recency_delivered_days,
        hist_delivered_order_count=features.hist_delivered_order_count,
        hist_delivered_order_value_inr=features.hist_delivered_order_value_inr,
    )
    segment = CustomerSegmentationService.predict_segment(seg_input)
    recs = RetentionRecommendationEngine.generate_recommendations(
        features=features,
        churn_pred=churn_pred,
        segment=segment,
    )
    return ApiResponse[RetentionRecommendationsResponse](
        success=True,
        data=recs,
    )


@router.post(
    "/customers/analyze",
    response_model=ApiResponse[CustomerAnalysisResponse],
    status_code=status.HTTP_200_OK,
    summary="Comprehensive Customer Intelligence Analysis",
    description="Combines churn prediction, RFM segmentation, and rule-based retention actions into a single response.",
)
async def analyze_customer(
    request: CustomerAnalysisRequest,
    persist: bool = False,
) -> ApiResponse[CustomerAnalysisResponse]:
    analysis = CustomerAnalysisService.analyze_customer(request, persist=persist)
    return ApiResponse[CustomerAnalysisResponse](
        success=True,
        data=analysis,
    )
