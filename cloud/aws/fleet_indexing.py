"""
AWS IoT Fleet Indexing Adapter Scaffolding.
Placeholder implementation of CloudFleetIndexingInterface for future AWS Fleet Indexing queries.
Currently disabled (local-first mode).
"""

import logging
from typing import Any, Dict, List, Optional
from cloud.interfaces.fleet import CloudFleetIndexingInterface
from cloud.aws.config import AWSConfig
from device_management.models import FleetDeviceRecord, FleetSummary

logger = logging.getLogger("cloud.aws.fleet_indexing")


class AWSIoTFleetIndexingAdapter(CloudFleetIndexingInterface):
    """
    Scaffold adapter for future AWS IoT Fleet Indexing integration.
    Planned Responsibility:
      - Synchronize Thing attributes and shadow state into AWS Fleet Indexing.
      - Support rich search queries (e.g., 'attributes.protocol:MODBUS_TCP AND shadow.reported.operating_mode:AUTO').
      - Provide real-time aggregate fleet health and connectivity metrics from AWS.
    """

    def __init__(self, config: Optional[AWSConfig] = None):
        self.config = config or AWSConfig()

    @property
    def is_enabled(self) -> bool:
        return self.config.enabled

    def index_thing(self, record: FleetDeviceRecord) -> bool:
        if not self.config.enabled:
            logger.debug(f"[Scaffold] index_thing for '{record.machine_id}' ignored (AWS disabled).")
            return True
        raise NotImplementedError("AWS IoT Fleet Indexing is not active in local-first mode.")

    def search_things(self, query_string: str) -> List[FleetDeviceRecord]:
        if not self.config.enabled:
            logger.debug(f"[Scaffold] search_things with query '{query_string}' returning empty list (AWS disabled).")
            return []
        raise NotImplementedError("AWS IoT Fleet Indexing is not active in local-first mode.")

    def get_cloud_fleet_summary(self) -> FleetSummary:
        if not self.config.enabled:
            return FleetSummary()
        raise NotImplementedError("AWS IoT Fleet Indexing is not active in local-first mode.")
