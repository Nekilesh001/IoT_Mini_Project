# Real-Time Feature Pipeline & Buffering

## 1. Machine-Aware Feature Buffering

The `MachineTelemetryBuffer` (`ml/inference/feature_buffer.py`) maintains a rolling window of recent `CanonicalTelemetry` observations per machine using a fixed-size `collections.deque`:

- **Duplicate Rejection**: Deduplicates events with identical `event_id`.
- **Chronological Sorting**: Ensures events are sorted by `event_time` in case of slight network or adapter jitter.
- **Bounded Memory**: Buffer is capped at `max_buffer_size` (default: 60 observations), bounding memory usage at edge nodes.

## 2. Warm-Up Policy

Real-time ML features require rolling temporal windows (`[5, 15, 30]`) and backward differences. When a machine begins emitting telemetry, it cannot compute full rolling statistics immediately.

- **Warm-Up Threshold**: `min_warmup_samples = 4` (default: 4 observations).
- **Status Lifecycle**:
  - `sample_count < min_warmup_samples` -> `InferenceStatus.NOT_READY` (returns clean result with `anomaly_score=None`, `predicted_rul_seconds=None`).
  - `sample_count >= min_warmup_samples` -> `InferenceStatus.READY` (computes full 1,019 feature vector and executes model inference).

## 3. Schema and Anti-Leakage Validation

The `FeatureSchemaValidator` (`ml/inference/validator.py`) inspects the generated 1,019-dimension feature vector prior to model prediction:
- Verifies exact feature count (1,019).
- Verifies exact feature naming and column ordering.
- Verifies no NaN/Inf values (replaces with 0.0 for safety).
- Checks all column names against `PROHIBITED_LEAKAGE_PATTERNS`.
