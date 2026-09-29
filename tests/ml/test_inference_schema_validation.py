"""
Unit tests for FeatureSchemaValidator and Anti-Leakage policy.
"""

import numpy as np
import pytest

from ml.inference.errors import (
    FeatureSchemaMismatchError,
    TargetLeakageError,
)
from ml.inference.validator import FeatureSchemaValidator


def test_schema_validator_valid_features():
    expected = ["feat_1", "feat_2", "feat_3"]
    validator = FeatureSchemaValidator(expected_feature_names=expected)

    arr = np.array([1.0, 2.0, 3.0], dtype=np.float32)
    validated = validator.validate_features(arr, ["feat_1", "feat_2", "feat_3"])

    assert validated.shape == (1, 3)
    assert np.allclose(validated[0], [1.0, 2.0, 3.0])


def test_schema_validator_count_mismatch_raises_error():
    expected = ["feat_1", "feat_2", "feat_3"]
    validator = FeatureSchemaValidator(expected_feature_names=expected)

    arr = np.array([1.0, 2.0], dtype=np.float32)
    with pytest.raises(FeatureSchemaMismatchError):
        validator.validate_features(arr, ["feat_1", "feat_2"])


def test_schema_validator_target_leakage_in_features_raises_error():
    expected = ["feat_temperature", "feat_vibration", "feat_speed"]
    validator = FeatureSchemaValidator(expected_feature_names=expected)

    with pytest.raises(TargetLeakageError):
        # Passing a prohibited target column name
        validator.validate_features(
            [1.0, 2.0, 3.0],
            ["feat_temperature", "target_is_anomaly", "feat_speed"]
        )
