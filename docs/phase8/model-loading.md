# Model Loading & Version Validation

## 1. Phase 7 Model Artifacts Consumed

The Edge ML subsystem consumes trained model artifacts and corresponding schema metadata generated during Phase 7:

- **Anomaly Detection Model**: `data/models/anomaly_isolation_forest_v1.0.0.joblib`
  - Metadata: `data/models/anomaly_isolation_forest_v1.0.0_metadata.json`
- **RUL Regressor Model**: `data/models/rul_gradient_boosting_v1.0.0.joblib`
  - Metadata: `data/models/rul_gradient_boosting_v1.0.0_metadata.json`
- **Optional ONNX Graphs**:
  - `data/models/anomaly_isolation_forest_v1.0.0.onnx`
  - `data/models/rul_gradient_boosting_v1.0.0.onnx`

## 2. ModelLoader Validation Guarantees

The `ModelLoader` class (`ml/inference/model_loader.py`) enforces strict validation upon initialization:

1. **Existence Verification**: Verifies both the binary model file and the JSON metadata file exist.
2. **Metadata Contract**: Validates `model_name`, `model_version`, `model_type`, and `feature_manifest_version`.
3. **Feature Count & Ordering Check**: Asserts the feature count equals exactly 1,019 columns matching the Phase 7 manifest.
4. **Anti-Leakage Inspection**: Verifies that no forbidden target strings exist in the metadata feature list.
5. **Thread-Safe Model Caching**: Models are loaded once at service boot and bundled into immutable `ModelBundle` instances, preventing redundant disk I/O.
