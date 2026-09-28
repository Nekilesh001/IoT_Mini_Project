"""
Unit tests for protocol server and adapter health status reporting.
"""

from simulator.runtime.factory_runtime import FactorySimulator
from protocols.manager import FactoryProtocolManager
from protocols.models import ProtocolHealth


def test_protocol_manager_health_status():
    factory = FactorySimulator(seed=42)
    manager = FactoryProtocolManager()
    manager.register_simulator(factory)

    # Initial disconnected status
    health_before = manager.get_health_status()
    assert health_before["modbus_server"] == ProtocolHealth.DISCONNECTED.value

    manager.start_all()
    health_after = manager.get_health_status()
    assert health_after["modbus_server"] == ProtocolHealth.CONNECTED.value
    assert health_after["opcua_server"] == ProtocolHealth.CONNECTED.value
    assert health_after["mqtt_publisher"] == ProtocolHealth.CONNECTED.value

    manager.stop_all()
    health_stopped = manager.get_health_status()
    assert health_stopped["modbus_server"] == ProtocolHealth.DISCONNECTED.value
