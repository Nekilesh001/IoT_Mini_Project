"""
Unit tests for OPC UA server manager and client adapter read operations.
"""

import time
from simulator.runtime.factory_runtime import FactorySimulator
from protocols.opcua.server import OPCUAServerManager
from protocols.opcua.adapter import OPCUAAdapter
from protocols.models import ProtocolType


def test_opcua_server_and_adapter_roundtrip():
    factory = FactorySimulator(seed=42)
    m = factory.get_machine("CNC-001")

    server = OPCUAServerManager(endpoint="opc.tcp://127.0.0.1:4840/freeopcua/server/", profiles={m.machine_id: m.profile})
    adapter = OPCUAAdapter(endpoint="opc.tcp://127.0.0.1:4840/freeopcua/server/", profiles={m.machine_id: m.profile})

    try:
        server.start()
        factory.start()
        factory.step()

        snap = m.generate_snapshot()
        server.update_from_telemetry(snap)
        time.sleep(0.5)

        reading = adapter.read_telemetry("CNC-001")
        assert reading is not None
        assert reading.machine_id == "CNC-001"
        assert reading.protocol == ProtocolType.OPC_UA
        assert reading.sequence == snap.sequence
        assert "spindle_speed_rpm" in reading.measurements
        assert reading.measurements["spindle_speed_rpm"] == snap.public_measurements["spindle_speed_rpm"]
    finally:
        server.stop()
