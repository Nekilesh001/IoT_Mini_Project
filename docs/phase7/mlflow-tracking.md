# Phase 7: Local MLflow Tracking & Experimentation

## 1. Local-First Experiment Management

To comply with zero-cloud and offline-first architectural constraints, experiment tracking is implemented locally using `mlflow-skinny` backed by a file store URI:

```python
tracking_uri = "file:./mlruns"
experiment_name = "SmartFactory-PredictiveMaintenance"
```

No remote servers, cloud databases, or credential configurations are required.

---

## 2. Tracked Parameters, Metrics & Artifacts

For each training execution of the Anomaly Detection and RUL pipelines, `MLflowTracker` logs:

### Run Parameters
- `model_name`, `model_type`, `version`, `random_seed`
- `dataset_source` (`simulation` or `postgres`)
- `train_val_test_split_ratios` (0.60 / 0.20 / 0.20)
- `rolling_windows` (`[5, 15, 30]`)
- `num_features`, `num_machines`, `num_samples`
- Model hyperparameters (`n_estimators`, `contamination`, `learning_rate`, `max_depth`)

### Metrics
- Validation & Test F1, Precision, Recall, ROC-AUC (Anomaly)
- Validation & Test MAE, RMSE, $R^2$, MedAE, Baseline MAE Improvement (RUL)
- Time-to-Detection for injected fault scenarios

### Artifacts Logged
- Complete Feature Manifest (`manifest.json`)
- Model Serialization (`model.joblib` / `cloudpickle`)
- Training Dataset Metadata (`dataset_metadata.json`)

---

## 3. Reviewing Local MLflow Experiments

To launch the local MLflow UI and inspect experiment runs in the browser:

```bash
mlflow ui --backend-store-uri ./mlruns --port 5000
```
Then navigate to `http://127.0.0.1:5000`.
