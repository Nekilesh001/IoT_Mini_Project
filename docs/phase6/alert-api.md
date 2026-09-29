# Phase 6: Alert & Fault Scenario REST API

## 1. Alert Endpoints

| Method | Endpoint | Description | Query Parameters |
|---|---|---|---|
| `GET` | `/api/alerts` | List historical and active alerts | `machine_id`, `severity`, `status`, `start`, `end`, `limit` |
| `GET` | `/api/alerts/active` | List all un-resolved alerts (`OPEN` / `ACKNOWLEDGED`) | `limit` (default: 50) |
| `GET` | `/api/alerts/summary` | Get aggregated factory alert KPIs | None |
| `GET` | `/api/alerts/{alert_id}` | Retrieve details for a specific alert | None |
| `POST` | `/api/alerts/{alert_id}/acknowledge` | Acknowledge an open alert | JSON body: `{"acknowledged_by": "operator"}` |
| `POST` | `/api/alerts/{alert_id}/resolve` | Resolve an active alert | JSON body: `{"resolution_notes": "..."}` |
| `GET` | `/api/machines/{machine_id}/alerts`| List alerts for a specific machine | `limit` (default: 50) |

---

## 2. Fault Scenario Control Endpoints (Developer / Demo)

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/scenarios` | List all registered fault scenarios and their active states |
| `POST` | `/api/scenarios/{scenario_id}/start` | Trigger a controlled fault scenario |
| `POST` | `/api/scenarios/{scenario_id}/stop` | Stop an active scenario and restore normal physics |
| `POST` | `/api/demo/faults/{scenario_id}` | Developer demo shortcut for fault injection |

---

## 3. Realtime SSE Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/realtime/events` | Multi-event stream emitting both `event: telemetry` and `event: alert` |
| `GET` | `/api/realtime/alerts` | Dedicated alert event stream for low-latency operational consoles |
