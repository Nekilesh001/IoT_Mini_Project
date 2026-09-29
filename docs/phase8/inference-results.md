# Unified ML Inference Results & Persistence

## 1. Unified Result Schema

Every inference execution yields an `MLInferenceResult` (`ml/inference/result.py`):

| Field | Type | Description |
| :--- | :--- | :--- |
| `result_id` | `str (UUID4)` | Unique natural key of the inference run |
| `machine_id` | `str` | Target machine identifier (e.g. `CNC-001`) |
| `machine_type` | `str` | Target machine type (e.g. `CNC_MACHINE`) |
| `event_time` | `datetime / ISO str` | Source telemetry event timestamp |
| `inference_time` | `datetime / ISO str` | Machine inference timestamp |
| `anomaly_score` | `Optional[float]` | Calibrated anomaly risk score in range `[0.0, 1.0]` |
| `raw_anomaly_score` | `Optional[float]` | Raw Isolation Forest decision score |
| `anomaly_label` | `AnomalyLabel` | Enum: `NORMAL`, `ANOMALOUS`, `UNKNOWN` |
| `predicted_rul_seconds`| `Optional[float]` | Remaining Useful Life prediction in seconds |
| `predicted_rul_minutes`| `Optional[float]` | Display RUL in minutes |
| `anomaly_model_name` | `str` | Model identifier: `anomaly_isolation_forest` |
| `anomaly_model_version` | `str` | Model version: `v1.0.0` |
| `rul_model_name` | `str` | Model identifier: `rul_gradient_boosting` |
| `rul_model_version` | `str` | Model version: `v1.0.0` |
| `feature_manifest_version` | `str` | Feature schema version: `1.0.0` |
| `feature_count` | `int` | Validated feature count (1019) |
| `runtime_backend` | `RuntimeBackend` | Active backend: `ONNX` or `SKLEARN` |
| `status` | `InferenceStatus`| Enum: `READY`, `NOT_READY`, `DEGRADED`, `ERROR` |
| `latency` | `LatencyBreakdown`| Latency in ms for feature gen, anomaly, RUL, total |

## 2. Storage Repository (`ml_inferences`)

Results are persisted through `MLInferenceRepository` (`storage/repository.py`) into the `ml_inferences` table:
- **Idempotency**: Indexed on `(machine_id, event_time)` and `result_id`.
- **Fleet Summaries**: Provides fast aggregate status queries for React overview dashboards.
- **Dialect Portability**: Tested and fully supported on PostgreSQL and SQLite.
