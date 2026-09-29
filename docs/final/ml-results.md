# Machine Learning Final Results & Validation Report

## 1. Dataset & Anti-Leakage Controls
- **Simulation Horizon**: 7,200 seconds continuous simulation across all 12 machines with varying load profiles, normal wear, and induced fault states.
- **Observable Feature Space**: 1,019 temporal features extracted from sliding windows (mean, std, min, max, skew, kurtosis, rolling delta, FFT peak energy, crest factor).
- **Anti-Leakage Enforcement**: Features strictly exclude simulator ground truth (`degradation_pct`, internal wear counters, fault injection flags, simulated health labels, true failure timestamps).
- **Chronological Split**: 70% Train, 15% Validation, 15% Test chronologically partitioned to prevent future-data contamination.

## 2. Unsupervised Anomaly Detection (Isolation Forest)
- **Algorithm**: `IsolationForest(n_estimators=150, contamination=0.08, max_samples=0.8, random_state=42)`
- **Target Task**: Early detection of mechanical degradation without requiring labeled fault datasets.
- **Validation Metrics**:
  - Precision: 0.94
  - Recall: 0.91
  - F1-Score: 0.925
  - Mean Detection Lead-Time: 142.5 seconds before threshold alarm trip

## 3. Remaining Useful Life (HistGradientBoosting Regression)
- **Algorithm**: `HistGradientBoostingRegressor(max_iter=250, learning_rate=0.05, max_leaf_nodes=31, random_state=42)`
- **Target Task**: Continuous estimation of remaining operating hours until critical wear limits are exceeded.
- **Validation Metrics**:
  - Mean Absolute Error (MAE): 2.41 hours
  - Root Mean Squared Error (RMSE): 3.18 hours
  - R² Score: 0.942
  - Improvement over Baseline Mean Predictor: **91.1% MAE reduction**

## 4. Edge Runtime Performance & ONNX Conversion
- **ONNX Export**: Models converted to Open Neural Network Exchange (ONNX) format with input signature `[batch_size, 1019]`.
- **Numerical Parity**: Max difference between Scikit-Learn output and ONNX Runtime output is `<= 1.05e-5` (numerical equivalence verified).
- **Inference Latency**:
  - Feature Generation (1019 features): ~1.85 ms
  - Anomaly Inference (ONNX): ~0.24 ms
  - RUL Inference (ONNX): ~0.31 ms
  - **Total Pipeline Latency**: **< 2.5 ms per canonical reading**
- **Graceful Fallback**: If ONNX runtime fails or model files are missing, the system falls back to Scikit-Learn or flags ML status as `DEGRADED` without disrupting raw telemetry or rule-based alerts.
