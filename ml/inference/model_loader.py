"""
Robust Model Loader and Schema Validator for Phase 7 Artifacts.
"""

import json
import logging
from pathlib import Path
from typing import Any, Dict, Optional
import joblib

from ml.inference.config import InferenceConfig
from ml.inference.errors import (
    ModelLoadError,
    ModelNotFoundError,
    ModelSchemaMismatchError,
)
from ml.inference.models import ModelBundle, ModelType, RuntimeBackend

logger = logging.getLogger(__name__)

try:
    import onnxruntime as ort
    HAS_ONNX_RUNTIME = True
except ImportError:
    HAS_ONNX_RUNTIME = False


class ModelLoader:
    """
    Loads, deserializes, and strictly validates machine learning model bundles.
    """

    def __init__(self, config: Optional[InferenceConfig] = None):
        self.config = config or InferenceConfig()

    def load_bundle(
        self,
        model_name: str,
        version: str,
        expected_type: Optional[ModelType] = None,
        prefer_backend: RuntimeBackend = RuntimeBackend.SKLEARN,
    ) -> ModelBundle:
        """
        Loads a single model bundle (binary + metadata JSON + optional ONNX session).
        """
        base_dir = self.config.models_dir
        joblib_path = base_dir / f"{model_name}_{version}.joblib"
        metadata_path = base_dir / f"{model_name}_{version}_metadata.json"
        onnx_path = base_dir / f"{model_name}_{version}.onnx"

        # 1. Verify existence of metadata
        if not metadata_path.exists():
            raise ModelNotFoundError(f"Model metadata JSON not found at {metadata_path}")

        try:
            with open(metadata_path, "r", encoding="utf-8") as f:
                metadata: Dict[str, Any] = json.load(f)
        except Exception as e:
            raise ModelLoadError(f"Failed to parse metadata JSON at {metadata_path}: {e}")

        # 2. Verify existence of joblib binary
        if not joblib_path.exists():
            raise ModelNotFoundError(f"Model artifact binary not found at {joblib_path}")

        try:
            raw_model = joblib.load(joblib_path)
        except Exception as e:
            raise ModelLoadError(f"Failed to deserialize model binary at {joblib_path}: {e}")

        # 3. Validate metadata vs artifact consistency
        meta_name = metadata.get("model_name")
        meta_ver = metadata.get("version")
        if meta_name != model_name:
            raise ModelSchemaMismatchError(
                f"Model name mismatch: expected '{model_name}', found '{meta_name}' in metadata"
            )
        if meta_ver != version:
            raise ModelSchemaMismatchError(
                f"Model version mismatch: expected '{version}', found '{meta_ver}' in metadata"
            )

        feature_names = metadata.get("feature_names", [])
        if not feature_names:
            raise ModelSchemaMismatchError(f"Model metadata at {metadata_path} contains empty feature_names")

        num_features = len(feature_names)
        underlying_model = getattr(raw_model, "_model", raw_model)
        if hasattr(underlying_model, "n_features_in_"):
            if underlying_model.n_features_in_ != num_features:
                raise ModelSchemaMismatchError(
                    f"Feature count mismatch: model expects {underlying_model.n_features_in_}, "
                    f"metadata lists {num_features}"
                )

        # 4. Resolve ModelType
        meta_type_str = metadata.get("model_type", "UNKNOWN")
        try:
            model_type = ModelType(meta_type_str)
        except ValueError:
            model_type = ModelType.UNKNOWN

        if expected_type and model_type != expected_type:
            raise ModelSchemaMismatchError(
                f"Model type mismatch: expected {expected_type}, found {model_type}"
            )

        # 5. Initialize ONNX runtime session if preferred and available
        onnx_session = None
        active_backend = RuntimeBackend.SKLEARN

        if prefer_backend == RuntimeBackend.ONNX and self.config.enable_onnx and HAS_ONNX_RUNTIME:
            if onnx_path.exists():
                try:
                    onnx_session = ort.InferenceSession(str(onnx_path))
                    active_backend = RuntimeBackend.ONNX
                    logger.info(f"Loaded ONNX session for {model_name}_{version} at {onnx_path}")
                except Exception as ex:
                    logger.warning(
                        f"Failed to initialize ONNX session for {onnx_path} ({ex}). Falling back to SKLEARN."
                    )
            else:
                logger.info(
                    f"ONNX artifact not found at {onnx_path}. Using SKLEARN runtime."
                )

        logger.info(
            f"Successfully loaded ModelBundle: {model_name}:{version} "
            f"({model_type.value}) with {num_features} features via {active_backend.value}"
        )

        return ModelBundle(
            model_name=model_name,
            model_type=model_type,
            version=version,
            feature_names=feature_names,
            num_features=num_features,
            raw_model=raw_model,
            metadata=metadata,
            runtime_backend=active_backend,
            onnx_session=onnx_session,
        )

    def load_anomaly_bundle(self, prefer_backend: Optional[RuntimeBackend] = None) -> ModelBundle:
        """Convenience loader for the configured Anomaly Detection model."""
        backend = prefer_backend or self.config.runtime_backend
        return self.load_bundle(
            model_name=self.config.anomaly_model_name,
            version=self.config.anomaly_model_version,
            expected_type=ModelType.ISOLATION_FOREST,
            prefer_backend=backend,
        )

    def load_rul_bundle(self, prefer_backend: Optional[RuntimeBackend] = None) -> ModelBundle:
        """Convenience loader for the configured RUL Regression model."""
        backend = prefer_backend or self.config.runtime_backend
        return self.load_bundle(
            model_name=self.config.rul_model_name,
            version=self.config.rul_model_version,
            expected_type=ModelType.HIST_GRADIENT_BOOSTING,
            prefer_backend=backend,
        )
