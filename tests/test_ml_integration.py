"""
Indian E-Commerce Customer Retention Intelligence System
Comprehensive ML Integration & Inference Test Suite (Phase 7.3)

Validates:
1. Model loading, checksum validation, singleton caching, and error safety.
2. 43-feature input contract, probability bounds, class mapping, and threshold boundary.
3. Segmentation RFM contract, zero-delivered imputation (1117.0 days), and 5-persona mapping.
4. Rule-based retention recommendations (categories, reasons, evidence, priorities).
5. All 5 FastAPI ML endpoints under /api/v1.
6. Multi-iteration inference latency and performance benchmark.
"""

import copy
import os
import sys
import time
import numpy as np
import pandas as pd
import pytest
from starlette.testclient import TestClient

# Ensure project root is in sys.path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from backend.app.core.config import settings
from backend.app.main import app
from backend.app.schemas.ml import (
    CustomerAnalysisRequest,
    RawCustomerFeatures,
    SegmentationInput,
)
from backend.app.core.dependencies import get_current_user
from backend.app.schemas.auth import AuthenticatedUser
from backend.app.services.churn_service import ChurnPredictionService
from backend.app.services.customer_analysis_service import CustomerAnalysisService
from backend.app.services.model_loader import ModelLoader, ModelLoadingError
from backend.app.services.retention_service import RetentionRecommendationEngine
from backend.app.services.segmentation_service import CustomerSegmentationService


@pytest.fixture(autouse=True)
def override_auth():
    """Simulates an authenticated employee for ML API integration tests."""
    app.dependency_overrides[get_current_user] = lambda: AuthenticatedUser(
        user_id="test-authorized-ml-analyst-uuid",
        email="ml_analyst@ecommerce.in",
    )
    yield
    app.dependency_overrides.pop(get_current_user, None)


@pytest.fixture(scope="module")
def client():
    """Provides a TestClient instance with startup/shutdown lifespan execution."""
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture(scope="module")
def sample_feature_dict():
    """Provides a genuine 43-feature dictionary extracted from the independent cohort."""
    df = pd.read_csv(os.path.join(PROJECT_ROOT, "data", "independent_test", "processed", "independent_features.csv"))
    cols = ChurnPredictionService.CONFIG_D_FEATURES
    row_dict = df[cols].iloc[0].to_dict()

    # Convert types for JSON compatibility
    int_cols = {
        "has_historical_orders", "has_delivered_order", "hist_order_count",
        "hist_delivered_order_count", "hist_returned_order_count", "hist_cancelled_order_count",
        "orders_last_30_days", "orders_last_90_days", "orders_last_180_days",
        "delivered_orders_last_30_days", "delivered_orders_last_90_days", "delivered_orders_last_180_days",
        "hist_delivery_delay_missing_count", "hist_discounted_order_count", "hist_discount_missing_count",
        "hist_payment_missing_count", "hist_cod_order_count", "hist_upi_order_count",
        "has_orders_last_90_days", "has_orders_last_180_days", "cluster_id",
    }
    cleaned = {}
    for k, v in row_dict.items():
        if pd.isna(v):
            cleaned[k] = None
        elif k in int_cols:
            cleaned[k] = int(v)
        elif isinstance(v, (int, float)):
            cleaned[k] = float(v)
        else:
            cleaned[k] = str(v)
    return cleaned


# ==============================================================================
# SECTION 1: Model Loading & Lifecycle Tests
# ==============================================================================

def test_model_loader_valid_loading():
    """Verify that ModelLoader successfully loads all artifacts with valid checksums."""
    ModelLoader.load_all()
    assert ModelLoader.is_loaded() is True

    rf_pipe = ModelLoader.get_rf_pipeline()
    assert rf_pipe is not None
    assert hasattr(rf_pipe, "predict_proba")

    scaler = ModelLoader.get_segmentation_scaler()
    assert scaler is not None
    assert hasattr(scaler, "transform")

    kmeans = ModelLoader.get_segmentation_kmeans()
    assert kmeans is not None
    assert hasattr(kmeans, "predict")


def test_model_loader_singleton_behavior():
    """Verify that calling load_all multiple times reuses instances without reloading."""
    pipe1 = ModelLoader.get_rf_pipeline()
    ModelLoader.load_all()
    pipe2 = ModelLoader.get_rf_pipeline()
    assert pipe1 is pipe2


def test_model_loader_missing_artifact_error(monkeypatch):
    """Verify that missing model file raises ModelLoadingError."""
    monkeypatch.setattr(settings, "LOCKED_RF_MODEL_PATH", "models/nonexistent_model.joblib")
    ModelLoader.unload_all()
    with pytest.raises(ModelLoadingError, match="Artifact not found"):
        ModelLoader.load_all()
    monkeypatch.undo()
    ModelLoader.unload_all()
    ModelLoader.load_all()  # Restore clean state


