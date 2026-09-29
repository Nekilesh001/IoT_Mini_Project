"""
Unit tests for ResilienceAssertions (zero data loss, deduplication, ground truth isolation, ML degradation).
"""

import pytest
from failure_testing.assertions import ResilienceAssertions


def test_assert_zero_data_loss():
    ok, msg = ResilienceAssertions.assert_zero_data_loss(100, 100)
    assert ok is True
    assert "Zero data loss verified" in msg

    failed, fail_msg = ResilienceAssertions.assert_zero_data_loss(100, 95)
    assert failed is False
    assert "Data loss detected" in fail_msg


def test_assert_zero_duplicate_persistence():
    class MockRecord:
        def __init__(self, machine_id, sequence):
            self.machine_id = machine_id
            self.sequence = sequence

    records = [MockRecord("CNC-001", 1), MockRecord("CNC-001", 2), MockRecord("CNC-001", 3)]
    ok, msg = ResilienceAssertions.assert_zero_duplicate_persistence(records)
    assert ok is True

    dup_records = [MockRecord("CNC-001", 1), MockRecord("CNC-001", 2), MockRecord("CNC-001", 1)]
    dup_ok, dup_msg = ResilienceAssertions.assert_zero_duplicate_persistence(dup_records)
    assert dup_ok is False
    assert "Duplicate persistence detected" in dup_msg


def test_assert_ground_truth_isolation():
    clean_dict = {
        "machine_id": "CNC-001",
        "temperature": 45.0,
        "vibration": 1.2,
    }
    ok, msg = ResilienceAssertions.assert_ground_truth_isolation(clean_dict)
    assert ok is True

    leaky_dict = {
        "machine_id": "CNC-001",
        "degradation_level": 0.45,
        "temperature": 45.0,
    }
    leak_ok, leak_msg = ResilienceAssertions.assert_ground_truth_isolation(leaky_dict)
    assert leak_ok is False
    assert "Target leakage detected" in leak_msg


def test_assert_graceful_ml_degradation():
    ok, msg = ResilienceAssertions.assert_graceful_ml_degradation(
        ml_status="ERROR",
        alerts_active=True,
        telemetry_flowing=True,
    )
    assert ok is True
    assert "Graceful ML degradation verified" in msg
