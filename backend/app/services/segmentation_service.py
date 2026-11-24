"""
Indian E-Commerce Customer Retention Intelligence System
Customer Segmentation Service (Phase 7.3)

Strict Invariants:
1. Frozen Scaler: models/segmentation_scaler.joblib (SHA-256: 892B9F3CDDA5427DD3965C76B95C1BC952661BAEA993FBBA94D5A3F56FB2EC4C)
2. Frozen KMeans: models/kmeans_customer_segmentation.joblib (SHA-256: A018E41C8DC78BBDEC7C157B71ED66FEAC698336F787B39D84583FAE9CB931B3)
3. Exact Input Contract:
   - recency_delivered_days (1117.0-day imputation for zero-delivered accounts)
   - hist_delivered_order_count
   - hist_delivered_order_value_inr
4. Official Cluster Persona Mapping (K=5):
   - Cluster 0: Champions & High-Value Loyalists
   - Cluster 1: At-Risk / Lapsed Low-Value Customers
   - Cluster 2: Zero Delivered-Purchase Customers
   - Cluster 3: Steady Core Repeaters
   - Cluster 4: Recent Low-Ticket / New Promising Customers
"""

from typing import Dict, Tuple
import numpy as np
import pandas as pd
from backend.app.core.logging import logger
from backend.app.schemas.ml import SegmentationInput, SegmentationResponse
from backend.app.services.model_loader import ModelLoader


class CustomerSegmentationService:
    """
    Dedicated service for assigning customers to official RFM personas using the
    pre-fitted Phase 4 Scaler and K-Means models.
    """

    RFM_FEATURE_COLUMNS = [
        "recency_delivered_days",
        "hist_delivered_order_count",
        "hist_delivered_order_value_inr",
    ]

    # Imputation constant established in Phase 4 (max_recency + 30 days = 1087 + 30 = 1117.0)
    ZERO_DELIVERED_RECENCY_IMPUTATION: float = 1117.0

    OFFICIAL_PERSONAS: Dict[int, Tuple[str, str]] = {
        0: (
            "Champions & High-Value Loyalists",
            "High order count, high spend (AOV ₹1,800+), low returns, low churn propensity.",
        ),
        1: (
            "At-Risk / Lapsed Low-Value Customers",
            "High recency days, single or few historical orders, high churn propensity.",
        ),
        2: (
            "Zero Delivered-Purchase Customers",
            "Zero fulfilled deliveries (never ordered or all orders cancelled/returned).",
        ),
        3: (
            "Steady Core Repeaters",
            "Consistent repeat buyers, moderate ticket size, balanced payment methods.",
        ),
        4: (
            "Recent Low-Ticket / New Promising Customers",
            "Low recency days, lower lifetime order count, highly sensitive to promotional discounts.",
        ),
    }

    @classmethod
    def predict_segment(cls, rfm_input: SegmentationInput) -> SegmentationResponse:
        """
        Assigns customer to one of the 5 official personas using pre-fitted scaler + KMeans.
        Reproduces exact Phase 4 transformation: log1p -> standard scaler -> kmeans.
        """
        scaler = ModelLoader.get_segmentation_scaler()
        kmeans = ModelLoader.get_segmentation_kmeans()

        # Handle zero-delivered recency imputation
        recency = rfm_input.recency_delivered_days
        delivered_count = rfm_input.hist_delivered_order_count
        delivered_value = rfm_input.hist_delivered_order_value_inr

        if recency is None or delivered_count == 0 or np.isnan(recency):
            recency = cls.ZERO_DELIVERED_RECENCY_IMPUTATION

        # Construct DataFrame matching exact feature names passed during fit
        raw_df = pd.DataFrame([{
            "recency_delivered_days": float(recency),
            "hist_delivered_order_count": float(delivered_count),
            "hist_delivered_order_value_inr": float(delivered_value),
        }], columns=cls.RFM_FEATURE_COLUMNS)

        # Apply log(1 + x) transformation as in Phase 4
        log_df = np.log1p(raw_df)

        # Scale using pre-fitted StandardScaler
        scaled_features = scaler.transform(log_df)

        # Predict cluster assignment
        cluster_id = int(kmeans.predict(scaled_features)[0])

        if cluster_id not in cls.OFFICIAL_PERSONAS:
            raise RuntimeError(f"Unexpected cluster ID {cluster_id} outside expected range [0, 4]")

        persona_name, behavioral_profile = cls.OFFICIAL_PERSONAS[cluster_id]

        logger.debug(
            "Segmentation: input=(%.1f, %d, %.2f) -> Cluster %d (%s)",
            recency, delivered_count, delivered_value, cluster_id, persona_name
        )

        return SegmentationResponse(
            cluster_id=cluster_id,
            persona_name=persona_name,
            behavioral_profile=behavioral_profile,
        )
