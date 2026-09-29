# Failure Modes & Resilience Handling

## 1. Failure Strategy: Non-Fatal Isolation

ML inference is an observational augmentation layer. Under no circumstance may an ML model exception or schema failure interrupt continuous factory telemetry ingestion, time-series storage, or rule-based safety alerts.

## 2. Explicit Error Codes

The system defines explicit domain errors (`ml/inference/errors.py`):

| Error Code | Description | Runtime Action |
| :--- | :--- | :--- |
| `MODEL_NOT_FOUND` | Model binary or metadata file missing | Falls back to stub / marks status `ERROR` |
| `MODEL_LOAD_ERROR` | Deserialization or corruption in model artifact | Logs warning, marks status `ERROR` |
| `MODEL_SCHEMA_MISMATCH` | Metadata/model contract mismatch | Rejects model at boot |
| `FEATURE_SCHEMA_MISMATCH` | Feature count or column ordering discrepancy | Aborts prediction, status `DEGRADED` |
| `INSUFFICIENT_HISTORY` | Machine buffer has not reached warmup | Returns clean `NOT_READY` result |
| `TARGET_LEAKAGE_DETECTED`| Prohibited ground-truth signal found in inputs | Immediate exception, aborts inference |
| `INVALID_TELEMETRY` | Telemetry payload missing required fields | Skips buffer insertion, status `ERROR` |
