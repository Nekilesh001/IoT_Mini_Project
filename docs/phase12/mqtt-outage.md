# Phase 12 — MQTT Event Bus Outage & Recovery

## Scenario Details
- **Fault Injection**: Local MQTT broker connection is dropped or simulated connection errors are injected.
- **Behavior**: Telemetry generator diverts events to `PersistentBuffer` (SQLite). No unhandled exceptions crash the process.
- **Recovery**: Once broker connectivity is restored, the buffered events are published in sequence order and marked delivered.
- **Verification Metric**: 100% of generated messages delivered; 0 duplicate messages; detection latency < 10ms.
