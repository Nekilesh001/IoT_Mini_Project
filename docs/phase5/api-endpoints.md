# REST API Endpoints Reference — Phase 5

This document defines the HTTP REST contracts for all endpoints implemented in the Phase 5 FastAPI application.

---

## 1. System & Health Endpoints

### `GET /api/health`
Checks backend service availability and database connectivity.

- **Response `200 OK`**:
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "database": "connected",
  "timestamp": "2026-09-29T10:00:00Z"
}
```

### `GET /api/protocols/health`
Provides status, connection state, and active machine counts for each industrial protocol adapter.

- **Response `200 OK`**:
```json
{
  "protocols": [
    {
      "protocol": "MODBUS_TCP",
      "status": "HEALTHY",
      "machineCount": 4,
      "lastEventTime": "2026-09-29T10:00:00Z"
    },
    {
      "protocol": "OPC_UA",
      "status": "HEALTHY",
      "machineCount": 4,
      "lastEventTime": "2026-09-29T10:00:00Z"
    },
    {
      "protocol": "MQTT",
      "status": "HEALTHY",
      "machineCount": 4,
      "lastEventTime": "2026-09-29T10:00:00Z"
    }
  ],
  "totalProtocols": 3,
  "timestamp": "2026-09-29T10:00:00Z"
}
```

---

## 2. Factory Operational Summary

### `GET /api/factory/summary`
Returns factory-wide operational aggregations, machine state breakdowns, protocol distributions, and latest telemetry indicators.

- **Response `200 OK`**:
```json
{
  "totalMachines": 12,
  "runningMachines": 8,
  "idleMachines": 2,
  "warningMachines": 1,
  "faultMachines": 1,
  "maintenanceMachines": 0,
  "offMachines": 0,
  "protocolSummary": {
    "MODBUS_TCP": 4,
    "OPC_UA": 4,
    "MQTT": 4
  },
  "latestTelemetryTime": "2026-09-29T10:00:00Z",
  "recentTelemetryCount": 1500,
  "timestamp": "2026-09-29T10:00:00Z"
}
```

---

## 3. Machine Endpoints

### `GET /api/machines`
Lists all 12 machines across the factory floor, enriched with current operating state, health status, sequence, and key measurements.

- **Query Parameters**:
  - `line` *(optional)*: Filter by line identifier (e.g. `LINE_1`, `LINE_2`, `LINE_3`).
  - `protocol` *(optional)*: Filter by protocol (e.g. `MODBUS_TCP`, `OPC_UA`, `MQTT`).
  - `state` *(optional)*: Filter by operating state (e.g. `RUNNING`, `WARNING`, `FAULT`).

- **Response `200 OK`**:
```json
[
  {
    "machineId": "CNC-001",
    "machineType": "CNC_MILL",
    "plant": "PLANT_1",
    "line": "LINE_1",
    "protocol": "MODBUS_TCP",
    "operatingState": "RUNNING",
    "healthState": "NORMAL",
    "latestSequence": 420,
    "latestEventTime": "2026-09-29T10:00:00Z",
    "keyMeasurements": {
      "spindle_speed_rpm": 3200.5,
      "feed_rate_mmpm": 850.0,
      "spindle_temp_c": 42.8,
      "vibration_rms_g": 0.045
    }
  }
]
```

### `GET /api/machines/{machine_id}`
Returns complete machine metadata, plant/line hierarchy, protocol adapter type, signal catalog with engineering units, and the latest full telemetry snapshot.

- **Path Parameters**:
  - `machine_id`: Unique machine identifier (e.g., `CNC-001`, `AGV-001`, `CHILLER-001`).

- **Response `200 OK`**:
```json
{
  "machineId": "CNC-001",
  "machineType": "CNC_MILL",
  "plant": "PLANT_1",
  "line": "LINE_1",
  "protocol": "MODBUS_TCP",
  "operatingState": "RUNNING",
  "healthState": "NORMAL",
  "latestSequence": 420,
  "latestEventTime": "2026-09-29T10:00:00Z",
  "signalCatalog": [
    {"signalName": "spindle_speed_rpm", "displayName": "Spindle Speed", "unit": "RPM", "dataType": "float"},
    {"signalName": "spindle_temp_c", "displayName": "Spindle Temperature", "unit": "°C", "dataType": "float"}
  ],
  "latestTelemetry": {
    "eventId": "123e4567-e89b-12d3-a456-426614174000",
    "eventTime": "2026-09-29T10:00:00Z",
    "ingestionTime": "2026-09-29T10:00:00.100Z",
    "sequence": 420,
    "operatingState": "RUNNING",
    "healthState": "NORMAL",
    "quality": "GOOD",
    "measurements": {
      "spindle_speed_rpm": 3200.5,
      "spindle_temp_c": 42.8
    },
    "derived": {
      "thermal_gradient": 1.2
    },
    "source": {
      "protocol": "MODBUS_TCP",
      "adapter": "modbus_edge_adapter",
      "ip": "192.168.1.10"
    }
  }
}
```

---

## 4. Telemetry & Historical Endpoints

### `GET /api/machines/{machine_id}/latest`
Retrieves the most recently recorded canonical telemetry payload for the specified machine.

### `GET /api/machines/{machine_id}/history`
Fetches a bounded time-series sequence of telemetry snapshots.

- **Query Parameters**:
  - `start` *(optional ISO-8601 string)*: Lower time boundary.
  - `end` *(optional ISO-8601 string)*: Upper time boundary.
  - `limit` *(optional integer, default=100, max=2000)*: Max records returned.
  - `signals` *(optional comma-separated string)*: Filter measurement keys.

- **Response `200 OK`**:
```json
{
  "machineId": "CNC-001",
  "count": 2,
  "records": [
    {
      "eventId": "123e4567-e89b-12d3-a456-426614174000",
      "eventTime": "2026-09-29T09:59:00Z",
      "sequence": 419,
      "operatingState": "RUNNING",
      "healthState": "NORMAL",
      "quality": "GOOD",
      "measurements": {"spindle_speed_rpm": 3195.0, "spindle_temp_c": 42.4}
    },
    {
      "eventId": "123e4567-e89b-12d3-a456-426614174001",
      "eventTime": "2026-09-29T10:00:00Z",
      "sequence": 420,
      "operatingState": "RUNNING",
      "healthState": "NORMAL",
      "quality": "GOOD",
      "measurements": {"spindle_speed_rpm": 3200.5, "spindle_temp_c": 42.8}
    }
  ]
}
```

### `GET /api/telemetry/latest`
Retrieves the latest canonical snapshot for all 12 machines across the factory.

---

## 5. Real-Time Streaming

### `GET /api/realtime/telemetry`
Server-Sent Events (SSE) streaming endpoint returning real-time canonical telemetry as new records are persisted.

- **Protocol**: `text/event-stream`
- **Payload Event Structure**:
```
event: telemetry
data: {"eventId": "...", "machineId": "CNC-001", "sequence": 421, "eventTime": "...", "state": "RUNNING", "health": "NORMAL", "quality": "GOOD", "measurements": {...}}
```
