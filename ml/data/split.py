"""
Chronological dataset splitting utilities for sequential telemetry datasets.
"""

from typing import Tuple
import pandas as pd


def chronological_train_val_test_split(
    df: pd.DataFrame,
    train_ratio: float = 0.60,
    val_ratio: float = 0.20,
    test_ratio: float = 0.20,
    time_column: str = "event_time",
    group_by_machine: bool = True,
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Performs a strictly chronological, non-random time-series train/validation/test split.
    Guarantees:
      - Train observations strictly precede Validation observations.
      - Validation observations strictly precede Test observations.
      - No random shuffling or future-window temporal leakage.
    """
    if df.empty:
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

    total_ratio = train_ratio + val_ratio + test_ratio
    train_pct = train_ratio / total_ratio
    val_pct = val_ratio / total_ratio

    df_sorted = df.copy()
    if time_column in df_sorted.columns:
        df_sorted[time_column] = pd.to_datetime(df_sorted[time_column])

    if group_by_machine and "machine_id" in df_sorted.columns:
        train_dfs = []
        val_dfs = []
        test_dfs = []

        for m_id, group in df_sorted.groupby("machine_id"):
            group = group.sort_values(time_column).reset_index(drop=True)
            n = len(group)
            train_end = int(n * train_pct)
            val_end = int(n * (train_pct + val_pct))

            train_dfs.append(group.iloc[:train_end])
            val_dfs.append(group.iloc[train_end:val_end])
            test_dfs.append(group.iloc[val_end:])

        train_df = pd.concat(train_dfs, ignore_index=True) if train_dfs else pd.DataFrame()
        val_df = pd.concat(val_dfs, ignore_index=True) if val_dfs else pd.DataFrame()
        test_df = pd.concat(test_dfs, ignore_index=True) if test_dfs else pd.DataFrame()
    else:
        df_sorted = df_sorted.sort_values(time_column).reset_index(drop=True)
        n = len(df_sorted)
        train_end = int(n * train_pct)
        val_end = int(n * (train_pct + val_pct))

        train_df = df_sorted.iloc[:train_end]
        val_df = df_sorted.iloc[train_end:val_end]
        test_df = df_sorted.iloc[val_end:]

    return train_df, val_df, test_df
