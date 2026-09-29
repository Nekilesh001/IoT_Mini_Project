"""
Domain models and enums for the Edge ML Inference subsystem.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional


class InferenceStatus(str, Enum):
    """Lifecycle / readiness status of an inference operation."""
    NOT_READY = "NOT_READY"      # Insufficient buffer history (warming up)
    READY = "READY"              # Successful inference with full temporal features
    DEGRADED = "DEGRADED"        # Partial features or fallback estimator used
    ERROR = "ERROR"              # Inference failed or schema mismatch


class AnomalyLabel(str, Enum):
    """Classification label output by the Anomaly Detection model."""
    NORMAL = "NORMAL"
    ANOMALOUS = "ANOMALOUS"
    UNKNOWN = "UNKNOWN"


class ModelType(str, Enum):
    """Type of machine learning model."""
    ISOLATION_FOREST = "ISOLATION_FOREST"
    HIST_GRADIENT_BOOSTING = "HIST_GRADIENT_BOOSTING"
    BASELINE_MEDIAN = "BASELINE_MEDIAN"
    UNKNOWN = "UNKNOWN"


class RuntimeBackend(str, Enum):
    """Execution runtime used for model scoring."""
    SKLEARN = "SKLEARN"
    ONNX = "ONNX"


@dataclass
class ModelBundle:
    """
    In-memory loaded model artifact accompanied by its verified metadata.
    """
    model_name: str
    model_type: ModelType
    version: str
    feature_names: List[str]
    num_features: int
    raw_model: Any
    metadata: Dict[str, Any]
    runtime_backend: RuntimeBackend = RuntimeBackend.SKLEARN
    loaded_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    onnx_session: Optional[Any] = None

    def get_feature_names(self) -> List[str]:
        return list(self.feature_names)


@dataclass
class LatencyBreakdown:
    """Microsecond/millisecond latency metrics for an inference pass."""
    feature_generation_ms: float = 0.0
    anomaly_inference_ms: float = 0.0
    rul_inference_ms: float = 0.0
    total_inference_ms: float = 0.0
