"""
Unit tests for MQTT publisher manager, embedded broker, and subscriber adapter operations.
"""

from simulator.runtime.factory_runtime import FactorySimulator
from protocols.mqtt.publisher import MQTTPublisherManager
from protocols.mqtt.adapter import MQTTAdapter
from protocols.models import ProtocolType


def test_mqtt_publisher_and_adapter_roundtrip():
    factory = FactorySimulator(seed=42)
    m = factory.get_machine("PMP-001")

    pub = MQTTPublisherManager(profiles={m.machine_id: m.profile})
    adapter = MQTTAdapter(profiles={m.machine_id: m.profile})

    try:
        pub.start()
        adapter.connect()

        factory.start()
        factory.step()

        snap = m.generate_snapshot()
        pub.update_from_telemetry(snap)

        reading = adapter.read_telemetry("PMP-001")
        assert reading is not None
        assert reading.machine_id == "PMP-001"
        assert reading.protocol == ProtocolType.MQTT
        assert reading.sequence == snap.sequence
        assert "bearing_temperature_c" in reading.measurements
        assert reading.measurements["bearing_temperature_c"] == snap.public_measurements["bearing_temperature_c"]
    finally:
        adapter.disconnect()
        pub.stop()
