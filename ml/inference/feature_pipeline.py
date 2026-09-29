"""
Real-Time Feature Pipeline converting Streaming Telemetry into Model Inputs.
"""

import logging
from typing import List, Optional, Tuple
import numpy as np
import pandas as pd

from edge.models import CanonicalTelemetry
from ml.features.extractor import FeatureExtractor
from ml.inference.config import InferenceConfig
from ml.inference.feature_buffer import TemporalFeatureBuffer
from ml.inference.models import InferenceStatus
from ml.inference.validator import FeatureSchemaValidator

logger = logging.getLogger(__name__)


class RealtimeFeaturePipeline:
    """
    Coordinates temporal telemetry buffering, physical feature extraction,
    and anti-leakage schema validation for real-time inference.
    """

    def __init__(
        self,
        expected_feature_names: List[str],
        config: Optional[InferenceConfig] = None,
    ):
        self.config = config or InferenceConfig()
        self.expected_feature_names = list(expected_feature_names)
        self.buffer = TemporalFeatureBuffer(
            max_buffer_size=self.config.max_buffer_size,
            min_warmup_samples=self.config.min_warmup_samples,
        )
        self.extractor = FeatureExtractor(
            rolling_windows=self.config.rolling_windows,
            include_rolling=True,
            include_rate_of_change=True,
            include_baseline_delta=True,
            fill_missing=True,
        )
        # Pre-prime extractor with expected feature names to guarantee identical column order
        self.extractor._feature_names = list(self.expected_feature_names)
        self.validator = FeatureSchemaValidator(expected_feature_names=self.expected_feature_names)

    def process_telemetry(
        self,
        telemetry: CanonicalTelemetry,
    ) -> Tuple[Optional[np.ndarray], InferenceStatus]:
        """
        Ingests telemetry for a machine and produces a validated 1D/2D feature vector.
        Returns (feature_vector, status).
        """
        # 1. Update temporal buffer
        self.buffer.add_telemetry(telemetry)

        # 2. Check warmup status
        if not self.buffer.is_machine_ready(telemetry.machine_id):
            return None, InferenceStatus.NOT_READY

        # 3. Extract temporal feature DataFrame from buffered history
        df_history = self.buffer.get_machine_dataframe(telemetry.machine_id)
        if df_history.empty:
            return None, InferenceStatus.NOT_READY

        try:
            feat_df, _ = self.extractor.extract_features(df_history, is_training=False)
            if feat_df.empty:
                return None, InferenceStatus.ERROR

            # Take the latest observation row (current event time)
            latest_row = feat_df.iloc[[-1]]

            # 4. Strictly validate against schema and anti-leakage rules
            validated_vec = self.validator.validate_features(
                latest_row,
                feat_df.columns,
            )

            return validated_vec, InferenceStatus.READY

        except Exception as e:
            logger.error(
                f"Feature extraction failed for machine {telemetry.machine_id}: {e}",
                exc_info=True,
            )
            return None, InferenceStatus.ERROR
