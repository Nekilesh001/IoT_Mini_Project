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

Current Status: **Phase 5 — FastAPI Backend Service & React Operations Dashboard (COMPLETED)**

- **Phase 0 — Architecture & Control Docs**: Completed.
- **Phase 1 — Factory Simulation Core**: Completed. Run local demo via `python -m simulator` or test suite via `python -m pytest tests/simulator/`.
- **Phase 2 — Protocol Simulation & Adapters**: Completed. Run local protocol demo via `python -m protocols.protocol_demo` or test suite via `python -m pytest tests/protocols/`.
- **Phase 3 — Canonical Telemetry & Edge Ingestion**: Completed. Run local edge demo via `python -m edge.demo` or test suite via `python -m pytest tests/edge/`.
- **Phase 4 — Local Storage, MQTT Event Bus & Buffering**: Completed. Run local storage demo via `python -m storage.demo` or test suite via `python -m pytest tests/storage/ tests/event_bus/ tests/integration/`.
- **Phase 5 — FastAPI Backend & React Dashboard**: Completed. Run API backend via `python -m api`, frontend via `cd dashboard/react-app && npm run dev`, end-to-end demo via `python -m api.demo`, or test suite via `python -m pytest tests/api/`.
- **Phase 6 — Fault Injection Framework & Rule-Based Alerts**: Next Target.

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

4. **Start React Operations Dashboard**:
   ```bash
   cd dashboard/react-app
   npm install
   npm run dev
   ```
   - Dashboard UI: `http://localhost:5173`

5. **Run One-Shot End-to-End API/SSE Verification Demo**:
   ```bash
   python -m api.demo
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

---

## Git Workflow

- **`main`**: Production-ready, stable releases.
- **`dev`**: Active development, feature implementation, and documentation.

All development occurs on `dev`. Merging to `main` is executed strictly via reviewed Pull Requests following full test verification.