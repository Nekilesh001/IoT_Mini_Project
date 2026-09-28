"""
End-to-end integration test for Machine Simulator -> Protocol Manager -> Servers -> Adapters -> ProtocolReadings.
"""

import time
from simulator.runtime.factory_runtime import FactorySimulator
from protocols.manager import FactoryProtocolManager


def test_end_to_end_all_12_machines_protocol_reading():
    factory = FactorySimulator(seed=42)
    manager = FactoryProtocolManager()
    manager.register_simulator(factory)

    try:
        manager.start_all()
        factory.start()
        factory.step(1.0)

        snapshots = factory.collect_telemetry()
        manager.update_from_simulator(snapshots)
        time.sleep(0.5)

        readings = manager.read_all_adapters()
        assert len(readings) == 12, "Must receive adapter readings for all 12 machines."

        read_ids = {r.machine_id for r in readings}
        assert len(read_ids) == 12, "All 12 machine IDs must be represented in readings."

        # Verify protocol type matching
        proto_map = {r.machine_id: r.protocol.value for r in readings}
        assert proto_map["CNC-001"] == "OPC_UA"
        assert proto_map["CNC-002"] == "MODBUS_TCP"
        assert proto_map["PMP-001"] == "MQTT"
    finally:
        factory.stop()
        manager.stop_all()
