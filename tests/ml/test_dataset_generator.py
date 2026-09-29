"""
Unit tests for deterministic simulator dataset generator.
"""

import pandas as pd
from ml.data.simulator_dataset import SimulatorDatasetGenerator


def test_simulator_dataset_generator_determinism():
    """Verify SimulatorDatasetGenerator produces identical datasets with the same random seed."""
    gen1 = SimulatorDatasetGenerator(seed=42)
    df1 = gen1.collect(num_ticks=20, dt_seconds=1.0)

    gen2 = SimulatorDatasetGenerator(seed=42)
    df2 = gen2.collect(num_ticks=20, dt_seconds=1.0)

    pd.testing.assert_frame_equal(df1, df2)
    assert len(df1) == 20 * 12  # 12 machines * 20 ticks = 240 samples
    assert "target_is_anomaly" in df1.columns
    assert "target_rul_seconds" in df1.columns
    assert set(df1["machine_id"].unique()) == {
        "CNC-001", "CNC-002", "ROB-001", "ROB-002",
        "CON-001", "PRS-001", "IMM-001", "CMP-001",
        "PMP-001", "CHL-001", "AGV-001", "VIS-001"
    }
