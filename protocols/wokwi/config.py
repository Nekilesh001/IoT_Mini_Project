"""
Configuration settings for External Wokwi IoT Device & HiveMQ MQTT Bridge.
"""

import os
from dataclasses import dataclass


@dataclass
class WokwiConfig:
    """Configuration for Wokwi external MQTT bridge."""
    enabled: bool = True
    broker: str = "broker.hivemq.com"
    port: int = 1883
    username: str = ""
    password: str = ""
    telemetry_topic: str = "iot/plant/PLANT_01/line/LINE_A/device/IOT-SENSOR-001/telemetry"
    command_topic: str = "iot/plant/PLANT_01/line/LINE_A/device/IOT-SENSOR-001/commands"
    client_id: str = "smart-factory-wokwi-bridge"
    keepalive: int = 60
    reconnect_delay_seconds: float = 5.0
    device_id: str = "IOT-SENSOR-001"
    device_type: str = "ENVIRONMENT_SENSOR"
    plant_id: str = "PLANT_01"
    line_id: str = "LINE_A"

    @classmethod
    def from_env(cls) -> "WokwiConfig":
        enabled_str = os.getenv("WOKWI_MQTT_ENABLED", "true").strip().lower()
        enabled = enabled_str in ("true", "1", "yes", "on")
        
        return cls(
            enabled=enabled,
            broker=os.getenv("WOKWI_MQTT_BROKER", "broker.hivemq.com"),
            port=int(os.getenv("WOKWI_MQTT_PORT", "1883")),
            username=os.getenv("WOKWI_MQTT_USERNAME", ""),
            password=os.getenv("WOKWI_MQTT_PASSWORD", ""),
            telemetry_topic=os.getenv(
                "WOKWI_MQTT_TELEMETRY_TOPIC",
                "iot/plant/PLANT_01/line/LINE_A/device/IOT-SENSOR-001/telemetry"
            ),
            command_topic=os.getenv(
                "WOKWI_MQTT_COMMAND_TOPIC",
                "iot/plant/PLANT_01/line/LINE_A/device/IOT-SENSOR-001/commands"
            ),
            client_id=os.getenv("WOKWI_MQTT_CLIENT_ID", "smart-factory-wokwi-bridge"),
            keepalive=int(os.getenv("WOKWI_MQTT_KEEPALIVE", "60")),
            reconnect_delay_seconds=float(os.getenv("WOKWI_MQTT_RECONNECT_DELAY", "5.0")),
            device_id=os.getenv("WOKWI_DEVICE_ID", "IOT-SENSOR-001"),
            device_type=os.getenv("WOKWI_DEVICE_TYPE", "ENVIRONMENT_SENSOR"),
            plant_id=os.getenv("WOKWI_PLANT_ID", "PLANT_01"),
            line_id=os.getenv("WOKWI_LINE_ID", "LINE_A"),
        )
