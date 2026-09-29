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

Current Status: **Phase 7 — ML Dataset Collection, Training & Model Evaluation (COMPLETED)**

- **Phase 0 — Architecture & Control Docs**: Completed.
- **Phase 1 — Factory Simulation Core**: Completed. Run local demo via `python -m simulator` or test suite via `python -m pytest tests/simulator/`.
- **Phase 2 — Protocol Simulation & Adapters**: Completed. Run local protocol demo via `python -m protocols.protocol_demo` or test suite via `python -m pytest tests/protocols/`.
- **Phase 3 — Canonical Telemetry & Edge Ingestion**: Completed. Run local edge demo via `python -m edge.demo` or test suite via `python -m pytest tests/edge/`.
- **Phase 4 — Local Storage, MQTT Event Bus & Buffering**: Completed. Run local storage demo via `python -m storage.demo` or test suite via `python -m pytest tests/storage/ tests/event_bus/ tests/integration/`.
- **Phase 5 — FastAPI Backend & React Dashboard**: Completed. Run API backend via `python -m api`, frontend via `cd dashboard/react-app && npm run dev`, end-to-end demo via `python -m api.demo`, or test suite via `python -m pytest tests/api/`.
- **Phase 6 — Fault Injection Framework & Rule-Based Alerts**: Completed. Run alert & fault demo via `python -m alerts.demo` or test suite via `python -m pytest tests/alerts/ tests/integration/`.
- **Phase 7 — ML Dataset Collection, Training & Model Evaluation**: Completed. Run ML demo via `python -m ml.demo` or individual training pipelines (`python -m ml.pipelines.build_dataset`, `python -m ml.pipelines.train_anomaly`, `python -m ml.pipelines.train_rul`).
- **Phase 8 — Edge ML Anomaly & Predictive Inference Engine**: Next Target.

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

5. **Run Phase 6 Fault-Injection & Alerting Verification Demo**:
   ```bash
   python -m alerts.demo
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
- [docs/phase6/rule-engine.md](docs/phase6/rule-engine.md) — Phase 6 rule evaluator and catalog.
- [docs/phase6/alert-lifecycle.md](docs/phase6/alert-lifecycle.md) — Phase 6 alert lifecycle and state machine.
- [docs/phase6/dashboard-alerts.md](docs/phase6/dashboard-alerts.md) — Phase 6 React alert console and components.
- [docs/phase7/ml-architecture.md](docs/phase7/ml-architecture.md) — Phase 7 ML architecture & pipeline overview.
- [docs/phase7/dataset-generation.md](docs/phase7/dataset-generation.md) — Phase 7 dataset collectors and simulation generator.
- [docs/phase7/feature-engineering.md](docs/phase7/feature-engineering.md) — Phase 7 temporal features and signal whitelisting.
- [docs/phase7/leakage-prevention.md](docs/phase7/leakage-prevention.md) — Phase 7 ground-truth isolation & anti-leakage controls.
- [docs/phase7/anomaly-detection.md](docs/phase7/anomaly-detection.md) — Phase 7 unsupervised Isolation Forest model.
- [docs/phase7/rul-regression.md](docs/phase7/rul-regression.md) — Phase 7 HistGradientBoosting RUL model.
- [docs/phase7/mlflow-tracking.md](docs/phase7/mlflow-tracking.md) — Phase 7 local MLflow experiment tracking.
- [docs/phase7/model-export.md](docs/phase7/model-export.md) — Phase 7 model binary & metadata export.
- [docs/phase7/evaluation-results.md](docs/phase7/evaluation-results.md) — Phase 7 evaluation benchmarks and results.
- [docs/phase7/reproducibility.md](docs/phase7/reproducibility.md) — Phase 7 reproducibility and command execution guide.

---

## Git Workflow

- **`main`**: Production-ready, stable releases.
- **`dev`**: Active development, feature implementation, and documentation.

All development occurs on `dev`. Merging to `main` is executed strictly via reviewed Pull Requests following full test verification.