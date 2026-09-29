"""
Unit tests for FeatureExtractor temporal transformations and backward causality.
"""

import pandas as pd
import numpy as np
from ml.features.extractor import FeatureExtractor


def test_feature_extractor_causality():
    """Verify that feature calculation at time T is independent of any future observations at T+1."""
    dates = pd.date_range("2026-01-01 00:00:00", periods=10, freq="1s")
    df_base = pd.DataFrame({
        "machine_id": ["PMP-001"] * 10,
        "machine_type": ["INDUSTRIAL_PUMP"] * 10,
        "event_time": dates,
        "operating_state": ["RUNNING"] * 10,
        "quality": ["GOOD"] * 10,
        "bearing_temperature_c": [50.0, 51.0, 52.0, 53.0, 54.0, 55.0, 56.0, 57.0, 58.0, 59.0],
    })

    # Mutate the future (rows 6 to 9) in an alternative dataframe
    df_future_spike = df_base.copy()
    df_future_spike.loc[6:, "bearing_temperature_c"] = [100.0, 150.0, 200.0, 250.0]

    extractor = FeatureExtractor(rolling_windows=[3])
    feats_base, _ = extractor.extract_features(df_base, is_training=True)
    feats_spike, _ = extractor.extract_features(df_future_spike, is_training=False)

    # Features at indices 0 through 5 must be 100% IDENTICAL
    pd.testing.assert_frame_equal(feats_base.iloc[:6], feats_spike.iloc[:6])


def test_feature_extractor_rolling_and_onehot():
    """Verify rolling statistics and machine type one-hot columns are correctly generated."""
    df = pd.DataFrame({
        "machine_id": ["PMP-001", "PMP-001"],
        "machine_type": ["INDUSTRIAL_PUMP", "INDUSTRIAL_PUMP"],
        "event_time": pd.date_range("2026-01-01 00:00:00", periods=2, freq="1s"),
        "operating_state": ["RUNNING", "RUNNING"],
        "quality": ["GOOD", "GOOD"],
        "bearing_temperature_c": [50.0, 60.0],
    })

    extractor = FeatureExtractor(rolling_windows=[2])
    feats, manifest = extractor.extract_features(df, is_training=True)

    assert "feat_raw_bearing_temperature_c" in feats.columns
    assert "feat_bearing_temperature_c_roll_mean_2" in feats.columns
    assert "feat_mtype_INDUSTRIAL_PUMP" in feats.columns

    # Check roll mean at second observation: (50 + 60) / 2 = 55.0
    assert np.isclose(feats["feat_bearing_temperature_c_roll_mean_2"].iloc[1], 55.0)
    assert feats["feat_mtype_INDUSTRIAL_PUMP"].iloc[0] == 1.0
