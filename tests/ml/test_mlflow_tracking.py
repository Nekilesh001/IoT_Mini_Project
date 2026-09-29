"""
Unit tests for local MLflow tracking.
"""

from pathlib import Path
from ml.tracking.mlflow_utils import MLflowTracker


def test_mlflow_local_tracking(tmp_path: Path):
    """Verify local MLflow tracker logs experiment runs, metrics, and parameters."""
    tracking_uri = f"file:{tmp_path / 'mlruns'}"
    tracker = MLflowTracker(tracking_uri=tracking_uri, experiment_name="Test-Experiment")

    run_id = tracker.log_run(
        run_name="unit_test_run",
        parameters={"learning_rate": 0.05, "n_estimators": 100},
        metrics={"f1_score": 0.92, "mae": 12.4},
        tags={"env": "test"},
    )

    assert isinstance(run_id, str)
    assert len(run_id) > 0
