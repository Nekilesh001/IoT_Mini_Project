"""
Base abstract interfaces for protocol servers/publishers and protocol adapters.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from simulator.core.domain import TelemetrySnapshot
from protocols.models import ProtocolHealth, ProtocolReading, ProtocolType


class BaseProtocolServer(ABC):
    """
    Abstract interface for protocol server/publisher implementations (Modbus, OPC UA, MQTT).
    Exposes simulated machine telemetry state over industrial protocols.
    """

    @property
    @abstractmethod
    def protocol_type(self) -> ProtocolType:
        pass

    @property
    @abstractmethod
    def is_running(self) -> bool:
        pass

    @abstractmethod
    def start(self) -> None:
        """Start the local protocol server / publisher background service."""
        pass

    @abstractmethod
    def stop(self) -> None:
        """Stop the protocol server / publisher cleanly."""
        pass

    @abstractmethod
    def update_from_telemetry(self, snapshot: TelemetrySnapshot) -> None:
        """Update internal server registers/nodes/topics from Phase 1 machine telemetry."""
        pass

    @abstractmethod
    def get_health(self) -> ProtocolHealth:
        """Return operational health status of the protocol server."""
        pass


class BaseProtocolAdapter(ABC):
    """
    Abstract interface for protocol client adapter implementations.
    Reads/receives telemetry from protocol servers/publishers and converts it
    into ProtocolReading objects.
    """

    @property
    @abstractmethod
    def protocol_type(self) -> ProtocolType:
        pass

    @abstractmethod
    def connect(self) -> bool:
        """Connect adapter to protocol server or broker endpoint."""
        pass

    @abstractmethod
    def disconnect(self) -> None:
        """Disconnect adapter cleanly."""
        pass

    @abstractmethod
    def read_telemetry(self, machine_id: str) -> Optional[ProtocolReading]:
        """Read current telemetry for machine_id over the protocol layer."""
        pass

    @abstractmethod
    def get_health(self) -> ProtocolHealth:
        """Return connection health status of the protocol adapter."""
        pass
