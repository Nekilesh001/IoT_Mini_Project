"""
Ground-truth label and target engineering for offline training and evaluation.

CRITICAL SAFETY BOUNDARY:
The functions in this module derive offline supervision targets (anomaly ground-truth and Remaining Useful Life)
using simulator degradation states and lifecycle information.
THESE DERIVED TARGETS MUST NEVER BE FED INTO THE FEATURE MATRIX.
"""

from typing import Dict, List, Optional
import pandas as pd
import numpy as np


def compute_ground_truth_labels(
    df: pd.DataFrame,
    degradation_anomaly_threshold: float = 30.0,
    max_rul_seconds: float = 3600.0,
) -> pd.DataFrame:
    """
    Computes offline supervision targets from raw simulator telemetry records:
    1. `target_is_anomaly` (int): 1 if an active fault/degradation exceeds threshold, else 0.
    2. `target_rul_seconds` (float): Remaining time in seconds before end-of-life or severe failure.

    This dataframe with targets is stored separately or joined strictly as target vectors (y),
    never as feature columns (X).
    """
    df_out = df.copy()

    # Determine ground-truth anomaly status
    is_fault = pd.Series(0, index=df_out.index)
    if "sim_active_conditions_count" in df_out.columns:
        is_fault = (df_out["sim_active_conditions_count"] > 0).astype(int)
    elif "sim_is_fault" in df_out.columns:
        is_fault = (df_out["sim_is_fault"] == 1).astype(int)

    is_degraded = pd.Series(0, index=df_out.index)
    if "sim_degradation_pct" in df_out.columns:
        is_degraded = (df_out["sim_degradation_pct"] >= degradation_anomaly_threshold).astype(int)

    df_out["target_is_anomaly"] = np.maximum(is_fault, is_degraded)

    # Compute Remaining Useful Life (RUL) per machine trajectory
    rul_series = pd.Series(max_rul_seconds, index=df_out.index, dtype=float)

    if "machine_id" in df_out.columns and "event_time" in df_out.columns:
        df_out["event_time"] = pd.to_datetime(df_out["event_time"])

        for m_id, group in df_out.groupby("machine_id"):
            group_sorted = group.sort_values("event_time")
            # If degradation percentage is present in simulation logs, calculate RUL to critical wear (>= 80%)
            if "sim_degradation_pct" in group_sorted.columns:
                critical_points = group_sorted[group_sorted["sim_degradation_pct"] >= 80.0]
                if not critical_points.empty:
                    failure_time = critical_points["event_time"].iloc[0]
                    time_diff = (failure_time - group_sorted["event_time"]).dt.total_seconds()
                    # RUL is capped at max_rul_seconds for healthy early operation (piecewise linear RUL)
                    rul_clipped = time_diff.clip(lower=0.0, upper=max_rul_seconds)
                    rul_series.loc[group_sorted.index] = rul_clipped
                else:
                    # Machine stayed healthy throughout run -> cap at max RUL
                    rul_series.loc[group_sorted.index] = max_rul_seconds
            else:
                # If no direct degradation trace, count backwards from end of test run
                max_time = group_sorted["event_time"].max()
                time_to_end = (max_time - group_sorted["event_time"]).dt.total_seconds()
                rul_series.loc[group_sorted.index] = time_to_end.clip(lower=0.0, upper=max_rul_seconds)

    df_out["target_rul_seconds"] = rul_series
    return df_out
