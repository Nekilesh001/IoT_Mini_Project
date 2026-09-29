# Phase 7: Anomaly Detection Evaluation Report

## 1. Model Overview
- **Algorithm**: `IsolationForest` (scikit-learn)
- **Model Version**: `v1.0.0`
- **Features Used**: `1019` engineered physical features
- **MLflow Run ID**: `c8cf0b0f911849d9aacf5255fbe2a14f`
- **Artifact**: `anomaly_isolation_forest_v1.0.0.joblib`

## 2. Test Set Evaluation Metrics
- **F1 Score**: `0.0000`
- **Precision**: `0.0000`
- **Recall**: `0.0000`
- **ROC-AUC**: `0.7231`
- **PR-AUC**: `0.333`

### Confusion Matrix
| Metric | Count |
| :--- | :--- |
| **True Positives (TP)** | `0` |
| **False Positives (FP)** | `2` |
| **True Negatives (TN)** | `577` |
| **False Negatives (FN)** | `141` |

## 3. Ground-Truth Isolation Verification
- **Target Leakage Status**: **CLEAN (Zero Leakage)**
- The Isolation Forest model was trained without knowledge of simulation fault identifiers, degradation flags, or future failure timestamps.
