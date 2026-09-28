# Phase 2: Protocol Architecture & Decoupling Model

## 1. Overview

Phase 2 implements the protocol simulation and adapter layer for the 12-machine Smart Factory. It provides protocol-specific servers and publishers for **Modbus TCP**, **OPC UA**, and **MQTT**, alongside client adapters that read/subscribe to values and output normalized `ProtocolReading` data structures.

```
+-------------------------------------------------------------------------+
|                  Phase 1: Machine Behaviour Core                       |
|   - Physics simulation, deterministic step execution, telemetry         |
|   - Zero knowledge of protocols or network communication                |
+-------------------------------------------------------------------------+
                                    |
                                    v (TelemetrySnapshot)
+-------------------------------------------------------------------------+
|                  Phase 2: Protocol Mapping & Servers                    |
|   - Modbus TCP Server (Unit IDs, holding registers, 16-bit encoding)    |
|   - OPC UA Server (Deterministic Node hierarchy, typed variants)        |
|   - MQTT Publisher (Deterministic topics, JSON payloads, local broker)  |
+-------------------------------------------------------------------------+
                                    |
                                    v (Network Sockets / TCP / PubSub)
+-------------------------------------------------------------------------+
|                  Phase 2: Protocol Client Adapters                      |
|   - Modbus Adapter (Read holding registers, decode engineering values)  |
|   - OPC UA Adapter (Read variable nodes, cast native types)             |
|   - MQTT Adapter (Subscribe to topics, parse payloads, track sequence)  |
+-------------------------------------------------------------------------+
                                    |
                                    v (ProtocolReading)
+-------------------------------------------------------------------------+
|             Phase 3: Canonical Ingestion Pipeline (Deferred)            |
|   - Canonical telemetry envelope, validation, normalization, storage    |
+-------------------------------------------------------------------------+
```

## 2. Decoupling Principle

1. **Simulator Independence**: The Phase 1 simulation core (`simulator/`) contains zero protocol imports (`pymodbus`, `asyncua`, `paho.mqtt`). It executes completely independently offline.
2. **One-Way Data Flow**: The protocol layer consumes `TelemetrySnapshot` instances produced by the simulator and translates them into protocol representations.
3. **Protocol Reading Abstraction**: Adapters yield intermediate `ProtocolReading` models containing protocol identity, source addresses, raw payloads, and decoded measurements.
