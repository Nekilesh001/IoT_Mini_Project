"""
Domain models and signal definitions for external IoT devices.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional
from simulator.core.domain import (
    MachineProfile,
    MachineType,
    ProtocolMetadata,
    SignalDefinition,
    SignalType,
)


class DeviceClass(str, Enum):
    INDUSTRIAL_MACHINE = "INDUSTRIAL_MACHINE"
    EXTERNAL_IOT = "EXTERNAL_IOT"


class ExternalDeviceType(str, Enum):
    ENVIRONMENT_SENSOR = "ENVIRONMENT_SENSOR"


@dataclass
class ExternalDeviceProfile:
    """
    Profile definition for an external IoT device (e.g. Raspberry Pi Pico W + DHT22).
    Completely decoupled from the 12 industrial factory machines.
    """
    device_id: str = "IOT-SENSOR-001"
    device_type: str = "ENVIRONMENT_SENSOR"
    device_class: DeviceClass = DeviceClass.EXTERNAL_IOT
    plant_id: str = "PLANT_01"
    line_id: str = "LINE_A"
    description: str = "External Raspberry Pi Pico W with DHT22 Environmental Sensor"
    protocol: str = "MQTT"
    ingress_broker: str = "broker.hivemq.com"
    telemetry_topic: str = "iot/plant/PLANT_01/line/LINE_A/device/IOT-SENSOR-001/telemetry"
    command_topic: str = "iot/plant/PLANT_01/line/LINE_A/device/IOT-SENSOR-001/commands"
    firmware_version: str = "0.1.0"
    hardware: str = "Raspberry Pi Pico W + DHT22 + Status LED"
    signals: List[SignalDefinition] = field(default_factory=lambda: [
        SignalDefinition(
            name="temperature_c",
            unit="°C",
            signal_type=SignalType.FLOAT,
            min_value=-40.0,
            max_value=80.0,
            nominal_value=25.0,
            description="Ambient temperature reading from DHT22",
        ),
        SignalDefinition(
            name="humidity_pct",
            unit="%",
            signal_type=SignalType.FLOAT,
            min_value=0.0,
            max_value=100.0,
            nominal_value=50.0,
            description="Relative humidity reading from DHT22",
        ),
    ])

    def to_machine_profile(self) -> MachineProfile:
        """
        Produce a compatible MachineProfile adapter representation for the Edge Ingestion Service.
        Preserves signals and validation bounds without altering factory machines.
        """
        # Create a dynamic MachineProfile with device_type as value
        return MachineProfile(
            machine_id=self.device_id,
            machine_type=self.device_type,  # type: ignore[arg-type]
            protocol_metadata=ProtocolMetadata.MQTT,
            plant_id=self.plant_id,
            line_id=self.line_id,
            description=self.description,
            nominal_load=0.0,
            signals=self.signals,
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "deviceId": self.device_id,
            "deviceType": self.device_type,
            "deviceClass": self.device_class.value,
            "plantId": self.plant_id,
            "lineId": self.line_id,
            "description": self.description,
            "protocol": self.protocol,
            "ingressBroker": self.ingress_broker,
            "telemetryTopic": self.telemetry_topic,
            "commandTopic": self.command_topic,
            "firmwareVersion": self.firmware_version,
            "hardware": self.hardware,
            "signals": [
                {
                    "name": s.name,
                    "unit": s.unit,
                    "type": s.signal_type.value,
                    "min": s.min_value,
                    "max": s.max_value,
                    "nominal": s.nominal_value,
                    "description": s.description,
                }
                for s in self.signals
            ],
        }
