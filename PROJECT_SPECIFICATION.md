# Project Specification — Smart Factory Machine Monitoring and Predictive Maintenance System

## 1. Project Overview & Goal

### 1.1 Project Title
**Smart Factory Machine Monitoring and Predictive Maintenance System**

### 1.2 Core Goal
To design and build a professional, end-to-end Industrial Internet of Things (IIoT) smart-factory simulation and predictive maintenance system. The system incorporates heterogeneous industrial machines, multiple industrial communication protocols, edge gateway processing, local operations, optional AWS cloud integration, operational dashboards, device/fleet management, and real machine learning (ML) predictive maintenance models.

The system is designed to be **realistic, modular, testable, fully documented, and 100% executable locally without requiring an active AWS connection**.

---

## 2. Factory Layout & Heterogeneous Machines

The baseline factory model simulates a production environment featuring **12 heterogeneous industrial machines**. Each machine operates with realistic behavior and exposes telemetry via one of three industrial communication protocols.

> **Note on Protocol Assignment**: The assigned protocols below represent a simulation design choice for testing multi-protocol ingestion. They do not imply a universal real-world rule for every machine of that class.

### 2.1 Factory Machine Catalog

| Machine ID | Machine Class | Primary Protocol | Simulated Machine Functions / Features |
| :--- | :--- | :--- | :--- |
| **CNC-001** | CNC Machining Center | OPC UA | Multi-axis milling, spindle motor dynamic load, feed rates, tool wear tracking |
| **CNC-002** | CNC Lathe | Modbus TCP | High-speed turning, chuck pressure, thermal expansion, cutting fluid telemetry |
| **ROB-001** | 6-Axis Industrial Robot | OPC UA | Heavy payload handling, joint motor temperatures, position tracking & torque errors |
| **ROB-002** | Spot/Arc Welding Robot | MQTT | High-speed welding cycle, arc current/voltage, weld tip condition, gas flow |
| **CON-001** | Industrial Conveyor | Modbus TCP | Continuous material transfer, belt tension, motor current, variable speed drive |
| **PRS-001** | Industrial Press | Modbus TCP | Hydraulic pressing cycles, tonnage, hydraulic oil pressure/temperature, stroke count |
| **IMM-001** | Injection Molding Machine | OPC UA | Plastic resin injection, mold clamp force, heater zone temperatures, cycle timing |
| **CMP-001** | Air Compressor | Modbus TCP | Plant compressed air supply, element discharge temperature, pressure, motor load |
| **PMP-001** | Industrial Pump | MQTT | Liquid coolant circulation, suction/discharge pressure, flow rate, bearing vibration |
| **VIS-001** | Vision Inspection Station | OPC UA | Automated optical quality inspection, pass/fail counters, lighting intensity, inference time |
| **AGV-001** | Autonomous Mobile Robot | MQTT | Material transport around factory, battery SOC, motor speed, LiDAR safety stop events |
| **CHL-001** | Industrial Chiller | Modbus TCP | Plant process cooling, refrigerant pressures, compressor current, supply/return temp |

---

## 3. Decoupled Architectural Pattern

To ensure clean software architecture and maintainability, **Machine Behaviour** and **Protocol Exposure** are strictly separated.

```
+---------------------+      +-----------------------------+      +------------------+      +---------------------+
| Machine Behaviour   | ---> | Protocol Server / Publisher | ---> | Protocol Adapter | ---> | Canonical Telemetry |
| (Physics Engine)    |      | (Modbus / OPC UA / MQTT)    |      | (Edge Ingestion) |      | (Standard JSON)     |
+---------------------+      +-----------------------------+      +------------------+      +---------------------+
```

1. **Machine Behaviour**: Simulates physical state, load dynamics, process physics, thermal dynamics, and degradation mechanisms.
2. **Protocol Server / Publisher**: Exposes machine state over standard protocols (Modbus TCP server registers, OPC UA node variables, or MQTT topic payloads).
3. **Protocol Adapter**: Ingests raw protocol messages at the edge gateway and converts them into normalized telemetry objects.
4. **Canonical Telemetry**: Protocol-agnostic telemetry envelope processed by downstream ingestion, storage, analytics, and ML components.

---

## 4. Communication Protocols & Adapter Stack

The project natively simulates and ingests three core industrial communication protocols:

- **Modbus TCP**: Uses candidate library `PyModbus` for industrial registers (Holding Registers, Input Registers, Coils, Discrete Inputs).
- **OPC UA**: Uses candidate library `asyncua` (Python OPC UA asyncio library) for object-oriented, node-based industrial communication.
- **MQTT**: Uses candidate library `paho-mqtt` for lightweight pub/sub event stream transport.

