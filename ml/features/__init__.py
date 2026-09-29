"""
Feature engineering and leakage validation package.
"""

from ml.features.extractor import FeatureExtractor
from ml.features.validation import validate_feature_names, filter_leakage_columns
from ml.features.machine_features import (
    OBSERVABLE_SIGNALS_BY_MACHINE_TYPE,
    OPERATING_STATE_ENCODING,
    QUALITY_ENCODING,
)
from ml.features.rolling import (
    compute_rolling_features,
    compute_rate_of_change,
    compute_baseline_delta,
)

__all__ = [
    "FeatureExtractor",
    "validate_feature_names",
    "filter_leakage_columns",
    "OBSERVABLE_SIGNALS_BY_MACHINE_TYPE",
    "OPERATING_STATE_ENCODING",
    "QUALITY_ENCODING",
    "compute_rolling_features",
    "compute_rate_of_change",
    "compute_baseline_delta",
]
