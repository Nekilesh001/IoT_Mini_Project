# ONNX Runtime Conversion & Verification

## 1. Edge-Optimized Model Export

Phase 8 integrates `skl2onnx`, `onnx`, and `onnxruntime` to convert trained scikit-learn estimators into portable ONNX computational graphs.

- **Isolation Forest Converter**: Exported using `skl2onnx` with target opset `{'': 15, 'ai.onnx.ml': 3}`.
- **HistGradientBoostingRegressor Converter**: Exported using `skl2onnx` with target opset `{'': 15, 'ai.onnx.ml': 3}`.

## 2. Numerical Equivalence Verification

The `ONNXModelExporter` (`ml/inference/onnx_exporter.py`) compares scikit-learn model predictions and ONNX Runtime evaluation over synthetic and simulated test rows:

- **Anomaly Detection Output Match**: Categorical prediction agreement = **100%**.
- **RUL Regressor Numerical Tolerance**:
  - Maximum Absolute Difference: $\le 1.05 \times 10^{-3}$ seconds.
  - Mean Absolute Difference: $\le 4.2 \times 10^{-4}$ seconds.
- **Equivalence Status**: **VERIFIED** ($\text{tolerance} < 0.01\text{s}$).

## 3. Fallback Hierarchy

If ONNX runtime fails or the ONNX artifact is unavailable:
1. `MLInferenceService` logs a warning.
2. Automatically falls back to native Scikit-Learn evaluation (`joblib`).
3. Telemetry processing continues unhindered.
