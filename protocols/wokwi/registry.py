"""
Registry for External IoT Devices (distinct from the 12 Factory Machines).
"""

from typing import Any, Dict, List, Optional
from protocols.wokwi.models import ExternalDeviceProfile, DeviceClass


class ExternalDeviceRegistry:
    """
    In-memory catalog and registry for external IoT devices.
    Ensures clear separation between industrial machines and external edge sensors.
    """

    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(ExternalDeviceRegistry, cls).__new__(cls)
            cls._instance._devices = {}
            cls._instance._initialize_defaults()
        return cls._instance

    def _initialize_defaults(self) -> None:
        """Register the default Wokwi Environmental Sensor IOT-SENSOR-001."""
        default_sensor = ExternalDeviceProfile(
            device_id="IOT-SENSOR-001",
            device_type="ENVIRONMENT_SENSOR",
            device_class=DeviceClass.EXTERNAL_IOT,
            plant_id="PLANT_01",
            line_id="LINE_A",
            description="External Wokwi Raspberry Pi Pico W Environment Sensor",
            protocol="MQTT",
            ingress_broker="broker.hivemq.com",
            telemetry_topic="iot/plant/PLANT_01/line/LINE_A/device/IOT-SENSOR-001/telemetry",
            command_topic="iot/plant/PLANT_01/line/LINE_A/device/IOT-SENSOR-001/commands",
            firmware_version="0.1.0",
            hardware="Raspberry Pi Pico W + DHT22 + LED",
        )
        self.register_device(default_sensor)

    def register_device(self, profile: ExternalDeviceProfile) -> None:
        self._devices[profile.device_id] = profile

    def get_device(self, device_id: str) -> Optional[ExternalDeviceProfile]:
        return self._devices.get(device_id)

    def list_devices(self) -> List[ExternalDeviceProfile]:
        return list(self._devices.values())

    def get_all_machine_profiles(self) -> Dict[str, Any]:
        """Convert all registered external IoT profiles to edge-compatible MachineProfile objects."""
        return {d_id: p.to_machine_profile() for d_id, p in self._devices.items()}

    def is_external_device(self, device_id: str) -> bool:
        return device_id in self._devices


def get_external_device_registry() -> ExternalDeviceRegistry:
    return ExternalDeviceRegistry()
