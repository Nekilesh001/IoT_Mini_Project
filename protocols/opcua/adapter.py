"""
OPC UA Client Adapter reading node values and returning ProtocolReading objects.
"""

import asyncio
from datetime import datetime, timezone
import logging
from typing import Dict, Optional

from asyncua import Client

from simulator.core.domain import MachineProfile
from protocols.base import BaseProtocolAdapter
from protocols.models import ProtocolHealth, ProtocolReading, ProtocolType
from protocols.opcua.mapping import OPCUAMapper

logger = logging.getLogger(__name__)


class OPCUAAdapter(BaseProtocolAdapter):
    """
    Client adapter reading node values over OPC UA from local server.
    """

    def __init__(self, endpoint: str = "opc.tcp://127.0.0.1:4840/freeopcua/server/", profiles: Optional[Dict[str, MachineProfile]] = None):
        self._endpoint: str = endpoint
        self._profiles: Dict[str, MachineProfile] = profiles or {}
        self._client: Optional[Client] = None
        self._is_connected: bool = False
        self._health: ProtocolHealth = ProtocolHealth.DISCONNECTED
        self._loop: Optional[asyncio.AbstractEventLoop] = None

    @property
    def protocol_type(self) -> ProtocolType:
        return ProtocolType.OPC_UA

    def register_machine_profile(self, profile: MachineProfile) -> None:
        self._profiles[profile.machine_id] = profile

    def connect(self) -> bool:
        """Connect OPC UA client."""
        if self._is_connected:
            return True

        try:
            self._client = Client(url=self._endpoint)
            # Run async connect synchronously
            asyncio.run(self._client.connect())
            self._is_connected = True
            self._health = ProtocolHealth.CONNECTED
            return True
        except Exception as e:
            logger.error(f"OPC UA adapter failed to connect to {self._endpoint}: {e}")
            self._health = ProtocolHealth.ERROR
            self._is_connected = False
            return False

    def disconnect(self) -> None:
        """Disconnect OPC UA client."""
        if self._client and self._is_connected:
            try:
                asyncio.run(self._client.disconnect())
            except Exception:
                pass
            self._client = None
        self._is_connected = False
        self._health = ProtocolHealth.DISCONNECTED

    def read_telemetry(self, machine_id: str) -> Optional[ProtocolReading]:
        """
        Read OPC UA nodes for machine_id and decode into a ProtocolReading object.
        """
        profile = self._profiles.get(machine_id)
        if not profile:
            logger.warning(f"No profile registered for OPC UA machine '{machine_id}'.")
            return None

        async def _async_read():
            client = Client(url=self._endpoint)
            await client.connect()
            try:
                measurements = {}
                seq = 0
                op_state = "RUNNING"

                # Read sequence node
                seq_node_str = f"ns=2;s={OPCUAMapper.get_node_id_string('PLANT_01', 'LINE_A', machine_id, 'sequence')}"
                try:
                    seq_node = client.get_node(seq_node_str)
                    seq = int(await seq_node.read_value())
                except Exception:
                    pass

                # Read operating state node
                st_node_str = f"ns=2;s={OPCUAMapper.get_node_id_string('PLANT_01', 'LINE_A', machine_id, 'operating_state')}"
                try:
                    st_node = client.get_node(st_node_str)
                    op_state = str(await st_node.read_value())
                except Exception:
                    pass

                # Read signal nodes
                for sig_def in profile.signals:
                    node_str = f"ns=2;s={OPCUAMapper.get_node_id_string('PLANT_01', 'LINE_A', machine_id, sig_def.name)}"
                    try:
                        node = client.get_node(node_str)
                        val = await node.read_value()
                        measurements[sig_def.name] = val
                    except Exception as sig_err:
                        logger.debug(f"Could not read OPC UA node {node_str}: {sig_err}")

                measurements["operating_state"] = op_state

                return ProtocolReading(
                    machine_id=machine_id,
                    machine_type=profile.machine_type.value,
                    protocol=ProtocolType.OPC_UA,
                    timestamp=datetime.now(timezone.utc).isoformat(),
                    sequence=seq,
                    measurements=measurements,
                    source_address=f"{self._endpoint}/ns=2;s=Factory/Plant_01/Line_A/{machine_id}",
                    raw_payload=measurements,
                    metadata={"endpoint": self._endpoint, "namespace_index": 2}
                )
            finally:
                await client.disconnect()

        try:
            reading = asyncio.run(_async_read())
            self._health = ProtocolHealth.CONNECTED
            return reading
        except Exception as e:
            logger.error(f"OPC UA adapter read exception for machine '{machine_id}': {e}")
            self._health = ProtocolHealth.ERROR
            return None

    def get_health(self) -> ProtocolHealth:
        return self._health
