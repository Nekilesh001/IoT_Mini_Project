# Resilience & Failure Recovery Final Summary

## 1. 15-Scenario Failure Catalog

| Scenario ID | Target Subsystem | Injected Fault Condition | Verified System Resilience Behavior |
|---|---|---|---|
| `MQTT_OUTAGE` | Event Bus | Local broker connection dropped | Telemetry buffered in SQLite `PersistentBuffer`; 100% replayed on reconnect with zero data loss. |
| `DATABASE_OUTAGE` | Storage | Primary PostgreSQL/SQLite throws ConnectionError | Upstream ingestion unblocked; store-and-forward queue accumulates records and drains on recovery. |
| `BUFFER_PRESSURE` | Buffer Queue | Extreme volume exceeding memory threshold | Circular eviction protects memory; critical alert telemetry prioritized. |
| `PROTOCOL_ADAPTER_FAILURE` | Protocol Layer | Single adapter connection dropped (`PMP-001`) | Machine isolated to `DEGRADED`/`OFFLINE`; remaining 11 machines continue normal publishing. |
| `INVALID_TELEMETRY` | Edge Ingestion | Corrupted schema or invalid datatypes | Rejected at edge validation boundary; routed to dead-letter log without pipeline crash. |
| `DUPLICATE_TELEMETRY` | Edge Ingestion | Duplicate event IDs or re-sent sequence numbers | Deduplication window drops duplicates; downstream tables remain clean. |
| `OUT_OF_ORDER_TELEMETRY` | Edge Ingestion | Non-monotonic sequence packet delivery | Sequence tracker flags sequence anomalies without dropping data. |
| `STALE_TELEMETRY` | Edge Ingestion | Stale timestamped packet arrival (>60s lag) | Quality engine tags `QualityCode.STALE`; excluded from real-time ML feature windows. |
| `ML_MODEL_MISSING` | ML Inference | Model `.joblib` or `.onnx` binary file deleted | Subsystem transitions to `DEGRADED`; raw telemetry ingestion and rule alerts continue. |
| `ML_INFERENCE_ERROR` | ML Inference | Inference runtime exception or dimension mismatch | Exception caught gracefully; error logged without crashing host ingestion worker. |
| `ALERT_PERSISTENCE_FAILURE` | Alert Engine | Alert repository database write failure | In-memory fallback captures active alerts; evaluated rules continue firing. |
| `API_DEPENDENCY_FAILURE` | REST Gateway | Backend service dependency timeout | Returns HTTP 503/200 partial status with degradation headers without unhandled 500 crash. |
| `JOB_RETRY_EXHAUSTION` | Device Jobs | Target machine unresponsive to command | Job retries up to max limit (3 attempts) with backoff; transitions cleanly to `FAILED`. |
| `NETWORK_INTERRUPTION` | Network | Transient network drop | Adapters enter backoff reconnect loop; store-and-forward preserves unpublished packets. |
| `SERVICE_RESTART_RECOVERY` | Edge Service | Process terminated while 50+ records buffered | Upon process restart, `PersistentBuffer` scans unacknowledged records and replays all. |

## 2. Invariant Verification Summary
- **Zero Data Loss**: In all controlled network and database outage tests, 100% of generated records were recovered and persisted.
- **Zero Duplicate Ingestion**: Deduplication engine prevents duplicate storage records.
- **Anti-Leakage Preservation**: Fault injection parameters and ground-truth wear levels never leak into telemetry, logs, or UI.
