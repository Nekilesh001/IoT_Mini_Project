"""
Strict target leakage validation and ground-truth isolation rules.

GUARANTEE:
Prevents any simulator internal counters, degradation percentages, fault flags,
or target columns from entering ML feature matrices.
"""

from typing import Iterable, List, Set
from ml.schemas import TargetLeakageError

# Set of forbidden column names and substrings that indicate ground-truth / target leakage
PROHIBITED_LEAKAGE_PATTERNS: Set[str] = {
    "sim_",
    "target_",
    "ground_truth",
    "degradation_level",
    "degradation_pct",
    "hidden_wear",
    "wear_counter",
    "active_conditions",
    "scenario_id",
    "is_fault",
    "fault_type",
    "fault_code",
    "rul_",
    "remaining_useful_life",
    "time_to_failure",
    "alert_code",
    "alert_id",
    "triggering_measurements",
    "resolution_notes",
    "ml_prediction",
}


def validate_feature_names(feature_names: Iterable[str]) -> None:
    """
    Validates that no feature name matches forbidden leakage patterns.
    Raises TargetLeakageError if a violation is detected.
    """
    violations: List[str] = []
    for name in feature_names:
        name_lower = name.lower()
        for pattern in PROHIBITED_LEAKAGE_PATTERNS:
            if pattern in name_lower:
                violations.append(f"Feature '{name}' matches prohibited leakage pattern '{pattern}'")
                break

    if violations:
        raise TargetLeakageError(
            f"TARGET LEAKAGE DETECTED in feature matrix! Violations: {violations}"
        )


def filter_leakage_columns(columns: Iterable[str]) -> List[str]:
    """Filters out any columns matching prohibited leakage patterns."""
    clean: List[str] = []
    for col in columns:
        col_lower = col.lower()
        is_leakage = any(pattern in col_lower for pattern in PROHIBITED_LEAKAGE_PATTERNS)
        if not is_leakage:
            clean.append(col)
    return clean
