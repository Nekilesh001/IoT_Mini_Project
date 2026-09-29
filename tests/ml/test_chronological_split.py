"""
Unit tests verifying strict chronological dataset splitting without future-window leakage.
"""

import pandas as pd
import numpy as np
from ml.data.split import chronological_train_val_test_split


def test_chronological_split_preserves_temporal_ordering():
    """Verify that train, val, and test splits do not overlap in time and preserve ordering."""
    dates = pd.date_range("2026-01-01 00:00:00", periods=100, freq="1s")
    df = pd.DataFrame({
        "machine_id": ["CNC-001"] * 100,
        "event_time": dates,
        "spindle_temperature_c": np.linspace(40, 70, 100),
        "target_is_anomaly": [0] * 80 + [1] * 20,
    })

    train_df, val_df, test_df = chronological_train_val_test_split(
        df,
        train_ratio=0.60,
        val_ratio=0.20,
        test_ratio=0.20,
        time_column="event_time",
        group_by_machine=True,
    )

    assert len(train_df) == 60
    assert len(val_df) == 20
    assert len(test_df) == 20

    # Strict temporal boundary checks
    assert train_df["event_time"].max() < val_df["event_time"].min()
    assert val_df["event_time"].max() < test_df["event_time"].min()


def test_chronological_split_multi_machine():
    """Verify chronological splitting across multiple machines maintains per-machine ratios."""
    dates = pd.date_range("2026-01-01 00:00:00", periods=50, freq="1s")
    df1 = pd.DataFrame({"machine_id": ["PMP-001"] * 50, "event_time": dates, "val": range(50)})
    df2 = pd.DataFrame({"machine_id": ["CON-001"] * 50, "event_time": dates, "val": range(50)})
    df = pd.concat([df1, df2], ignore_index=True)

    train_df, val_df, test_df = chronological_train_val_test_split(
        df,
        train_ratio=0.60,
        val_ratio=0.20,
        test_ratio=0.20,
        group_by_machine=True,
    )

    assert len(train_df) == 60  # 30 per machine
    assert len(val_df) == 20    # 10 per machine
    assert len(test_df) == 20   # 10 per machine
    assert set(train_df["machine_id"].unique()) == {"PMP-001", "CON-001"}
