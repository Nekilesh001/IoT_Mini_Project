"""
Unit tests for failure scenario catalog and failure injector state transitions.
"""

import pytest
from failure_testing.models import FailureScenarioType, FailureTarget
from failure_testing.scenarios import SCENARIO_DEFINITIONS
from failure_testing.injector import FailureInjector


def test_scenario_catalog_coverage():
    assert len(SCENARIO_DEFINITIONS) == 15
    for sc_type in FailureScenarioType:
        assert sc_type in SCENARIO_DEFINITIONS
        meta = SCENARIO_DEFINITIONS[sc_type]
        assert "name" in meta
        assert "target" in meta
        assert "expected" in meta


def test_failure_injector_lifecycle():
    injector = FailureInjector()

    assert injector.is_fault_active(FailureScenarioType.MQTT_OUTAGE) is False

    # Inject fault
    injector.inject_fault(FailureScenarioType.MQTT_OUTAGE)
    assert injector.is_fault_active(FailureScenarioType.MQTT_OUTAGE) is True

    # Recover fault
    injector.recover_fault(FailureScenarioType.MQTT_OUTAGE)
    assert injector.is_fault_active(FailureScenarioType.MQTT_OUTAGE) is False
