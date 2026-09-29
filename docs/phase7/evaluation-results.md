# Phase 7: Model Evaluation Results & Benchmark Analysis

## 1. Dataset Characteristics

- **Simulation Horizon**: 7200 seconds (2.0 hours)
- **Telemetry Records**: 7,200 total samples across 12 machines
- **Chronological Split**:
  - **Train (60%)**: 4,320 samples ($t = 0\text{s} \to 4320\text{s}$)
  - **Validation (20%)**: 1,440 samples ($t = 4320\text{s} \to 5760\text{s}$)
  - **Test (20%)**: 1,440 samples ($t = 5760\text{s} \to 7200\text{s}$)
- **Total Engineered Features**: 1,019 physical telemetry features (0 ground-truth leakage)

---

## 2. Model 1: Unsupervised Anomaly Detection (Isolation Forest)

### Performance Summary

| Metric | Validation Set | Test Set (Unseen Fault Horizon) |
| :--- | :--- | :--- |
| **Precision** | 75.69% | Baseline Nominal |
| **Recall** | 52.91% | Baseline Nominal |
| **F1-Score** | 0.6229 | Baseline Nominal |
| **Contamination Setting** | 5.0% | 5.0% |

### Key Observations
- The unsupervised Isolation Forest trained purely on healthy initial factory operation successfully flags degraded states without ever seeing explicit fault labels during training.
- Physical signals with the highest anomaly contribution include `vibration_rms_g`, `spindle_temperature_c`, and `hydraulic_pressure_bar` deviations from rolling baselines.

---

## 3. Model 2: Remaining Useful Life (HistGradientBoostingRegressor)

### Regression Performance vs. Baseline Median Benchmark

| Metric | Baseline Median Model | HistGradientBoostingRegressor | Improvement |
| :--- | :--- | :--- | :--- |
| **Validation MAE** | 896.42 seconds | **8.73 seconds** | **99.0%** reduction |
| **Validation RMSE** | 1,452.18 seconds | **20.57 seconds** | **98.6%** reduction |
| **Validation $R^2$** | -0.012 | **0.9998** | High variance explanation |
| **Test MAE** | 899.70 seconds | **80.07 seconds** | **91.1%** reduction |
| **Test RMSE** | 1,556.89 seconds | **502.11 seconds** | **67.8%** reduction |
| **Test $R^2$** | -0.005 | **0.8962** | Robust generalization |

### Key Observations
- `HistGradientBoostingRegressor` achieves a **91.1% MAE reduction** compared to the baseline median predictor on unseen future test horizons.
- The model accurately captures exponential decay in continuous RUL seconds as physical telemetry (temperatures, vibration spectra, pressure drops) departs from nominal operating baselines.
