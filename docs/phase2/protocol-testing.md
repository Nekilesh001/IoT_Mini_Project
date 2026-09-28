# Phase 2: Protocol Testing Strategy

## 1. Test Suite Structure

Phase 2 includes 18 automated tests located in `tests/protocols/`:

1. `test_protocol_registry.py`: Verifies protocol assignments and metadata loading for all 12 factory machines.
2. `test_modbus_mapping.py`: Validates deterministic Unit IDs, float scaling, and 16-bit register round-trip encoding/decoding.
3. `test_modbus_adapter.py`: Validates Modbus TCP server startup, live client adapter reads across sequence 1 and sequence 2 ticks.
4. `test_opcua_mapping.py`: Validates deterministic node IDs and OPC UA data type casting.
5. `test_opcua_adapter.py`: Validates OPC UA server startup, node creation, and client reading over OPC UA TCP sockets.
6. `test_mqtt_mapping.py`: Validates deterministic topic generation and JSON serialization.
7. `test_mqtt_adapter.py`: Validates local broker routing, publisher delivery, and adapter reception.
8. `test_protocol_health.py`: Verifies health state transitions (`CONNECTED`, `DISCONNECTED`, `ERROR`).
9. `test_protocol_failures.py`: Verifies error handling when servers are stopped or malformed payloads are received.
10. `test_protocol_integration.py`: End-to-end integration test advancing all 12 machines across all 3 protocols simultaneously.

## 2. Test Execution Command

```bash
# Run all Phase 2 protocol tests
python -m pytest tests/protocols/ -v

# Run entire repository test suite (Phase 1 + Phase 2)
python -m pytest tests/simulator/ tests/protocols/ -v
```

## 3. Offline Independence

All tests run locally using loopback TCP interfaces (`127.0.0.1`) and embedded brokers with zero external network or cloud dependencies.
