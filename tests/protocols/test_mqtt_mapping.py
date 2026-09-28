"""
Unit tests for MQTT topic construction and raw JSON payload encoding.
"""

from simulator.runtime.factory_runtime import FactorySimulator
from protocols.mqtt.mapping import MQTTMapper


def test_mqtt_topic_generation():
    top = MQTTMapper.get_telemetry_topic("PLANT_01", "LINE_A", "PMP-001")
    assert top == "factory/PLANT_01/LINE_A/PMP-001/telemetry"

    st_top = MQTTMapper.get_status_topic("PLANT_01", "LINE_A", "PMP-001")
    assert st_top == "factory/PLANT_01/LINE_A/PMP-001/status"


def test_mqtt_payload_encoding():
    factory = FactorySimulator(seed=42)
    m = factory.get_machine("PMP-001")
    factory.start()
    factory.step()

    snap = m.generate_snapshot()
    payload = MQTTMapper.encode_payload(
        profile=m.profile,
        measurements=snap.public_measurements,
        sequence=snap.sequence,
        operating_state=snap.operating_state,
        timestamp=snap.timestamp
    )

    assert payload["machineId"] == "PMP-001"
    assert payload["sequence"] == snap.sequence
    assert payload["operatingState"] == "RUNNING"
    assert "bearing_temperature_c" in payload["measurements"]
