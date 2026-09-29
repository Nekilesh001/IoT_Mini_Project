"""
Configuration for the Edge ML Inference engine.
"""

from dataclasses import dataclass, field
import os
from pathlib import Path
from typing import List, Optional

from ml.inference.models import RuntimeBackend


@dataclass
class InferenceConfig:
    """
    Configuration parameters for loading models, temporal feature buffering,
    inference execution, and alert thresholds.
    """
    # Base paths
    models_dir: Path = field(default_factory=lambda: Path(os.getenv("ML_MODELS_DIR", "data/models")))

    # Model identifiers
    anomaly_model_name: str = os.getenv("ML_ANOMALY_MODEL_NAME", "anomaly_isolation_forest")
    anomaly_model_version: str = os.getenv("ML_ANOMALY_MODEL_VERSION", "v1.0.0")

    rul_model_name: str = os.getenv("ML_RUL_MODEL_NAME", "rul_gradient_boosting")
    rul_model_version: str = os.getenv("ML_RUL_MODEL_VERSION", "v1.0.0")

    # Feature Buffering & Warmup
    min_warmup_samples: int = int(os.getenv("ML_MIN_WARMUP_SAMPLES", "5"))
    max_buffer_size: int = int(os.getenv("ML_MAX_BUFFER_SIZE", "60"))
    rolling_windows: List[int] = field(default_factory=lambda: [5, 15, 30])

    # Runtime Execution Backend
    runtime_backend: RuntimeBackend = RuntimeBackend(os.getenv("ML_RUNTIME", "SKLEARN").upper())
    enable_onnx: bool = os.getenv("ML_ENABLE_ONNX", "true").lower() in ("true", "1", "yes")

    # Alert Thresholds (Configurable)
    anomaly_alert_threshold: float = float(os.getenv("ML_ANOMALY_THRESHOLD", "0.65"))
    rul_warning_threshold_seconds: float = float(os.getenv("ML_RUL_WARNING_SECONDS", "1800.0"))  # 30 minutes
    rul_critical_threshold_seconds: float = float(os.getenv("ML_RUL_CRITICAL_SECONDS", "600.0")) # 10 minutes

    # Service & Ingestion Switch
    enabled: bool = os.getenv("ML_INFERENCE_ENABLED", "true").lower() in ("true", "1", "yes")
    persist_inferences: bool = os.getenv("ML_PERSIST_INFERENCES", "true").lower() in ("true", "1", "yes")
    metrics_window_size: int = int(os.getenv("ML_METRICS_WINDOW_SIZE", "1000"))

    def get_anomaly_joblib_path(self) -> Path:
        return self.models_dir / f"{self.anomaly_model_name}_{self.anomaly_model_version}.joblib"

    def get_anomaly_metadata_path(self) -> Path:
        return self.models_dir / f"{self.anomaly_model_name}_{self.anomaly_model_version}_metadata.json"

    def get_anomaly_onnx_path(self) -> Path:
        return self.models_dir / f"{self.anomaly_model_name}_{self.anomaly_model_version}.onnx"

    def get_rul_joblib_path(self) -> Path:
        return self.models_dir / f"{self.rul_model_name}_{self.rul_model_version}.joblib"

    def get_rul_metadata_path(self) -> Path:
        return self.models_dir / f"{self.rul_model_name}_{self.rul_model_version}_metadata.json"

    def get_rul_onnx_path(self) -> Path:
        return self.models_dir / f"{self.rul_model_name}_{self.rul_model_version}.onnx"
