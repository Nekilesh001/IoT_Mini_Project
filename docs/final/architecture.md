# Final System Architecture — Smart Factory Machine Monitoring & Predictive Maintenance

## 1. High-Level System Architecture

The Smart Factory system implements a **Local-First, Cloud-Optional Hybrid Architecture**. All operational capabilities—including multi-protocol simulation, edge ingestion, time-series storage, rule alerting, ML inference, Device Shadow digital twins, management jobs, and RBAC security—execute completely offline on local compute. An AWS-ready cloud interface layer is architected for future hybrid synchronization without creating active runtime dependencies.

```mermaid
graph TD
    subgraph Factory Floor [12 Heterogeneous Simulated Machines]
        M1[CNC-001 / CNC-002]
        M2[ROB-001 / ROB-002]
        M3[CON-001 / PRS-001]
        M4[IMM-001 / CMP-001]
        M5[PMP-001 / VIS-001]
        M6[AGV-001 / CHL-001]
    end

    subgraph Protocol Layer [Multi-Protocol Adapters]
        P_MB[Modbus TCP Server & Adapter]
        P_OPC[OPC UA Server & Adapter]
        P_MQTT[MQTT Broker & Adapter]
    end

    subgraph Edge Gateway [Edge Ingestion & ML Pipeline]
        NORM[Unit Normalization & Validation]
        SEQ[Sequence & Deduplication Engine]
        CANON[Canonical Telemetry JSON]
        FEAT[Realtime Temporal Feature Extractor]
        ML_ANOM[Isolation Forest Anomaly Model]
        ML_RUL[HistGradientBoosting RUL Model]
    end

    subgraph Operations & Storage [Local Event Bus & Data Persistence]
        EB[MQTT Event Bus]
        BUF[Persistent Store-and-Forward SQLite Buffer]
        PG[(PostgreSQL / SQLite Database)]
        RULES[Deterministic Rule Alert Engine]
        SHADOW[Device Shadow & Fleet Job Engine]
    end

    subgraph Application & Presentation [Edge API & UI]
        API[FastAPI Gateway + RBAC Middleware]
        REACT[React Operations Dashboard]
    end

    subgraph Security Boundary [Local Defense-in-Depth]
        PKI[Local X.509 CA & TLS/mTLS Context]
        AUTH[JWT Authentication & PBKDF2]
        RBAC[4-Tier RBAC Policy Engine]
        AUDIT[Security Audit Trail with Secret Scrubbing]
    end

    subgraph Cloud Scaffold [Phase 11: Planned / Not Connected]
        AWS_ADAPTER[AWS IoT Core / Shadow / Jobs Adapter Scaffolding]
    end

    %% Flow connections
    M1 & M2 & M3 & M4 & M5 & M6 --> P_MB & P_OPC & P_MQTT
    P_MB & P_OPC & P_MQTT --> NORM
    NORM --> SEQ --> CANON
    CANON --> EB --> BUF --> PG
    CANON --> RULES --> PG
    CANON --> FEAT --> ML_ANOM & ML_RUL --> PG
    SHADOW <--> PG
    PG --> API
    API --> REACT
    SECURITY_PERIMETER -.-> PKI & AUTH & RBAC & AUDIT
    API -.-> AWS_ADAPTER
```

---

## 2. Telemetry Ingestion Flow

```mermaid
sequenceDiagram
    participant Machine as Factory Machine (Physics Sim)
    participant Protocol as Protocol Server/Adapter
    participant Edge as Edge Ingestion Service
    participant Buffer as Persistent Store-and-Forward Buffer
    participant DB as PostgreSQL / SQLite Storage
    participant ML as ML Inference Engine
    participant Alerts as Alert Engine
    participant Dashboard as React Dashboard (SSE)

    Machine->>Protocol: Raw Sensor State (Modbus/OPC UA/MQTT)
    Protocol->>Edge: ProtocolReading Envelope
    Edge->>Edge: Validate Schema, Range & Physical Limits
    Edge->>Edge: Engineering Unit Normalization (SI Units)
    Edge->>Edge: Sequence Tracking & Deduplication
    Edge->>Buffer: Store Canonical Telemetry
    Buffer->>DB: Batch Insert (Zero Loss)
    Edge->>ML: Feed Observable Features
    ML->>ML: Isolation Forest Anomaly + RUL Estimation
    Edge->>Alerts: Evaluate Deterministic Rules & Hysteresis
    DB->>Dashboard: Stream Canonical Telemetry, Alerts & ML Predictions via SSE
```

