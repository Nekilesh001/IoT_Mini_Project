# Phase 12 — Protocol Adapter Failure & Machine Isolation

## Scenario Details
- **Fault Injection**: Protocol adapter for machine `PMP-001` (MQTT/OPC-UA/Modbus) encounters connection failure or malformed frames.
- **Behavior**: Adapter flags `PMP-001` state as `DEGRADED`/`OFFLINE` and enters backoff reconnection loop. Unaffected machines (`CNC-001`, `ROB-001`, `ENV-001`) continue normal publishing.
- **Recovery**: When the adapter reconnects, machine status transitions back to `ONLINE`.
- **Verification Metric**: Zero impact on adjacent factory lines; isolation maintained.
