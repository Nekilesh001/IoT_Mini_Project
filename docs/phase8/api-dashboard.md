# API Endpoints & React Dashboard

## 1. FastAPI REST Endpoints

Mounted under `/api/ml`:

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/api/ml/status` | Global Edge ML engine health, active models, backend |
| `GET` | `/api/ml/models` | Detailed catalog of loaded model versions and metadata |
| `GET` | `/api/ml/machines/{machine_id}` | Latest ML inference result for a specific machine |
| `GET` | `/api/ml/inferences` | Paginated query of recent ML inference records |
| `GET` | `/api/ml/metrics` | In-memory latency metrics (mean, p95, percentiles) |
| `GET` | `/api/ml/fleet-summary` | Fleetwide summary of anomalous and low-RUL machines |

## 2. Real-Time Server-Sent Events (SSE)

Real-time predictions are broadcasted over the existing `/api/realtime/stream` SSE channel using a distinct event type:

```
event: ml_inference
data: {"machine_id": "CNC-001", "anomaly_score": 0.654, "anomaly_label": "ANOMALOUS", "predicted_rul_seconds": 3600.0, "latency_ms": 657.8, ...}
```

## 3. React Dashboard Visualizations

- **Overview Page (`/`)**: Added Fleet Predictive Health KPI cards (`Anomalous Machines`, `Critical RUL Machines`).
- **Dedicated Predictive ML Page (`/ml`)**: Added live telemetry table, loaded model status cards, and latency percentiles.
- **Machine Detail Page (`/machines/:id`)**: Added Edge ML Predictive Maintenance card with live anomaly score gauge, status badge, and RUL forecast.
