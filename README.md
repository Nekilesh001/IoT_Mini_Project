# Smart Factory Machine Monitoring and Predictive Maintenance System

A professional, end-to-end Industrial Internet of Things (IIoT) smart-factory simulation and predictive maintenance platform. The system features 12 heterogeneous industrial machines, multi-protocol communication (Modbus TCP, OPC UA, MQTT), edge gateway ingestion, local storage and processing, operational dashboards, state/fleet management, and machine learning inference for anomaly detection and Remaining Useful Life (RUL) prediction.

> [!NOTE]
> **Educational & Engineering Simulation Disclaimer**: This repository is an educational engineering simulation and software architecture demonstration project. It is **not** a safety-critical real-world industrial machine control system.

---

## High-Level System Architecture

The project employs a **Local-First, Cloud-Optional Hybrid Architecture**. The system operates fully offline using local services and can optionally synchronize with AWS IoT Core.

```
Factory Floor (12 Machines)
       ↓
Protocol Servers (Modbus TCP / OPC UA / MQTT)
       ↓
Edge Gateway & Processing Engine (Validation, Normalization, Explicit Filtering, Buffer, Edge ML)
       ↓
Canonical JSON Telemetry Stream
       ↓
Local Event Bus (MQTT) & Storage (PostgreSQL / SQLite)
       ↓
FastAPI Backend & React Operations Dashboard
```

---

## Candidate Implementation Technologies

> [!NOTE]
> **Validation Notice**: The libraries, frameworks, and tools listed below represent **candidate implementation technologies** subject to prototyping and empirical validation during future development phases, rather than permanently frozen architectural choices.

- **Simulation & Edge (Candidate Stack)**: Python 3.11+, PyModbus, asyncua, Eclipse Paho MQTT, ONNX Runtime.
- **Message Bus & Storage (Candidate Stack)**: Eclipse Mosquitto (MQTT), PostgreSQL / TimescaleDB, SQLite.
- **Backend API (Candidate Stack)**: FastAPI, Uvicorn, Pydantic, SQLAlchemy.
- **Frontend Dashboard (Candidate Stack)**: React, Vite, Vanilla CSS / Tailwind CSS, Recharts / Canvas.
- **Machine Learning (Candidate Stack)**: Scikit-Learn, XGBoost, PyTorch / ONNX Runtime.
- **Cloud (Optional Candidate Services)**: AWS IoT Core, AWS DynamoDB, AWS Lambda, AWS CloudWatch.

---

## Factory Layout & Supported Protocols

The baseline factory models **12 heterogeneous simulated machines**:

1. **CNC-001** (CNC Machining Center) — OPC UA
2. **CNC-002** (CNC Lathe) — Modbus TCP
3. **ROB-001** (6-Axis Industrial Robot) — OPC UA
4. **ROB-002** (Spot/Arc Welding Robot) — MQTT
5. **CON-001** (Industrial Conveyor) — Modbus TCP
6. **PRS-001** (Industrial Press) — Modbus TCP
7. **IMM-001** (Injection Molding Machine) — OPC UA
8. **CMP-001** (Air Compressor) — Modbus TCP
9. **PMP-001** (Industrial Pump) — MQTT
10. **VIS-001** (Vision Inspection Station) — OPC UA
11. **AGV-001** (Autonomous Mobile Robot) — MQTT
12. **CHL-001** (Industrial Chiller) — Modbus TCP

---

## Predictive Maintenance & Edge Filtering

- **Causal Physics Simulation**: Generates realistic sensor telemetry under normal, degraded, and fault conditions.
- **Edge Filtering & Deduplication**: Deduplication is performed strictly based on event identity and sequence numbers (`eventId` / `sequence`). Signal filtering/noise reduction is explicit and signal-specific, preserving telemetry state continuity without automatically discarding unchanged values.
- **Target Leakage Prevention**: ML feature extraction strictly excludes simulator ground-truth variables, hidden degradation counters, simulated fault flags, simulator-derived health labels, and existing ML predictions.
- **Edge Inference**: Models are exported to ONNX format for zero-dependency execution at the edge gateway.

---

## Development Status & Roadmap

Current Status: **Phase 8 — Edge ML Anomaly & Predictive Inference Engine (COMPLETED)**

