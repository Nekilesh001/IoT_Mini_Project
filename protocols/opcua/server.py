"""
OPC UA Server Manager exposing simulated machine nodes over local OPC UA TCP endpoint.
"""

import asyncio
import logging
import threading
import time
from typing import Dict, Optional

from asyncua import Server, ua

from simulator.core.domain import TelemetrySnapshot, MachineProfile
from protocols.base import BaseProtocolServer
from protocols.models import ProtocolHealth, ProtocolType
from protocols.opcua.mapping import OPCUAMapper

logger = logging.getLogger(__name__)


class OPCUAServerManager(BaseProtocolServer):
    """
    Manages local OPC UA server exposing OPC UA-assigned machines (CNC-001, ROB-001, IMM-001, VIS-001).
    Nodes are structured under Factory / Plant_01 / Line_A / {machine_id}.
    """

    def __init__(self, endpoint: str = "opc.tcp://127.0.0.1:4840/freeopcua/server/", profiles: Optional[Dict[str, MachineProfile]] = None):
        self._endpoint: str = endpoint
        self._profiles: Dict[str, MachineProfile] = profiles or {}
        self._server: Optional[Server] = None
        self._is_running: bool = False
        self._thread: Optional[threading.Thread] = None
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self._health: ProtocolHealth = ProtocolHealth.DISCONNECTED
        self._namespace_idx: int = 2
        # machine_id -> (signal_name -> Node)
        self._node_map: Dict[str, Dict[str, Any]] = {}

    @property
    def protocol_type(self) -> ProtocolType:
        return ProtocolType.OPC_UA

    @property
    def is_running(self) -> bool:
        return self._is_running

    def register_machine_profile(self, profile: MachineProfile) -> None:
        self._profiles[profile.machine_id] = profile

    def start(self) -> None:
        """Start the OPC UA server in a background event loop thread."""
        if self._is_running:
            return

        self._loop = asyncio.new_event_loop()
        self._is_running = True
        self._health = ProtocolHealth.CONNECTED

        def _run():
            asyncio.set_event_loop(self._loop)
            async def _init_and_start():
                self._server = Server()
                await self._server.init()
                self._server.set_endpoint(self._endpoint)
                self._namespace_idx = await self._server.register_namespace(OPCUAMapper.NAMESPACE_URI)
                await self._setup_node_hierarchy()
                await self._server.start()

            self._loop.run_until_complete(_init_and_start())
            self._loop.run_forever()

        self._thread = threading.Thread(target=_run, daemon=True)
        self._thread.start()
        time.sleep(1.0)  # Allow OPC UA server startup time

    async def _setup_node_hierarchy(self) -> None:
        """Build deterministic OPC UA node hierarchy for registered OPC UA machines."""
        if not self._server:
            return

        objects = self._server.nodes.objects
        # Create folder hierarchy
        factory_folder = await objects.add_folder(self._namespace_idx, "Factory")
        plant_folder = await factory_folder.add_folder(self._namespace_idx, "Plant_01")
        line_folder = await plant_folder.add_folder(self._namespace_idx, "Line_A")

        for m_id, profile in self._profiles.items():
            if profile.protocol_metadata.value != "OPC_UA":
                continue

            m_folder = await line_folder.add_folder(self._namespace_idx, m_id)
            self._node_map[m_id] = {}

            # Add sequence node
            seq_id = ua.NodeId(OPCUAMapper.get_node_id_string("PLANT_01", "LINE_A", m_id, "sequence"), self._namespace_idx)
            seq_node = await m_folder.add_variable(seq_id, "sequence", 0, ua.VariantType.Int64)
            self._node_map[m_id]["sequence"] = seq_node

            # Add operating_state node
            st_id = ua.NodeId(OPCUAMapper.get_node_id_string("PLANT_01", "LINE_A", m_id, "operating_state"), self._namespace_idx)
            st_node = await m_folder.add_variable(st_id, "operating_state", "OFF", ua.VariantType.String)
            self._node_map[m_id]["operating_state"] = st_node

            # Add signal nodes from profile catalog
            for sig_def in profile.signals:
                n_id_str = OPCUAMapper.get_node_id_string("PLANT_01", "LINE_A", m_id, sig_def.name)
                n_id = ua.NodeId(n_id_str, self._namespace_idx)
                v_type = OPCUAMapper.get_variant_type(sig_def.signal_type)
                init_val = OPCUAMapper.cast_to_variant_val(sig_def.nominal_value, sig_def.signal_type)
                node = await m_folder.add_variable(n_id, sig_def.name, init_val, v_type)
                self._node_map[m_id][sig_def.name] = node

    def update_from_telemetry(self, snapshot: TelemetrySnapshot) -> None:
        """Update OPC UA node values for machine_id synchronously across loop."""
        if not self._is_running or not self._loop or snapshot.machine_id not in self._node_map:
            return

        async def _async_update():
            nodes = self._node_map[snapshot.machine_id]
            profile = self._profiles.get(snapshot.machine_id)
            if not profile:
                return

            tasks = []
            if "sequence" in nodes:
                tasks.append(nodes["sequence"].write_value(int(snapshot.sequence)))
            if "operating_state" in nodes:
                tasks.append(nodes["operating_state"].write_value(str(snapshot.operating_state)))

            for sig_def in profile.signals:
                if sig_def.name in nodes and sig_def.name in snapshot.public_measurements:
                    val = snapshot.public_measurements[sig_def.name]
                    v_val = OPCUAMapper.cast_to_variant_val(val, sig_def.signal_type)
                    tasks.append(nodes[sig_def.name].write_value(v_val))

            if tasks:
                await asyncio.gather(*tasks)

        future = asyncio.run_coroutine_threadsafe(_async_update(), self._loop)
        try:
            future.result(timeout=2.0)
        except Exception as e:
            logger.error(f"Error updating OPC UA node values: {e}")

    def stop(self) -> None:
        """Stop the OPC UA server cleanly."""
        if not self._is_running:
            return

        self._is_running = False
        self._health = ProtocolHealth.DISCONNECTED

        if self._loop and self._server:
            async def _async_stop():
                try:
                    await self._server.stop()
                except Exception:
                    pass
                self._loop.stop()

            asyncio.run_coroutine_threadsafe(_async_stop(), self._loop)

        if self._thread:
            self._thread.join(timeout=2.0)
            self._thread = None

    def get_health(self) -> ProtocolHealth:
        return self._health
