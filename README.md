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
Local Event Bus (MQTT) & Storage (PostgreSQL / TimescaleDB)
       ↓
FastAPI Backend & React Operations Dashboard
```

---

## Candidate Implementation Technologies

> [!NOTE]
> **Validation Notice**: The libraries, frameworks, and tools listed below represent **candidate implementation technologies** subject to prototyping and empirical validation during future development phases, rather than permanently frozen architectural choices.

- **Simulation & Edge (Candidate Stack)**: Python 3.11+, PyModbus, asyncua, Eclipse Paho MQTT, ONNX Runtime.
- **Message Bus & Storage (Candidate Stack)**: Eclipse Mosquitto (MQTT), PostgreSQL / TimescaleDB, Redis.
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

Current Status: **Phase 2 — Protocol Simulation and Protocol Adapters (COMPLETED)**

- **Phase 0 — Architecture & Control Docs**: Completed.
- **Phase 1 — Factory Simulation Core**: Completed. Run local demo via `python -m simulator` or test suite via `python -m pytest tests/simulator/`.
- **Phase 2 — Protocol Simulation & Adapters**: Completed. Run local protocol demo via `python -m protocols.protocol_demo` or test suite via `python -m pytest tests/protocols/`.
- **Phase 3 — Canonical Telemetry & Edge Ingestion**: Next Target.

For detailed architectural details and documentation:
- [AGENTS.md](AGENTS.md) — AI agent execution guidelines and strict constraints.
- [PROJECT_SPECIFICATION.md](PROJECT_SPECIFICATION.md) — Master architectural blueprint and data schemas.
- [PHASE_STATUS.md](PHASE_STATUS.md) — Current implementation milestone tracker.
- [docs/phase1/simulation-architecture.md](docs/phase1/simulation-architecture.md) — Phase 1 simulation architecture.
- [docs/phase2/protocol-architecture.md](docs/phase2/protocol-architecture.md) — Phase 2 protocol architecture and adapters.

---

## Git Workflow

- **`main`**: Production-ready, stable releases.
- **`dev`**: Active development, feature implementation, and documentation.

All development occurs on `dev`. Merging to `main` is executed strictly via reviewed Pull Requests following full test verification.