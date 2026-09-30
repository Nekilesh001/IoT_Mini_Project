"""
Edge ML Inference Service coordinating model execution, buffering, latency tracking, and resilience.
"""

from datetime import datetime, timezone
import logging
import time
from typing import Any, Dict, List, Optional
import numpy as np

from edge.models import CanonicalTelemetry
from ml.inference.config import InferenceConfig
from ml.inference.feature_pipeline import RealtimeFeaturePipeline
from ml.inference.metrics import InferenceLatencyTracker
from ml.inference.model_loader import ModelLoader
from ml.inference.models import (
    AnomalyLabel,
    InferenceStatus,
    LatencyBreakdown,
    ModelBundle,
    RuntimeBackend,
)
from ml.inference.predictor import AnomalyPredictor, RULPredictor
from ml.inference.result import MLInferenceResult

logger = logging.getLogger(__name__)


class MLInferenceService:
    """
    Production-grade edge inference service.
    Processes live streaming canonical telemetry, extracts physical features,
    and produces real-time anomaly scores and RUL estimates with sub-millisecond tracking.
    """

    def __init__(self, config: Optional[InferenceConfig] = None):
        self.config = config or InferenceConfig()
        self.loader = ModelLoader(self.config)
        self.metrics_tracker = InferenceLatencyTracker(max_samples=self.config.metrics_window_size)
        self.feature_pipeline: Optional[RealtimeFeaturePipeline] = None
        self.anomaly_predictor: Optional[AnomalyPredictor] = None
        self.rul_predictor: Optional[RULPredictor] = None
        self.anomaly_bundle: Optional[ModelBundle] = None
        self.rul_bundle: Optional[ModelBundle] = None
        self._latest_inferences: Dict[str, MLInferenceResult] = {}
        self._is_initialized: bool = False
        self._init_error: Optional[str] = None

        if self.config.enabled:
            self._initialize_service()

    def _initialize_service(self) -> None:
        """Loads models, feature definitions, and builds the inference pipeline."""
        try:
            logger.info("Initializing Edge ML Inference Service...")
            # 1. Load Anomaly Detection Model
            self.anomaly_bundle = self.loader.load_anomaly_bundle()
            self.anomaly_predictor = AnomalyPredictor(self.anomaly_bundle)

            # 2. Load RUL Predictive Maintenance Model
            self.rul_bundle = self.loader.load_rul_bundle()
            self.rul_predictor = RULPredictor(self.rul_bundle)

            # 3. Build Feature Pipeline using anomaly model's verified feature schema
            expected_features = self.anomaly_bundle.feature_names
            self.feature_pipeline = RealtimeFeaturePipeline(
                expected_feature_names=expected_features,
                config=self.config,
            )

            self._is_initialized = True
            logger.info(
                f"Edge ML Inference Service initialized successfully with "
                f"{len(expected_features)} features."
            )

        except Exception as e:
            self._init_error = str(e)
            logger.error(f"Failed to initialize ML Inference Service: {e}", exc_info=True)
            self._is_initialized = False

    @property
    def is_ready(self) -> bool:
        return self._is_initialized and self.feature_pipeline is not None

    def infer(self, telemetry: CanonicalTelemetry) -> MLInferenceResult:
        """
        Executes real-time inference on an incoming canonical telemetry event.
        Guarantees that no exception will escape or crash the host ingestion worker.
        """
        start_total = time.perf_counter()
        m_id = telemetry.machine_id
        m_type = telemetry.machine_type
        ev_time = telemetry.event_time

        result = MLInferenceResult(
            machine_id=m_id,
            machine_type=m_type,
            event_time=ev_time,
            anomaly_model_name=self.anomaly_bundle.model_name if self.anomaly_bundle else self.config.anomaly_model_name,
            anomaly_model_version=self.anomaly_bundle.version if self.anomaly_bundle else self.config.anomaly_model_version,
            rul_model_name=self.rul_bundle.model_name if self.rul_bundle else self.config.rul_model_name,
            rul_model_version=self.rul_bundle.version if self.rul_bundle else self.config.rul_model_version,
            feature_count=self.anomaly_bundle.num_features if self.anomaly_bundle else 1019,
            runtime_backend=self.config.runtime_backend,
        )

        if not self.config.enabled:
            result.status = InferenceStatus.NOT_READY
            result.error_message = "ML Inference subsystem is disabled in configuration"
            return result

        # Explicit exclusion path for external IoT sensors (no industrial ML models applicable)
        if m_type == "ENVIRONMENT_SENSOR" or m_id == "IOT-SENSOR-001" or str(m_id).startswith("IOT-"):
            result.status = InferenceStatus.NOT_READY
            result.error_message = "External IoT device is excluded from industrial predictive maintenance ML"
            return result

        if not self._is_initialized:
            result.status = InferenceStatus.ERROR
            result.error_code = "SERVICE_NOT_INITIALIZED"
            result.error_message = self._init_error or "ML Inference Service failed initialization"
            self._latest_inferences[m_id] = result
            return result

        breakdown = LatencyBreakdown()

        try:
            # 1. Feature Generation & Anti-Leakage Validation
            t_feat_start = time.perf_counter()
            feature_vec, status = self.feature_pipeline.process_telemetry(telemetry)
            breakdown.feature_generation_ms = (time.perf_counter() - t_feat_start) * 1000.0

            if status != InferenceStatus.READY or feature_vec is None:
                result.status = status
                breakdown.total_inference_ms = (time.perf_counter() - start_total) * 1000.0
                result.latency = breakdown
                self._latest_inferences[m_id] = result
                return result

            # 2. Anomaly Detection Inference
            t_anom_start = time.perf_counter()
            anom_score, raw_score, anom_label, anom_backend = self.anomaly_predictor.predict(feature_vec)
            breakdown.anomaly_inference_ms = (time.perf_counter() - t_anom_start) * 1000.0

            result.anomaly_score = anom_score
            result.raw_anomaly_score = raw_score
            result.anomaly_label = anom_label

            # 3. RUL Regression Inference
            t_rul_start = time.perf_counter()
            rul_seconds, rul_backend = self.rul_predictor.predict(feature_vec)
            breakdown.rul_inference_ms = (time.perf_counter() - t_rul_start) * 1000.0

            result.predicted_rul_seconds = rul_seconds
            result.predicted_rul_minutes = round(rul_seconds / 60.0, 2)
            result.predicted_rul_hours = round(rul_seconds / 3600.0, 2)

            # Record active runtime backend used
            result.runtime_backend = anom_backend

            # 4. Finalize Success Status & Total Latency
            result.status = InferenceStatus.READY
            breakdown.total_inference_ms = (time.perf_counter() - start_total) * 1000.0
            result.latency = breakdown

            # Track in-memory metrics
            self.metrics_tracker.record(breakdown, success=True)
            self._latest_inferences[m_id] = result

        except Exception as ex:
            logger.error(f"Inference execution failed for {m_id}: {ex}", exc_info=True)
            result.status = InferenceStatus.ERROR
            result.error_code = "INFERENCE_EXECUTION_ERROR"
            result.error_message = str(ex)
            breakdown.total_inference_ms = (time.perf_counter() - start_total) * 1000.0
            result.latency = breakdown
            self.metrics_tracker.record(breakdown, success=False)
            self._latest_inferences[m_id] = result

        return result

    def get_latest_inference(self, machine_id: str) -> Optional[MLInferenceResult]:
        """Returns the most recent inference result for a machine."""
        return self._latest_inferences.get(machine_id)

    def get_all_latest_inferences(self) -> Dict[str, MLInferenceResult]:
        """Returns a map of latest inferences for all active machines."""
        return dict(self._latest_inferences)

    def get_status(self) -> Dict[str, Any]:
        """Returns overarching health and configuration status of the ML subsystem."""
        return {
            "enabled": self.config.enabled,
            "initialized": self._is_initialized,
            "runtime_backend": self.config.runtime_backend.value,
            "onnx_enabled": self.config.enable_onnx,
            "min_warmup_samples": self.config.min_warmup_samples,
            "anomaly_model": {
                "name": self.config.anomaly_model_name,
                "version": self.config.anomaly_model_version,
                "loaded": self.anomaly_bundle is not None,
            },
            "rul_model": {
                "name": self.config.rul_model_name,
                "version": self.config.rul_model_version,
                "loaded": self.rul_bundle is not None,
            },
            "active_machine_buffers": self.feature_pipeline.buffer.get_all_machine_ids() if self.feature_pipeline else [],
            "metrics": self.metrics_tracker.get_summary(),
        }

    def get_models(self) -> List[Dict[str, Any]]:
        """Returns descriptive catalog of loaded models."""
        models = []
        if self.anomaly_bundle:
            models.append({
                "model_name": self.anomaly_bundle.model_name,
                "model_type": self.anomaly_bundle.model_type.value,
                "version": self.anomaly_bundle.version,
                "num_features": self.anomaly_bundle.num_features,
                "loaded_at": self.anomaly_bundle.loaded_at.isoformat(),
                "runtime_backend": self.anomaly_bundle.runtime_backend.value,
                "hyperparameters": self.anomaly_bundle.metadata.get("hyperparameters", {}),
            })
        if self.rul_bundle:
            models.append({
                "model_name": self.rul_bundle.model_name,
                "model_type": self.rul_bundle.model_type.value,
                "version": self.rul_bundle.version,
                "num_features": self.rul_bundle.num_features,
                "loaded_at": self.rul_bundle.loaded_at.isoformat(),
                "runtime_backend": self.rul_bundle.runtime_backend.value,
                "hyperparameters": self.rul_bundle.metadata.get("hyperparameters", {}),
            })
        return models
