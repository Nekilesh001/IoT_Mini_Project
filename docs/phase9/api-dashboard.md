# API Endpoints & React Operations Console

## 1. REST API Endpoints

- `GET /api/devices`: List all registered fleet machines with optional connectivity/management filters.
- `GET /api/devices/{machine_id}`: Retrieve machine metadata.
- `PATCH /api/devices/{machine_id}`: Update machine metadata or versions.
- `GET /api/devices/{machine_id}/shadow`: Fetch digital twin shadow and delta.
- `PATCH /api/devices/{machine_id}/shadow`: Update desired configuration with optimistic concurrency validation.
- `POST /api/devices/{machine_id}/shadow/sync`: Acknowledge reported state synchronization.
- `GET /api/devices/{machine_id}/jobs`: Machine job history.
- `GET /api/jobs`: Fleetwide job list with filters.
- `POST /api/jobs`: Dispatch new management job.
- `POST /api/commands/execute`: Validate and dispatch administrative command.
- `GET /api/jobs/{job_id}`: Query job status.
- `POST /api/jobs/{job_id}/execute`: Execute job locally through its lifecycle.
- `POST /api/jobs/{job_id}/cancel`: Cancel pending/running job.
- `GET /api/jobs/{job_id}/attempts`: Detailed execution attempts.
- `GET /api/fleet/summary`: Aggregated KPI counts.
- `GET /api/management/audit`: Chronological audit trail.

## 2. React Management Console (`/management`)

- Integrated into main operations layout with sidebar navigation.
- Real-time fleet KPI summary cards.
- Interactive fleet inventory table with per-machine shadow inspection.
- Side-by-side Desired vs. Reported JSON viewer with pending sync indicators.
- One-click state synchronization trigger.
- Management job creation form with live execution and attempt tracking.
