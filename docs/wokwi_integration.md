# External Wokwi IoT Device & HiveMQ MQTT Bridge Integration

This document outlines the architecture, payload normalization, bridge routing, real-time telemetry streaming, and verification procedure for integrating the **External Wokwi Raspberry Pi Pico W IoT Environmental Sensor (`IOT-SENSOR-001`)** into the **Smart Factory IIoT Platform**.

---

## 1. Architectural Overview & Design Rationale

### Why Wokwi is a Separate External IoT Device
The Smart Factory platform simulates **12 heterogeneous industrial machines** (CNC Machining Centers, Industrial Robots, Presses, Pumps, Compressors, Chillers, etc.) executing industrial physics and degradation mechanics over Modbus TCP, OPC UA, and Local MQTT. 

The Wokwi node (`IOT-SENSOR-001`) represents an **external environmental sensor**:
- **Hardware**: Raspberry Pi Pico W + DHT22 Temperature & Humidity Sensor + LED Actuator.
- **Role**: Continuous monitoring of ambient shop-floor temperature and relative humidity.
- **Physical Scope**: Environmental context, strictly decoupled from heavy machinery degradation physics and industrial ML predictive maintenance models.

### Why HiveMQ Public Broker is Used as Transport Ingress
Wokwi's browser-based simulator runs in a sandboxed WebAssembly/cloud environment that cannot directly access a user's private `localhost` or local in-process MQTT broker. Therefore:
- The Pico W simulator publishes to the public MQTT broker: `broker.hivemq.com:1883`.
- The Smart Factory application runs a **Local Wokwi MQTT Bridge** that subscribes to HiveMQ, consumes raw telemetry, normalizes it into **Canonical Telemetry**, and injects it directly into the local edge ingestion pipeline.

---

## 2. Architecture & Message Flow

```
+-------------------------------------------------------------------------+
|                  Wokwi Simulation Environment (Cloud / Wasm)            |
|                                                                         |
|   +-----------------------+         +-------------------------------+   |
|   | Raspberry Pi Pico W   | ------> | DHT22 Sensor (Temp & Hum)     |   |
|   | MicroPython Firmware  | <------ | Local LED Hysteresis (>=30°C) |   |
|   +-----------------------+         +-------------------------------+   |
+-------------------|-----------------------------------------------------+
                    |
                    | MQTT Publish (QoS 1)
                    v
+-------------------------------------------------------------------------+
|                HiveMQ Public Broker (broker.hivemq.com:1883)            |
|   Topic: iot/plant/PLANT_01/line/LINE_A/device/IOT-SENSOR-001/telemetry  |
+-------------------|-----------------------------------------------------+
                    |
                    | MQTT Subscribe (QoS 1)
                    v
+-------------------------------------------------------------------------+
|               Local Smart Factory Platform (Local Ingestion)            |
|                                                                         |
|   +-----------------------------------------------------------------+   |
|   |                   Local Wokwi MQTT Bridge                       |   |
|   |   - Auto-reconnect & connection loss handling                   |   |
|   |   - Payload validation & JSON schema normalization              |   |
|   +-------------------------------|---------------------------------+   |
|                                   v                                     |
|   +-----------------------------------------------------------------+   |
|   |               Edge Ingestion & Validation Service               |   |
|   |   - Monotonic sequence tracking & deduplication                 |   |
|   |   - Unit normalization & Quality Code assignment (GOOD/BAD)     |   |
|   |   - CanonicalTelemetry envelope creation                        |   |
|   +-------------------|---------------------------------------------+   |
|                       |                                                 |
|         +-------------+-------------+-------------+                     |
|         v                           v             v                     |
|   +------------+              +------------+ +------------+             |
|   | PostgreSQL |              | Alert      | | ML Safety  |             |
|   | / SQLite   |              | Engine     | | Path       |             |
|   | Repository |              | (>=30°C    | | (Excluded  |             |
|   +------------+              |  >=35°C)   | |  from Ind. |             |
|         |                     +------------+ |  Inference)|             |
|         v                           |        +------------+             |
|   +---------------------------------+                                   |
|   |                                                                     |
|   v                                                                     |
|   +-----------------------------------------------------------------+   |
|   |                 FastAPI Realtime Service (SSE)                  |   |
|   |   - GET /api/realtime/telemetry (Live Server-Sent Events)       |   |
|   |   - GET /api/iot-devices (External IoT catalog & status)        |   |
|   +-------------------------------|---------------------------------+   |
|                                   v                                     |
|   +-----------------------------------------------------------------+   |
|   |             React Operational Dashboard (Frontend)              |   |
|   |   - Dedicated External IoT Card with live gauges & sparkline    |   |
|   |   - Dynamic updates in real-time without page refresh           |   |
|   +-----------------------------------------------------------------+   |
+-------------------------------------------------------------------------+
```

---

## 3. Telemetry Payload & Canonical Mapping

### Raw Wokwi MicroPython Payload
```json
{
  "deviceId": "IOT-SENSOR-001",
  "deviceType": "ENVIRONMENT_SENSOR",
  "plantId": "PLANT_01",
  "lineId": "LINE_A",
  "eventType": "TELEMETRY",
  "sequence": 42,
  "timestamp": "2026-09-30T10:00:00Z",
  "readings": {
    "temperatureC": 31.4,
    "humidityPct": 68.2
  },
  "actuator": {
    "type": "LED",
    "state": "ON"
  },
  "control": {
    "mode": "AUTO",
    "alertThresholdC": 30.0,
    "normalThresholdC": 28.0
  },
  "firmwareVersion": "0.1.0"
}
```

