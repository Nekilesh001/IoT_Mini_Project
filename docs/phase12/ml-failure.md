# Phase 12 — ML Inference Failure & Degradation Isolation

## Scenario Details
- **Fault Injection**: ONNX model file missing, model throws inference runtime exception, or input feature vector dimension mismatch.
- **Behavior**: ML subsystem marks inference status as `DEGRADED`. The telemetry pipeline continues ingesting, storing, and evaluating deterministic rule-based alerts without interruption.
- **Recovery**: Restoring model file or updating model session restores ML anomaly detection and RUL estimation to `ACTIVE`.
- **Verification Metric**: Zero missed rule-based critical alerts during ML outage; ground-truth target leakage prevented.
