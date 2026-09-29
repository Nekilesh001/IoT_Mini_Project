"""
Cloud Fleet Indexing & Registry Interface.
Abstract contract for querying dynamic fleet groups, search indexing, and thing shadows in cloud IoT systems.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from device_management.models import FleetDeviceRecord, FleetSummary


class CloudFleetIndexingInterface(ABC):
    """
    Interface for synchronizing and querying fleet registry data via Cloud IoT Fleet Indexing (e.g. AWS IoT Fleet Indexing).
    """

    @abstractmethod
    def index_thing(self, record: FleetDeviceRecord) -> bool:
        """Register or update a Thing in the cloud registry with attributes and shadow indexing."""
        pass

    @abstractmethod
    def search_things(self, query_string: str) -> List[FleetDeviceRecord]:
        """Execute a structured search query against indexed fleet attributes."""
        pass

    @abstractmethod
    def get_cloud_fleet_summary(self) -> FleetSummary:
        """Retrieve aggregated count and connectivity breakdown from cloud fleet indexing."""
        pass