Downstream edge pipelines remain strictly **protocol-agnostic** by consuming canonical telemetry from the adapter layer.

---

## 5. System Architecture & Flow

### 5.1 End-to-End Data Pipeline

```
Factory Machines (12 Simulated Units)
       ↓
Protocol Layer (Modbus TCP / OPC UA / MQTT)
       ↓
Edge Gateway & Processing Layer
       ├── Ingestion & Validation
       ├── Unit Normalization & Quality Assignment
       ├── Explicit Filtering, Deduplication & Derived Metrics
       ├── Local Rule Engine & Alert Dispatch
       ├── Edge ML Anomaly & Degradation Inference
       └── Persistent Buffer (Store-and-Forward)
       ↓
Canonical Telemetry Stream
       ↓
Local MQTT Event Bus (Mosquitto / EMQX)
       ↓
Local Storage (PostgreSQL + TimescaleDB / SQLite)
       ↓
FastAPI Backend Application
       ↓
React Dashboard (Real-time Operations & Predictive Maintenance UI)
```

### 5.2 Local-First & Hybrid AWS Architecture

The core project operates in a **Local-First** mode. AWS Cloud integration is an optional hybrid extension, ensuring full system functionality during network disconnections or offline operations.

```
                              [ Factory Floor ]
                                      │
                         [ Edge Gateway Ingestion ]
                                      │
                  ┌───────────────────┴───────────────────┐
                  ▼                                       ▼
        [ Local Mode (Offline) ]              [ Hybrid Mode (Cloud Sync) ]
        ├── Local MQTT Broker                 ├── AWS IoT Core MQTT
        ├── PostgreSQL Storage                ├── AWS DynamoDB / Timestream
        ├── Local Python ML Inference         ├── AWS CloudWatch Monitoring
        ├── Local FastAPI Services            ├── AWS Lambda Processing
        └── React Operations Dashboard        └── AWS IoT Shadows & Jobs
```

#### AWS Fallback Component Mapping

| Service Category | Cloud Implementation (AWS) | Local-First Implementation (Default) |
| :--- | :--- | :--- |
| **Message Broker** | AWS IoT Core MQTT | Local MQTT Broker (Eclipse Mosquitto) |
| **Primary Telemetry Storage** | AWS DynamoDB / Timestream | PostgreSQL (with TimescaleDB extension) |
| **Compute Worker** | AWS Lambda | Local Python Background Workers (Celery/FastAPI) |
| **Monitoring & Alarms** | AWS CloudWatch | Local Monitoring Stack (Prometheus/Grafana/UI) |
| **State Synchronization** | AWS IoT Device Shadow | Local State Manager (Redis/PostgreSQL) |
| **Fleet / OTA Jobs** | AWS IoT Jobs | Local Fleet Job Manager |
| **Predictive Inference** | AWS SageMaker Endpoint | Local Python ONNX / Scikit-Learn Inference |

---

## 6. Machine Telemetry & Dynamic Signal Catalogs

Telemetry schemas are machine-specific and dynamic. Universal identical sensor models are strictly prohibited.

### 6.1 Machine-Specific Signal Catalog Examples

#### CNC Machining Center & Lathe
- `spindle_speed` (RPM)
- `spindle_load` (%)
- `spindle_temperature` (°C)
- `vibration_rms` (mm/s)
- `feed_rate` (mm/min)
- `coolant_pressure` (bar)
- `tool_wear_index` (%)
- `axis_x_position`, `axis_y_position`, `axis_z_position` (mm)

#### Industrial 6-Axis & Welding Robots
- `joint_1_temp` through `joint_6_temp` (°C)
- `joint_1_torque` through `joint_6_torque` (Nm)
- `position_error_norm` (mm)
- `weld_current` (A) *(Welding Robot)*
- `weld_voltage` (V) *(Welding Robot)*
- `shield_gas_flow` (L/min) *(Welding Robot)*

#### Industrial Conveyor
- `belt_speed` (m/s)
- `drive_motor_current` (A)
- `drive_motor_temp` (°C)
- `vibration_amplitude` (mm)
- `belt_tension` (N)
- `throughput_rate` (units/min)

#### Air Compressor & Industrial Chiller
- `discharge_pressure` (bar)
- `element_temperature` (°C)
- `compressor_current` (A)
- `refrigerant_high_pressure` (bar) *(Chiller)*
- `supply_fluid_temp`, `return_fluid_temp` (°C) *(Chiller)*
- `fluid_flow_rate` (L/min)

