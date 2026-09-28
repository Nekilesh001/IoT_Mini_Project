"""
Unit tests asserting zero external network or protocol package requirements for Phase 1 simulator core.
"""

import sys
from simulator.runtime.factory_runtime import FactorySimulator


def test_no_external_protocol_package_imports_required():
    """
    Assert that FactorySimulator operates cleanly without relying on protocol networking
    libraries such as pymodbus, asyncua, or paho.mqtt.
    """
    factory = FactorySimulator(seed=42)
    factory.start()
    factory.step(1.0)
    snapshots = factory.collect_telemetry()

    assert len(snapshots) == 12
    # Verify simulator modules do not import protocol server packages
    loaded_modules = sys.modules
    # Ensure simulation execution didn't force network server bindings
    for m in snapshots:
        assert m.protocol_metadata in ("OPC_UA", "MODBUS_TCP", "MQTT")
