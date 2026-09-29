"""
Unit and numerical equivalence tests for ONNX runtime export and inference.
"""

from pathlib import Path
import numpy as np
import pytest

from ml.inference.config import InferenceConfig
from ml.inference.models import RuntimeBackend
from ml.inference.model_loader import ModelLoader
from ml.inference.onnx_exporter import ONNXModelExporter
from ml.inference.predictor import RULPredictor


def test_onnx_export_and_numerical_equivalence():
    exporter = ONNXModelExporter()
    report = exporter.export_all()

    assert report["anomaly_export"]["verified"] is True
    assert report["rul_export"]["tolerance_verified"] is True
    assert report["rul_export"]["max_absolute_diff"] < 1e-2


def test_onnx_runtime_predictor():
    cfg = InferenceConfig(runtime_backend=RuntimeBackend.ONNX)
    loader = ModelLoader(cfg)
    bundle = loader.load_rul_bundle(prefer_backend=RuntimeBackend.ONNX)

    assert bundle.runtime_backend == RuntimeBackend.ONNX
    assert bundle.onnx_session is not None

    predictor = RULPredictor(bundle)
    dummy = np.zeros((1, 1019), dtype=np.float32)
    predicted_rul, backend = predictor.predict(dummy)

    assert backend == RuntimeBackend.ONNX
    assert isinstance(predicted_rul, float)
    assert predicted_rul >= 0.0
