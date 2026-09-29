"""
Remaining Useful Life (RUL) Training Pipeline.
"""

from typing import Any, Dict, Optional, Tuple
import pandas as pd
import numpy as np

from ml.config import MLConfig
from ml.rul.model import RULRegressionModel, BaselineMedianRULModel
from ml.rul.evaluate import evaluate_rul_model


def train_rul_pipeline(
    X_train: pd.DataFrame,
    X_val: pd.DataFrame,
    X_test: pd.DataFrame,
    y_train: np.ndarray,
    y_val: np.ndarray,
    y_test: np.ndarray,
    config: Optional[MLConfig] = None,
) -> Tuple[RULRegressionModel, BaselineMedianRULModel, Dict[str, Any], Dict[str, Any]]:
    """
    Trains the HistGradientBoosting RUL Regressor and Baseline Median Predictor.
    Evaluates on validation and test sets.
    """
    cfg = config or MLConfig()

    # 1. Baseline Model
    baseline_model = BaselineMedianRULModel()
    baseline_model.fit(X_train, y_train)

    # 2. Main Supervised Model
    model = RULRegressionModel(
        max_iter=cfg.rul_max_iter,
        learning_rate=cfg.rul_learning_rate,
        random_state=cfg.random_state,
    )
    model.fit(X_train, y_train)

    # 3. Evaluate Validation Set
    val_preds = model.predict(X_val)
    val_base_preds = baseline_model.predict(X_val)
    val_metrics = evaluate_rul_model(y_val, val_preds, val_base_preds)

    # 4. Evaluate Test Set
    test_preds = model.predict(X_test)
    test_base_preds = baseline_model.predict(X_test)
    test_metrics = evaluate_rul_model(y_test, test_preds, test_base_preds)

    return model, baseline_model, val_metrics, test_metrics
