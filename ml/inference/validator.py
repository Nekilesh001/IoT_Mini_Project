"""
Feature Schema and Anti-Leakage Validator for Real-Time Inference.
"""

import logging
from typing import List, Sequence
import numpy as np
import pandas as pd

from ml.features.validation import PROHIBITED_LEAKAGE_PATTERNS
from ml.inference.errors import (
    FeatureSchemaMismatchError,
    TargetLeakageError,
)

logger = logging.getLogger(__name__)


class FeatureSchemaValidator:
    """
    Guarantees that runtime feature vectors strictly adhere to the trained schema
    and contain zero prohibited target/ground-truth leakage.
    """

    def __init__(self, expected_feature_names: Sequence[str]):
        self.expected_feature_names: List[str] = list(expected_feature_names)
        self.expected_feature_count: int = len(self.expected_feature_names)
        self._validate_contract()

    def _validate_contract(self) -> None:
        """Validates that the expected feature names themselves are leakage-free."""
        for name in self.expected_feature_names:
            name_lower = name.lower()
            for pattern in PROHIBITED_LEAKAGE_PATTERNS:
                if pattern in name_lower:
                    raise TargetLeakageError(
                        f"Expected feature '{name}' violates anti-leakage policy (matched '{pattern}')"
                    )

    def validate_features(self, df_or_array: Sequence[float], feature_names: Sequence[str]) -> np.ndarray:
        """
        Validates the extracted runtime features against expected schema, order, and validity.
        Returns a validated 2D float32 numpy array ready for model inference.
        """
        actual_names = list(feature_names)

        # 1. Strict anti-leakage check on all incoming actual names
        for name in actual_names:
            name_lower = name.lower()
            for pattern in PROHIBITED_LEAKAGE_PATTERNS:
                if pattern in name_lower:
                    raise TargetLeakageError(
                        f"Prohibited target/ground-truth leakage detected in runtime feature: '{name}'"
                    )

        # 2. Check feature count
        if len(actual_names) != self.expected_feature_count:
            raise FeatureSchemaMismatchError(
                f"Feature count mismatch: expected {self.expected_feature_count}, got {len(actual_names)}"
            )

        # 3. Check feature names and ordering
        if actual_names != self.expected_feature_names:
            diff = set(self.expected_feature_names) ^ set(actual_names)
            if diff:
                raise FeatureSchemaMismatchError(
                    f"Feature names mismatch. Discrepant features: {list(diff)[:5]}"
                )
            else:
                raise FeatureSchemaMismatchError(
                    "Feature ordering mismatch between runtime vector and model contract."
                )

        # 4. Convert and check numerical validity (finiteness)
        if isinstance(df_or_array, pd.DataFrame):
            vec = df_or_array[self.expected_feature_names].to_numpy(dtype=np.float32)
        elif isinstance(df_or_array, np.ndarray):
            vec = df_or_array.astype(np.float32)
            if vec.ndim == 1:
                vec = vec.reshape(1, -1)
        else:
            vec = np.array(df_or_array, dtype=np.float32)
            if vec.ndim == 1:
                vec = vec.reshape(1, -1)

        # Check for NaN / Inf
        if not np.all(np.isfinite(vec)):
            # Cleanly replace NaNs or Infs with 0.0 for robust edge execution
            logger.debug("Non-finite values detected in feature vector; replacing with 0.0")
            vec = np.nan_to_num(vec, nan=0.0, posinf=0.0, neginf=0.0)

        return vec
