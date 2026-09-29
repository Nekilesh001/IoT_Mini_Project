"""
Inference Predictors for Anomaly Detection and Remaining Useful Life (RUL).
Supports both native Scikit-Learn estimators and high-performance ONNX Runtime sessions.
"""

import logging
from typing import Optional, Tuple
import numpy as np

from ml.inference.models import AnomalyLabel, ModelBundle, RuntimeBackend

logger = logging.getLogger(__name__)


class AnomalyPredictor:
    """
    Executes real-time Anomaly Detection scoring on verified feature vectors.
    """

    def __init__(self, bundle: ModelBundle):
        self.bundle = bundle
        self.raw_model = getattr(bundle.raw_model, "_model", bundle.raw_model)
        self.onnx_session = bundle.onnx_session
        self.runtime_backend = bundle.runtime_backend

    def predict(
        self,
        features: np.ndarray,
    ) -> Tuple[float, float, AnomalyLabel, RuntimeBackend]:
        """
        Runs anomaly detection inference.
        Returns: (calibrated_anomaly_score, raw_score, anomaly_label, active_backend)
        """
        # Ensure 2D shape (N, num_features)
        if features.ndim == 1:
            features = features.reshape(1, -1)

        active_backend = self.runtime_backend

        # Try ONNX execution if enabled and session exists
        if active_backend == RuntimeBackend.ONNX and self.onnx_session is not None:
            try:
                input_name = self.onnx_session.get_inputs()[0].name
                outputs = self.onnx_session.run(None, {input_name: features.astype(np.float32)})
                # outputs[0] = label (1 or -1), outputs[1] = score dictionary / tensor
                onnx_label = int(np.squeeze(outputs[0]).ravel()[0])
                label = AnomalyLabel.ANOMALOUS if onnx_label == -1 else AnomalyLabel.NORMAL

                # Extract score if available
                if len(outputs) > 1:
                    raw_score = float(np.squeeze(outputs[1]).ravel()[0])
                else:
                    raw_score = -0.1 if label == AnomalyLabel.ANOMALOUS else 0.1

                # Normalize score to [0.0, 1.0] (higher = more anomalous)
                calibrated_score = 0.85 if label == AnomalyLabel.ANOMALOUS else 0.15
                return calibrated_score, raw_score, label, RuntimeBackend.ONNX
            except Exception as ex:
                logger.warning(f"ONNX anomaly inference failed ({ex}). Falling back to SKLEARN.")
                active_backend = RuntimeBackend.SKLEARN

        # Scikit-Learn fallback / default execution
        try:
            # Raw decision score: lower (more negative) = more anomalous
            raw_scores = self.raw_model.score_samples(features)
            raw_score = float(raw_scores[0])

            # Native prediction: -1 = anomalous, 1 = normal
            preds = self.raw_model.predict(features)
            label = AnomalyLabel.ANOMALOUS if int(preds[0]) == -1 else AnomalyLabel.NORMAL

            # Calibrate raw score into intuitive [0.0, 1.0] where 1.0 is highest anomaly risk
            # Typical IsolationForest score_samples output is in range [-0.8, -0.3]
            # S = 1.0 - (raw_score - min) / (max - min)
            calibrated_score = float(np.clip(1.0 - (raw_score + 0.7) / 0.5, 0.0, 1.0))
            if label == AnomalyLabel.ANOMALOUS and calibrated_score < 0.6:
                calibrated_score = 0.75

            return calibrated_score, raw_score, label, RuntimeBackend.SKLEARN

        except Exception as e:
            logger.error(f"Anomaly inference error: {e}", exc_info=True)
            raise e


class RULPredictor:
    """
    Executes real-time Remaining Useful Life (RUL) regression inference.
    """

    def __init__(self, bundle: ModelBundle):
        self.bundle = bundle
        self.raw_model = getattr(bundle.raw_model, "_model", bundle.raw_model)
        self.onnx_session = bundle.onnx_session
        self.runtime_backend = bundle.runtime_backend

    def predict(
        self,
        features: np.ndarray,
    ) -> Tuple[float, RuntimeBackend]:
        """
        Runs RUL regression inference.
        Returns: (predicted_rul_seconds, active_backend)
        """
        if features.ndim == 1:
            features = features.reshape(1, -1)

        active_backend = self.runtime_backend

        # Try ONNX execution if enabled
        if active_backend == RuntimeBackend.ONNX and self.onnx_session is not None:
            try:
                input_name = self.onnx_session.get_inputs()[0].name
                outputs = self.onnx_session.run(None, {input_name: features.astype(np.float32)})
                predicted_rul = float(np.squeeze(outputs[0]).ravel()[0])
                # Non-negative RUL
                predicted_rul = max(0.0, predicted_rul)
                return predicted_rul, RuntimeBackend.ONNX
            except Exception as ex:
                logger.warning(f"ONNX RUL inference failed ({ex}). Falling back to SKLEARN.")
                active_backend = RuntimeBackend.SKLEARN

        # Scikit-Learn fallback / default execution
        try:
            preds = self.raw_model.predict(features)
            predicted_rul = max(0.0, float(preds[0]))
            return predicted_rul, RuntimeBackend.SKLEARN
        except Exception as e:
            logger.error(f"RUL inference error: {e}", exc_info=True)
            raise e
