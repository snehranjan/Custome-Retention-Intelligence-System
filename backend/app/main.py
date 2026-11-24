"""
Indian E-Commerce Customer Retention Intelligence System
FastAPI Application Entry Point & Factory

Provides:
- Application factory (create_app)
- Lifespan context manager for startup and shutdown
- Safe ML module path registration (MLServiceBoundary)
- Strict CORS middleware restricted to configured origins
- Centralized exception handlers for clean error envelopes without secret leakage
- Versioned routing under /api/v1
- Interactive OpenAPI / Swagger documentation
"""

from contextlib import asynccontextmanager
from typing import AsyncGenerator, Dict, Any
from fastapi import FastAPI, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from starlette.exceptions import HTTPException as StarletteHTTPException

from backend.app.core.config import settings
from backend.app.core.errors import (
    AppException,
    app_exception_handler,
    generic_exception_handler,
    http_exception_handler,
    validation_exception_handler,
)
from backend.app.core.logging import logger, setup_logging
from backend.app.routes import health
from backend.app.routes.api import api_router
from backend.app.schemas.common import ApiResponse
from backend.app.services.ml_boundary import MLServiceBoundary
from backend.app.services.model_loader import ModelLoader


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Application lifespan context manager.
    Executes startup initialization and graceful shutdown tasks.
    """
    # 1. Initialize logging
    setup_logging()
    logger.info("Initializing %s (v%s)...", settings.PROJECT_NAME, settings.VERSION)
    logger.info("Environment: %s | Debug: %s", settings.ENVIRONMENT, settings.DEBUG)

    # 2. Setup ML environment & load production model artifacts (Phase 7.3)
    MLServiceBoundary.setup_ml_environment()
    ModelLoader.load_all()
    logger.info("ML Models Loaded: %s", ModelLoader.is_loaded())

    yield

    # 3. Shutdown cleanup
    ModelLoader.unload_all()
    logger.info("Shutting down %s...", settings.PROJECT_NAME)


def create_app() -> FastAPI:
    """Factory creating and configuring the FastAPI application instance."""
    app = FastAPI(
        title=settings.PROJECT_NAME,
        version=settings.VERSION,
        description=settings.DESCRIPTION,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        lifespan=lifespan,
    )

    # Configure CORS with explicitly restricted origins
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.BACKEND_CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["*"],
    )

    # Register centralized exception handlers
    app.add_exception_handler(AppException, app_exception_handler)
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(Exception, generic_exception_handler)

    # Direct top-level healthcheck endpoint: GET /health
    app.include_router(health.router, prefix="", tags=["System Health"])

    # Versioned API router: /api/v1
    app.include_router(api_router, prefix=settings.API_V1_STR)

    # Root informational endpoint
    @app.get(
        "/",
        response_model=ApiResponse[Dict[str, Any]],
        status_code=status.HTTP_200_OK,
        tags=["System Information"],
        summary="API Root Information",
        description="Returns system metadata, documentation links, and operational status.",
    )
    async def root_info() -> ApiResponse[Dict[str, Any]]:
        return ApiResponse[Dict[str, Any]](
            success=True,
            data={
                "name": settings.PROJECT_NAME,
                "version": settings.VERSION,
                "environment": settings.ENVIRONMENT,
                "docs_url": "/docs",
                "redoc_url": "/redoc",
                "api_v1_prefix": settings.API_V1_STR,
                "health_url": f"{settings.API_V1_STR}/health",
            },
        )

    return app


# Default ASGI application instance for uvicorn
app = create_app()
