# Operations Runbook — Smart Factory System

## 1. System Lifecycle Operations

### Starting the System
1. **Database & Storage**: Ensure local SQLite (`data/telemetry_dev.db`) or PostgreSQL instance is accessible.
2. **FastAPI Edge Gateway**:
   ```bash
   uvicorn api.main:app --host 0.0.0.0 --port 8000
   ```
3. **React Operations Dashboard**:
   ```bash
   cd dashboard/react-app && npm run dev
   ```

### Stopping the System
- Gracefully stop FastAPI using `Ctrl+C`.
- In-memory buffers flush uncommitted events to `data/telemetry_dev.db` before shutdown.

---

## 2. Operational Health Checks

| Check Target | Command / Endpoint | Expected Healthy Response |
|---|---|---|
| **API Gateway Health** | `GET http://localhost:8000/api/health` | `{"status": "ok", "timestamp": "..."}` |
| **Active Machine List** | `GET http://localhost:8000/api/machines` | Array of 12 machine objects with `operating` states |
| **Active Alerts Triage** | `GET http://localhost:8000/api/alerts/active` | Array of unacknowledged and active alert records |
| **ML Inference Status** | `GET http://localhost:8000/api/ml/status` | `{"status": "READY", "features": 1019, "backend": "SKLEARN"}` |
| **Fleet Device Summary** | `GET http://localhost:8000/api/fleet/summary` | Aggregated count of `ONLINE`, `DEGRADED`, `MAINTENANCE` |
| **Security Status** | `GET http://localhost:8000/api/security/status` | `{"tls_enabled": false, "rbac_enabled": true}` |
| **Resilience Status** | `GET http://localhost:8000/api/resilience/status` | Component health metrics and active fault indicators |

---

## 3. Operations & Maintenance Procedures

### Alert Acknowledgment
- **API**: `POST /api/alerts/{alert_id}/ack` (Requires `OPERATOR` role).
- **Dashboard**: Click "Acknowledge" on the `/alerts` page.

### Device Shadow Desired State Update
- **API**: `POST /api/devices/{machine_id}/shadow` with payload `{"desired_state": {"target_rpm": 1500}}` (Requires `OPERATOR` role).
- **Dashboard**: Use digital twin editor on the `/management` page.

### Executing Management Jobs
- **API**: `POST /api/jobs/config` with payload `{"machine_id": "CNC-001", "parameters": {...}}` (Requires `MAINTAINER` role).

### Running Security Hygiene & Resilience Scans
- Secret scanner: `python -m security.validation`
- Failure recovery suite: `python -m failure_testing.demo`
- System benchmarks: `python -m benchmarking.demo`
