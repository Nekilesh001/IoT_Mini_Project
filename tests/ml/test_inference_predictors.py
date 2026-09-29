"""
Unit tests for AnomalyPredictor and RULPredictor.
"""

import numpy as np
from ml.inference.model_loader import ModelLoader
from ml.inference.models import AnomalyLabel
from ml.inference.predictor import AnomalyPredictor, RULPredictor


def test_anomaly_predictor_execution():
    loader = ModelLoader()
    bundle = loader.load_anomaly_bundle()
    predictor = AnomalyPredictor(bundle)

    dummy_features = np.zeros((1, 1019), dtype=np.float32)
    score, raw_score, label, backend = predictor.predict(dummy_features)

    assert 0.0 <= score <= 1.0
    assert isinstance(raw_score, float)
    assert label in (AnomalyLabel.NORMAL, AnomalyLabel.ANOMALOUS)


def test_rul_predictor_execution():
    loader = ModelLoader()
    bundle = loader.load_rul_bundle()
    predictor = RULPredictor(bundle)

    dummy_features = np.zeros((1, 1019), dtype=np.float32)
    predicted_rul, backend = predictor.predict(dummy_features)

    assert isinstance(predicted_rul, float)
    assert predicted_rul >= 0.0