def test_model_loader_checksum_mismatch_error(monkeypatch):
    """Verify that artifact tampering or checksum mismatch raises ModelLoadingError."""
    monkeypatch.setattr(settings, "LOCKED_RF_MODEL_SHA256", "0000000000000000000000000000000000000000000000000000000000000000")
    ModelLoader.unload_all()
    with pytest.raises(ModelLoadingError, match="Random Forest model SHA-256 mismatch"):
        ModelLoader.load_all()
    monkeypatch.undo()
    ModelLoader.unload_all()
    ModelLoader.load_all()  # Restore clean state


# ==============================================================================
# SECTION 2: Churn Prediction Service Tests
# ==============================================================================

def test_churn_prediction_contract_and_inference(sample_feature_dict):
    """Verify genuine model inference, probability properties, and threshold boundary."""
    features = RawCustomerFeatures(**sample_feature_dict)
    response = ChurnPredictionService.predict(features)

    # 1. Bounds check
    assert 0.0 <= response.churn_probability <= 1.0
    assert 0.0 <= response.retention_probability <= 1.0

    # 2. Probability sum check
    prob_sum = response.churn_probability + response.retention_probability
    assert abs(prob_sum - 1.0) < 1e-3

    # 3. Threshold boundary check (tau = 0.50)
    assert response.decision_threshold == 0.50
    if response.churn_probability >= 0.50:
        assert response.predicted_class == 1
        assert response.prediction_label == "Churn"
    else:
        assert response.predicted_class == 0
        assert response.prediction_label == "Retained"

    # 4. Risk tier
    if response.churn_probability >= 0.70:
        assert response.risk_tier == "HIGH"
    elif response.churn_probability >= 0.50:
        assert response.risk_tier == "MODERATE"
    else:
        assert response.risk_tier == "LOW"


def test_churn_prediction_with_null_optional_fields(sample_feature_dict):
    """Verify pipeline handles nullable optional features without error."""
    null_features = copy.deepcopy(sample_feature_dict)
    null_features["recency_days"] = None
    null_features["recency_delivered_days"] = None
    null_features["hist_return_rate"] = None
    null_features["hist_cancellation_rate"] = None
    null_features["hist_average_delivery_delay_days"] = None
    null_features["velocity_ratio_30_90"] = None
    null_features["velocity_ratio_90_180"] = None
    null_features["delay_friction_score"] = None

    features = RawCustomerFeatures(**null_features)
    response = ChurnPredictionService.predict(features)
    assert 0.0 <= response.churn_probability <= 1.0


def test_churn_prediction_rejects_extra_fields(sample_feature_dict):
    """Verify RawCustomerFeatures rejects unexpected fields."""
    extra_features = copy.deepcopy(sample_feature_dict)
    extra_features["unexpected_column"] = "malicious_data"
    with pytest.raises(ValueError):
        RawCustomerFeatures(**extra_features)


def test_churn_prediction_rejects_infinite_values(sample_feature_dict):
    """Verify RawCustomerFeatures rejects infinite floats."""
    inf_features = copy.deepcopy(sample_feature_dict)
    inf_features["hist_total_order_value_inr"] = float("inf")
    with pytest.raises(ValueError):
        RawCustomerFeatures(**inf_features)


# ==============================================================================
# SECTION 3: Segmentation Service Tests
# ==============================================================================

def test_segmentation_all_five_personas():
    """Verify that segmentation model maps clusters to official persona descriptions."""
    for cid in range(5):
        assert cid in CustomerSegmentationService.OFFICIAL_PERSONAS
        name, desc = CustomerSegmentationService.OFFICIAL_PERSONAS[cid]
        assert len(name) > 0
        assert len(desc) > 0


def test_segmentation_zero_delivered_imputation():
    """Verify that zero delivered orders trigger 1117.0-day recency imputation and Cluster 2."""
    zero_deliv_input = SegmentationInput(
        recency_delivered_days=None,
        hist_delivered_order_count=0,
        hist_delivered_order_value_inr=0.0,
    )
    result = CustomerSegmentationService.predict_segment(zero_deliv_input)
    assert result.cluster_id == 2
    assert result.persona_name == "Zero Delivered-Purchase Customers"


def test_segmentation_active_customer():
    """Verify segmentation handles active high-frequency purchasing customers."""
    active_input = SegmentationInput(
        recency_delivered_days=15.0,
        hist_delivered_order_count=20,
        hist_delivered_order_value_inr=35000.0,
    )
    result = CustomerSegmentationService.predict_segment(active_input)
    assert result.cluster_id in [0, 3]  # High spend repeater/champion
    assert len(result.persona_name) > 0


# ==============================================================================
# SECTION 4: Retention Recommendation Engine Tests
# ==============================================================================

def test_retention_recommendations_rules(sample_feature_dict):
    """Verify retention engine generates prioritized, evidenced recommendations."""
    features = RawCustomerFeatures(**sample_feature_dict)
    recs = RetentionRecommendationEngine.generate_recommendations(features)
    assert recs.total_recommendations > 0
    assert recs.top_priority in ["HIGH", "MEDIUM", "LOW"]

    for item in recs.recommendations:
        assert len(item.category) > 0
        assert len(item.suggested_action) > 0
        assert len(item.reason) > 0
        assert len(item.evidence) > 0
        assert item.priority in ["HIGH", "MEDIUM", "LOW"]


