"""
Factory Protocol Manager coordinating protocol servers, publishers, and client adapters for all 12 machines.
"""

import logging
from typing import Dict, List, Optional

from simulator.core.domain import TelemetrySnapshot, MachineProfile
from simulator.runtime.factory_runtime import FactorySimulator
from protocols.base import BaseProtocolAdapter, BaseProtocolServer
from protocols.models import ProtocolHealth, ProtocolReading, ProtocolType
from protocols.modbus.server import ModbusServerManager
from protocols.modbus.adapter import ModbusAdapter
from protocols.opcua.server import OPCUAServerManager
from protocols.opcua.adapter import OPCUAAdapter
from protocols.mqtt.publisher import MQTTPublisherManager
from protocols.mqtt.adapter import MQTTAdapter

logger = logging.getLogger(__name__)


class FactoryProtocolManager:
    """
    Coordinates protocol servers, publishers, and adapters across Modbus TCP, OPC UA, and MQTT.
    Does NOT modify machine physics or simulation logic.
    """

    def __init__(self, modbus_port: int = 5020, opcua_port: int = 4840, mqtt_port: int = 1883):
        self._modbus_port: int = modbus_port
        self._opcua_port: int = opcua_port
        self._mqtt_port: int = mqtt_port

        self._modbus_server = ModbusServerManager(port=modbus_port)
        self._modbus_adapter = ModbusAdapter(port=modbus_port)

        self._opcua_server = OPCUAServerManager(endpoint=f"opc.tcp://127.0.0.1:{opcua_port}/freeopcua/server/")
        self._opcua_adapter = OPCUAAdapter(endpoint=f"opc.tcp://127.0.0.1:{opcua_port}/freeopcua/server/")

        self._mqtt_publisher = MQTTPublisherManager(port=mqtt_port)
        self._mqtt_adapter = MQTTAdapter(port=mqtt_port)

        self._profiles: Dict[str, MachineProfile] = {}
        self._is_running: bool = False

    def register_simulator(self, simulator: FactorySimulator) -> None:
        """Register machine profiles from FactorySimulator instance."""
        for machine in simulator.get_all_machines():
            profile = machine.profile
            self._profiles[profile.machine_id] = profile
            proto = profile.protocol_metadata

            if proto == ProtocolType.MODBUS_TCP:
                self._modbus_server.register_machine_profile(profile)
                self._modbus_adapter.register_machine_profile(profile)
            elif proto == ProtocolType.OPC_UA:
                self._opcua_server.register_machine_profile(profile)
                self._opcua_adapter.register_machine_profile(profile)
            elif proto == ProtocolType.MQTT:
                self._mqtt_publisher.register_machine_profile(profile)
                self._mqtt_adapter.register_machine_profile(profile)

    def start_all(self) -> None:
        """Start all protocol servers, publishers, and adapters."""
        if self._is_running:
            return

        logger.info("Starting Modbus TCP server...")
        self._modbus_server.start()
        self._modbus_adapter.connect()

        logger.info("Starting OPC UA server...")
        self._opcua_server.start()
        self._opcua_adapter.connect()

        logger.info("Starting MQTT publisher & adapter...")
        self._mqtt_publisher.start()
        self._mqtt_adapter.connect()

        self._is_running = True

    def stop_all(self) -> None:
        """Stop all protocol servers, publishers, and adapters cleanly."""
        if not self._is_running:
            return

        logger.info("Stopping protocol adapters and servers...")
        self._modbus_adapter.disconnect()
        self._modbus_server.stop()

        self._opcua_adapter.disconnect()
        self._opcua_server.stop()

        self._mqtt_adapter.disconnect()
        self._mqtt_publisher.stop()

        self._is_running = False

    def update_from_simulator(self, snapshots: List[TelemetrySnapshot]) -> None:
        """
        Update protocol servers with new machine telemetry snapshots from simulator.
        """
        for snap in snapshots:
            proto = snap.protocol_metadata
            if proto == "MODBUS_TCP":
                self._modbus_server.update_from_telemetry(snap)
            elif proto == "OPC_UA":
                self._opcua_server.update_from_telemetry(snap)
            elif proto == "MQTT":
                self._mqtt_publisher.update_from_telemetry(snap)

    def read_all_adapters(self) -> List[ProtocolReading]:
        """
        Read telemetry from all 12 machines through their respective protocol adapters.
        """
        readings = []
        for m_id, profile in self._profiles.items():
            proto = profile.protocol_metadata
            reading = None
            if proto == ProtocolType.MODBUS_TCP:
                reading = self._modbus_adapter.read_telemetry(m_id)
            elif proto == ProtocolType.OPC_UA:
                reading = self._opcua_adapter.read_telemetry(m_id)
            elif proto == ProtocolType.MQTT:
                reading = self._mqtt_adapter.read_telemetry(m_id)

            if reading:
                readings.append(reading)
        return readings

    def get_health_status(self) -> Dict[str, str]:
        """Return protocol health status for servers and adapters."""
        return {
            "modbus_server": self._modbus_server.get_health().value,
            "modbus_adapter": self._modbus_adapter.get_health().value,
            "opcua_server": self._opcua_server.get_health().value,
            "opcua_adapter": self._opcua_adapter.get_health().value,
            "mqtt_publisher": self._mqtt_publisher.get_health().value,
            "mqtt_adapter": self._mqtt_adapter.get_health().value,
        }
