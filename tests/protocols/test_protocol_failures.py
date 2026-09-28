"""
Unit tests for protocol-level failure handling, disconnected server reads, and malformed payload rejection.
"""

from simulator.runtime.factory_runtime import FactorySimulator
from protocols.modbus.adapter import ModbusAdapter
from protocols.opcua.adapter import OPCUAAdapter
from protocols.mqtt.adapter import MQTTAdapter


def test_modbus_adapter_read_disconnected_returns_none():
    adapter = ModbusAdapter(host="127.0.0.1", port=5999)  # Non-existent port
    reading = adapter.read_telemetry("CNC-002")
    assert reading is None, "Reading from unavailable Modbus server should return None."


def test_opcua_adapter_read_disconnected_returns_none():
    adapter = OPCUAAdapter(endpoint="opc.tcp://127.0.0.1:4999/nonexistent/")
    reading = adapter.read_telemetry("CNC-001")
    assert reading is None, "Reading from unavailable OPC UA server should return None."


def test_mqtt_adapter_rejects_malformed_payload():
    adapter = MQTTAdapter()
    adapter.connect()

    # Dispatch malformed non-JSON payload
    adapter._on_message("factory/PLANT_01/LINE_A/ROB-002/telemetry", b"NOT_VALID_JSON{{{", qos=1)

    reading = adapter.read_telemetry("ROB-002")
    assert reading is None, "Adapter must reject malformed non-JSON MQTT payload."