- **Phase 0 — Architecture & Control Docs**: Completed.
- **Phase 1 — Factory Simulation Core**: Completed. Run local demo via `python -m simulator` or test suite via `python -m pytest tests/simulator/`.
- **Phase 2 — Protocol Simulation & Adapters**: Completed. Run local protocol demo via `python -m protocols.protocol_demo` or test suite via `python -m pytest tests/protocols/`.
- **Phase 3 — Canonical Telemetry & Edge Ingestion**: Completed. Run local edge demo via `python -m edge.demo` or test suite via `python -m pytest tests/edge/`.
- **Phase 4 — Local Storage, MQTT Event Bus & Buffering**: Completed. Run local storage demo via `python -m storage.demo` or test suite via `python -m pytest tests/storage/ tests/event_bus/ tests/integration/`.
- **Phase 5 — FastAPI Backend & React Dashboard**: Completed. Run API backend via `python -m api`, frontend via `cd dashboard/react-app && npm run dev`, end-to-end demo via `python -m api.demo`, or test suite via `python -m pytest tests/api/`.
- **Phase 6 — Fault Injection Framework & Rule-Based Alerts**: Completed. Run alert & fault demo via `python -m alerts.demo` or test suite via `python -m pytest tests/alerts/ tests/integration/`.
- **Phase 7 — ML Dataset Collection, Training & Model Evaluation**: Completed. Run ML demo via `python -m ml.demo` or individual training pipelines (`python -m ml.pipelines.build_dataset`, `python -m ml.pipelines.train_anomaly`, `python -m ml.pipelines.train_rul`).
- **Phase 8 — Edge ML Anomaly & Predictive Inference Engine**: Completed. Run Edge ML demo via `python -m ml.inference.demo` or test suite via `python -m pytest tests/ml/`.
- **Phase 9 — Device Shadow, Fleet Management & Local Job Engine**: Next Target.

### Running Edge ML Inference Engine

1. **Run Real-Time Edge ML Inference Demonstration**:
   ```bash
   python -m ml.inference.demo
   ```

2. **Start Storage & Continuous Ingestion Worker with ML Inference**:
   ```bash
   python -m storage.worker
   ```

3. **Query ML Endpoints via FastAPI**:
   - ML Health Status: `http://localhost:8000/api/ml/status`
   - Loaded Model Metadata: `http://localhost:8000/api/ml/models`
   - Fleet Anomaly/RUL Summary: `http://localhost:8000/api/ml/fleet-summary`
   - Inference Latency Metrics: `http://localhost:8000/api/ml/metrics`

4. **Inspect Live Predictive Maintenance UI**:
   - React ML Console: `http://localhost:5173/ml`

### Running ML Pipelines & Experiment Tracking

1. **Build Dataset & Feature Manifest**:
   ```bash
   python -m ml.pipelines.build_dataset
   ```

2. **Train Unsupervised Anomaly Detection (Isolation Forest)**:
   ```bash
   python -m ml.pipelines.train_anomaly
   ```

3. **Train RUL Predictive Maintenance Regressor (HistGradientBoosting)**:
   ```bash
   python -m ml.pipelines.train_rul
   ```

4. **Run End-to-End ML Pipeline Verification Demo**:
   ```bash
   python -m ml.demo
   ```

5. **Launch Local MLflow Tracking UI**:
   ```bash
   mlflow ui --backend-store-uri ./mlruns --port 5000
   ```

### Running Local Infrastructure & Operational Dashboard

1. **Start PostgreSQL & Event Bus (Docker Compose)**:
   ```bash
   docker compose up -d
   ```

2. **Start Factory Simulation & Edge Ingestion Worker**:
   ```bash
   python -m storage.worker
   ```

3. **Start FastAPI Backend**:
   ```bash
   python -m api
   ```
   - OpenAPI Docs: `http://localhost:8000/docs`
   - API Base: `http://localhost:8000/api`
   - Active Alerts: `http://localhost:8000/api/alerts/active`
   - Realtime Events: `http://localhost:8000/api/realtime/events`

4. **Start React Operations Dashboard**:
   ```bash
   cd dashboard/react-app
   npm install
   npm run dev
   ```
   - Dashboard UI: `http://localhost:5173`
   - Alerts Console: `http://localhost:5173/alerts`
   - Predictive ML Console: `http://localhost:5173/ml`

5. **Run Phase 6 Fault-Injection & Alerting Verification Demo**:
   ```bash
   python -m alerts.demo
   ```

6. **Run Phase 10 Security Hardening Demo & Hygiene Scanner**:
   ```bash
   python -m security.demo
   python -m security.validation
   ```

7. **Run Phase 12 End-to-End Failure Testing & Resilience Verification Demo**:
   ```bash
   python -m failure_testing.demo
   ```

