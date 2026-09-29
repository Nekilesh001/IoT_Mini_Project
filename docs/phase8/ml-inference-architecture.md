# Phase 8: Edge ML Inference Engine Architecture

## 1. Overview & Objective

Phase 8 transforms the offline Phase 7 Machine Learning models (`IsolationForest` anomaly detector and `HistGradientBoostingRegressor` Remaining Useful Life predictor) into an edge-ready, real-time inference subsystem embedded inside the Smart Factory telemetry pipeline.

The entire inference loop operates **local-first** and **completely offline without AWS dependencies**.

```mermaid
flowchart TD
    Factory[Factory Physical Simulation] --> Protocols[OPC-UA / MQTT / Modbus / HTTP]
    Protocols --> Adapters[Protocol Adapters]
    Adapters --> Canonical[Canonical Telemetry Ingestion]
    Canonical --> Buffer[Temporal Feature Buffer (Machine-Aware)]
    Buffer --> ReadyCheck{Warm-up Ready? >= 4 samples}
    ReadyCheck -- No --> NotReady[Emit MLInferenceResult: NOT_READY]
    ReadyCheck -- Yes --> Extractor[Observable Feature Pipeline]
    Extractor --> Validator[Anti-Leakage & Schema Validator (1,019 features)]
    Validator --> MLRuntime[Edge ML Predictors (ONNX / Scikit-Learn)]
    MLRuntime --> AnomalyScore[Isolation Forest Anomaly Score]
    MLRuntime --> RULScore[HistGBM Predicted RUL]
    AnomalyScore --> Result[Unified MLInferenceResult]
    RULScore --> Result
    Result --> Storage[SQLite / PostgreSQL (ml_inferences)]
    Result --> AlertAdapter[ML-to-Alert Adapter (source='ML')]
    AlertAdapter --> AlertRepo[AlertRepository Lifecycle]
    Result --> SSE[FastAPI SSE Stream (event: ml_inference)]
    SSE --> Dashboard[React Predictive Maintenance Dashboard]
```

## 2. Decoupled Pipeline Architecture

The Edge ML system adheres to the core architecture principles:
1. **Zero Protocol Leakage**: The ML pipeline is completely agnostic of whether telemetry originated from OPC-UA, MQTT, Modbus TCP, or HTTP REST. It only processes normalized `CanonicalTelemetry`.
2. **Strict Anti-Leakage Contract**: Model inputs exclude all ground-truth degradation wear, simulation flags, scenario tags, fault injection identifiers, and previous ML predictions.
3. **Graceful Degradation**: ML failures never halt the continuous telemetry ingestion or storage loop.
4. **Multi-Machine State Isolation**: Each machine maintains an independent temporal feature buffer without cross-contamination.
