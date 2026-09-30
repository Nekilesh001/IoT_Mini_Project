"""
Unit tests for Edge Ingestion Service processing Wokwi telemetry.
"""

import json
import pytest
from datetime import datetime, timezone

from edge.models import IngestionStatus, QualityCode
from edge.service import EdgeIngestionService
from protocols.wokwi.normalizer import WokwiPayloadNormalizer
from protocols.wokwi.registry import get_external_device_registry


@pytest.fixture
def edge_service():
    registry = get_external_device_registry()
    service = EdgeIngestionService(profiles=registry.get_all_machine_profiles())
    return service


@pytest.fixture
def normalizer():
    return WokwiPayloadNormalizer()


def test_edge_ingestion_accepts_valid_wokwi_reading(edge_service, normalizer):
    payload = json.dumps({
        "deviceId": "IOT-SENSOR-001",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "sequence": 1,
        "readings": {"temperatureC": 28.5, "humidityPct": 62.0}
    })

    reading, _ = normalizer.normalize(payload)
    assert reading is not None

    res = edge_service.ingest_reading(reading)
    assert res.status == IngestionStatus.ACCEPTED
    assert res.canonical_telemetry is not None
    assert res.canonical_telemetry.machine_id == "IOT-SENSOR-001"
    assert res.canonical_telemetry.machine_type == "ENVIRONMENT_SENSOR"
    assert res.canonical_telemetry.measurements["temperature_c"] == 28.5
    assert res.canonical_telemetry.measurements["humidity_pct"] == 62.0
    assert res.canonical_telemetry.quality == QualityCode.GOOD


def test_edge_ingestion_duplicate_sequence(edge_service, normalizer):
    payload = json.dumps({
        "deviceId": "IOT-SENSOR-001",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "sequence": 10,
        "readings": {"temperatureC": 28.5, "humidityPct": 62.0}
    })

    reading, _ = normalizer.normalize(payload)
    res1 = edge_service.ingest_reading(reading)
    assert res1.status == IngestionStatus.ACCEPTED

    # Re-ingest exact same sequence
    res2 = edge_service.ingest_reading(reading)
    assert res2.status == IngestionStatus.DUPLICATE


def test_edge_ingestion_out_of_order_sequence(edge_service, normalizer):
    payload_high = json.dumps({
        "deviceId": "IOT-SENSOR-001",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "sequence": 20,
        "readings": {"temperatureC": 28.5, "humidityPct": 62.0}
    })
    payload_low = json.dumps({
        "deviceId": "IOT-SENSOR-001",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "sequence": 15,
        "readings": {"temperatureC": 28.5, "humidityPct": 62.0}
    })

    r_high, _ = normalizer.normalize(payload_high)
    r_low, _ = normalizer.normalize(payload_low)

    res_high = edge_service.ingest_reading(r_high)
    assert res_high.status == IngestionStatus.ACCEPTED

    res_low = edge_service.ingest_reading(r_low)
    assert res_low.status == IngestionStatus.OUT_OF_ORDER
