"""
Cloud Device State (Shadow) Interface.
Abstract contract for synchronizing device desired and reported twins with cloud IoT brokers.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
from device_management.models import DeviceShadowRecord


class CloudDeviceStateInterface(ABC):
    """
    Interface for synchronizing local DeviceShadow state with a cloud Device Shadow service (e.g., AWS IoT Device Shadow).
    """

    @abstractmethod
    def get_shadow(self, thing_name: str) -> Optional[DeviceShadowRecord]:
        """Fetch the latest shadow document from cloud IoT."""
        pass

    @abstractmethod
    def update_desired_state(
        self,
        thing_name: str,
        desired_state: Dict[str, Any],
        client_token: Optional[str] = None,
    ) -> DeviceShadowRecord:
        """Publish updated desired state document to cloud shadow topic."""
        pass

    @abstractmethod
    def update_reported_state(
        self,
        thing_name: str,
        reported_state: Dict[str, Any],
        client_token: Optional[str] = None,
    ) -> DeviceShadowRecord:
        """Publish updated reported state document to cloud shadow topic."""
        pass

    @abstractmethod
    def delete_shadow(self, thing_name: str) -> bool:
        """Delete device shadow document."""
        pass
