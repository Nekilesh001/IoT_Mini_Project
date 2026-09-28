# Phase 3: Canonical Telemetry Schema Specification

## 1. JSON Envelope

The canonical schema represents a normalized, protocol-agnostic industrial telemetry payload:

```json
{
  "schemaVersion": "1.0.0",
  "eventId": "evt_984f1a2b-3c4d-4e5f-a6b7-8c9d0e1f2a3b",
  "eventType": "TELEMETRY",
  "plantId": "PLANT_01",
  "lineId": "LINE_A",
  "machineId": "CNC-001",
  "machineType": "CNC_MACHINING_CENTER",
  "source": {
    "protocol": "OPC_UA",
    "endpoint": "opc.tcp://127.0.0.1:4840",
    "sourceAddress": "ns=2;s=Factory/Plant_01/Line_A/CNC-001"
  },
  "eventTime": "2026-09-28T14:00:00.123Z",
  "ingestionTime": "2026-09-28T14:00:00.145Z",
  "sequence": 142058,
  "state": {
    "operating": "RUNNING",
    "health": "HEALTHY"
  },
  "quality": "GOOD",
  "measurements": {
    "spindle_speed_rpm": 9013.94,
    "spindle_load_pct": 73.58,
    "spindle_temperature_c": 46.85
  },
  "derived": {
    "estimated_spindle_power_kw": 11.04
  },
  "ml": {}
}
```

## 2. Mandatory Fields

- `schemaVersion`: Semantic contract version (default `1.0.0`).
- `eventId`: Stable unique event identifier (`evt_<uuid>`).
- `eventType`: Event category (`TELEMETRY`, `STATUS`, `FAULT`, `ALERT`, etc.).
- `plantId` & `lineId`: Hierarchical factory location.
- `machineId` & `machineType`: Distinct machine identifier and class.
- `source`: Provenance metadata (`protocol`, `endpoint`, `sourceAddress`).
- `eventTime`: Origin timestamp (UTC).
- `ingestionTime`: Edge pipeline processing timestamp (UTC).
- `sequence`: Per-machine monotonically increasing counter.
- `state`: Current operating and health classification.
- `quality`: Aggregate telemetry quality code.
- `measurements`: Key-value physical measurements catalog.
- `derived`: Calculated edge-side engineering metrics.
- `ml`: Machine learning metadata placeholder (for Phase 8).
