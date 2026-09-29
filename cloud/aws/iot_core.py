"""
AWS IoT Core Adapter Scaffolding.
Placeholder implementation for MQTT transport bridging over TLS with AWS IoT Core.
Currently disabled (local-first mode).
"""

import logging
from typing import Any, Callable, Dict, Optional
from cloud.aws.config import AWSConfig

logger = logging.getLogger("cloud.aws.iot_core")


class AWSIoTCoreAdapter:
    """
    Scaffold adapter for future AWS IoT Core MQTT connectivity.
    Planned Responsibility:
      - Establish mTLS connection with AWS IoT Core endpoint.
      - Route canonical telemetry and state deltas to AWS IoT MQTT topics ($aws/things/.../shadow/...).
      - Handle cloud disconnects and offline store-and-forward buffering.
    """

    def __init__(self, config: Optional[AWSConfig] = None):
        self.config = config or AWSConfig()
        self._is_connected: bool = False

    @property
    def is_enabled(self) -> bool:
        return self.config.enabled

    @property
    def is_connected(self) -> bool:
        return self._is_connected

    def connect(self) -> bool:
        if not self.config.enabled:
            logger.info("AWS IoT Core adapter is disabled (local-first mode active). No connection attempted.")
            return False
        raise NotImplementedError("Live AWS IoT Core integration is planned for a future phase.")

    def disconnect(self) -> None:
        self._is_connected = False

    def publish_telemetry(self, topic: str, payload: Dict[str, Any], qos: int = 1) -> bool:
        if not self.config.enabled:
            logger.debug(f"[Scaffold] Telemetry publish ignored for topic '{topic}' (AWS disabled).")
            return False
        raise NotImplementedError("Live AWS IoT Core publishing is not configured.")

    def subscribe(self, topic: str, callback: Callable[[str, Dict[str, Any]], None], qos: int = 1) -> bool:
        if not self.config.enabled:
            logger.debug(f"[Scaffold] Subscription ignored for topic '{topic}' (AWS disabled).")
            return False
        raise NotImplementedError("Live AWS IoT Core subscription is not configured.")
