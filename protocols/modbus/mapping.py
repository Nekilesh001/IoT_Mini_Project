"""
Modbus TCP register mapping and encoding/decoding rules.
"""

from typing import Any, Dict, List, Tuple
from simulator.core.domain import MachineProfile


class ModbusSignalMapper:
    """
    Handles deterministic mapping between Python machine telemetry signals and Modbus 16-bit registers/coils.
    """

    UNIT_ID_MAP: Dict[str, int] = {
        "CNC-002": 1,
        "CON-001": 2,
        "PRS-001": 3,
        "CMP-001": 4,
        "CHL-001": 5,
    }

    # Signal scaling rules: (scale_factor, signed)
    DEFAULT_SCALE: float = 0.1

    @classmethod
    def get_unit_id(cls, machine_id: str) -> int:
        return cls.UNIT_ID_MAP.get(machine_id, 1)

    @classmethod
    def signal_to_register(cls, signal_name: str, value: Any) -> int:
        """Encode a native Python signal value into a 16-bit unsigned Modbus register integer."""
        if isinstance(value, bool):
            return 1 if value else 0
        elif isinstance(value, str):
            state_codes = {
                "OFF": 0, "STARTING": 1, "IDLE": 2, "RUNNING": 3,
                "WARNING": 4, "FAULT": 5, "MAINTENANCE": 6, "RECOVERY": 7,
                "CUTTING": 3, "MOVING": 3, "INSPECTING": 3, "CLEAR": 0, "NORMAL": 0
            }
            return state_codes.get(value.upper(), 0)
        elif isinstance(value, int):
            return max(0, min(65535, value % 65536))
        elif isinstance(value, float):
            # Scale float value to integer register
            scaled = int(round(value / cls.DEFAULT_SCALE))
            return max(0, min(65535, scaled if scaled >= 0 else (65536 + scaled)))
        return 0

    @classmethod
    def register_to_signal(cls, signal_name: str, raw_register: int, original_type: str = "FLOAT") -> Any:
        """Decode a 16-bit unsigned Modbus register integer back to native Python value."""
        if original_type == "BOOL":
            return bool(raw_register != 0)
        elif original_type == "INT":
            return int(raw_register)
        elif original_type == "STRING" or original_type == "ENUM":
            code_states = {
                0: "OFF", 1: "STARTING", 2: "IDLE", 3: "RUNNING",
                4: "WARNING", 5: "FAULT", 6: "MAINTENANCE", 7: "RECOVERY"
            }
            return code_states.get(raw_register, "UNKNOWN")
        else: # FLOAT
            # Handle 16-bit signed conversion if needed
            val = raw_register if raw_register <= 32767 else (raw_register - 65536)
            return round(val * cls.DEFAULT_SCALE, 2)

    @classmethod
    def encode_snapshot_to_registers(cls, profile: MachineProfile, measurements: Dict[str, Any], sequence: int, operating_state: str) -> List[int]:
        """
        Encode snapshot measurements into an ordered list of 16-bit holding registers.
        Register 0: sequence low word
        Register 1: sequence high word
        Register 2: operating state code
        Register 3..N: machine signal measurements in profile order
        """
        registers = [
            sequence & 0xFFFF,
            (sequence >> 16) & 0xFFFF,
            cls.signal_to_register("operating_state", operating_state)
        ]

        for sig_def in profile.signals:
            val = measurements.get(sig_def.name, sig_def.nominal_value)
            reg_val = cls.signal_to_register(sig_def.name, val)
            registers.append(reg_val)

        return registers

    @classmethod
    def decode_registers_to_measurements(cls, profile: MachineProfile, registers: List[int]) -> Tuple[int, str, Dict[str, Any]]:
        """Decode list of 16-bit holding registers back to (sequence, operating_state, measurements)."""
        if len(registers) < 3:
            return 0, "OFF", {}

        seq = (registers[1] << 16) | registers[0]
        op_state = cls.register_to_signal("operating_state", registers[2], original_type="ENUM")

        measurements = {}
        for idx, sig_def in enumerate(profile.signals):
            reg_idx = 3 + idx
            if reg_idx < len(registers):
                raw_val = registers[reg_idx]
                decoded_val = cls.register_to_signal(sig_def.name, raw_val, original_type=sig_def.signal_type.value)
                measurements[sig_def.name] = decoded_val

        return seq, op_state, measurements
