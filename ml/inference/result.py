"""
Unified Inference Result Schema for Edge ML Predictions.
"""

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
import uuid
from typing import Any, Dict, Optional

from ml.inference.models import AnomalyLabel, InferenceStatus, LatencyBreakdown, RuntimeBackend


@dataclass
class MLInferenceResult:
    """
    Unified result object produced for each machine telemetry observation.
    Captures anomaly scores, predicted Remaining Useful Life (RUL), model provenance, and latency.
    """
    machine_id: str
    machine_type: str
    event_time: datetime
    inference_time: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    result_id: str = field(default_factory=lambda: str(uuid.uuid4()))

    # Anomaly Output
    anomaly_score: Optional[float] = None       # Calibrated [0.0, 1.0] (1.0 = highly anomalous)
    raw_anomaly_score: Optional[float] = None   # Raw model decision function
    anomaly_label: AnomalyLabel = AnomalyLabel.UNKNOWN

    # RUL Output
    predicted_rul_seconds: Optional[float] = None
    predicted_rul_minutes: Optional[float] = None
    predicted_rul_hours: Optional[float] = None

    # Model Metadata & Provenance
    anomaly_model_name: Optional[str] = None
    anomaly_model_version: Optional[str] = None
    rul_model_name: Optional[str] = None
    rul_model_version: Optional[str] = None
    feature_manifest_version: str = "1.0.0"
    feature_count: int = 1019
    runtime_backend: RuntimeBackend = RuntimeBackend.SKLEARN

    # Lifecycle & Latency
    status: InferenceStatus = InferenceStatus.NOT_READY
    latency: LatencyBreakdown = field(default_factory=LatencyBreakdown)
    error_code: Optional[str] = None
    error_message: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Converts result to a JSON-serializable dictionary."""
        return {
            "result_id": self.result_id,
            "machine_id": self.machine_id,
            "machine_type": self.machine_type,
            "event_time": self.event_time.isoformat() if isinstance(self.event_time, datetime) else (str(self.event_time) if self.event_time else None),
            "inference_time": self.inference_time.isoformat() if isinstance(self.inference_time, datetime) else (str(self.inference_time) if self.inference_time else None),
            "anomaly_score": round(self.anomaly_score, 4) if self.anomaly_score is not None else None,
            "raw_anomaly_score": round(self.raw_anomaly_score, 4) if self.raw_anomaly_score is not None else None,
            "anomaly_label": self.anomaly_label.value,
            "predicted_rul_seconds": round(self.predicted_rul_seconds, 2) if self.predicted_rul_seconds is not None else None,
            "predicted_rul_minutes": round(self.predicted_rul_minutes, 2) if self.predicted_rul_minutes is not None else None,
            "predicted_rul_hours": round(self.predicted_rul_hours, 2) if self.predicted_rul_hours is not None else None,
            "anomaly_model_name": self.anomaly_model_name,
            "anomaly_model_version": self.anomaly_model_version,
            "rul_model_name": self.rul_model_name,
            "rul_model_version": self.rul_model_version,
            "feature_manifest_version": self.feature_manifest_version,
            "feature_count": self.feature_count,
            "runtime_backend": self.runtime_backend.value,
            "status": self.status.value,
            "latency_ms": {
                "feature_generation_ms": round(self.latency.feature_generation_ms, 3),
                "anomaly_inference_ms": round(self.latency.anomaly_inference_ms, 3),
                "rul_inference_ms": round(self.latency.rul_inference_ms, 3),
                "total_inference_ms": round(self.latency.total_inference_ms, 3),
            },
            "error_code": self.error_code,
            "error_message": self.error_message,
        }
