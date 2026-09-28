# Phase 2: MQTT Publisher & Adapter

## 1. Overview

MQTT provides publish/subscribe messaging for distributed edge and mobile factory machines.

## 2. Machine Assignments

MQTT is assigned to:
- `ROB-002` (`WELDING_ROBOT`)
- `PMP-001` (`INDUSTRIAL_PUMP`)
- `AGV-001` (`AUTONOMOUS_MOBILE_ROBOT`)

## 3. Topic Hierarchy

Topic structure follows the deterministic factory hierarchy:

- **Telemetry Topic**: `factory/{plant}/{line}/{machine_id}/telemetry`
- **Status Topic**: `factory/{plant}/{line}/{machine_id}/status`
- **Events Topic**: `factory/{plant}/{line}/{machine_id}/events`

Example: `factory/PLANT_01/LINE_A/ROB-002/telemetry`

## 4. Payload Structure

Raw JSON payload published per telemetry event:

```json
{
  "machine_id": "ROB-002",
  "machine_type": "WELDING_ROBOT",
  "sequence": 142,
  "timestamp": "2026-09-28T12:30:00Z",
  "operating_state": "RUNNING",
  "measurements": {
    "joint_1_temp_c": 46.2,
    "position_error_norm_mm": 0.026
  }
}
```

## 5. Local Broker & Adapter

- **Embedded Local Broker**: `LocalMQTTBroker` provides an in-memory topic routing engine for offline testing without public Internet broker dependencies.
- **Publisher**: `MQTTPublisherManager` encodes snapshots into JSON and publishes with configurable QoS (default QoS 1).
- **Client Adapter**: `MQTTAdapter` subscribes to the machine telemetry topics, parses JSON payloads, validates message identity, and produces `ProtocolReading` instances.
