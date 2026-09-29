"""
AWS IoT Device Shadow Adapter Scaffolding.
Placeholder implementation of CloudDeviceStateInterface for future AWS IoT Shadow synchronization.
Currently disabled (local-first mode).
"""

import logging
from typing import Any, Dict, Optional
from cloud.interfaces.device_state import CloudDeviceStateInterface
from cloud.aws.config import AWSConfig
from device_management.models import DeviceShadowRecord

logger = logging.getLogger("cloud.aws.device_shadow")


class AWSIoTDeviceShadowAdapter(CloudDeviceStateInterface):
    """
    Scaffold adapter for future AWS IoT Device Shadow synchronization.
    Planned Responsibility:
      - Map local DeviceShadowState to AWS IoT Thing Shadow JSON document format ($aws/things/{thingName}/shadow/update).
      - Subscribe to $aws/things/{thingName}/shadow/update/delta for incoming cloud-desired configuration.
      - Publish reported state changes upon local confirmation.
    """

    def __init__(self, config: Optional[AWSConfig] = None):
        self.config = config or AWSConfig()

    @property
    def is_enabled(self) -> bool:
        return self.config.enabled

    def get_shadow(self, thing_name: str) -> Optional[DeviceShadowRecord]:
        if not self.config.enabled:
            logger.debug(f"[Scaffold] get_shadow for '{thing_name}' returning None (AWS disabled).")
            return None
        raise NotImplementedError("AWS IoT Device Shadow API call is not active in local-first mode.")

    def update_desired_state(
        self,
        thing_name: str,
        desired_state: Dict[str, Any],
        client_token: Optional[str] = None,
    ) -> DeviceShadowRecord:
        if not self.config.enabled:
            logger.debug(f"[Scaffold] update_desired_state for '{thing_name}' ignored (AWS disabled).")
            return DeviceShadowRecord(device_id=thing_name, desired_state=desired_state)
        raise NotImplementedError("AWS IoT Device Shadow API call is not active in local-first mode.")

    def update_reported_state(
        self,
        thing_name: str,
        reported_state: Dict[str, Any],
        client_token: Optional[str] = None,
    ) -> DeviceShadowRecord:
        if not self.config.enabled:
            logger.debug(f"[Scaffold] update_reported_state for '{thing_name}' ignored (AWS disabled).")
            return DeviceShadowRecord(device_id=thing_name, reported_state=reported_state)
        raise NotImplementedError("AWS IoT Device Shadow API call is not active in local-first mode.")

    def delete_shadow(self, thing_name: str) -> bool:
        if not self.config.enabled:
            return False
        raise NotImplementedError("AWS IoT Device Shadow API call is not active in local-first mode.")
