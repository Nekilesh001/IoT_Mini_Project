"""
Modbus TCP Server Manager exposing simulated machine telemetry over local Modbus TCP sockets.
"""

import asyncio
import logging
import threading
import time
from typing import Dict, Optional

from pymodbus.server import ModbusTcpServer
from pymodbus.datastore import ModbusServerContext, ModbusDeviceContext, ModbusSequentialDataBlock

from simulator.core.domain import TelemetrySnapshot, MachineProfile
from protocols.base import BaseProtocolServer
from protocols.models import ProtocolHealth, ProtocolType
from protocols.modbus.mapping import ModbusSignalMapper

logger = logging.getLogger(__name__)


class ModbusServerManager(BaseProtocolServer):
    """
    Manages local Modbus TCP server exposing Modbus-assigned factory machines (CNC-002, CON-001, PRS-001, CMP-001, CHL-001).
    Each machine is mapped to a deterministic Modbus Unit ID (Slave ID).
    Uses the supported PyModbus 3.15 ModbusTcpServer and async_setValues API.
    """

    def __init__(self, host: str = "127.0.0.1", port: int = 5020, profiles: Optional[Dict[str, MachineProfile]] = None):
        self._host: str = host
        self._port: int = port
        self._profiles: Dict[str, MachineProfile] = profiles or {}
        self._slaves: Dict[int, ModbusDeviceContext] = {}
        self._context: Optional[ModbusServerContext] = None
        self._server: Optional[ModbusTcpServer] = None
        self._is_running: bool = False
        self._thread: Optional[threading.Thread] = None
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self._health: ProtocolHealth = ProtocolHealth.DISCONNECTED

        self._initialize_datastore()

    def _initialize_datastore(self) -> None:
        """Initialize slave contexts and data blocks for all Modbus machines."""
        for m_id, unit_id in ModbusSignalMapper.UNIT_ID_MAP.items():
            block = ModbusSequentialDataBlock(1, [0] * 100)
            slave = ModbusDeviceContext(hr=block)
            self._slaves[unit_id] = slave

        self._context = ModbusServerContext(devices=self._slaves, single=False)

    @property
    def protocol_type(self) -> ProtocolType:
        return ProtocolType.MODBUS_TCP

    @property
    def is_running(self) -> bool:
        return self._is_running

    def register_machine_profile(self, profile: MachineProfile) -> None:
        self._profiles[profile.machine_id] = profile

    def start(self) -> None:
        """Start the Modbus TCP server in a dedicated background event loop thread."""
        if self._is_running:
            return

        self._loop = asyncio.new_event_loop()
        self._is_running = True
        self._health = ProtocolHealth.CONNECTED
        server_ready = threading.Event()

        async def _serve():
            try:
                self._server = ModbusTcpServer(context=self._context, address=(self._host, self._port))
                server_ready.set()
                await self._server.serve_forever()
            except Exception as e:
                logger.error(f"Modbus TCP Server runtime error: {e}")
                self._health = ProtocolHealth.ERROR
                server_ready.set()

        def _run_server():
            asyncio.set_event_loop(self._loop)
            try:
                self._loop.run_until_complete(_serve())
            except Exception as e:
                logger.error(f"Modbus TCP Server loop exception: {e}")
                self._health = ProtocolHealth.ERROR

        self._thread = threading.Thread(target=_run_server, daemon=True)
        self._thread.start()
        server_ready.wait(timeout=3.0)
        time.sleep(0.1)

    def stop(self) -> None:
        """Stop the Modbus TCP server cleanly."""
        if not self._is_running:
            return

        self._is_running = False
        self._health = ProtocolHealth.DISCONNECTED

        if self._server and self._loop and self._loop.is_running():
            try:
                future = asyncio.run_coroutine_threadsafe(self._server.shutdown(), self._loop)
                future.result(timeout=2.0)
            except Exception as e:
                logger.debug(f"Modbus server shutdown exception: {e}")

        if self._loop and self._loop.is_running():
            self._loop.call_soon_threadsafe(self._loop.stop)

        if self._thread:
            self._thread.join(timeout=2.0)
            self._thread = None
        self._server = None

    def update_from_telemetry(self, snapshot: TelemetrySnapshot) -> None:
        """
        Update holding registers for machine_id based on snapshot measurements
        using the supported PyModbus async_setValues API scheduled on the server loop.
        """
        machine_id = snapshot.machine_id
        if machine_id not in ModbusSignalMapper.UNIT_ID_MAP:
            return

        unit_id = ModbusSignalMapper.get_unit_id(machine_id)
        profile = self._profiles.get(machine_id)
        if not profile:
            return

        registers = ModbusSignalMapper.encode_snapshot_to_registers(
            profile=profile,
            measurements=snapshot.public_measurements,
            sequence=snapshot.sequence,
            operating_state=snapshot.operating_state
        )

        if self._server and hasattr(self._server, "context") and self._loop and self._loop.is_running():
            try:
                # func_code 3 = Holding Registers, start address 0
                future = asyncio.run_coroutine_threadsafe(
                    self._server.context.async_setValues(unit_id, 3, 0, registers),
                    self._loop
                )
                future.result(timeout=2.0)
            except Exception as e:
                logger.error(f"Failed to update Modbus registers for machine {machine_id}: {e}")
                self._health = ProtocolHealth.DEGRADED

    def get_health(self) -> ProtocolHealth:
        return self._health
