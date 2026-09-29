# API Architecture — Phase 5 Application Layer

This document details the architecture, design principles, and data flow of the FastAPI application layer in the Smart Factory Machine Monitoring and Predictive Maintenance System.

---

## 1. Architectural Role & Boundary

The FastAPI application serves as the primary query, streaming, and REST abstraction layer for operational dashboards and client tooling. It bridges the Phase 4 persistent store (PostgreSQL) and the frontend dashboard without coupling to raw industrial communication protocols or simulation mechanics.

```
+-------------------------------------------------------------+
|                      Edge & Ingestion                       |
|  Simulator -> Industrial Adapters -> Edge Pipeline -> DB   |
+-------------------------------------------------------------+
                               |
                               v
                     [ PostgreSQL Database ]
                               |
                               v
+-------------------------------------------------------------+
|                      Phase 5 Backend                        |
|   TelemetryRepository -> API Services -> FastAPI Routes     |
+-------------------------------------------------------------+
                               |
                               v
+-------------------------------------------------------------+
|                      Frontend Layer                         |
|      React + Vite Dashboard (REST Queries + SSE Stream)     |
+-------------------------------------------------------------+
```

### Strict Architectural Boundaries
- **No Physics or Simulation Logic**: The API layer never computes physics, synthetic degradation, or simulator counters.
- **No Direct Protocol Server Logic**: Modbus/OPC UA/MQTT servers are isolated in the simulator/protocol tier. The API interacts solely with normalized canonical telemetry records in the repository.
- **Decoupled Database Access**: Route handlers do not write ad-hoc SQL or SQLAlchemy queries; all data queries route through dedicated service classes (`FactoryService`, `TelemetryService`, `RealtimeService`) and the `TelemetryRepository`.
- **Target Leakage Prohibition**: Ground-truth simulation counters (`degradation_level`, `fault_label`, `hidden_wear_counter`, `scenario_id`, `_simulationGroundTruth`) are strictly omitted from API models and schema serialization.

---

## 2. Directory Layout

The `api/` package is structured into modular layers:

```
api/
├── __init__.py
├── __main__.py          # Execution entrypoint (python -m api)
├── config.py            # Pydantic Settings (CORS, DB URL, ports, intervals)
├── dependencies.py      # Dependency injection (DB session, repository, machine profiles)
├── demo.py              # End-to-end local integration demo
├── main.py              # FastAPI application factory and route registration
├── schemas/             # Pydantic schemas for API inputs and outputs
│   ├── factory.py       # FactorySummary, PlantSummary, LineSummary
│   ├── health.py        # SystemHealthResponse, ProtocolHealthSummary
│   ├── machine.py       # MachineOverview, MachineDetail, SignalCatalogEntry
│   └── telemetry.py     # CanonicalTelemetryResponse, HistoryQueryResponse
├── services/            # Business and query aggregation layer
│   ├── factory_service.py
│   ├── telemetry_service.py
│   └── realtime_service.py
└── routes/              # FastAPI APIRouter endpoints
    ├── health.py        # /api/health, /api/protocols/health
    ├── factory.py       # /api/factory/summary
    ├── machines.py      # /api/machines, /api/machines/{id}, /api/machines/{id}/history
    ├── telemetry.py     # /api/telemetry/latest
    └── realtime.py      # /api/realtime/telemetry (SSE stream)
```

---

## 3. Core Components

### Configuration (`api.config`)
- Configured via environment variables with sensible local defaults:
  - `DATABASE_URL`: PostgreSQL connection string (defaults to `postgresql://postgres:postgres@localhost:5432/smart_factory`).
  - `API_HOST`: `0.0.0.0`
  - `API_PORT`: `8000`
  - `CORS_ORIGINS`: Comma-separated allowed frontend origins (defaults to `["http://localhost:5173", "http://localhost:3000"]`).
  - `REALTIME_POLL_INTERVAL`: Server-side SSE poll frequency (defaults to `1.0` seconds).
  - `MAX_TELEMETRY_HISTORY_LIMIT`: Query ceiling (defaults to `2000`).

### Dependency Injection (`api.dependencies`)
- Provides singleton engine management with multi-threaded SQLite fallback support for testing (`StaticPool`).
- Yields scoped `Session` instances and initializes `TelemetryRepository`.
- Injects immutable 12-machine metadata profiles across 3 production lines (CNC, AGV, Chiller, Robot Arm, Injection Molding, CMM, Conveyor, Packager).

### Query Services (`api.services`)
- **FactoryService**: Computes aggregate machine counts, operational state distribution (RUNNING, IDLE, WARNING, FAULT, MAINTENANCE, OFF), protocol coverage, and plant/line hierarchies.
- **TelemetryService**: Fetches latest readings, time-bounded telemetry sequences, bounded pagination, and signal sub-selection.
- **RealtimeService**: Manages an async generator streaming newly ingested telemetry records via Server-Sent Events with sequence-based deduplication and graceful client disconnection handling.

---

## 4. Error Handling & OpenAPI Documentation

- Standardized HTTP status codes:
  - `200 OK`: Successful query or telemetry retrieval.
  - `400 Bad Request`: Invalid time range parameter (`start` > `end`).
  - `404 Not Found`: Unknown `machine_id`.
  - `422 Unprocessable Entity`: Schema/parameter validation failure.
  - `500 Internal Server Error`: Safe error envelope with sanitized message.
- Interactive API documentation is available at `/docs` (Swagger UI) and `/redoc` (ReDoc), generated from Pydantic schemas.