#### Industrial Pump
- `suction_pressure` (bar)
- `discharge_pressure` (bar)
- `flow_rate` (m³/h)
- `power_consumption` (kW)
- `bearing_vibration_x`, `bearing_vibration_y` (mm/s)
- `seal_temperature` (°C)

#### Autonomous Mobile Robot (AGV)
- `battery_soc` (%)
- `battery_voltage` (V)
- `battery_temperature` (°C)
- `wheel_motor_speed` (RPM)
- `posX`, `posY`, `orientation` (m, deg)
- `safety_lidar_status` (CLEAR / WARN / STOP)

---

## 7. Canonical Telemetry Data Schema

All ingested machine readings are converted into a standardized JSON envelope.

### 7.1 Schema Envelope

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
    "endpoint": "opc.tcp://192.168.1.100:4840",
    "sourceAddress": "ns=2;s=CNC001.Spindle"
  },
  "eventTime": "2026-09-28T14:00:00.123Z",
  "ingestionTime": "2026-09-28T14:00:00.145Z",
  "sequence": 142058,
  "state": {
    "operating": "RUNNING",
    "health": "WARNING"
  },
  "quality": "GOOD",
  "measurements": {
    "spindleSpeed": 12000.0,
    "spindleLoad": 78.4,
    "spindleTemp": 68.2,
    "vibrationRms": 2.45,
    "feedRate": 1500.0
  },
  "derived": {
    "thermalExpansionDelta": 0.012,
    "powerKw": 14.2
  },
  "ml": {
    "anomalyScore": 0.34,
    "predictedRULHours": 142.5,
    "faultRisk": "MEDIUM"
  }
}
```

### 7.2 Telemetry Quality Enum

- `GOOD`: Valid sensor reading within normal operational limits.
- `BAD`: Invalid physical reading or protocol parsing error.
- `STALE`: Outdated telemetry cached due to connection stall.
- `MISSING`: Expected payload signal missing from source message.
- `OUT_OF_RANGE`: Signal exceeds physical sensor range limits.
- `ESTIMATED`: Imputed value calculated during transient signal gaps.

---

## 8. Machine State Model

Machine state management distinguishes between **Operating State** (what the machine is doing) and **Health State** (condition of the machine).

### 8.1 Operating States
- `OFF`: Power down / uninitialized.
- `STARTING`: Warm-up or homing sequence.
- `IDLE`: Powered on, awaiting job command.
- `RUNNING`: Active processing / production.
- `MAINTENANCE`: Under routine service or repair.
- `RECOVERY`: Resetting safety interlocks after fault.

### 8.2 Health States
- `HEALTHY`: Normal degradation curve.
- `WARNING`: Early degradation detected (e.g., elevated vibration or temperature).
- `FAULT`: Critical failure or safety shutdown.

---

## 9. Simulation Dynamics & Fault Injection

The factory simulation is driven by **causal physics models**. Independent random signal generators are strictly forbidden.

### 9.1 Causal Mechanisms
- Telemetry dynamically changes based on operating load, cycle time, thermal build-up, and mechanical wear.
- Progressive degradation affects correlated signals simultaneously (e.g., bearing wear increases motor current, raises bearing temperature, and increases vibration RMS).

### 9.2 Fault Taxonomy

1. **MACHINE_FAULT**: Mechanical bearing failure, spindle seizure, hydraulic leak, tool breakage.
2. **SENSOR_FAULT**: Sensor drift, stuck signal value, signal noise spike, open circuit.
3. **PROTOCOL_FAULT**: Malformed register response, OPC UA node timeout, MQTT payload syntax error.
4. **NETWORK_FAULT**: Packet loss, high latency, connection disconnect, subnet isolation.
5. **EDGE_FAULT**: Buffer overflow, CPU throttling, local DB write failure.
6. **CLOUD_FAULT**: AWS IoT endpoint rejection, TLS handshake timeout, rate limiting.

### 9.3 Fault Lifecycle Model

```
FAULT_START ──> ACTIVE ──> FAULT_END ──> MAINTENANCE/RECOVERY ──> RUNNING
```

### 9.4 Target Leakage Prevention
Ground-truth simulation parameters, hidden degradation counters, simulated fault flags, simulator-derived health labels, and existing ML predictions are used solely for dataset labeling, ground-truth evaluation, and supervisory validation. They **MUST NEVER** be included as input features in ML feature vectors or passed into production edge inference pipelines.

---

## 10. Edge Processing Pipeline

The Edge Gateway performs 12 distinct processing steps:

1. **Protocol Ingestion**: Read raw payloads via Modbus, OPC UA, or MQTT adapters.
2. **Validation**: Validate envelope structure and signal presence against machine specifications.
3. **Normalization**: Standardize units (e.g., Celsius, Bar, RPM, mm/s).
4. **Quality Assignment**: Stamp signals with quality flags (`GOOD`, `BAD`, `STALE`, etc.).
5. **Filtering & Deduplication**: Deduplicate incoming events based strictly on event identity and sequence numbers (`eventId` / `sequence`). Perform explicit, signal-specific filtering and noise reduction (such as moving average or low-pass filtering on dynamic physical measurements) rather than automatically discarding telemetry with unchanged values, ensuring state continuity and complete event auditing.
6. **Aggregation**: Calculate rolling statistics (mean, RMS, min, max over window).
7. **Derived Metrics**: Compute calculated operational indicators (e.g., hydraulic efficiency).
8. **Persistent Buffering**: Store telemetry in SQLite/RocksDB when network links fail (Store-and-Forward).
9. **Local Rules Engine**: Trigger local alarms on immediate safety limit breaches.
10. **ML Edge Inference**: Run local ONNX anomaly detection models without cloud latency.
11. **Local Event Publishing**: Publish canonical JSON telemetry to the local MQTT broker.
12. **Cloud Synchronization**: Sync buffered telemetry and state changes to AWS when connected.

---

## 11. Machine Learning & Predictive Maintenance

ML is a mandatory core component of the system.

### 11.1 ML Pipeline Workflow
1. **Dataset Generation**: Run simulation scenarios to gather normal, degraded, and fault telemetry datasets.
2. **Preprocessing & Cleaning**: Handle missing values, filter sensor noise, scale dynamic ranges.
3. **Feature Engineering**: Compute time-domain features (RMS, kurtosis, peak-to-peak) and rolling statistics. Exclude all simulator ground-truth variables, hidden counters, fault flags, health labels, and existing ML predictions from input feature vectors.
4. **Model Training**: Train models for:
   - **Anomaly Detection** (e.g., Isolation Forest, Autoencoders).
   - **Remaining Useful Life (RUL) Prediction** (e.g., Random Forest Regression, XGBoost, LSTM).
5. **Evaluation**: Evaluate performance using precision/recall, F1-score, MAE/RMSE for RUL.
6. **Edge Deployment**: Export trained models to ONNX format for zero-dependency local edge execution.

---

## 12. Device Shadows, Fleet Management & Jobs

The system implements state management and fleet operations locally (with AWS IoT equivalents when cloud-enabled):

- **Device Shadow Pattern**: Maintains state synchronization across three layers:
  - `desired`: Targeted configuration or operational mode set by operator.
  - `applied`: Configuration validated and staged by edge control.
  - `reported`: Verified active state returned by machine control.
- **Fleet Jobs**: Staged firmware/configuration updates with batch rollout, status monitoring, and automatic rollback criteria.

---

## 13. Security Architecture

- **Transport Layer Security (TLS)**: Encrypted communication across all network boundaries.
- **X.509 Authentication**: Mutual TLS (mTLS) certificate validation for edge gateways and brokers.
- **Least Privilege Access**: Role-based access control (RBAC) for FastAPI endpoints and MQTT topic access policies.
- **Secrets Isolation**: Storage of credentials in `.env` files (gitignored). `.env.example` provided as template.

---

## 14. Project Execution Roadmap (14 Phases)

- **Phase 0 — Architecture, Factory Definition, Machine R&D** *(Current)*
- **Phase 1 — Factory Simulation Core**
- **Phase 2 — Protocol Simulation and Adapters**
- **Phase 3 — Canonical Telemetry and Edge Ingestion**
- **Phase 4 — Local Storage, MQTT, Buffering and Processing**
- **Phase 5 — API and React Dashboard**
- **Phase 6 — Fault Injection and Rule-Based Alerts**
- **Phase 7 — ML Dataset, Training and Evaluation**
- **Phase 8 — Edge ML Inference**
- **Phase 9 — Device Shadow / Fleet / Jobs**
- **Phase 10 — Security Hardening**
- **Phase 11 — AWS Integration**
- **Phase 12 — Failure Testing and End-to-End Validation**
- **Phase 13 — Documentation and Final Demo**

---

## 15. Git Workflow & Governance

### 15.1 Branch Model
- **`main`**: Production-ready, reviewed, stable releases.
- **`dev`**: Active development, feature implementation, testing, and documentation updates.

### 15.2 Commit Message Standards
- `feat:` New features or capabilities.
- `fix:` Bug fixes.
- `test:` Test suites and validation scripts.
- `docs:` Documentation updates.
- `refactor:` Code restructuring without functional changes.
