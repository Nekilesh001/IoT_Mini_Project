"""
Unit tests for Modbus TCP server manager and client adapter read operations.
"""

import time
from simulator.runtime.factory_runtime import FactorySimulator
from protocols.modbus.server import ModbusServerManager
from protocols.modbus.adapter import ModbusAdapter
from protocols.models import ProtocolType


def test_modbus_server_and_adapter_roundtrip():
    factory = FactorySimulator(seed=42)
    m = factory.get_machine("CNC-002")

    server = ModbusServerManager(port=5020, profiles={m.machine_id: m.profile})
    adapter = ModbusAdapter(port=5020, profiles={m.machine_id: m.profile})

    try:
        server.start()
        assert adapter.connect()

        # Step 1: Sequence 1
        factory.start()
        factory.step()

        snap1 = m.generate_snapshot()
        assert snap1.sequence == 1
        server.update_from_telemetry(snap1)

        reading1 = adapter.read_telemetry("CNC-002")
        assert reading1 is not None
        assert reading1.machine_id == "CNC-002"
        assert reading1.protocol == ProtocolType.MODBUS_TCP
        assert reading1.sequence == 1
        assert "spindle_speed_rpm" in reading1.measurements

        # Step 2: Sequence 2
        factory.step()
        snap2 = m.generate_snapshot()
        assert snap2.sequence == 2
        server.update_from_telemetry(snap2)

        reading2 = adapter.read_telemetry("CNC-002")
        assert reading2 is not None
        assert reading2.machine_id == "CNC-002"
        assert reading2.sequence == 2
        assert "spindle_speed_rpm" in reading2.measurements
    finally:
        adapter.disconnect()
        server.stop()
