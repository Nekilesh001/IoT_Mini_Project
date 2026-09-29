# Phase 7: Model Export & Serialization

## 1. Export Architecture

Trained models and their accompanying runtime schemas are exported directly to [`data/models/`](file:///d:/ONE_DATA/IoT_mini/data/models/) to prepare for subsequent Phase 8 edge inference integration without introducing runtime dependencies on training scripts.

### Saved Artifacts

1. **Joblib Model Binary (`.joblib`)**:
   Contains the serialized, fitted scikit-learn estimator or wrapper.
2. **Comprehensive Metadata JSON (`_metadata.json`)**:
   Contains all operational parameters required to validate and safely load the model in downstream systems.

---

## 2. Metadata Schema (`ModelMetadata`)

```json
{
  "model_name": "anomaly_isolation_forest",
  "model_type": "IsolationForest",
  "version": "v1.0.0",
  "created_at": "2026-09-29T12:25:35",
  "random_seed": 42,
  "num_features": 1019,
  "feature_names": [
    "CNC-001__spindle_speed_rpm",
    "CNC-001__spindle_temperature_c",
    "CNC-001__spindle_temperature_c__rolling_mean_w5",
    "..."
  ],
  "hyperparameters": {
    "n_estimators": 100,
    "contamination": 0.05,
    "random_state": 42
  },
  "metrics": {
    "val_f1": 0.6229,
    "val_precision": 0.7569,
    "val_recall": 0.5291
  },
  "runtime_dependencies": {
    "scikit-learn": "1.9.0",
    "pandas": "3.0.3",
    "numpy": "2.4.6",
    "joblib": "1.5.3"
  }
}
```

---

## 3. Verification & Model Reloading

The export module [`ml/export/model_export.py`](file:///d:/ONE_DATA/IoT_mini/ml/export/model_export.py) provides `load_model_artifact(name, version)` which:
1. Validates that the metadata JSON matches the binary artifact.
2. Checks that feature names and schema dimensions are identical.
3. Deserializes the model and confirms that test predictions can be executed successfully.
