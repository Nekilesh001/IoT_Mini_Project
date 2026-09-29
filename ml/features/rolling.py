"""
Temporal rolling window and rate-of-change feature calculations.

GUARANTEE:
All calculations are strictly backward-looking in time (using observations at or before time T).
No future-window observations are ever used.
"""

from typing import List, Optional
import pandas as pd
import numpy as np


def compute_rolling_features(
    series: pd.Series,
    window_sizes: List[int],
    include_min_max: bool = True,
) -> pd.DataFrame:
    """
    Computes backward-looking rolling statistics (mean, std, min, max) for a single numerical signal series.
    """
    out = pd.DataFrame(index=series.index)
    col_name = str(series.name)

    for w in window_sizes:
        # Rolling mean
        roll = series.rolling(window=w, min_periods=1)
        out[f"{col_name}_roll_mean_{w}"] = roll.mean()
        # Rolling std (filled with 0 for initial single observation)
        out[f"{col_name}_roll_std_{w}"] = roll.std().fillna(0.0)

        if include_min_max:
            out[f"{col_name}_roll_min_{w}"] = roll.min()
            out[f"{col_name}_roll_max_{w}"] = roll.max()

    return out


def compute_rate_of_change(series: pd.Series, periods: int = 1) -> pd.Series:
    """
    Computes backward-looking rate of change: x(t) - x(t - periods).
    """
    diff = series.diff(periods=periods).fillna(0.0)
    diff.name = f"{series.name}_diff_{periods}"
    return diff


def compute_baseline_delta(series: pd.Series, baseline_window: int = 30) -> pd.Series:
    """
    Computes deviation from recent backward-looking rolling baseline: x(t) - mean(x(t-w:t)).
    """
    baseline = series.rolling(window=baseline_window, min_periods=1).mean()
    delta = series - baseline
    delta.name = f"{series.name}_delta_base_{baseline_window}"
    return delta
