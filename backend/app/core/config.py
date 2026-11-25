"""
Indian E-Commerce Customer Retention Intelligence System
Centralized Application Settings and Configuration Management
"""

import os
from typing import List, Optional, Union
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application Settings loaded from environment variables and .env files.
    All secrets and environment-specific values are strictly externalized.
    """
    model_config = SettingsConfigDict(
        env_file=(".env", "backend/.env"),
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # Project Information
    PROJECT_NAME: str = "Indian E-Commerce Customer Retention Intelligence System"
    VERSION: str = "1.0.0"
    DESCRIPTION: str = (
        "Enterprise-grade Machine Learning backend predicting customer churn, "
        "segmenting purchasing personas, and recommending retention strategies "
        "for Indian e-commerce businesses."
    )
    API_V1_STR: str = "/api/v1"

    # Server Configuration
    ENVIRONMENT: str = "development"
    DEBUG: bool = False
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    LOG_LEVEL: str = "INFO"

    # Security & CORS
    BACKEND_CORS_ORIGINS: List[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "https://retainiq-77c6be.netlify.app",
        "https://retainiq-retention-system.netlify.app",
    ]

    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",") if i.strip()]
        elif isinstance(v, list):
            return v
        return [
            "http://localhost:5173",
            "http://127.0.0.1:5173",
            "http://localhost:3000",
            "http://127.0.0.1:3000",
            "https://retainiq-77c6be.netlify.app",
            "https://retainiq-retention-system.netlify.app",
        ]

    # Database & Supabase Configuration (Phase 7.4)
    STORAGE_MODE: str = "sqlite"
    LOCAL_DATABASE_PATH: str = os.path.join("data", "local_database.db")
    SUPABASE_URL: Optional[str] = "https://hyngxdkuanugcvqhkaas.supabase.co"
    SUPABASE_PUBLISHABLE_KEY: Optional[str] = "sb_publishable_NaJSKZOjztFxbMD_SOY0xA_aqwuEPf1"
    SUPABASE_ANON_KEY: Optional[str] = None
    SUPABASE_SECRET_KEY: Optional[str] = None
    SUPABASE_SERVICE_ROLE_KEY: Optional[str] = None
    SUPABASE_JWKS_URL: Optional[str] = "https://hyngxdkuanugcvqhkaas.supabase.co/auth/v1/.well-known/jwks.json"
    USE_LOCAL_FALLBACK: bool = True

    # Supabase Authentication & JWT Security Settings (Phase 7.5)
    JWT_ALGORITHMS: List[str] = ["ES256"]
    JWT_AUDIENCE: str = "authenticated"
    JWT_LEEWAY_SECONDS: int = 10
    JWKS_CACHE_TTL_SECONDS: int = 600
    SUPABASE_AUTH_ISSUER: Optional[str] = None

    # Server-Controlled Employee Authorization Registry (Phase 8.4.4)
    # Enforces the ADMIN-CONTROLLED EMPLOYEE ACCOUNTS policy (fail-closed by default).
    # Only users explicitly listed here or approved server-side can access employee endpoints.
    AUTHORIZED_EMPLOYEE_EMAILS: List[str] = []
    AUTHORIZED_EMPLOYEE_USER_IDS: List[str] = []

    # Administrator Authorization Registry (Phase 8.4.5)
    # Strictly fail-closed: empty by default; only explicitly configured admin identities are authorized.
    ADMIN_EMAILS: List[str] = []
    ADMIN_USER_IDS: List[str] = []

    @field_validator(
        "AUTHORIZED_EMPLOYEE_EMAILS",
        "AUTHORIZED_EMPLOYEE_USER_IDS",
        "ADMIN_EMAILS",
        "ADMIN_USER_IDS",
        mode="before",
    )
    @classmethod
    def assemble_authorized_lists(cls, v: Union[str, List[str], None]) -> List[str]:
        if v is None:
            return []
        if isinstance(v, str):
            return [i.strip() for i in v.split(",") if i.strip()]
        elif isinstance(v, list):
            return [str(i).strip() for i in v if str(i).strip()]
        return []

    def get_supabase_auth_issuer(self) -> str:
        """Returns the expected Supabase Auth issuer URL."""
        if self.SUPABASE_AUTH_ISSUER:
            return self.SUPABASE_AUTH_ISSUER.rstrip("/")
        base_url = (self.SUPABASE_URL or "https://hyngxdkuanugcvqhkaas.supabase.co").rstrip("/")
        return f"{base_url}/auth/v1"

    def get_supabase_jwks_url(self) -> str:
        """Returns the authoritative JWKS URL for cryptographic signature verification."""
        if self.SUPABASE_JWKS_URL:
            return self.SUPABASE_JWKS_URL
        base_url = (self.SUPABASE_URL or "https://hyngxdkuanugcvqhkaas.supabase.co").rstrip("/")
        return f"{base_url}/auth/v1/.well-known/jwks.json"

    def get_supabase_secret_key(self) -> Optional[str]:
        """Returns the privileged secret key or service role key if configured."""
        return self.SUPABASE_SECRET_KEY or self.SUPABASE_SERVICE_ROLE_KEY

    def get_supabase_publishable_key(self) -> str:
        """Returns the public publishable anon key."""
        return self.SUPABASE_PUBLISHABLE_KEY or self.SUPABASE_ANON_KEY or ""

    def get_supabase_key(self) -> Optional[str]:
        """Returns the active key (preferring secret key for backend operations)."""
        return self.get_supabase_secret_key() or self.get_supabase_publishable_key()

    # Machine Learning Model Artifact Paths (Phase 7.3)
    LOCKED_RF_MODEL_PATH: str = os.path.join(
        "models", "phase5_1", "final_model", "final_churn_rf_pipeline.joblib"
    )
    LOCKED_RF_MODEL_SHA256: str = "24F1F0E33C75B5590906369960DB6E5951EC95DF9AE40384DA60082B3438F301"
    LOCKED_DECISION_THRESHOLD: float = 0.50

    SEGMENTATION_SCALER_PATH: str = os.path.join("models", "segmentation_scaler.joblib")
    SEGMENTATION_SCALER_SHA256: str = "892B9F3CDDA5427DD3965C76B95C1BC952661BAEA993FBBA94D5A3F56FB2EC4C"

    SEGMENTATION_KMEANS_PATH: str = os.path.join("models", "kmeans_customer_segmentation.joblib")
    SEGMENTATION_KMEANS_SHA256: str = "A018E41C8DC78BBDEC7C157B71ED66FEAC698336F787B39D84583FAE9CB931B3"

    # Data Source Fallback Paths
    LOCAL_CUSTOMERS_PATH: str = os.path.join("data", "processed", "customer_features.csv")
    LOCAL_ORDERS_PATH: str = os.path.join("data", "raw", "orders.csv")


# Central singleton instance
settings = Settings()
