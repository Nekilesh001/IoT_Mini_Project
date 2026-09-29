"""
Integration tests for FailureTestRunner scenarios and recovery metrics.
"""

import pytest
from failure_testing.runner import FailureTestRunner


@pytest.fixture
def runner():
    return FailureTestRunner()


def test_mqtt_outage_scenario(runner):
    result = runner.test_mqtt_outage()
    assert result.status == "PASSED"
    assert result.metrics.buffered_events_count > 0
    assert result.metrics.replayed_events_count == result.metrics.buffered_events_count
    assert len(result.assertions_failed) == 0


def test_database_outage_scenario(runner):
    result = runner.test_database_outage()
    assert result.status == "PASSED"
    assert result.metrics.buffered_events_count > 0
    assert result.metrics.replayed_events_count == result.metrics.buffered_events_count


def test_protocol_failure_scenario(runner):
    result = runner.test_protocol_failure()
    assert result.status == "PASSED"
    assert result.target_machine_id == "PMP-001"


def test_telemetry_corruption_scenario(runner):
    result = runner.test_telemetry_corruption()
    assert result.status == "PASSED"


def test_ml_failure_scenario(runner):
    result = runner.test_ml_failure()
    assert result.status == "PASSED"


def test_alert_persistence_failure_scenario(runner):
    result = runner.test_alert_persistence_failure()
    assert result.status == "PASSED"


def test_job_retry_failure_scenario(runner):
    result = runner.test_job_retry_failure()
    assert result.status == "PASSED"


def test_restart_recovery_scenario(runner):
    result = runner.test_restart_recovery()
    assert result.status == "PASSED"
