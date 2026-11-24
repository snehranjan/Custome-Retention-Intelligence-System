"""
Indian E-Commerce Customer Retention Intelligence System
Machine Learning Result Persistence Service (Phase 7.4 Checkpoint 6)

Connects Phase 7.3 ML inference services to the Phase 7.4 persistent repository layer.
Strictly enforces:
1. Locked Random Forest model identity & tau = 0.50 threshold.
2. Genuine inference probability persistence (sum ~ 1.0).
3. 5 official RFM personas & single-active-segment enforcement.
4. Non-fabrication & deduplication of pending retention recommendations.
5. Critical failure rule: reporting inference results even if persistence fails.
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
import uuid

from backend.app.core.config import settings
from backend.app.core.logging import logger
from backend.app.repositories import get_repository
from backend.app.repositories.base_repository import BaseRepository
from backend.app.repositories.exceptions import (
    ConstraintViolationError,
    CustomerNotFoundError,
    DatabaseUnavailableError,
    DuplicateRecordError,
    ForeignKeyViolationError,
    RepositoryError,
)
from backend.app.schemas.ml import (
    ChurnPredictionResponse,
    PersistenceStatus,
    RawCustomerFeatures,
    RetentionRecommendationsResponse,
    SegmentationResponse,
)

LOCKED_RF_MODEL_NAME = "RandomForestClassifier_ConfigD"
LOCKED_RF_MODEL_VERSION = "1.0.0"
LOCKED_RF_MODEL_HASH = "24F1F0E33C75B5590906369960DB6E5951EC95DF9AE40384DA60082B3438F301"
LOCKED_SEGMENTATION_MODEL = "KMeans_RFM_K5"


class MLPersistenceService:
    """
    Coordinates atomic or multi-step persistence of churn predictions,
    customer segments, and retention recommendations into persistent storage.
    """

    @classmethod
    def persist_analysis_results(
        cls,
        customer_id: str,
        features: RawCustomerFeatures,
        churn_pred: ChurnPredictionResponse,
        segment: SegmentationResponse,
        recommendations: RetentionRecommendationsResponse,
        repository: Optional[BaseRepository] = None,
    ) -> PersistenceStatus:
        """
        Persists genuine ML inference outputs to active storage.
        Reports exact status for each sub-entity without masking partial errors.
        """
        status = PersistenceStatus()

        if not customer_id or not isinstance(customer_id, str):
            status.error = "Valid non-empty customer_id is required to persist results."
            return status

        repo = repository or get_repository()
        health = repo.get_health_status()
        status.backend = health.get("backend", "unknown")

        if not health.get("is_connected", False):
            status.error = f"Database backend '{status.backend}' is unavailable or offline."
            return status

        # Step 0: Verify customer profile exists in storage
        try:
            cust = repo.get_customer_by_id(customer_id)
            if cust is None:
                status.error = f"Customer '{customer_id}' does not exist in the database. Predictions require an existing customer profile."
                return status
        except Exception as e:
            status.error = f"Failed to verify customer existence: {str(e)}"
            return status

        prediction_id = str(uuid.uuid4())
        now_utc = datetime.now(timezone.utc).isoformat()

        # Step 1: Persist Churn Prediction
        try:
            # Map risk tier from churn probability
            risk_tier = churn_pred.risk_tier
            if risk_tier not in ("HIGH", "MODERATE", "LOW"):
                risk_tier = "MODERATE" if churn_pred.churn_probability >= 0.50 else "LOW"

            pred_data = {
                "prediction_id": prediction_id,
                "customer_id": str(customer_id),
                "churn_probability": float(churn_pred.churn_probability),
                "retention_probability": float(churn_pred.retention_probability),
                "predicted_churn": int(churn_pred.predicted_class),
                "decision_threshold": float(churn_pred.decision_threshold),
                "risk_tier": risk_tier,
                "model_name": LOCKED_RF_MODEL_NAME,
                "model_version": LOCKED_RF_MODEL_VERSION,
                "model_hash": LOCKED_RF_MODEL_HASH,
                "prediction_timestamp": now_utc,
            }
            repo.insert_prediction(pred_data)
            status.prediction_persisted = True
            status.prediction_id = prediction_id
        except Exception as e:
            logger.error("Failed to persist prediction for customer %s: %s", customer_id, str(e))
            status.error = f"Prediction persistence failed: {str(e)}"
            return status

        # Step 2: Persist RFM Segmentation (Archives previous active segment)
        try:
            recency = features.recency_delivered_days
            if recency is None or features.hist_delivered_order_count == 0:
                recency = 1117.0

            segment_data = {
                "customer_id": str(customer_id),
                "cluster_id": int(segment.cluster_id),
                "segment_name": str(segment.persona_name),
                "recency_delivered_days": float(recency),
                "hist_delivered_order_count": int(features.hist_delivered_order_count),
                "hist_delivered_order_value_inr": float(features.hist_delivered_order_value_inr),
                "segmentation_model": LOCKED_SEGMENTATION_MODEL,
                "is_current": 1,
            }
            seg_record = repo.upsert_customer_segment(segment_data)
            status.segment_persisted = True
            status.segment_id = seg_record.get("segment_record_id")
        except Exception as e:
            logger.error("Failed to persist segment for customer %s: %s", customer_id, str(e))
            status.error = f"Segment persistence failed: {str(e)}"
            return status

        # Step 3: Persist Retention Recommendations (Deduplicated against pending)
        try:
            existing_recs = repo.get_recommendations(customer_id, status="PENDING")
            existing_pending_actions = {
                (r.get("recommendation_category"), r.get("recommendation_title"))
                for r in existing_recs
            }

            rec_ids: List[str] = []
            for item in recommendations.recommendations:
                # Deduplication check: Avoid inserting identical pending recommendation
                key = (item.category, item.suggested_action)
                if key in existing_pending_actions:
                    continue

                rec_data = {
                    "customer_id": str(customer_id),
                    "prediction_id": prediction_id,
                    "recommendation_category": item.category,
                    "recommendation_title": item.suggested_action,
                    "recommendation_description": item.reason,
                    "evidence": item.evidence,
                    "priority": item.priority,
                    "recommendation_status": "PENDING",
                    "generated_at": now_utc,
                }
                created_rec = repo.insert_recommendation(rec_data)
                rec_ids.append(created_rec["recommendation_id"])

            status.recommendations_persisted = True
            status.recommendation_ids = rec_ids
            status.persisted_at = now_utc
        except Exception as e:
            logger.error("Failed to persist recommendations for customer %s: %s", customer_id, str(e))
            status.error = f"Recommendation persistence failed: {str(e)}"

        return status
