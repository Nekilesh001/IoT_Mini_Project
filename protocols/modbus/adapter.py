"""
Modbus TCP client adapter reading holding registers and returning ProtocolReading objects.
"""

from datetime import datetime, timezone
import logging
from typing import Dict, Optional

from pymodbus.client import ModbusTcpClient

from simulator.core.domain import MachineProfile
from protocols.base import BaseProtocolAdapter
from protocols.models import ProtocolHealth, ProtocolReading, ProtocolType
from protocols.modbus.mapping import ModbusSignalMapper

logger = logging.getLogger(__name__)


class ModbusAdapter(BaseProtocolAdapter):
    """
    Client adapter reading telemetry over Modbus TCP from local server.
    """

    def __init__(self, host: str = "127.0.0.1", port: int = 5020, profiles: Optional[Dict[str, MachineProfile]] = None):
        self._host: str = host
        self._port: int = port
        self._profiles: Dict[str, MachineProfile] = profiles or {}
        self._client: Optional[ModbusTcpClient] = None
        self._is_connected: bool = False
        self._health: ProtocolHealth = ProtocolHealth.DISCONNECTED

    @property
    def protocol_type(self) -> ProtocolType:
        return ProtocolType.MODBUS_TCP

    def register_machine_profile(self, profile: MachineProfile) -> None:
        self._profiles[profile.machine_id] = profile

    def connect(self) -> bool:
        """Connect Modbus TCP client."""
        if self._is_connected and self._client:
            return True

        try:
            self._client = ModbusTcpClient(host=self._host, port=self._port, timeout=2.0)
            self._is_connected = self._client.connect()
            self._health = ProtocolHealth.CONNECTED if self._is_connected else ProtocolHealth.ERROR
            return self._is_connected
        except Exception as e:
            logger.error(f"Modbus adapter failed to connect: {e}")
            self._health = ProtocolHealth.ERROR
            self._is_connected = False
            return False

    def disconnect(self) -> None:
        """Disconnect Modbus TCP client cleanly."""
        if self._client:
            try:
                self._client.close()
            except Exception:
                pass
            self._client = None
        self._is_connected = False
        self._health = ProtocolHealth.DISCONNECTED

    def read_telemetry(self, machine_id: str) -> Optional[ProtocolReading]:
        """
        Read holding registers for machine_id and decode into a ProtocolReading object.
        """
        if not self._is_connected or not self._client:
            if not self.connect():
                return None

        unit_id = ModbusSignalMapper.get_unit_id(machine_id)
        profile = self._profiles.get(machine_id)
        if not profile:
            logger.warning(f"No profile registered for machine '{machine_id}'.")
            return None

        reg_count = len(profile.signals) + 3

        try:
            # Try device_id parameter (pymodbus 3.15+), fallback to slave parameter
            try:
                rr = self._client.read_holding_registers(address=0, count=reg_count, device_id=unit_id)
            except TypeError:
                rr = self._client.read_holding_registers(address=0, count=reg_count, slave=unit_id)

            if rr.isError():
                logger.error(f"Modbus read error for machine '{machine_id}' (unit {unit_id}): {rr}")
                self._health = ProtocolHealth.DEGRADED
                return None

            registers = rr.registers
            seq, op_state, measurements = ModbusSignalMapper.decode_registers_to_measurements(profile, registers)
            measurements["operating_state"] = op_state

            self._health = ProtocolHealth.CONNECTED

            return ProtocolReading(
                machine_id=machine_id,
                machine_type=profile.machine_type.value,
                protocol=ProtocolType.MODBUS_TCP,
                timestamp=datetime.now(timezone.utc).isoformat(),
                sequence=seq,
                measurements=measurements,
                source_address=f"{self._host}:{self._port}/unit={unit_id}",
                raw_payload=registers,
                metadata={"unit_id": unit_id, "register_start": 1, "register_count": reg_count}
            )

        except Exception as e:
            logger.error(f"Modbus adapter exception reading machine '{machine_id}': {e}")
            self._health = ProtocolHealth.ERROR
            return None

    def get_health(self) -> ProtocolHealth:
        return self._health
