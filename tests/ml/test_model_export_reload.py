"""
Unit tests for model export, metadata generation, and reloading.
"""

import json
from pathlib import Path
import numpy as np
import pandas as pd
from ml.anomaly.model import AnomalyDetectionModel
from ml.export.model_export import export_model_artifact, load_model_artifact


def test_model_export_and_reload(tmp_path: Path):
    """Verify export_model_artifact serializes model and load_model_artifact accurately reloads it."""
    X = pd.DataFrame({
        "feat_a": [1.0, 2.0, 3.0, 4.0, 5.0],
        "feat_b": [10.0, 20.0, 30.0, 40.0, 50.0],
    })

    model = AnomalyDetectionModel(n_estimators=10, random_state=42)
    model.fit(X)
    orig_preds = model.predict(X)

    bin_path, meta_path = export_model_artifact(
        model=model,
        model_name="test_anomaly",
        model_type="ISOLATION_FOREST",
        version="v1.0.0",
        feature_names=list(X.columns),
        metrics={"precision": 0.95, "recall": 0.90},
        dataset_metadata={"dataset_id": "DS-TEST-01"},
        output_dir=tmp_path,
    )

    assert bin_path.exists()
    assert meta_path.exists()

    with open(meta_path) as f:
        meta = json.load(f)
        assert meta["model_name"] == "test_anomaly"
        assert meta["feature_count"] == 2
        assert meta["metrics"]["precision"] == 0.95

    reloaded = load_model_artifact(bin_path)
    reloaded_preds = reloaded.predict(X)

    np.testing.assert_array_equal(orig_preds, reloaded_preds)
