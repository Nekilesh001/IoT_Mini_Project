"""
Unit tests for Anomaly Detection Model and evaluation metrics.
"""

import numpy as np
import pandas as pd
from ml.anomaly.model import AnomalyDetectionModel
from ml.anomaly.evaluate import evaluate_anomaly_model


def test_anomaly_detection_model_fit_and_predict():
    """Verify Isolation Forest model fits on features and predicts binary anomaly status."""
    rng = np.random.RandomState(42)
    # Generate 100 normal points and 10 outliers
    normal_data = rng.normal(loc=0.0, scale=1.0, size=(100, 4))
    anomaly_data = rng.normal(loc=10.0, scale=2.0, size=(10, 4))

    X_train = pd.DataFrame(normal_data, columns=[f"feat_{i}" for i in range(4)])
    X_test = pd.DataFrame(np.vstack([normal_data[:20], anomaly_data]), columns=[f"feat_{i}" for i in range(4)])
    y_test = np.array([0] * 20 + [1] * 10)

    model = AnomalyDetectionModel(n_estimators=50, contamination=0.1, random_state=42)
    model.fit(X_train)

    preds = model.predict(X_test)
    scores = model.score_samples(X_test)

    assert len(preds) == 30
    assert set(np.unique(preds)).issubset({0, 1})
    assert len(scores) == 30

    metrics = evaluate_anomaly_model(y_test, preds, scores)
    assert "f1_score" in metrics
    assert "precision" in metrics
    assert "recall" in metrics
    assert metrics["total_samples"] == 30
    assert metrics["ground_truth_anomalies"] == 10
