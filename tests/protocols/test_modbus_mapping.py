"""
Unit tests for Modbus TCP register encoding, decoding, scaling, and round-trip consistency.
"""

from simulator.runtime.factory_runtime import FactorySimulator
from protocols.modbus.mapping import ModbusSignalMapper


def test_modbus_unit_ids_deterministic():
    assert ModbusSignalMapper.get_unit_id("CNC-002") == 1
    assert ModbusSignalMapper.get_unit_id("CON-001") == 2
    assert ModbusSignalMapper.get_unit_id("PRS-001") == 3
    assert ModbusSignalMapper.get_unit_id("CMP-001") == 4
    assert ModbusSignalMapper.get_unit_id("CHL-001") == 5


def test_modbus_signal_to_register_scaling():
    # Float scaling (0.1 scale)
    reg_val = ModbusSignalMapper.signal_to_register("temperature", 42.5)
    assert reg_val == 425

    # Reverse decoding
    decoded = ModbusSignalMapper.register_to_signal("temperature", 425, original_type="FLOAT")
    assert decoded == 42.5

    # Bool scaling
    assert ModbusSignalMapper.signal_to_register("jam_state", True) == 1
    assert ModbusSignalMapper.signal_to_register("jam_state", False) == 0
    assert ModbusSignalMapper.register_to_signal("jam_state", 1, original_type="BOOL") is True


def test_modbus_roundtrip_snapshot_encoding():
    factory = FactorySimulator(seed=42)
    cnc = factory.get_machine("CNC-002")
    factory.start()
    factory.step()

    snap = cnc.generate_snapshot()
    registers = ModbusSignalMapper.encode_snapshot_to_registers(
        profile=cnc.profile,
        measurements=snap.public_measurements,
        sequence=snap.sequence,
        operating_state=snap.operating_state
    )

    assert len(registers) == len(cnc.profile.signals) + 3

    seq, op_state, decoded_meas = ModbusSignalMapper.decode_registers_to_measurements(cnc.profile, registers)
    assert seq == snap.sequence
    assert op_state == snap.operating_state
    assert "spindle_speed_rpm" in decoded_meas
