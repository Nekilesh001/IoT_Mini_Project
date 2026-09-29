"""
Unit tests for Remaining Useful Life (RUL) models and evaluation metrics.
"""

import numpy as np
import pandas as pd
from ml.rul.model import RULRegressionModel, BaselineMedianRULModel
from ml.rul.evaluate import evaluate_rul_model


def test_rul_regression_model_fit_and_predict():
    """Verify HistGradientBoostingRegressor fits and predicts non-negative RUL."""
    rng = np.random.RandomState(42)
    X = pd.DataFrame(rng.uniform(0, 100, size=(100, 5)), columns=[f"feat_{i}" for i in range(5)])
    # Linear target with noise
    y = np.clip(1000.0 - 5.0 * X["feat_0"].values + rng.normal(0, 10, size=100), 0.0, None)

    baseline = BaselineMedianRULModel()
    baseline.fit(X, y)
    base_preds = baseline.predict(X)
    assert len(base_preds) == 100

    model = RULRegressionModel(max_iter=30, random_state=42)
    model.fit(X, y)
    preds = model.predict(X)

    assert len(preds) == 100
    assert (preds >= 0.0).all()

    metrics = evaluate_rul_model(y, preds, baseline_pred=base_preds)
    assert "mean_absolute_error_seconds" in metrics
    assert "root_mean_squared_error_seconds" in metrics
    assert "r2_score" in metrics
    assert metrics["r2_score"] > 0.5
    assert metrics.get("mae_improvement_pct", 0) > 0
