"""
Resilience Invariant Assertions.
Validates core correctness invariants during and after simulated failure recovery.
"""

from typing import Any, Dict, List, Tuple
from failure_testing.models import ScenarioResult


class ResilienceAssertions:
    """
    Standard invariant verification helpers.
    """

    @staticmethod
    def assert_zero_data_loss(sent_count: int, persisted_count: int) -> Tuple[bool, str]:
        """Verify that all generated telemetry events were eventually persisted."""
        if sent_count == persisted_count:
            return True, f"Zero data loss verified ({sent_count}/{persisted_count} events persisted)"
        return False, f"Data loss detected: {sent_count} sent vs {persisted_count} persisted ({sent_count - persisted_count} lost)"

    @staticmethod
    def assert_zero_duplicate_persistence(records: List[Any], key_extractor=lambda r: (r.machine_id, r.sequence)) -> Tuple[bool, str]:
        """Verify that no duplicate (machine_id, sequence) records exist in storage."""
        seen = set()
        duplicates = 0
        for r in records:
            key = key_extractor(r)
            if key in seen:
                duplicates += 1
            seen.add(key)

        if duplicates == 0:
            return True, f"Zero duplicate persistence verified across {len(records)} records"
        return False, f"Duplicate persistence detected: {duplicates} duplicates found"

    @staticmethod
    def assert_ground_truth_isolation(payload: Dict[str, Any]) -> Tuple[bool, str]:
        """Verify that ML leakage boundary holds (no simulation ground truth in public payloads)."""
        forbidden_keys = {"degradation_level", "hidden_wear_counter", "fault_label", "ground_truth", "scenario_id"}
        found = forbidden_keys.intersection(payload.keys())
        if not found:
            return True, "Ground truth isolation verified (zero target leakage)"
        return False, f"Target leakage detected! Found forbidden keys: {found}"

    @staticmethod
    def assert_graceful_ml_degradation(ml_status: str, alerts_active: bool, telemetry_flowing: bool) -> Tuple[bool, str]:
        """Verify that ML failure does not bring down telemetry or rule alerts."""
        if ml_status in ("ERROR", "DEGRADED", "NOT_READY") and alerts_active and telemetry_flowing:
            return True, "Graceful ML degradation verified (telemetry and rule alerts continue uninterrupted)"
        return False, f"ML failure compromised system: ml_status={ml_status}, alerts_active={alerts_active}, telemetry_flowing={telemetry_flowing}"
