"""
Supervised Remaining Useful Life (RUL) Regression Model using HistGradientBoostingRegressor.
"""

from typing import Any, Dict, List, Optional
import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.preprocessing import StandardScaler


class BaselineMedianRULModel:
    """Simple baseline model predicting the training-set median RUL."""

    def __init__(self):
        self.median_rul_: float = 0.0

    def fit(self, X: pd.DataFrame, y: np.ndarray) -> "BaselineMedianRULModel":
        self.median_rul_ = float(np.median(y)) if len(y) > 0 else 0.0
        return self

    def predict(self, X: pd.DataFrame) -> np.ndarray:
        return np.full(shape=(len(X),), fill_value=self.median_rul_)


class RULRegressionModel:
    """
    Remaining Useful Life (RUL) Predictive Maintenance Regression Model.
    Predicts estimated seconds / operating units remaining before failure.
    """

    def __init__(
        self,
        max_iter: int = 150,
        learning_rate: float = 0.05,
        max_leaf_nodes: int = 31,
        min_samples_leaf: int = 10,
        random_state: int = 42,
    ):
        self.max_iter = max_iter
        self.learning_rate = learning_rate
        self.max_leaf_nodes = max_leaf_nodes
        self.min_samples_leaf = min_samples_leaf
        self.random_state = random_state

        self._model = HistGradientBoostingRegressor(
            max_iter=max_iter,
            learning_rate=learning_rate,
            max_leaf_nodes=max_leaf_nodes,
            min_samples_leaf=min_samples_leaf,
            random_state=random_state,
        )
        self.feature_names: List[str] = []
        self.is_fitted: bool = False

    def fit(self, X: pd.DataFrame, y: np.ndarray) -> "RULRegressionModel":
        """Fits the regression model on training features and targets."""
        self.feature_names = list(X.columns)
        self._model.fit(X.values, y)
        self.is_fitted = True
        return self

    def predict(self, X: pd.DataFrame) -> np.ndarray:
        """Predicts remaining useful life in seconds, clipped to non-negative values."""
        if not self.is_fitted:
            raise RuntimeError("Model is not fitted yet.")

        X_aligned = X[self.feature_names].values
        preds = self._model.predict(X_aligned)
        return np.clip(preds, a_min=0.0, a_max=None)
