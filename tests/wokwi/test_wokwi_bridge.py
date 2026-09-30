"""
Unit tests for Wokwi MQTT Bridge lifecycle and callbacks (mocked network).
"""

from unittest.mock import MagicMock, patch
import json
import pytest

from protocols.models import ProtocolHealth
from protocols.wokwi.config import WokwiConfig
from protocols.wokwi.bridge import WokwiMQTTBridge


def test_bridge_disabled_configuration():
    config = WokwiConfig(enabled=False)
    bridge = WokwiMQTTBridge(config)

    assert bridge.start() is False
    assert bridge.is_running is False
    assert bridge.get_health() == ProtocolHealth.DISCONNECTED


@patch("paho.mqtt.client.Client")
def test_bridge_start_and_connect(mock_client_cls):
    mock_instance = MagicMock()
    mock_client_cls.return_value = mock_instance

    config = WokwiConfig(
        enabled=True,
        broker="test.broker.local",
        port=1883,
        telemetry_topic="iot/plant/PLANT_01/line/LINE_A/device/IOT-SENSOR-001/telemetry",
    )
    bridge = WokwiMQTTBridge(config)
    started = bridge.start()
    assert started is True

    # Simulate connection callback
    bridge._on_connect(mock_instance, None, None, 0)
    assert bridge.get_health() == ProtocolHealth.CONNECTED
    assert bridge.is_connected is True

    # Check status dictionary
    status = bridge.get_status()
    assert status["enabled"] is True
    assert status["connected"] is True
    assert status["broker"] == "test.broker.local"

    # Simulate receiving telemetry message
    msg = MagicMock()
    msg.topic = config.telemetry_topic
    msg.payload = json.dumps({
        "deviceId": "IOT-SENSOR-001",
        "sequence": 1,
        "readings": {"temperatureC": 29.0, "humidityPct": 55.0}
    }).encode("utf-8")

    bridge._on_message(mock_instance, None, msg)
    assert bridge.get_status()["received_count"] == 1

    readings = bridge.pop_all_readings()
    assert len(readings) == 1
    assert readings[0].machine_id == "IOT-SENSOR-001"
    assert readings[0].measurements["temperature_c"] == 29.0

    # Clean up
    bridge.stop()
    assert bridge.get_health() == ProtocolHealth.DISCONNECTED


@patch("paho.mqtt.client.Client")
def test_bridge_reconnect_handling(mock_client_cls):
    mock_instance = MagicMock()
    mock_client_cls.return_value = mock_instance

    config = WokwiConfig(enabled=True)
    bridge = WokwiMQTTBridge(config)
    bridge.start()

    # Connect
    bridge._on_connect(mock_instance, None, None, 0)
    assert bridge.is_connected is True

    # Unexpected Disconnect
    bridge._on_disconnect(mock_instance, None, 1)
    assert bridge.get_health() == ProtocolHealth.DISCONNECTED
    assert bridge.get_status()["reconnect_count"] == 1

    bridge.stop()
