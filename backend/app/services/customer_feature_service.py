"""
Indian E-Commerce Customer Retention Intelligence System
Customer Feature Retrieval Service (Phase 8.4.8)

Provides in-memory cached lookup of authoritative 43-feature behavioral profiles
for the 7,000 synthetic Indian e-commerce customers.
"""

import os
from typing import Any, Dict, Optional
import pandas as pd

from backend.app.core.logging import logger
from backend.app.schemas.ml import RawCustomerFeatures
from backend.app.services.churn_service import ChurnPredictionService
from backend.ml.advanced_feature_engineering import compute_advanced_features

CLUSTER_PERSONAS = {
    0: "Champions & High-Value Loyalists",
    1: "At-Risk / Lapsed Low-Value Customers",
    2: "Zero Delivered-Purchase Customers",
    3: "Steady Core Repeaters",
    4: "Recent Low-Ticket / New Promising Customers",
}

OPTIONAL_COLS = {
    "recency_days", "recency_delivered_days", "hist_return_rate",
    "hist_cancellation_rate", "hist_average_delivery_delay_days",
    "velocity_ratio_30_90", "velocity_ratio_90_180", "delay_friction_score"
}

INT_COLS = {
    "has_historical_orders", "has_delivered_order", "hist_order_count",
    "hist_delivered_order_count", "hist_returned_order_count", "hist_cancelled_order_count",
    "orders_last_30_days", "orders_last_90_days", "orders_last_180_days",
    "delivered_orders_last_30_days", "delivered_orders_last_90_days", "delivered_orders_last_180_days",
    "hist_delivery_delay_missing_count", "hist_discounted_order_count", "hist_discount_missing_count",
    "hist_payment_missing_count", "hist_cod_order_count", "hist_upi_order_count",
    "has_orders_last_90_days", "has_orders_last_180_days", "missing_friction_score", "cluster_id"
}


class CustomerFeatureService:
    """Singleton cache providing high-performance feature lookup for customers."""

    _features_dict: Optional[Dict[str, Dict[str, Any]]] = None
    _initialized: bool = False

    @classmethod
    def initialize(cls) -> None:
        """Loads and augments feature dataset into fast memory lookup table."""
        if cls._initialized and cls._features_dict is not None:
            return

        feat_path = "data/processed/customer_features.csv"
        seg_path = "data/processed/customer_segments.csv"

        if not os.path.exists(feat_path) or not os.path.exists(seg_path):
            logger.warning("Feature files not found at %s or %s", feat_path, seg_path)
            cls._features_dict = {}
            cls._initialized = True
            return

        logger.info("Initializing CustomerFeatureService cache from %s...", feat_path)
        df_feat = pd.read_csv(feat_path)
        df_seg = pd.read_csv(seg_path)
        df_seg['segment_name'] = df_seg['cluster_id'].map(CLUSTER_PERSONAS)
        df_full = df_feat.merge(df_seg[['customer_id', 'cluster_id', 'segment_name']], on='customer_id')
        df_augmented = compute_advanced_features(df_full)

        features_cache = {}
        for _, row in df_augmented.iterrows():
            cid = str(row['customer_id'])
            row_dict = {}
            for col in ChurnPredictionService.CONFIG_D_FEATURES:
                val = row.get(col)
                if pd.isna(val):
                    row_dict[col] = None if col in OPTIONAL_COLS else (0 if col in INT_COLS else 0.0)
                else:
                    if col in INT_COLS:
                        row_dict[col] = int(val)
                    elif col in ("city", "state"):
                        row_dict[col] = str(val)
                    else:
                        row_dict[col] = float(val)
            features_cache[cid] = row_dict

        cls._features_dict = features_cache
        cls._initialized = True
        logger.info("CustomerFeatureService cached %d customer feature profiles.", len(features_cache))

    @classmethod
    def get_features(cls, customer_id: str) -> Optional[Dict[str, Any]]:
        """Retrieves dictionary of raw and engineered 43 Config D features for a customer."""
        if not cls._initialized:
            cls.initialize()
        return (cls._features_dict or {}).get(str(customer_id).strip())

    @classmethod
    def get_raw_customer_features(cls, customer_id: str) -> Optional[RawCustomerFeatures]:
        """Retrieves strictly typed RawCustomerFeatures model for live model inference."""
        raw = cls.get_features(customer_id)
        if not raw:
            return None
        return RawCustomerFeatures(**raw)
