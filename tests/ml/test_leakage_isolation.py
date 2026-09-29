"""
Unit tests proving strict ground-truth isolation and zero target leakage.
"""

import pytest
import pandas as pd
import numpy as np

from ml.features.validation import validate_feature_names, filter_leakage_columns
from ml.features.extractor import FeatureExtractor
from ml.schemas import TargetLeakageError


def test_validation_raises_on_prohibited_leakage_patterns():
    """Verify that any column name matching prohibited ground truth patterns triggers TargetLeakageError."""
    prohibited_names = [
        "sim_degradation_pct",
        "target_is_anomaly",
        "target_rul_seconds",
        "hidden_wear_counter",
        "active_conditions_count",
        "degradation_level",
        "scenario_id",
        "is_fault",
        "alert_code_triggered",
    ]
    for name in prohibited_names:
        with pytest.raises(TargetLeakageError):
            validate_feature_names([name])


def test_validation_passes_on_observable_features():
    """Verify that clean observable sensor features pass validation."""
    clean_names = [
        "feat_raw_spindle_temperature_c",
        "feat_spindle_temperature_c_roll_mean_5",
        "feat_spindle_temperature_c_roll_std_15",
        "feat_spindle_temperature_c_diff_1",
        "feat_raw_vibration_rms_mm_s",
        "feat_operating_state_enc",
        "feat_quality_enc",
        "feat_mtype_CNC_MACHINING_CENTER",
    ]
    # Must not raise
    validate_feature_names(clean_names)


def test_filter_leakage_columns():
    """Verify filter_leakage_columns strips prohibited fields while keeping valid signals."""
    cols = [
        "machine_id",
        "event_time",
        "spindle_temperature_c",
        "sim_degradation_pct",
        "target_rul_seconds",
        "hidden_wear_counter",
        "vibration_rms_mm_s",
    ]
    clean = filter_leakage_columns(cols)
    assert "sim_degradation_pct" not in clean
    assert "target_rul_seconds" not in clean
    assert "hidden_wear_counter" not in clean
    assert "spindle_temperature_c" in clean
    assert "vibration_rms_mm_s" in clean


def test_feature_extractor_rejects_ground_truth_inputs():
    """Verify FeatureExtractor strips ground-truth columns and only produces valid observable features."""
    df = pd.DataFrame({
        "machine_id": ["PMP-001", "PMP-001", "PMP-001"],
        "machine_type": ["INDUSTRIAL_PUMP", "INDUSTRIAL_PUMP", "INDUSTRIAL_PUMP"],
        "event_time": pd.date_range("2026-01-01 08:00:00", periods=3, freq="1s"),
        "operating_state": ["RUNNING", "RUNNING", "RUNNING"],
        "quality": ["GOOD", "GOOD", "GOOD"],
        "bearing_temperature_c": [65.0, 65.5, 66.0],
        "vibration_x_mm_s": [1.2, 1.3, 1.4],
        "sim_degradation_pct": [20.0, 30.0, 40.0],  # Ground truth
        "target_is_anomaly": [0, 1, 1],             # Supervision target
        "target_rul_seconds": [3600.0, 3500.0, 3400.0],
    })

    extractor = FeatureExtractor(rolling_windows=[2])
    features, manifest = extractor.extract_features(df, is_training=True)

    # Feature matrix must contain NO target/sim columns
    for col in features.columns:
        assert not col.startswith("sim_")
        assert not col.startswith("target_")
        assert "degradation" not in col
        assert "rul" not in col

    # Must contain physical features
    assert "feat_raw_bearing_temperature_c" in features.columns
    assert "feat_raw_vibration_x_mm_s" in features.columns
