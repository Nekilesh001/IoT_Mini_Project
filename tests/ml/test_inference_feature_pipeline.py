"""
Unit tests for RealtimeFeaturePipeline and feature schema alignment.
"""

from ml.inference.config import InferenceConfig
from ml.inference.feature_pipeline import RealtimeFeaturePipeline
from ml.inference.model_loader import ModelLoader
from ml.inference.models import InferenceStatus
from tests.ml.test_inference_feature_buffer import create_sample_telemetry


def test_feature_pipeline_warmup_and_extraction():
    loader = ModelLoader()
    bundle = loader.load_anomaly_bundle()
    expected_features = bundle.feature_names

    cfg = InferenceConfig(min_warmup_samples=3)
    pipeline = RealtimeFeaturePipeline(expected_feature_names=expected_features, config=cfg)

    # 1. First 2 samples -> NOT_READY
    t1 = create_sample_telemetry("CNC-001", 1, temp=40.0)
    vec1, status1 = pipeline.process_telemetry(t1)
    assert status1 == InferenceStatus.NOT_READY
    assert vec1 is None

    t2 = create_sample_telemetry("CNC-001", 2, temp=41.0)
    vec2, status2 = pipeline.process_telemetry(t2)
    assert status2 == InferenceStatus.NOT_READY
    assert vec2 is None

    # 2. 3rd sample -> READY, produces 2D vector with exact feature count
    t3 = create_sample_telemetry("CNC-001", 3, temp=42.0)
    vec3, status3 = pipeline.process_telemetry(t3)

    assert status3 == InferenceStatus.READY
    assert vec3 is not None
    assert vec3.shape == (1, 1019)
    assert vec3.dtype.name == "float32"
