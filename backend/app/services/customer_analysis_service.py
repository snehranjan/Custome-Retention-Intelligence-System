"""
Indian E-Commerce Customer Retention Intelligence System
Customer Analysis Coordinator Service (Phase 7.3)

Coordinates churn prediction, RFM segmentation, and rule-based retention recommendations
into a unified single-customer analytics response.
"""

from typing import Optional
from backend.app.repositories.base_repository import BaseRepository
from backend.app.schemas.ml import (
    CustomerAnalysisRequest,
    CustomerAnalysisResponse,
    PersistenceStatus,
    RawCustomerFeatures,
    SegmentationInput,
)
from backend.app.services.churn_service import ChurnPredictionService
from backend.app.services.ml_persistence_service import MLPersistenceService
from backend.app.services.retention_service import RetentionRecommendationEngine
from backend.app.services.segmentation_service import CustomerSegmentationService


class CustomerAnalysisService:
    """
    Coordinates end-to-end customer intelligence: Churn Prediction + RFM Persona + Retention Actions,
    with optional audit-compliant database persistence.
    """

    @classmethod
    def analyze_customer(
        cls,
        request: CustomerAnalysisRequest,
        persist: bool = False,
        repository: Optional[BaseRepository] = None,
    ) -> CustomerAnalysisResponse:
        features = request.features

        # 1. Execute Segmentation (RFM Preprocessing + Scaler + KMeans)
        seg_input = SegmentationInput(
            recency_delivered_days=features.recency_delivered_days,
            hist_delivered_order_count=features.hist_delivered_order_count,
            hist_delivered_order_value_inr=features.hist_delivered_order_value_inr,
        )
        segment_response = CustomerSegmentationService.predict_segment(seg_input)

        # 2. Ensure cluster_id in features aligns with predicted segment
        features_dict = features.model_dump()
        features_dict["cluster_id"] = segment_response.cluster_id
        aligned_features = RawCustomerFeatures(**features_dict)

        # 3. Execute Churn Prediction with verified 43 features
        churn_response = ChurnPredictionService.predict(aligned_features)

        # 4. Generate Explainable Retention Recommendations
        retention_response = RetentionRecommendationEngine.generate_recommendations(
            features=aligned_features,
            churn_pred=churn_response,
            segment=segment_response,
        )

        # 5. Optional ML Result Persistence (Phase 7.4 Checkpoint 6)
        persistence_status: Optional[PersistenceStatus] = None
        should_persist = persist or getattr(request, "persist_results", False)
        if should_persist:
            if not request.customer_id:
                persistence_status = PersistenceStatus(
                    error="customer_id must be provided to persist analysis results."
                )
            else:
                persistence_status = MLPersistenceService.persist_analysis_results(
                    customer_id=request.customer_id,
                    features=aligned_features,
                    churn_pred=churn_response,
                    segment=segment_response,
                    recommendations=retention_response,
                    repository=repository,
                )

        return CustomerAnalysisResponse(
            customer_id=request.customer_id,
            churn_prediction=churn_response,
            segmentation=segment_response,
            retention_recommendations=retention_response,
            persistence_status=persistence_status,
        )
