"""
Unsupervised Anomaly Detection Model wrapper using Isolation Forest.
"""

from typing import Any, Dict, List, Optional
import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler


class AnomalyDetectionModel:
    """
    Unsupervised Anomaly Detection Model based on scikit-learn Isolation Forest.
    Outputs continuous anomaly scores (higher = more anomalous) and binary flags (1 = anomaly, 0 = normal).
    """

    def __init__(
        self,
        n_estimators: int = 100,
        contamination: float = 0.05,
        random_state: int = 42,
        scale_features: bool = True,
    ):
        self.n_estimators = n_estimators
        self.contamination = contamination
        self.random_state = random_state
        self.scale_features = scale_features
        self._scaler = StandardScaler() if scale_features else None
        self._model = IsolationForest(
            n_estimators=n_estimators,
            contamination=contamination,
            random_state=random_state,
            n_jobs=-1,
        )
        self.feature_names: List[str] = []
        self.is_fitted: bool = False

    def fit(self, X: pd.DataFrame) -> "AnomalyDetectionModel":
        """Fits the Isolation Forest on training feature observations."""
        self.feature_names = list(X.columns)
        X_mat = X.values

        if self._scaler:
            X_mat = self._scaler.fit_transform(X_mat)

        self._model.fit(X_mat)
        self.is_fitted = True
        return self

    def score_samples(self, X: pd.DataFrame) -> np.ndarray:
        """
        Computes anomaly score for observations.
        Higher score indicates higher degree of abnormality.
        In scikit-learn IsolationForest, score_samples returns negative anomaly score (lower is more anomalous).
        We invert it: anomaly_score = -score_samples(X).
        """
        if not self.is_fitted:
            raise RuntimeError("Model is not fitted yet.")

        X_aligned = X[self.feature_names].values
        if self._scaler:
            X_aligned = self._scaler.transform(X_aligned)

        raw_scores = self._model.score_samples(X_aligned)
        return -raw_scores

    def predict(self, X: pd.DataFrame) -> np.ndarray:
        """
        Predicts binary anomaly status: 1 = ANOMALY, 0 = NORMAL.
        scikit-learn IsolationForest returns -1 for anomaly, 1 for normal.
        """
        if not self.is_fitted:
            raise RuntimeError("Model is not fitted yet.")

        X_aligned = X[self.feature_names].values
        if self._scaler:
            X_aligned = self._scaler.transform(X_aligned)

        raw_preds = self._model.predict(X_aligned)
        return np.where(raw_preds == -1, 1, 0)
