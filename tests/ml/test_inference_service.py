"""
Integration tests for MLInferenceService end-to-end telemetry execution.
"""

from ml.inference.config import InferenceConfig
from ml.inference.models import InferenceStatus
from ml.inference.service import MLInferenceService
from tests.ml.test_inference_feature_buffer import create_sample_telemetry


def test_ml_inference_service_lifecycle():
    cfg = InferenceConfig(min_warmup_samples=3)
    service = MLInferenceService(cfg)
    assert service.is_ready

    # Telemetry before warmup -> NOT_READY
    t1 = create_sample_telemetry("CNC-001", 1, temp=40.0)
    res1 = service.infer(t1)
    assert res1.status == InferenceStatus.NOT_READY
    assert res1.anomaly_score is None

    t2 = create_sample_telemetry("CNC-001", 2, temp=42.0)
    res2 = service.infer(t2)
    assert res2.status == InferenceStatus.NOT_READY

    # 3rd observation -> READY with predictions
    t3 = create_sample_telemetry("CNC-001", 3, temp=45.0)
    res3 = service.infer(t3)
    assert res3.status == InferenceStatus.READY
    assert res3.anomaly_score is not None
    assert 0.0 <= res3.anomaly_score <= 1.0
    assert res3.predicted_rul_seconds is not None
    assert res3.latency.total_inference_ms > 0.0

    # Verify latest inference lookup
    latest = service.get_latest_inference("CNC-001")
    assert latest is not None
    assert latest.result_id == res3.result_id

    # Verify metrics summary
    metrics = service.metrics_tracker.get_summary()
    assert metrics["successful_inferences"] >= 1
