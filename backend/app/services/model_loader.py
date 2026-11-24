"""
Indian E-Commerce Customer Retention Intelligence System
Model Loading and Lifecycle Service (Phase 7.3)

Strict Invariants:
1. Random Forest Pipeline SHA-256: 24F1F0E33C75B5590906369960DB6E5951EC95DF9AE40384DA60082B3438F301
2. Segmentation Scaler SHA-256:     892B9F3CDDA5427DD3965C76B95C1BC952661BAEA993FBBA94D5A3F56FB2EC4C
3. Segmentation KMeans SHA-256:     A018E41C8DC78BBDEC7C157B71ED66FEAC698336F787B39D84583FAE9CB931B3

Loads models once during application startup, validates checksums, and caches singletons.
"""

import hashlib
import os
import sys
from typing import Any, Dict, Optional
import joblib
from backend.app.core.config import settings
from backend.app.core.logging import logger


class ModelLoadingError(RuntimeError):
    """Raised when model loading fails due to missing files, checksum mismatch, or unpickling errors."""
    pass


class ModelLoader:
    """
    Singleton service managing model loading, cryptographic integrity verification,
    and runtime artifact lifecycle.
    """

    _rf_pipeline: Optional[Any] = None
    _segmentation_scaler: Optional[Any] = None
    _segmentation_kmeans: Optional[Any] = None
    _initialized: bool = False
    _load_metadata: Dict[str, Any] = {}

    @classmethod
    def _compute_sha256(cls, file_path: str) -> str:
        """Computes SHA-256 checksum of an artifact on disk."""
        if not os.path.isfile(file_path):
            raise ModelLoadingError(f"Artifact not found at path: {file_path}")
        hasher = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(65536), b""):
                hasher.update(chunk)
        return hasher.hexdigest().upper()

    @classmethod
    def setup_python_path(cls) -> None:
        """Ensures backend/ml is registered in sys.path and advanced_feature_engineering is imported."""
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
        ml_dir = os.path.join(project_root, "backend", "ml")

        if os.path.isdir(ml_dir) and ml_dir not in sys.path:
            sys.path.insert(0, ml_dir)
            logger.info("Registered ML module path: %s", ml_dir)

        try:
            import advanced_feature_engineering  # noqa: F401
            logger.info("Pre-imported 'advanced_feature_engineering' custom transformer classes.")
        except ImportError as e:
            raise ModelLoadingError(
                f"Failed to import 'advanced_feature_engineering' for model deserialization: {e}"
            ) from e

    @classmethod
    def load_all(cls, project_root: Optional[str] = None) -> None:
        """
        Loads and cryptographically verifies all production ML artifacts once.
        Fails fast if any artifact is missing, altered, or corrupt.
        """
        if cls._initialized and cls._rf_pipeline is not None:
            logger.info("ModelLoader already initialized; reusing existing instances.")
            return

        if project_root is None:
            project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))

        # 1. Setup Python path for Joblib unpickling
        cls.setup_python_path()

        # 2. Verify and Load Random Forest Churn Pipeline
        rf_path = os.path.join(project_root, settings.LOCKED_RF_MODEL_PATH)
        actual_rf_hash = cls._compute_sha256(rf_path)
        if actual_rf_hash != settings.LOCKED_RF_MODEL_SHA256:
            raise ModelLoadingError(
                f"Random Forest model SHA-256 mismatch!\n"
                f"Expected: {settings.LOCKED_RF_MODEL_SHA256}\n"
                f"Actual:   {actual_rf_hash}\n"
                f"Model artifact at {rf_path} has been tampered with or replaced!"
            )

        try:
            logger.info("Loading production Random Forest pipeline from: %s", rf_path)
            cls._rf_pipeline = joblib.load(rf_path)
            logger.info("Random Forest pipeline successfully loaded into memory.")
        except Exception as e:
            raise ModelLoadingError(f"Failed to deserialize Random Forest pipeline: {e}") from e

        # 3. Verify and Load Segmentation Scaler
        scaler_path = os.path.join(project_root, settings.SEGMENTATION_SCALER_PATH)
        actual_scaler_hash = cls._compute_sha256(scaler_path)
        if actual_scaler_hash != settings.SEGMENTATION_SCALER_SHA256:
            raise ModelLoadingError(
                f"Segmentation scaler SHA-256 mismatch!\n"
                f"Expected: {settings.SEGMENTATION_SCALER_SHA256}\n"
                f"Actual:   {actual_scaler_hash}"
            )

        try:
            logger.info("Loading segmentation scaler from: %s", scaler_path)
            cls._segmentation_scaler = joblib.load(scaler_path)
            logger.info("Segmentation scaler successfully loaded.")
        except Exception as e:
            raise ModelLoadingError(f"Failed to deserialize segmentation scaler: {e}") from e

        # 4. Verify and Load Segmentation KMeans Model
        kmeans_path = os.path.join(project_root, settings.SEGMENTATION_KMEANS_PATH)
        actual_kmeans_hash = cls._compute_sha256(kmeans_path)
        if actual_kmeans_hash != settings.SEGMENTATION_KMEANS_SHA256:
            raise ModelLoadingError(
                f"Segmentation KMeans SHA-256 mismatch!\n"
                f"Expected: {settings.SEGMENTATION_KMEANS_SHA256}\n"
                f"Actual:   {actual_kmeans_hash}"
            )

        try:
            logger.info("Loading segmentation KMeans model from: %s", kmeans_path)
            cls._segmentation_kmeans = joblib.load(kmeans_path)
            logger.info("Segmentation KMeans model successfully loaded.")
        except Exception as e:
            raise ModelLoadingError(f"Failed to deserialize segmentation KMeans model: {e}") from e

        cls._initialized = True
        cls._load_metadata = {
            "rf_model_sha256": actual_rf_hash,
            "rf_model_path": rf_path,
            "decision_threshold": settings.LOCKED_DECISION_THRESHOLD,
            "scaler_sha256": actual_scaler_hash,
            "kmeans_sha256": actual_kmeans_hash,
        }
        logger.info("All ML artifacts verified and ready for inference.")

    @classmethod
    def get_rf_pipeline(cls) -> Any:
        """Returns the loaded, verified Random Forest pipeline."""
        if not cls._initialized or cls._rf_pipeline is None:
            cls.load_all()
        return cls._rf_pipeline

    @classmethod
    def get_segmentation_scaler(cls) -> Any:
        """Returns the loaded, verified segmentation scaler."""
        if not cls._initialized or cls._segmentation_scaler is None:
            cls.load_all()
        return cls._segmentation_scaler

    @classmethod
    def get_segmentation_kmeans(cls) -> Any:
        """Returns the loaded, verified segmentation KMeans model."""
        if not cls._initialized or cls._segmentation_kmeans is None:
            cls.load_all()
        return cls._segmentation_kmeans

    @classmethod
    def is_loaded(cls) -> bool:
        """Returns True if all models are loaded in memory."""
        return (
            cls._initialized
            and cls._rf_pipeline is not None
            and cls._segmentation_scaler is not None
            and cls._segmentation_kmeans is not None
        )

    @classmethod
    def get_status(cls) -> Dict[str, Any]:
        """Returns status metadata regarding model loading and artifact verification."""
        return {
            "is_loaded": cls.is_loaded(),
            "metadata": cls._load_metadata,
        }

    @classmethod
    def unload_all(cls) -> None:
        """Clean shutdown lifecycle: frees references to model instances."""
        logger.info("Unloading ML models from memory...")
        cls._rf_pipeline = None
        cls._segmentation_scaler = None
        cls._segmentation_kmeans = None
        cls._initialized = False
        cls._load_metadata = {}
        logger.info("ML models unloaded successfully.")
