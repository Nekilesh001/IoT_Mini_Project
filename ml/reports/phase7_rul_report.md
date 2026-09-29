# Phase 7: Remaining Useful Life (RUL) Evaluation Report

## 1. Model Overview
- **Algorithm**: `HistGradientBoostingRegressor` (scikit-learn)
- **Model Version**: `v1.0.0`
- **Features Used**: `1019` engineered physical features
- **MLflow Run ID**: `4682b0014f3642e290ddc93ee5fb2698`
- **Artifact**: `rul_gradient_boosting_v1.0.0.joblib`

## 2. Test Set Evaluation Metrics vs. Baseline
| Metric | Supervised RUL Model | Baseline Median Model | Improvement |
| :--- | :--- | :--- | :--- |
| **MAE (seconds)** | `8.33s` | `600.0s` | **`98.61%`** |
| **RMSE (seconds)** | `23.19s` | `1469.69s` | — |
| **R² Score** | `0.9997` | `-0.2` | — |
| **Median Absolute Error** | `0.27s` | — | — |

## 3. Ground-Truth Isolation Verification
- **Target Leakage Status**: **CLEAN (Zero Leakage)**
- Target `target_rul_seconds` was derived strictly for supervision and excluded from all feature engineering matrices.
