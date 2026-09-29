# Phase 4 — Local MQTT Event Bus & Topic Conventions

## 1. Topic Hierarchy

Phase 4 defines deterministic topic structures for canonical telemetry and status events, isolating them from raw protocol simulation topics used in Phase 2.

### Canonical Telemetry Topic
```
factory/{plant_id}/{line_id}/{machine_id}/telemetry/canonical
```
*Example*: `factory/PLANT_01/LINE_A/CNC-001/telemetry/canonical`

### Wildcard Subscription Patterns
- All machines in factory: `factory/+/+/+/telemetry/canonical`
- Specific line: `factory/PLANT_01/LINE_A/+/telemetry/canonical`

## 2. Canonical Payload Schema

The payload published over MQTT is the JSON-serialized `CanonicalTelemetry` object defined in Phase 3:

```json
{
  "schemaVersion": "1.0.0",
  "eventId": "evt_d74b1a58-34e0-47e0-b45a-5626ee0e6b17",
  "eventType": "TELEMETRY",
  "plantId": "PLANT_01",
  "lineId": "LINE_A",
  "machineId": "CNC-001",
  "machineType": "CNC_MACHINING_CENTER",
  "source": {
    "protocol": "OPC_UA",
    "endpoint": "opc.tcp://127.0.0.1:4840/freeopcua/server/",
    "sourceAddress": "ns=2;s=Factory/Plant_01/Line_A/CNC-001"
  },
  "eventTime": "2026-09-29T04:00:00.000000Z",
  "ingestionTime": "2026-09-29T04:00:00.050000Z",
  "sequence": 42,
  "state": {
    "operating": "RUNNING",
    "health": "HEALTHY"
  },
  "quality": "GOOD",
  "measurements": {
    "spindle_speed_rpm": 9200.0,
    "spindle_load_pct": 68.0,
    "spindle_temperature_c": 44.0,
    "vibration_rms_mm_s": 0.92
  },
  "derived": {
    "estimated_spindle_power_kw": 11.2
  },
  "ml": {}
}
```

## 3. Publisher & Consumer Implementation

- **`CanonicalTelemetryPublisher`**: Handles connecting, publishing with QoS 1, detecting network failures, and routing failed events to `PersistentBuffer`.
- **`CanonicalTelemetryConsumer`**: Subscribes to the canonical hierarchy, parses incoming envelopes, validates schema integrity, and invokes `TelemetryRepository.insert()`.
