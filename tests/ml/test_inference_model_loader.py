"""
Unit tests for ModelLoader and artifact validation.
"""

import pytest
from ml.inference.config import InferenceConfig
from ml.inference.errors import (
    ModelLoadError,
    ModelNotFoundError,
    ModelSchemaMismatchError,
)
from ml.inference.model_loader import ModelLoader
from ml.inference.models import ModelType, RuntimeBackend


def test_load_anomaly_model_bundle_success():
    loader = ModelLoader()
    bundle = loader.load_anomaly_bundle()

    assert bundle.model_name == "anomaly_isolation_forest"
    assert bundle.version == "v1.0.0"
    assert bundle.model_type == ModelType.ISOLATION_FOREST
    assert bundle.num_features == 1019
    assert len(bundle.feature_names) == 1019
    assert bundle.raw_model is not None


def test_load_rul_model_bundle_success():
    loader = ModelLoader()
    bundle = loader.load_rul_bundle()

    assert bundle.model_name == "rul_gradient_boosting"
    assert bundle.version == "v1.0.0"
    assert bundle.model_type == ModelType.HIST_GRADIENT_BOOSTING
    assert bundle.num_features == 1019
    assert len(bundle.feature_names) == 1019
    assert bundle.raw_model is not None


def test_load_nonexistent_model_raises_not_found():
    loader = ModelLoader()
    with pytest.raises(ModelNotFoundError):
        loader.load_bundle(model_name="nonexistent_model", version="v9.9.9")


def test_load_model_type_mismatch_raises_schema_error():
    loader = ModelLoader()
    # Expecting HIST_GRADIENT_BOOSTING but loading ISOLATION_FOREST
    with pytest.raises(ModelSchemaMismatchError):
        loader.load_bundle(
            model_name="anomaly_isolation_forest",
            version="v1.0.0",
            expected_type=ModelType.HIST_GRADIENT_BOOSTING,
        )
