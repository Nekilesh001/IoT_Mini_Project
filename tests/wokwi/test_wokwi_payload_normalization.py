"""
Unit tests for Wokwi payload normalization and edge validation.
"""

import json
import pytest
from datetime import datetime, timezone
from protocols.wokwi.normalizer import WokwiPayloadNormalizer
from protocols.models import ProtocolType, ProtocolHealth


@pytest.fixture
def normalizer():
    norm = WokwiPayloadNormalizer()
    norm.reset_sequence("IOT-SENSOR-001", 0)
    return norm


def test_valid_wokwi_payload(normalizer):
    raw_payload = json.dumps({
        "deviceId": "IOT-SENSOR-001",
        "timestamp": "2026-09-30T10:00:00Z",
        "sequence": 42,
        "eventType": "TELEMETRY",
        "plantId": "PLANT_01",
        "lineId": "LINE_A",
        "deviceType": "ENVIRONMENT_SENSOR",
        "readings": {
            "temperatureC": 31.4,
            "humidityPct": 68.2
        },
        "actuator": {
            "type": "LED",
            "state": "ON"
        },
        "control": {
            "mode": "AUTO",
            "alertThresholdC": 30,
            "normalThresholdC": 28
        },
        "firmwareVersion": "0.1.0"
    })

    reading, err = normalizer.normalize(
        raw_payload=raw_payload,
        topic="iot/plant/PLANT_01/line/LINE_A/device/IOT-SENSOR-001/telemetry",
        ingress_broker="broker.hivemq.com"
    )

    assert err is None
    assert reading is not None
    assert reading.machine_id == "IOT-SENSOR-001"
    assert reading.machine_type == "ENVIRONMENT_SENSOR"
    assert reading.protocol == ProtocolType.MQTT
    assert reading.sequence == 42
    assert reading.measurements["temperature_c"] == 31.4
    assert reading.measurements["humidity_pct"] == 68.2
    assert reading.metadata["firmwareVersion"] == "0.1.0"
    assert reading.metadata["actuator"]["state"] == "ON"
    assert reading.metadata["ingress_broker"] == "broker.hivemq.com"


def test_invalid_json(normalizer):
    raw_payload = "NOT_A_VALID_JSON{abc"
    reading, err = normalizer.normalize(raw_payload)
    assert reading is None
    assert "Malformed JSON" in err


def test_missing_device_id(normalizer):
    raw_payload = json.dumps({
        "readings": {"temperatureC": 25.0, "humidityPct": 50.0}
    })
    reading, err = normalizer.normalize(raw_payload)
    assert reading is None
    assert "Missing required field 'deviceId'" in err


def test_unregistered_device_id(normalizer):
    raw_payload = json.dumps({
        "deviceId": "UNKNOWN-DEV-999",
        "readings": {"temperatureC": 25.0, "humidityPct": 50.0}
    })
    reading, err = normalizer.normalize(raw_payload)
    assert reading is None
    assert "Unregistered external deviceId" in err


def test_missing_temperature(normalizer):
    raw_payload = json.dumps({
        "deviceId": "IOT-SENSOR-001",
        "readings": {"humidityPct": 60.0}
    })
    reading, err = normalizer.normalize(raw_payload)
    assert reading is None
    assert "Missing required temperature" in err


def test_missing_humidity(normalizer):
    raw_payload = json.dumps({
        "deviceId": "IOT-SENSOR-001",
        "readings": {"temperatureC": 25.0}
    })
    reading, err = normalizer.normalize(raw_payload)
    assert reading is None
    assert "Missing required humidity" in err


def test_non_numeric_readings(normalizer):
    raw_payload = json.dumps({
        "deviceId": "IOT-SENSOR-001",
        "readings": {"temperatureC": "INVALID_NUMBER", "humidityPct": 50.0}
    })
    reading, err = normalizer.normalize(raw_payload)
    assert reading is None
    assert "Non-numeric measurement" in err


def test_missing_sequence_generates_monotonic_sequence(normalizer):
    raw_payload_1 = json.dumps({
        "deviceId": "IOT-SENSOR-001",
        "readings": {"temperatureC": 22.0, "humidityPct": 45.0}
    })
    raw_payload_2 = json.dumps({
        "deviceId": "IOT-SENSOR-001",
        "readings": {"temperatureC": 22.5, "humidityPct": 46.0}
    })

    reading1, err1 = normalizer.normalize(raw_payload_1)
    reading2, err2 = normalizer.normalize(raw_payload_2)

    assert err1 is None and err2 is None
    assert reading1.sequence == 1
    assert reading2.sequence == 2


def test_malformed_timestamp_fallback(normalizer):
    raw_payload = json.dumps({
        "deviceId": "IOT-SENSOR-001",
        "timestamp": "INVALID_DATE_TIME",
        "readings": {"temperatureC": 25.0, "humidityPct": 50.0}
    })
    reading, err = normalizer.normalize(raw_payload)
    assert err is None
    assert reading is not None
    # Must produce a valid ISO timestamp
    parsed = datetime.fromisoformat(reading.timestamp)
    assert parsed is not None
