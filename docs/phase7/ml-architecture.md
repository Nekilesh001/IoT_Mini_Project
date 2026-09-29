# Phase 7: ML Architecture & Pipeline Overview

## 1. Executive Summary

Phase 7 implements an offline, reproducible Machine Learning training, evaluation, and experiment tracking pipeline for the **Smart Factory Machine Monitoring & Predictive Maintenance System**.

The pipeline ingests observable machine telemetry across all 12 heterogeneous machines in the factory simulation, extracts temporal physical features under strict anti-leakage constraints, enforces chronological train/validation/test splits, trains unsupervised anomaly detection and supervised Remaining Useful Life (RUL) regression models, tracks runs with local MLflow, and exports production-ready model artifacts.

```
┌────────────────────────────────────────────────────────────────────────┐
│                          ML DATA SOURCES                               │
│  ┌───────────────────────────────┐   ┌──────────────────────────────┐  │
│  │  Postgres / SQLite Storage    │   │  Deterministic Simulator     │  │
│  │  (Observable Telemetry Rows)  │   │  (7200s Multi-Fault Replay)  │  │
│  └───────────────┬───────────────┘   └──────────────┬───────────────┘  │
└──────────────────┼──────────────────────────────────┼──────────────────┘
                   ▼                                  ▼
┌────────────────────────────────────────────────────────────────────────┐
│               DATA INGESTION & GROUND TRUTH ISOLATION                  │
│  - Raw Observable DataFrames (machine_id, timestamp, signals)          │
│  - Offline Ground Truth Target Derivation (is_anomaly, rul_seconds)    │
│  - Target fields segregated from feature vectors                       │
└──────────────────────────────────┬─────────────────────────────────────┘
                                   ▼
┌────────────────────────────────────────────────────────────────────────┐
│               FEATURE EXTRACTION & LEAKAGE ENFORCEMENT                 │
│  - Signal Whitelisting per Machine Type (CNC, Robot, Kiln, etc.)       │
│  - Backward-Looking Rolling Aggregations (5s, 15s, 30s)                │
│  - Rate of Change & Baseline Deviation                                 │
│  - Categorical & Quality Indicator Encodings                           │
│  - Strict Feature Whitelist & Leakage Regex Validation                 │
└──────────────────────────────────┬─────────────────────────────────────┘
                                   ▼
┌────────────────────────────────────────────────────────────────────────┐
│                     CHRONOLOGICAL DATA SPLIT                           │
│  - Train Set:      60% (Earliest Historical Period)                    │
│  - Validation Set: 20% (Mid Chronological Period)                      │
│  - Test Set:       20% (Latest Future Horizon Period)                  │
└──────────────────┬──────────────────────────────────┬──────────────────┘
                   ▼                                  ▼
┌──────────────────────────────────┐   ┌─────────────────────────────────┐
│     ANOMALY DETECTION MODEL      │   │          RUL REGRESSION         │
│  - Unsupervised Isolation Forest │   │  - HistGradientBoostingRegressor│
│  - Trained on Baseline History   │   │  - Baseline Median Benchmark    │
│  - Anomaly Score & Flag Outputs  │   │  - Continuous Seconds Horizon   │
└──────────────────┬───────────────┘   └──────────────┬──────────────────┘
                   ▼                                  ▼
┌────────────────────────────────────────────────────────────────────────┐
│                   LOCAL MLFLOW EXPERIMENT TRACKING                     │
│  - Local file-based URI (`mlruns/`)                                    │
│  - Hyperparameters, Metrics, Manifest Artifacts, Model Signatures      │
└──────────────────────────────────┬─────────────────────────────────────┘
                                   ▼
┌────────────────────────────────────────────────────────────────────────┐
│                   ARTIFACT EXPORT & MODEL METADATA                     │
│  - Joblib Model Binaries (`data/models/`)                              │
│  - Complete JSON Metadata (Input Schemas, Feature Order, Metrics)      │
│  - Markdown Evaluation Reports (`ml/reports/`)                         │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Package Structure

The `ml/` package is structured into clean decoupled modules:

| Subpackage / Module | Role |
| :--- | :--- |
| [`ml/config.py`](file:///d:/ONE_DATA/IoT_mini/ml/config.py) | Central configuration parameters for simulation, feature extraction, split ratios, model hyperparameters, and storage paths. |
| [`ml/schemas.py`](file:///d:/ONE_DATA/IoT_mini/ml/schemas.py) | Pydantic and dataclass models for feature manifests, dataset metadata, model metadata, and `TargetLeakageError`. |
| [`ml/data/`](file:///d:/ONE_DATA/IoT_mini/ml/data/) | Dataset collectors (`PostgresTelemetryCollector`, `SimulatorDatasetGenerator`), target builders (`compute_ground_truth_labels`), and chronological splitters. |
| [`ml/features/`](file:///d:/ONE_DATA/IoT_mini/ml/features/) | Signal whitelists, machine-specific feature mapping, backward-looking rolling stats, and strict anti-leakage validators. |
| [`ml/anomaly/`](file:///d:/ONE_DATA/IoT_mini/ml/anomaly/) | Unsupervised `IsolationForest` wrapper, training pipeline, and classification/time-to-detection evaluators. |
| [`ml/rul/`](file:///d:/ONE_DATA/IoT_mini/ml/rul/) | `HistGradientBoostingRegressor` and `BaselineMedianRULModel` wrappers, training pipeline, and regression metrics. |
| [`ml/tracking/`](file:///d:/ONE_DATA/IoT_mini/ml/tracking/) | Local file-based MLflow client (`mlruns/`) with cloudpickle model logging and metadata tracking. |
| [`ml/export/`](file:///d:/ONE_DATA/IoT_mini/ml/export/) | Serialization helpers for saving joblib binaries and comprehensive JSON metadata. |
| [`ml/pipelines/`](file:///d:/ONE_DATA/IoT_mini/ml/pipelines/) | CLI-runnable standalone pipelines (`build_dataset.py`, `train_anomaly.py`, `train_rul.py`). |
| [`ml/demo.py`](file:///d:/ONE_DATA/IoT_mini/ml/demo.py) | Comprehensive end-to-end demo exercising all Phase 7 components. |
| [`ml/reports/`](file:///d:/ONE_DATA/IoT_mini/ml/reports/) | Markdown and JSON evaluation reports generated by pipelines. |

---

## 3. Key Design Decisions

1. **Deterministic Multi-Fault Generation**:
   The generator runs the actual Phase 1-6 `FactorySimulator` for 7200 seconds (seed=42) cycling through normal operation, thermal runaway, bearing wear, pressure loss, vibration anomalies, and coolant degradation across all 12 machines.
2. **Strict Ground-Truth Isolation**:
   Feature extraction occurs strictly on observable canonical telemetry. Hidden simulator variables (such as wear percentage or internal fault counters) are only accessed in an offline label builder to create `target_is_anomaly` and `target_rul_seconds`.
3. **No Target Leakage in Features**:
   Every feature matrix is screened against prohibited regex patterns prior to fitting or prediction.
4. **Chronological Splitting**:
   Data is partitioned chronologically per machine (60% Train, 20% Validation, 20% Test) rather than randomly shuffled, avoiding time-travel leakage.
5. **Completely Local & Offline**:
   No cloud connections, AWS dependencies, or remote databases required. MLflow logs to `mlruns/` using local file storage.
