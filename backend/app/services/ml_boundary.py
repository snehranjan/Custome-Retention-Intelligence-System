"""
Indian E-Commerce Customer Retention Intelligence System
ML Service Boundary & Environment Preparation

Prepares the runtime environment and module resolution for Phase 7.3 ML integration.
Ensures custom transformers (Log1pTransformer, CorrelationPruner) in backend/ml
can be unpickled cleanly by Joblib without repeated disk lookups or retraining.
"""

import hashlib
import os
import sys
from typing import Dict, Tuple
from backend.app.core.config import settings
from backend.app.core.logging import logger


class MLServiceBoundary:
    """
    Manages runtime ML path resolution and verifies artifact availability.
    Strictly read-only; does not load weights or perform inference in Phase 7.2.
    """

    _initialized: bool = False
    _artifacts_status: Dict[str, bool] = {}

    @classmethod
    def setup_ml_environment(cls) -> None:
        """
        Registers backend/ml directory in sys.path to enable unpickling of custom
        transformer classes (Log1pTransformer, CorrelationPruner) from advanced_feature_engineering.
        """
        if cls._initialized:
            return

        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
        ml_dir = os.path.join(project_root, "backend", "ml")

        if os.path.isdir(ml_dir) and ml_dir not in sys.path:
            sys.path.insert(0, ml_dir)
            logger.info("Registered ML module path: %s", ml_dir)

        # Pre-import advanced_feature_engineering so classes are registered in sys.modules
        try:
            import advanced_feature_engineering  # noqa: F401
            logger.info("Successfully registered 'advanced_feature_engineering' custom transformers.")
        except ImportError as e:
            logger.warning("Could not pre-import advanced_feature_engineering: %s", e)

        cls._verify_artifact_presence(project_root)
        cls._initialized = True

    @classmethod
    def _verify_artifact_presence(cls, project_root: str) -> None:
        """Verifies existence and checksum invariants of required ML artifacts."""
        artifacts = {
            "locked_rf_model": (settings.LOCKED_RF_MODEL_PATH, settings.LOCKED_RF_MODEL_SHA256),
            "segmentation_scaler": (settings.SEGMENTATION_SCALER_PATH, settings.SEGMENTATION_SCALER_SHA256),
            "segmentation_kmeans": (settings.SEGMENTATION_KMEANS_PATH, settings.SEGMENTATION_KMEANS_SHA256),
        }

        for name, (rel_path, expected_hash) in artifacts.items():
            full_path = os.path.join(project_root, rel_path)
            if not os.path.isfile(full_path):
                logger.warning("ML Artifact missing at: %s", full_path)
                cls._artifacts_status[name] = False
                continue

            try:
                hasher = hashlib.sha256()
                with open(full_path, "rb") as f:
                    for chunk in iter(lambda: f.read(65536), b""):
                        hasher.update(chunk)
                actual_hash = hasher.hexdigest().upper()
                if actual_hash == expected_hash:
                    cls._artifacts_status[name] = True
                    logger.info("ML Artifact verified: %s (SHA-256 match)", name)
                else:
                    logger.error(
                        "ML Artifact checksum mismatch for %s!\nExpected: %s\nActual:   %s",
                        name, expected_hash, actual_hash
                    )
                    cls._artifacts_status[name] = False
            except Exception as e:
                logger.error("Error verifying artifact %s: %s", name, e)
                cls._artifacts_status[name] = False

    @classmethod
    def are_artifacts_ready(cls) -> bool:
        """Returns True if all required ML artifacts exist and match expected checksums."""
        if not cls._initialized:
            cls.setup_ml_environment()
        return len(cls._artifacts_status) > 0 and all(cls._artifacts_status.values())

    @classmethod
    def get_artifact_status(cls) -> Dict[str, bool]:
        if not cls._initialized:
            cls.setup_ml_environment()
        return dict(cls._artifacts_status)
