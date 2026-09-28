"""
Unit tests for machine protocol metadata assignments and protocol manager registration.
"""

from simulator.runtime.factory_runtime import FactorySimulator
from protocols.manager import FactoryProtocolManager
from protocols.models import ProtocolType


def test_protocol_assignments_all_12_machines():
    factory = FactorySimulator(seed=42)

    expected = {
        "CNC-001": ProtocolType.OPC_UA,
        "CNC-002": ProtocolType.MODBUS_TCP,
        "ROB-001": ProtocolType.OPC_UA,
        "ROB-002": ProtocolType.MQTT,
        "CON-001": ProtocolType.MODBUS_TCP,
        "PRS-001": ProtocolType.MODBUS_TCP,
        "IMM-001": ProtocolType.OPC_UA,
        "CMP-001": ProtocolType.MODBUS_TCP,
        "PMP-001": ProtocolType.MQTT,
        "VIS-001": ProtocolType.OPC_UA,
        "AGV-001": ProtocolType.MQTT,
        "CHL-001": ProtocolType.MODBUS_TCP,
    }

    for m_id, exp_proto in expected.items():
        m = factory.get_machine(m_id)
        assert m.protocol_metadata.value == exp_proto.value, f"{m_id} protocol assignment mismatch."


def test_protocol_manager_registration():
    factory = FactorySimulator(seed=42)
    manager = FactoryProtocolManager()
    manager.register_simulator(factory)

    assert len(manager._profiles) == 12