def test_retention_recommendations_high_delay_friction(sample_feature_dict):
    """Verify high delivery delay friction triggers Delivery Experience intervention."""
    friction_dict = copy.deepcopy(sample_feature_dict)
    friction_dict["hist_average_delivery_delay_days"] = 5.5
    friction_dict["delay_friction_score"] = 2.0
    features = RawCustomerFeatures(**friction_dict)

    recs = RetentionRecommendationEngine.generate_recommendations(features)
    categories = [r.category for r in recs.recommendations]
    assert "Delivery Experience" in categories


# ==============================================================================
# SECTION 5: FastAPI ML Endpoints Tests
# ==============================================================================

def test_api_ml_status(client):
    """Verify GET /api/v1/ml/status returns correct metadata and active loading."""
    response = client.get("/api/v1/ml/status")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["data"]["rf_pipeline_loaded"] is True
    assert data["data"]["rf_model_sha256"] == settings.LOCKED_RF_MODEL_SHA256
    assert data["data"]["decision_threshold"] == 0.50
    assert data["data"]["raw_feature_count"] == 43


def test_api_predict_churn(client, sample_feature_dict):
    """Verify POST /api/v1/predictions/churn returns genuine prediction envelope."""
    response = client.post("/api/v1/predictions/churn", json=sample_feature_dict)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "churn_probability" in data["data"]
    assert "retention_probability" in data["data"]
    assert data["data"]["decision_threshold"] == 0.50


def test_api_predict_segment(client):
    """Verify POST /api/v1/segmentation/predict returns persona mapping."""
    payload = {
        "recency_delivered_days": 45.0,
        "hist_delivered_order_count": 8,
        "hist_delivered_order_value_inr": 12000.0,
    }
    response = client.post("/api/v1/segmentation/predict", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["data"]["cluster_id"] in range(5)
    assert "persona_name" in data["data"]


def test_api_retention_recommendations(client, sample_feature_dict):
    """Verify POST /api/v1/retention/recommendations returns explainable actions."""
    response = client.post("/api/v1/retention/recommendations", json=sample_feature_dict)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["data"]["total_recommendations"] >= 1


def test_api_customers_analyze(client, sample_feature_dict):
    """Verify POST /api/v1/customers/analyze returns end-to-end intelligence envelope."""
    payload = {
        "customer_id": "IND_CUST_TEST_001",
        "features": sample_feature_dict,
    }
    response = client.post("/api/v1/customers/analyze", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["data"]["customer_id"] == "IND_CUST_TEST_001"
    assert "churn_prediction" in data["data"]
    assert "segmentation" in data["data"]
    assert "retention_recommendations" in data["data"]


def test_api_predict_churn_invalid_payload(client):
    """Verify POST /api/v1/predictions/churn returns 422 on incomplete payload."""
    invalid_payload = {"city": "Delhi"}  # Missing 42 required features
    response = client.post("/api/v1/predictions/churn", json=invalid_payload)
    assert response.status_code == 422
    data = response.json()
    assert data["success"] is False
    assert data["error"]["code"] == "REQUEST_VALIDATION_ERROR"


# ==============================================================================
# SECTION 6: Multi-Iteration Performance Benchmark
# ==============================================================================

def test_inference_performance_benchmark(client, sample_feature_dict):
    """
    Measures multi-iteration inference latency across 50 consecutive requests.
    Calculates warm-up time, median latency, and 95th percentile latency.
    """
    iterations = 50
    latencies = []

    # Warm-up request
    t0 = time.perf_counter()
    r_warmup = client.post("/api/v1/predictions/churn", json=sample_feature_dict)
    warmup_time = (time.perf_counter() - t0) * 1000.0
    assert r_warmup.status_code == 200

    for _ in range(iterations):
        t_start = time.perf_counter()
        r = client.post("/api/v1/predictions/churn", json=sample_feature_dict)
        elapsed = (time.perf_counter() - t_start) * 1000.0
        assert r.status_code == 200
        latencies.append(elapsed)

    median_lat = float(np.median(latencies))
    p95_lat = float(np.percentile(latencies, 95))
    min_lat = float(np.min(latencies))
    max_lat = float(np.max(latencies))

    print(f"\n--- Multi-Iteration Latency Benchmark (N={iterations}) ---")
    print(f"Warm-up Latency:     {warmup_time:.2f} ms")
    print(f"Minimum Latency:     {min_lat:.2f} ms")
    print(f"Median Latency:      {median_lat:.2f} ms")
    print(f"95th Pct Latency:    {p95_lat:.2f} ms")
    print(f"Maximum Latency:     {max_lat:.2f} ms")

    # In local testing, median latency should easily be < 50ms
    assert median_lat < 50.0, f"Median latency {median_lat:.2f}ms exceeded 50ms SLA"
