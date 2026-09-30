"""
Wokwi External IoT Device & HiveMQ MQTT Bridge Integration.
"""

from protocols.wokwi.config import WokwiConfig
from protocols.wokwi.models import ExternalDeviceProfile, DeviceClass
from protocols.wokwi.registry import ExternalDeviceRegistry, get_external_device_registry
from protocols.wokwi.normalizer import WokwiPayloadNormalizer
from protocols.wokwi.bridge import WokwiMQTTBridge

__all__ = [
    "WokwiConfig",
    "ExternalDeviceProfile",
    "DeviceClass",
    "ExternalDeviceRegistry",
    "get_external_device_registry",
    "WokwiPayloadNormalizer",
    "WokwiMQTTBridge",
]
