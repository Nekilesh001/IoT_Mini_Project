# Phase 12 — Failure Scenario Catalog

## 15-Scenario Catalog

| ID | Scenario Name | Target Component | Expected Resilience Behavior |
|---|---|---|---|
| `mqtt_outage` | MQTT Event Bus Outage | `EVENT_BUS` | Buffers messages to SQLite store-and-forward; replays on broker reconnection with zero loss. |
| `database_outage` | PostgreSQL / Storage Outage | `DATABASE` | Upstream pipeline unblocked; retries with exponential backoff; auto-flushes buffer on recovery. |
| `buffer_pressure` | Storage Buffer Pressure | `STORAGE` | Circular eviction prevents crash under extreme disk pressure; critical alerts prioritized. |
| `protocol_adapter_failure` | Protocol Adapter Failure | `PROTOCOL_ADAPTER` | Single machine failure isolates error; unaffected machines continue publishing telemetry. |
| `invalid_telemetry` | Invalid Telemetry Payload | `EDGE_QUALITY` | Schema validation catches corrupted schema and routes to dead-letter queue. |
| `duplicate_telemetry` | Duplicate Telemetry Messages | `EDGE_QUALITY` | Sliding-window deduplication drops exact duplicate event IDs. |
| `out_of_order_telemetry` | Out-of-Order Telemetry | `EDGE_QUALITY` | Monotonic sequence tracker orders messages or flags sequence anomalies. |
| `stale_telemetry` | Stale Timestamped Telemetry | `EDGE_QUALITY` | Late arrival detector tags stale data without corrupting real-time models. |
| `ml_model_missing` | ML Model File Missing | `ML_INFERENCE` | Pipeline marks ML subsystem DEGRADED; raw telemetry and rule alerts unaffected. |
| `ml_inference_error` | ML Inference Runtime Exception | `ML_INFERENCE` | Error caught gracefully; logged without crashing edge worker. |
| `alert_persistence_failure` | Alert Persistence Failure | `ALERT_ENGINE` | Transient database error in alert engine buffered; rule evaluation continues. |
| `api_dependency_failure` | API Dependency Failure | `API` | Degradation indicators returned with HTTP 503/200 partial data without unhandled 500 crashes. |
| `job_retry_exhaustion` | Job Failure & Retry Exhaustion | `DEVICE_JOB` | Retries up to max limit with backoff; transitions cleanly to FAILED; audit record emitted. |
| `network_interruption` | Network Interruption Simulation | `NETWORK` | Adapters enter reconnection state; buffer preserves unpublished telemetry. |
| `service_restart_recovery` | Service Restart During Buffering | `RESTART` | Persistent SQLite buffer recovers undelivered events across process restarts. |
