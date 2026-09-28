# Phase 1 — Simulation Assumptions & Boundaries

## Core Assumptions

1. **Simulation Timestep**: Default simulation tick frequency is `1.0 second`. Step intervals can be configured deterministically or run in real-time execution mode.
2. **Determinism**: Setting a fixed random seed (`seed=42`) guarantees byte-for-byte reproducible telemetry snapshots across executions.
3. **Offline & Zero-Dependency Execution**: The simulator core executes fully offline using Python standard library primitives. No network interfaces, MQTT brokers, OPC UA servers, Modbus TCP sockets, or AWS infrastructure are required for Phase 1.
4. **Protocol Metadata Isolation**: Protocol enum labels (`OPC_UA`, `MODBUS_TCP`, `MQTT`) are configuration metadata attached to machine profiles for Phase 2 adapter consumption. No protocol network encoding occurs in Phase 1.
5. **Ground-Truth Target Isolation**: Internal wear counters, fault scenario labels, and continuous degradation levels are stored strictly inside internal `SimulationGroundTruth` objects and excluded from public measurement dictionaries.

## Deferred / Future Phase Deliverables

- **Phase 2**: Modbus TCP servers (`PyModbus`), OPC UA servers (`asyncua`), MQTT publishers (`paho-mqtt`), and protocol adapters.
- **Phase 3**: Canonical JSON envelope parsing, edge gateway validation, unit normalization, explicit signal-specific filtering & deduplication.
- **Phase 4**: Local MQTT broker integration (Mosquitto), persistent storage (PostgreSQL/TimescaleDB), store-and-forward buffer.
- **Phase 5**: FastAPI backend endpoints and React dashboard UI.
- **Phase 6**: Systematic fault injection framework & alert rules.
- **Phase 7+**: ML dataset generation, training, and edge ONNX inference models.
