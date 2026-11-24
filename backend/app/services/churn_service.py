"""
Indian E-Commerce Customer Retention Intelligence System
Churn Prediction Service (Phase 7.3)

Strict Invariants:
1. Production Random Forest Pipeline: models/phase5_1/final_model/final_churn_rf_pipeline.joblib
2. Exact 43 raw Config D features (40 numerical + 3 categorical).
3. Locked Decision Threshold: tau = 0.50.
4. Dynamic inspection of pipeline.classes_ to identify churn (class 1) vs retention (class 0).
"""

from typing import Any, Dict, List, Tuple
import numpy as np
import pandas as pd
from backend.app.core.config import settings
from backend.app.core.logging import logger
from backend.app.schemas.ml import ChurnPredictionResponse, RawCustomerFeatures
from backend.app.services.model_loader import ModelLoader


class ChurnPredictionService:
    """
    Dedicated service for customer churn probability inference using the locked
    Random Forest Configuration D pipeline.
    """

    # Authoritative 43-feature schema and column order
    CONFIG_D_FEATURES: List[str] = [
        # 40 Numerical Features
        "customer_tenure_days",
        "has_historical_orders",
        "recency_days",
        "recency_delivered_days",
        "has_delivered_order",
        "hist_order_count",
        "hist_delivered_order_count",
        "hist_returned_order_count",
        "hist_cancelled_order_count",
        "hist_total_order_value_inr",
        "hist_delivered_order_value_inr",
        "hist_total_recorded_discount_inr",
        "hist_average_order_value_inr",
        "orders_last_30_days",
        "orders_last_90_days",
        "orders_last_180_days",
        "delivered_orders_last_30_days",
        "delivered_orders_last_90_days",
        "delivered_orders_last_180_days",
        "hist_return_rate",
        "hist_cancellation_rate",
        "hist_average_delivery_delay_days",
        "hist_delivery_delay_missing_count",
        "hist_delivery_delay_missing_rate",
        "hist_average_discount_amount_inr",
        "hist_discounted_order_count",
        "hist_discount_missing_count",
        "hist_discount_missing_rate",
        "hist_payment_missing_count",
        "hist_payment_missing_rate",
        "hist_cod_order_count",
        "hist_cod_usage_rate",
        "hist_upi_order_count",
        "hist_upi_usage_rate",
        "velocity_ratio_30_90",
        "velocity_ratio_90_180",
        "has_orders_last_90_days",
        "has_orders_last_180_days",
        "delay_friction_score",
        "missing_friction_score",
        # 3 Categorical Features
        "city",
        "state",
        "cluster_id",
    ]

    LOCKED_THRESHOLD: float = 0.50

    @classmethod
    def prepare_dataframe(cls, features: RawCustomerFeatures) -> pd.DataFrame:
        """Converts RawCustomerFeatures into a single-row DataFrame with strict column ordering."""
        feature_dict = features.model_dump()
        row_data = {col: [feature_dict[col]] for col in cls.CONFIG_D_FEATURES}
        df = pd.DataFrame(row_data, columns=cls.CONFIG_D_FEATURES)
        return df

    @classmethod
    def predict(cls, features: RawCustomerFeatures) -> ChurnPredictionResponse:
        """
        Executes real model inference using the locked Random Forest pipeline.
        Inspects pipeline.classes_ to extract true class probabilities.
        """
        pipeline = ModelLoader.get_rf_pipeline()
        df = cls.prepare_dataframe(features)

        # Execute genuine model inference
        prob_matrix = pipeline.predict_proba(df)

        # Inspect classes_ to dynamically map class 0 vs class 1
        classes = list(getattr(pipeline, "classes_", [0, 1]))
        if 1 not in classes or 0 not in classes:
            raise RuntimeError(f"Pipeline classes_ {classes} does not contain expected binary labels [0, 1]")

        churn_idx = classes.index(1)
        retention_idx = classes.index(0)

        churn_prob = float(prob_matrix[0, churn_idx])
        retention_prob = float(prob_matrix[0, retention_idx])

        # Apply locked decision boundary (tau = 0.50)
        predicted_class = 1 if churn_prob >= cls.LOCKED_THRESHOLD else 0
        prediction_label = "Churn" if predicted_class == 1 else "Retained"

        # Determine risk tier
        if churn_prob >= 0.70:
            risk_tier = "HIGH"
        elif churn_prob >= cls.LOCKED_THRESHOLD:
            risk_tier = "MODERATE"
        else:
            risk_tier = "LOW"

        logger.debug(
            "Inference: churn_prob=%.4f, retention_prob=%.4f, pred=%d (%s)",
            churn_prob, retention_prob, predicted_class, prediction_label
        )

        return ChurnPredictionResponse(
            churn_probability=round(churn_prob, 4),
            retention_probability=round(retention_prob, 4),
            predicted_class=predicted_class,
            decision_threshold=cls.LOCKED_THRESHOLD,
            prediction_label=prediction_label,
            risk_tier=risk_tier,
        )
