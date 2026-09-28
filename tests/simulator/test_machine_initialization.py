"""
Unit tests for factory machine initialization and profile validation.
"""

import pytest
from simulator.runtime.factory_runtime import FactorySimulator
from simulator.core.domain import ProtocolMetadata, MachineType


def test_factory_initialization_count_and_uniqueness():
    factory = FactorySimulator(seed=42)
    machines = factory.get_all_machines()
    assert len(machines) == 12, "Factory must initialize exactly 12 machines."

    machine_ids = [m.machine_id for m in machines]
    assert len(set(machine_ids)) == 12, "Machine IDs must be unique."


def test_machine_types_and_protocols():
    factory = FactorySimulator(seed=42)

    expected_catalog = {
        "CNC-001": (MachineType.CNC_MACHINING_CENTER, ProtocolMetadata.OPC_UA),
        "CNC-002": (MachineType.CNC_LATHE, ProtocolMetadata.MODBUS_TCP),
        "ROB-001": (MachineType.INDUSTRIAL_ROBOT_6AXIS, ProtocolMetadata.OPC_UA),
        "ROB-002": (MachineType.WELDING_ROBOT, ProtocolMetadata.MQTT),
        "CON-001": (MachineType.INDUSTRIAL_CONVEYOR, ProtocolMetadata.MODBUS_TCP),
        "PRS-001": (MachineType.INDUSTRIAL_PRESS, ProtocolMetadata.MODBUS_TCP),
        "IMM-001": (MachineType.INJECTION_MOLDING_MACHINE, ProtocolMetadata.OPC_UA),
        "CMP-001": (MachineType.AIR_COMPRESSOR, ProtocolMetadata.MODBUS_TCP),
        "PMP-001": (MachineType.INDUSTRIAL_PUMP, ProtocolMetadata.MQTT),
        "VIS-001": (MachineType.VISION_INSPECTION_STATION, ProtocolMetadata.OPC_UA),
        "AGV-001": (MachineType.AUTONOMOUS_MOBILE_ROBOT, ProtocolMetadata.MQTT),
        "CHL-001": (MachineType.INDUSTRIAL_CHILLER, ProtocolMetadata.MODBUS_TCP),
    }

    for m_id, (exp_type, exp_proto) in expected_catalog.items():
        machine = factory.get_machine(m_id)
        assert machine.machine_type == exp_type, f"{m_id} machine type mismatch."
        assert machine.protocol_metadata == exp_proto, f"{m_id} protocol metadata mismatch."
