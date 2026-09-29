"""
Anomaly Detection Model Training Pipeline with MLflow tracking and export.
"""

from typing import Any, Dict, Optional, Tuple
import pandas as pd
import numpy as np

from ml.config import MLConfig
from ml.anomaly.model import AnomalyDetectionModel
from ml.anomaly.evaluate import evaluate_anomaly_model


def train_anomaly_pipeline(
    X_train: pd.DataFrame,
    X_val: pd.DataFrame,
    X_test: pd.DataFrame,
    y_val: np.ndarray,
    y_test: np.ndarray,
    config: Optional[MLConfig] = None,
) -> Tuple[AnomalyDetectionModel, Dict[str, Any], Dict[str, Any]]:
    """
    Trains the Isolation Forest anomaly detector on X_train,
    evaluates against validation and test sets, and returns model and metrics.
    """
    cfg = config or MLConfig()

    model = AnomalyDetectionModel(
        n_estimators=cfg.anomaly_n_estimators,
        contamination=cfg.anomaly_contamination,
        random_state=cfg.random_state,
        scale_features=True,
    )

    # Train model
    model.fit(X_train)

    # Evaluate on validation set
    val_preds = model.predict(X_val)
    val_scores = model.score_samples(X_val)
    val_metrics = evaluate_anomaly_model(y_val, val_preds, val_scores)

    # Evaluate on test set
    test_preds = model.predict(X_test)
    test_scores = model.score_samples(X_test)
    test_metrics = evaluate_anomaly_model(y_test, test_preds, test_scores)

    return model, val_metrics, test_metrics