For detailed architectural details and documentation:
- [AGENTS.md](AGENTS.md) — AI agent execution guidelines and strict constraints.
- [PROJECT_SPECIFICATION.md](PROJECT_SPECIFICATION.md) — Master architectural blueprint and data schemas.
- [PHASE_STATUS.md](PHASE_STATUS.md) — Current implementation milestone tracker.
- [docs/phase1/simulation-architecture.md](docs/phase1/simulation-architecture.md) — Phase 1 simulation architecture.
- [docs/phase2/protocol-architecture.md](docs/phase2/protocol-architecture.md) — Phase 2 protocol architecture and adapters.
- [docs/phase3/edge-architecture.md](docs/phase3/edge-architecture.md) — Phase 3 edge ingestion architecture and canonical schema.
- [docs/phase4/event-bus-architecture.md](docs/phase4/event-bus-architecture.md) — Phase 4 event bus and storage architecture.
- [docs/phase5/api-architecture.md](docs/phase5/api-architecture.md) — Phase 5 FastAPI backend and streaming architecture.
- [docs/phase5/dashboard-architecture.md](docs/phase5/dashboard-architecture.md) — Phase 5 React operations console.
- [docs/phase6/fault-architecture.md](docs/phase6/fault-architecture.md) — Phase 6 fault injection & alerting architecture.
- [docs/phase7/ml-architecture.md](docs/phase7/ml-architecture.md) — Phase 7 ML architecture & pipeline overview.
- [docs/phase8/ml-inference-architecture.md](docs/phase8/ml-inference-architecture.md) — Phase 8 edge ML inference engine architecture.
- [docs/phase9/device-management-architecture.md](docs/phase9/device-management-architecture.md) — Phase 9 device shadow, fleet & jobs architecture.
- [docs/phase10/security-architecture.md](docs/phase10/security-architecture.md) — Phase 10 security architecture & hardening.
- [docs/phase10/secrets.md](docs/phase10/secrets.md) — Phase 10 secrets management & scanner.
- [docs/phase10/tls-mtls.md](docs/phase10/tls-mtls.md) — Phase 10 local X.509 PKI & mTLS.
- [docs/phase10/authentication.md](docs/phase10/authentication.md) — Phase 10 local authentication & JWT.
- [docs/phase10/rbac.md](docs/phase10/rbac.md) — Phase 10 role-based access control matrix.
- [docs/phase10/authorization.md](docs/phase10/authorization.md) — Phase 10 API authorization dependencies.
- [docs/phase10/security-audit.md](docs/phase10/security-audit.md) — Phase 10 security audit trail.
- [docs/phase10/api-security.md](docs/phase10/api-security.md) — Phase 10 API hardening headers & middleware.
- [docs/phase10/testing.md](docs/phase10/testing.md) — Phase 10 security verification tests.
- [docs/phase12/failure-architecture.md](docs/phase12/failure-architecture.md) — Phase 12 failure & resilience architecture.
- [docs/phase12/failure-scenarios.md](docs/phase12/failure-scenarios.md) — Phase 12 failure scenario catalog (15 modes).
- [docs/phase12/mqtt-outage.md](docs/phase12/mqtt-outage.md) — Phase 12 MQTT outage & buffer replay.
- [docs/phase12/database-outage.md](docs/phase12/database-outage.md) — Phase 12 database outage recovery.
- [docs/phase12/protocol-failure.md](docs/phase12/protocol-failure.md) — Phase 12 protocol adapter failure isolation.
- [docs/phase12/ml-failure.md](docs/phase12/ml-failure.md) — Phase 12 ML failure & graceful degradation.
- [docs/phase12/alert-failure.md](docs/phase12/alert-failure.md) — Phase 12 alert persistence resilience.
- [docs/phase12/job-failure.md](docs/phase12/job-failure.md) — Phase 12 job retry exhaustion & terminal states.
- [docs/phase12/restart-recovery.md](docs/phase12/restart-recovery.md) — Phase 12 process restart buffer persistence.
- [docs/phase12/recovery-metrics.md](docs/phase12/recovery-metrics.md) — Phase 12 recovery latency & reliability metrics.
- [docs/phase12/test-results.md](docs/phase12/test-results.md) — Phase 12 test execution summary.
- [docs/phase12/limitations.md](docs/phase12/limitations.md) — Phase 12 scope, assumptions & limitations.

---

## Git Workflow

- **`main`**: Production-ready, stable releases.
- **`dev`**: Active development, feature implementation, and documentation.

All development occurs on `dev`. Merging to `main` is executed strictly via reviewed Pull Requests following full test verification.