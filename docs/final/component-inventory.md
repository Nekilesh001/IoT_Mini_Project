# System Component Inventory — Smart Factory System

| Component | Purpose | Primary Inputs | Primary Outputs | Technology | Introduced | Status |
|---|---|---|---|---|:---:|:---:|
| **Factory Simulator** | Physics and state simulation for 12 heterogeneous machines | Simulation clock tick, operational load factor | Raw sensor metrics, machine state snapshots | Python, NumPy, SciPy | Phase 1 | Active |
| **Modbus TCP Server & Adapter** | Industrial register mapping for CNCs, Presses, Compressors | Simulated telemetry registers | `ProtocolReading` objects | PyModbus, Python | Phase 2 | Active |
| **OPC UA Server & Adapter** | Structured node address space for Robots, Milling, Inspection | Simulated telemetry nodes | `ProtocolReading` objects | asyncua, Python | Phase 2 | Active |
| **MQTT Publisher & Adapter** | Publish/subscribe broker messaging for Pumps, AGVs, Robots | JSON telemetry topics | `ProtocolReading` objects | Paho MQTT, Python | Phase 2 | Active |
| **Edge Ingestion Service** | Normalization, validation, sequence tracking, deduplication | `ProtocolReading` objects | `CanonicalTelemetry` envelopes | Pydantic, Python | Phase 3 | Active |
| **Persistent Buffer** | Local SQLite store-and-forward queue surviving outages/restarts | Unrouted canonical telemetry | Replayed batch records | SQLite, Python | Phase 4 | Active |
| **Storage Repository** | Time-series and relational persistence | Canonical telemetry, alerts, ML inferences, job records | Query results, history slices | PostgreSQL / SQLite, SQLAlchemy | Phase 4 | Active |
| **Rule Alert Engine** | Deterministic threshold alarms with hysteresis and cooldown | Streaming `CanonicalTelemetry` | `AlertRecord` mutations | Python, SQLAlchemy | Phase 6 | Active |
| **ML Feature Pipeline** | Temporal window aggregations and feature extraction (1019 features) | Streamed machine measurements | 1019-dimensional feature vectors | NumPy, Scikit-Learn | Phase 7/8 | Active |
| **Isolation Forest Anomaly Model** | Unsupervised edge anomaly detection | 1019 temporal feature vector | Anomaly score (0.0–1.0), label | Scikit-Learn, ONNX Runtime | Phase 7/8 | Active |
| **HistGradientBoosting RUL Model** | Regression Remaining Useful Life estimation | 1019 temporal feature vector | Estimated RUL in operating hours | Scikit-Learn, ONNX Runtime | Phase 7/8 | Active |
| **Edge ML Inference Service** | Sub-millisecond real-time model scoring and fallback management | Streaming `CanonicalTelemetry` | `MLInferenceResult` records | ONNX Runtime, Python | Phase 8 | Active |
| **Device Shadow Manager** | Digital twin desired/reported state tracking and delta computation | Desired state patches, live telemetry | `DeviceShadowRecord`, deltas | SQLAlchemy, Python | Phase 9 | Active |
| **Job Manager & Retry Engine** | Management job scheduling, execution, and attempt tracking | Job create requests, machine commands | `ManagementJobRecord`, attempt logs | SQLAlchemy, Python | Phase 9 | Active |
| **Security Subsystem** | Identity verification, JWT tokens, RBAC, X.509 PKI, audit logging | User credentials, API requests, certs | JWT tokens, audit records, SSLContext | Cryptography, PyJWT, PBKDF2 | Phase 10 | Active |
| **Failure Testing Suite** | Deterministic chaos injection and recovery verification | Scenario triggers (15 catalog modes) | `ScenarioExecutionResult`, metrics | Python, SQLite | Phase 12 | Active |
| **FastAPI Backend Gateway** | REST API endpoints, SSE streams, security middleware | Client HTTP/SSE requests | JSON responses, SSE event streams | FastAPI, Uvicorn, Starlette | Phase 5/10 | Active |
| **React Operations Console** | Visual operational monitoring and administrative management | REST/SSE data from edge API | Interactive UI views and charts | React 19, TypeScript, Vite | Phase 5/9/10/12 | Active |
| **Benchmarking Suite** | Automated local performance and throughput profiling | Benchmark iterations | Console summary, JSON artifact | Python, psutil | Phase 13 | Active |
| **AWS Scaffolding** | Cloud-ready abstract interfaces and adapter templates | Local shadow, fleet, job states | (Planned cloud synchronization) | Python abstract interfaces | Phase 9/11 | Planned / Not Connected |