---

## 3. Device Management & Digital Twin Flow

```mermaid
graph LR
    subgraph Operator / Dashboard
        UI[React Management Console]
    end

    subgraph FastAPI Gateway
        EP[REST Endpoints /api/devices /api/jobs]
        AUTH_GUARD[RBAC Authorization Dependency]
    end

    subgraph Device Management Core
        SHADOW_MGR[Device Shadow Manager]
        JOB_ENG[Management Job Engine]
        AUDIT_LOG[Management Audit Repository]
    end

    subgraph Factory Simulator
        SIM[Machine State Controller]
    end

    UI -->|POST /desired state| EP
    EP --> AUTH_GUARD
    AUTH_GUARD --> SHADOW_MGR
    SHADOW_MGR -->|Compute Delta| SHADOW_MGR
    SHADOW_MGR -->|Record Mutation| AUDIT_LOG
    SHADOW_MGR -->|Dispatch Action| JOB_ENG
    JOB_ENG -->|Execute Command| SIM
    SIM -->|Reported State| SHADOW_MGR
```

---

## 4. Security & Access Control Boundaries

- **Authentication**: Stateless Bearer JWT tokens signed with HMAC-SHA256 (`HS256`). Development accounts bootstrapped via environment configuration (`admin`, `operator`, `maintainer`, `viewer`).
- **Authorization**: Granular permissions mapped hierarchically:
  - `VIEWER`: Read-only access to telemetry, machine status, active alerts, and ML predictions.
  - `OPERATOR`: Viewer permissions + alert acknowledgement/resolution, command execution, and desired-state modifications.
  - `MAINTAINER`: Operator permissions + configuration job dispatch, OTA simulation, and fault scenario injection.
  - `ADMIN`: Full management access + security audit trail and certificate operations.
- **Secret Scrubbing**: Automatic regex and high-entropy string masking (`[REDACTED]`) across all error handlers and security audit logs.
- **Transport Security**: Local X.509 PKI certificate generation and mutual TLS (mTLS) enforcement with safe fallback (`TLS_ENABLED=false`).

---

## 5. Failure Injection & Resilience Boundaries

- **Store-and-Forward Buffering**: When the event bus or database storage is unavailable, telemetry is diverted to a local SQLite buffer table.
- **Deterministic Replay**: Upon reconnection, a background replay worker drains buffered records in sequence order, guaranteeing zero data loss and preventing duplicate persistence.
- **Circuit Isolation**: Failure in an individual machine protocol adapter (e.g. `PMP-001` MQTT disconnect) isolates the machine to `DEGRADED`/`OFFLINE` without impacting adjacent production lines.
- **Graceful ML Fallback**: If an ONNX runtime or model file is unavailable, the ML subsystem marks inference status as `DEGRADED` while raw telemetry ingestion and deterministic rule-based alerts continue uninterrupted.
- **Anti-Leakage Boundary**: Ground-truth degradation percentages and hidden failure timestamps are strictly prohibited from leaking into operational telemetry, REST APIs, or UI components.

---

## 6. AWS Future Integration Architecture (Phase 11 Scaffolding)

```mermaid
graph TD
    subgraph Local Edge Environment [Current Verified Implementation]
        L_SHADOW[Local Device Shadow]
        L_JOBS[Local Job Engine]
        L_FLEET[Local Fleet Catalog]
        L_MQTT[Local MQTT Event Bus]
    end

    subgraph Cloud Interface Layer [Phase 9/11 Abstract Scaffold]
        IF_SHADOW[CloudDeviceStateInterface]
        IF_JOBS[CloudJobsInterface]
        IF_FLEET[CloudFleetIndexingInterface]
    end

    subgraph AWS Cloud [Future Optional Connection]
        AWS_SHADOW[AWS IoT Device Shadow]
        AWS_JOBS[AWS IoT Jobs]
        AWS_INDEX[AWS IoT Fleet Indexing]
        AWS_CORE[AWS IoT Core Broker]
    end

    L_SHADOW -.-> IF_SHADOW -.-> AWS_SHADOW
    L_JOBS -.-> IF_JOBS -.-> AWS_JOBS
    L_FLEET -.-> IF_FLEET -.-> AWS_INDEX
    L_MQTT -.-> AWS_CORE
```
