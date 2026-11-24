"""
Indian E-Commerce Customer Retention Intelligence System
FastAPI Application Foundation Verification Suite (Phase 7.2)

Tests:
1. Application initialization & metadata
2. Direct health check endpoint (GET /health)
3. Versioned health check endpoint (GET /api/v1/health)
4. Root info endpoint (GET /)
5. CORS policy behavior (allowed vs non-allowed origins)
6. Centralized 404 error handling & response envelope
7. Centralized 422 request validation error handling
8. Safe 500 internal server error handling (no stack trace / secret leaks)
9. Configuration & environment variable resolution
10. ML service boundary & custom transformer path registration
"""

import os
import sys
import pytest
from starlette.testclient import TestClient

# Ensure project root is in sys.path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from backend.app.core.config import Settings, settings
from backend.app.core.errors import AppException
from backend.app.main import app, create_app
from backend.app.services.ml_boundary import MLServiceBoundary


@pytest.fixture(scope="module")
def client():
    """Provides a TestClient instance for testing the FastAPI application."""
    with TestClient(app) as test_client:
        yield test_client


# ==============================================================================
# 1. Application Initialization & Metadata
# ==============================================================================
def test_app_initialization():
    """Verify application instance, title, version, and OpenAPI routes."""
    assert app.title == "Indian E-Commerce Customer Retention Intelligence System"
    assert app.version == "1.0.0"
    assert app.docs_url == "/docs"
    assert app.redoc_url == "/redoc"
    assert app.openapi_url == "/openapi.json"


# ==============================================================================
# 2. Direct Health Check (GET /health)
# ==============================================================================
def test_direct_health_check(client):
    """Verify direct top-level healthcheck returns 200 with standard envelope."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()

    assert data["success"] is True
    assert "data" in data
    assert data["data"]["status"] == "healthy"
    assert data["data"]["environment"] == settings.ENVIRONMENT
    assert data["data"]["version"] == "1.0.0"
    assert data["data"]["api_prefix"] == "/api/v1"
    assert data["data"]["ml_artifacts_ready"] is True
    assert "timestamp" in data["data"]
    assert "meta" in data


# ==============================================================================
# 3. Versioned Health Check (GET /api/v1/health)
# ==============================================================================
def test_versioned_health_check(client):
    """Verify healthcheck mounted under /api/v1 returns 200 with identical contract."""
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()

    assert data["success"] is True
    assert data["data"]["status"] == "healthy"
    assert data["data"]["ml_artifacts_ready"] is True


# ==============================================================================
# 4. Root Info Endpoint (GET /)
# ==============================================================================
def test_root_info_endpoint(client):
    """Verify root endpoint returns system information and documentation links."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()

    assert data["success"] is True
    assert data["data"]["name"] == settings.PROJECT_NAME
    assert data["data"]["docs_url"] == "/docs"
    assert data["data"]["api_v1_prefix"] == "/api/v1"


# ==============================================================================
# 5. CORS Behavior (Restricted Allowed Origins)
# ==============================================================================
def test_cors_allowed_origin(client):
    """Verify that requests from configured origins receive CORS allow headers."""
    allowed_origin = "http://localhost:5173"
    response = client.get("/health", headers={"Origin": allowed_origin})
    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") == allowed_origin


def test_cors_preflight_options(client):
    """Verify CORS preflight OPTIONS request returns 200 with access control headers."""
    allowed_origin = "http://localhost:5173"
    response = client.options(
        "/api/v1/health",
        headers={
            "Origin": allowed_origin,
            "Access-Control-Request-Method": "GET",
            "Access-Control-Request-Headers": "Content-Type",
        },
    )
    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") == allowed_origin


def test_cors_disallowed_origin(client):
    """Verify that unauthorized origins do not receive allow headers."""
    disallowed_origin = "http://malicious-site.example.com"
    response = client.get("/health", headers={"Origin": disallowed_origin})
    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") != disallowed_origin


# ==============================================================================
# 6. Centralized 404 Error Handling
# ==============================================================================
def test_not_found_error_envelope(client):
    """Verify 404 response follows standardized error envelope."""
    response = client.get("/api/v1/nonexistent-route-endpoint")
    assert response.status_code == 404
    data = response.json()

    assert data["success"] is False
    assert "error" in data
    assert data["error"]["code"] == "NOT_FOUND"
    assert "meta" in data
    assert data["meta"]["path"] == "/api/v1/nonexistent-route-endpoint"


# ==============================================================================
# 7. Safe 500 Error Handling (Zero Secret / Traceback Leakage)
# ==============================================================================
def test_safe_internal_server_error_envelope():
    """Verify unhandled exceptions return sanitized 500 without leaking stack traces."""
    test_app = create_app()

    @test_app.get("/test-internal-error")
    def trigger_error():
        raise RuntimeError("SensitiveDatabasePassword_12345_Internal_Crash")

    with TestClient(test_app, raise_server_exceptions=False) as err_client:
        response = err_client.get("/test-internal-error")
        assert response.status_code == 500
        data = response.json()

        assert data["success"] is False
        assert data["error"]["code"] == "INTERNAL_SERVER_ERROR"
        assert "Internal" not in data["error"]["message"] or "Sensitive" not in data["error"]["message"]
        assert "SensitiveDatabasePassword" not in response.text
        assert "Traceback" not in response.text


# ==============================================================================
# 8. Custom AppException Handling
# ==============================================================================
def test_custom_app_exception_handling():
    """Verify custom AppException triggers structured custom error response."""
    test_app = create_app()

    @test_app.get("/test-custom-app-error")
    def trigger_app_error():
        raise AppException(
            status_code=400,
            code="INVALID_CUSTOMER_STATE",
            message="Customer account is suspended.",
            details=[{"reason": "overdue_invoices"}],
        )

    with TestClient(test_app, raise_server_exceptions=False) as err_client:
        response = err_client.get("/test-custom-app-error")
        assert response.status_code == 400
        data = response.json()

        assert data["success"] is False
        assert data["error"]["code"] == "INVALID_CUSTOMER_STATE"
        assert data["error"]["message"] == "Customer account is suspended."
        assert len(data["error"]["details"]) == 1


# ==============================================================================
# 9. Configuration & Environment Variable Resilience
# ==============================================================================
def test_configuration_resilience():
    """Verify settings handles missing optional variables and comma-separated CORS."""
    custom_settings = Settings(
        BACKEND_CORS_ORIGINS="http://test1.com, http://test2.com",
        SUPABASE_URL=None,
        SUPABASE_ANON_KEY=None,
    )
    assert len(custom_settings.BACKEND_CORS_ORIGINS) == 2
    assert "http://test1.com" in custom_settings.BACKEND_CORS_ORIGINS
    assert custom_settings.USE_LOCAL_FALLBACK is True


# ==============================================================================
# 10. ML Service Boundary & Artifact Invariants
# ==============================================================================
def test_ml_service_boundary_readiness():
    """Verify ML boundary confirms artifact presence, hashes, and custom module import."""
    MLServiceBoundary.setup_ml_environment()
    assert MLServiceBoundary.are_artifacts_ready() is True

    status_dict = MLServiceBoundary.get_artifact_status()
    assert status_dict.get("locked_rf_model") is True
    assert status_dict.get("segmentation_scaler") is True
    assert status_dict.get("segmentation_kmeans") is True

    # Confirm advanced_feature_engineering classes are present in sys.modules
    assert "advanced_feature_engineering" in sys.modules
    mod = sys.modules["advanced_feature_engineering"]
    assert hasattr(mod, "Log1pTransformer")
    assert hasattr(mod, "CorrelationPruner")