### Normalization to Canonical Telemetry Envelope
| Wokwi Field | Canonical Model Field | Target Type | Normalization Rule |
| :--- | :--- | :--- | :--- |
| `deviceId` | `machine_id` | `str` | `"IOT-SENSOR-001"` |
| `deviceType` | `machine_type` | `str` | `"ENVIRONMENT_SENSOR"` |
| `plantId` / `lineId` | `plant_id` / `line_id` | `str` | Preserved (`"PLANT_01"`, `"LINE_A"`) |
| `sequence` | `sequence` | `int` | Monotonic counter |
| `timestamp` | `event_time` | `str` (ISO-8601) | Normalized to UTC ISO-8601 |
| `readings.temperatureC` | `measurements.temperature_c` | `float` | Rounded to 2 decimal places (°C) |
| `readings.humidityPct` | `measurements.humidity_pct` | `float` | Rounded to 2 decimal places (%) |
| `actuator` / `control` | `raw_payload.metadata` | `dict` | Preserved in metadata |
| — | `source.protocol` | `str` | `"MQTT"` |
| — | `quality` | `QualityCode` | `GOOD` |

---

## 4. Alerting & ML Isolation

### Operational Alert Rules
The alert engine evaluates `IOT-SENSOR-001` telemetry against dedicated environmental rules:
1. **`ENV_TEMP_HIGH_WARNING`**: `temperature_c >= 30.0°C` &rarr; Severity: `WARNING` (Clear hysteresis: `< 28.0°C`).
2. **`ENV_TEMP_HIGH_CRITICAL`**: `temperature_c >= 35.0°C` &rarr; Severity: `CRITICAL` (Clear hysteresis: `< 33.0°C`).
3. **`ENV_HUMIDITY_HIGH_WARNING`**: `humidity_pct >= 85.0%` &rarr; Severity: `WARNING`.

### Machine Learning Isolation Guarantee
- **Target Leakage Prevention**: External IoT devices are explicitly excluded from industrial feature extraction pipelines and predictive maintenance models (Isolation Forest / HistGBM).
- **Buffer Integrity**: `IOT-SENSOR-001` telemetry is never added to industrial machine temporal feature buffers, ensuring zero training or inference contamination.

---

## 5. Configuration & Environment Variables

| Variable | Default Value | Description |
| :--- | :--- | :--- |
| `WOKWI_MQTT_ENABLED` | `true` | Enable/disable Wokwi bridge service |
| `WOKWI_MQTT_BROKER` | `broker.hivemq.com` | HiveMQ public ingress broker host |
| `WOKWI_MQTT_PORT` | `1883` | Ingress broker MQTT port |
| `WOKWI_MQTT_USERNAME` | `""` | Optional broker username |
| `WOKWI_MQTT_PASSWORD` | `""` | Optional broker password |
| `WOKWI_MQTT_TELEMETRY_TOPIC` | `iot/plant/PLANT_01/line/LINE_A/device/IOT-SENSOR-001/telemetry` | Telemetry topic to subscribe |
| `WOKWI_MQTT_COMMAND_TOPIC` | `iot/plant/PLANT_01/line/LINE_A/device/IOT-SENSOR-001/commands` | Downlink command topic |
| `WOKWI_MQTT_CLIENT_ID` | `smart-factory-wokwi-bridge` | Bridge MQTT client identifier |

---

## 6. MicroPython Firmware Setup for Wokwi

1. Open Wokwi at [https://wokwi.com](https://wokwi.com) and create a **Raspberry Pi Pico W** MicroPython project.
2. Replace `main.py` with the code in [`protocols/wokwi/firmware/main.py`](file:///d:/ONE_DATA/IoT_mini/protocols/wokwi/firmware/main.py).
3. Replace `diagram.json` with [`protocols/wokwi/firmware/diagram.json`](file:///d:/ONE_DATA/IoT_mini/protocols/wokwi/firmware/diagram.json).
4. Start the simulation. The Pico W will connect to `Wokwi-GUEST`, sync UTC time via NTP, and begin publishing live DHT22 telemetry to `broker.hivemq.com:1883`.

---

## 7. Execution & Verification Procedure

### Automated Verification
Run the dedicated test suite:
```powershell
python -m pytest tests/wokwi/ -v
```

Run the end-to-end integration demo:
```powershell
python -m protocols.wokwi.demo
```

### Manual End-to-End Live Verification
1. **Start Storage Worker**:
   ```powershell
   python -m storage.worker
   ```
2. **Start FastAPI Backend**:
   ```powershell
   python -m api
   ```
3. **Start React Dashboard**:
   ```powershell
   cd dashboard/react-app
   npm run dev
   ```
4. **Start Wokwi Pico W Simulation**:
   - In the Wokwi browser window, click **Play**.
   - Move the DHT22 temperature slider in Wokwi (e.g. from 24°C to 33°C).
   - Observe in the React Dashboard:
     - The **External IoT Node (`IOT-SENSOR-001`)** card updates in real time.
     - The temperature changes live, the high temperature badge appears, and the LED status updates to **ON**.
     - An operational alert is raised in the **Live Operational Alarms** panel.

---

## 8. Limitations & Edge Cases

1. **Public Broker Latency & Ingress Security**: `broker.hivemq.com` is a shared public broker. For private air-gapped deployments, set `WOKWI_MQTT_BROKER` to a local or VPC Mosquitto broker with TLS and token authentication.
2. **Offline Buffer Capacity**: The Pico W firmware buffers up to 50 readings in RAM during network drops. If disconnections exceed 50 samples, the oldest samples are rolled over to prevent RAM exhaustion.
