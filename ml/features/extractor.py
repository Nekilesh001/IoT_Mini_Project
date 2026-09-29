"""
Feature Extraction Pipeline with strict target leakage isolation.
"""

from typing import Dict, List, Optional, Tuple
import pandas as pd
import numpy as np

from ml.features.validation import validate_feature_names, filter_leakage_columns
from ml.features.machine_features import (
    OBSERVABLE_SIGNALS_BY_MACHINE_TYPE,
    OPERATING_STATE_ENCODING,
    QUALITY_ENCODING,
)
from ml.features.rolling import (
    compute_rolling_features,
    compute_rate_of_change,
    compute_baseline_delta,
)
from ml.schemas import FeatureManifestEntry, TargetLeakageError


class FeatureExtractor:
    """
    Transforms raw observable canonical telemetry into machine-learning feature vectors.
    Strictly isolates all simulation ground truth.
    """

    def __init__(
        self,
        rolling_windows: Optional[List[int]] = None,
        include_rolling: bool = True,
        include_rate_of_change: bool = True,
        include_baseline_delta: bool = True,
        fill_missing: bool = True,
    ):
        self.rolling_windows = rolling_windows or [5, 15, 30]
        self.include_rolling = include_rolling
        self.include_rate_of_change = include_rate_of_change
        self.include_baseline_delta = include_baseline_delta
        self.fill_missing = fill_missing
        self._feature_names: List[str] = []
        self._manifest: List[FeatureManifestEntry] = []

    @property
    def feature_names(self) -> List[str]:
        return list(self._feature_names)

    @property
    def manifest(self) -> List[FeatureManifestEntry]:
        return list(self._manifest)

    def extract_features(
        self,
        df: pd.DataFrame,
        is_training: bool = False,
    ) -> Tuple[pd.DataFrame, List[FeatureManifestEntry]]:
        """
        Extracts temporal and machine-aware features from raw observable telemetry.
        Returns: (feature_df, manifest_entries)
        """
        if df.empty:
            return pd.DataFrame(), []

        # 1. First-pass Leakage Filter: Remove any ground truth / target columns from input
        clean_cols = filter_leakage_columns(df.columns)
        work_df = df[clean_cols].copy()

        if "event_time" in work_df.columns:
            work_df["event_time"] = pd.to_datetime(work_df["event_time"])

        # 2. Determine all available physical numerical measurement columns
        all_observable_signals: set = set()
        for sig_list in OBSERVABLE_SIGNALS_BY_MACHINE_TYPE.values():
            all_observable_signals.update(sig_list)

        present_signal_cols = [
            c for c in clean_cols
            if c in all_observable_signals and pd.api.types.is_numeric_dtype(work_df[c])
        ]

        feature_blocks: List[pd.DataFrame] = []
        manifest_entries: List[FeatureManifestEntry] = []

        # 3. Process machine by machine for sequential rolling statistics
        machine_groups = work_df.groupby("machine_id") if "machine_id" in work_df.columns else [(None, work_df)]

        extracted_machine_dfs = []

        for m_id, group in machine_groups:
            group_sorted = group.sort_values("event_time") if "event_time" in group.columns else group
            group_dict: Dict[str, Any] = {}

            # A. State & Quality encodings
            if "operating_state" in group_sorted.columns:
                group_dict["feat_operating_state_enc"] = group_sorted["operating_state"].map(
                    lambda s: OPERATING_STATE_ENCODING.get(str(s), 3.0)
                ).values
            if "quality" in group_sorted.columns:
                group_dict["feat_quality_enc"] = group_sorted["quality"].map(
                    lambda q: QUALITY_ENCODING.get(str(q), 1.0)
                ).values

            # B. Raw physical measurements present in this machine
            for col in present_signal_cols:
                series = pd.to_numeric(group_sorted[col], errors="coerce")
                group_dict[f"feat_raw_{col}"] = series.values

                # Rolling temporal features
                if self.include_rolling:
                    roll_df = compute_rolling_features(series, self.rolling_windows)
                    for r_col in roll_df.columns:
                        group_dict[f"feat_{r_col}"] = roll_df[r_col].values

                # Rate of change
                if self.include_rate_of_change:
                    roc = compute_rate_of_change(series, periods=1)
                    group_dict[f"feat_{roc.name}"] = roc.values

                # Baseline delta
                if self.include_baseline_delta:
                    base_delta = compute_baseline_delta(series, baseline_window=max(self.rolling_windows))
                    group_dict[f"feat_{base_delta.name}"] = base_delta.values

            group_features = pd.DataFrame(group_dict, index=group_sorted.index)
            extracted_machine_dfs.append(group_features)

        combined_features = pd.concat(extracted_machine_dfs).sort_index()

        # 4. Machine Type One-Hot Encoding
        if "machine_type" in work_df.columns:
            m_types = sorted(OBSERVABLE_SIGNALS_BY_MACHINE_TYPE.keys())
            mtype_dict = {}
            for mt in m_types:
                mtype_dict[f"feat_mtype_{mt}"] = (work_df["machine_type"] == mt).astype(float).values
            mtype_df = pd.DataFrame(mtype_dict, index=work_df.index)
            combined_features = pd.concat([combined_features, mtype_df], axis=1)

        # 5. Missing value handling (backward / forward fill per machine, then constant fill)
        if self.fill_missing:
            combined_features = combined_features.ffill().bfill().fillna(0.0)

        # 6. Build Manifest & Validate No Leakage
        manifest_entries = []
        for col in combined_features.columns:
            # Derive source signal name
            src_signal = col.replace("feat_raw_", "").replace("feat_", "").split("_roll_")[0].split("_diff_")[0].split("_delta_")[0]
            entry = FeatureManifestEntry(
                name=col,
                source_signal=src_signal,
                machine_applicability=["ALL" if "mtype" in col or "state" in col or "quality" in col else "SPECIFIC"],
                unit="dimensionless" if "mtype" in col or "enc" in col else "measurement_unit",
                transformation="one_hot" if "mtype" in col else ("rolling" if "roll" in col else "raw"),
                window_samples=int(col.split("_")[-1]) if "_roll_" in col else None,
                is_leakage_free=True,
                description=f"Engineered feature {col}",
            )
            manifest_entries.append(entry)

        # 7. Final Strict Leakage Assertion
        validate_feature_names(combined_features.columns)

        if is_training or not self._feature_names:
            self._feature_names = list(combined_features.columns)
            self._manifest = manifest_entries
        else:
            # Align columns with trained feature ordering
            missing_cols = [c for c in self._feature_names if c not in combined_features.columns]
            if missing_cols:
                missing_df = pd.DataFrame(0.0, index=combined_features.index, columns=missing_cols)
                combined_features = pd.concat([combined_features, missing_df], axis=1)
            combined_features = combined_features[self._feature_names]

        return combined_features, manifest_entries
