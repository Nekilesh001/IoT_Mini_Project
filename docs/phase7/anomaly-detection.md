# Phase 7: Anomaly Detection Model Architecture & Evaluation

## 1. Algorithm Selection: Unsupervised Isolation Forest

For industrial factory telemetry, abnormal fault states are rare, evolving, and often unlabelled in real-world deployment. Consequently, an unsupervised anomaly detection paradigm was chosen.

We utilize `sklearn.ensemble.IsolationForest` configured with:
- `n_estimators`: 100 decision trees
- `contamination`: 0.05 (expected nominal anomaly rate in healthy factory baseline)
- `random_state`: 42 (deterministic reproducibility)
- `max_samples`: "auto"
- `bootstrap`: False

---

## 2. Training Protocol

1. **Baseline Ingestion**: The model is fitted strictly on the earliest historical observations (`X_train`) where machines operate under nominal load and baseline conditions.
2. **Missing Value Imputation**: Imputed using historical median values computed on the training set only.
3. **Score Calibration**: Isolation Forest raw decision functions produce continuous anomaly scores $s \in (-\infty, +\infty)$ where more negative values indicate deeper isolation (stronger anomalies). The wrapper scales these to $[0.0, 1.0]$ for intuitive alerting thresholds.

---

## 3. Evaluation Metrics

Evaluated against offline fault injection ground truth:
- **Precision**: Ratio of true anomalous alarms to total alarms triggered.
- **Recall**: Proportion of true injected anomalies successfully flagged.
- **F1 Score**: Harmonic mean of Precision and Recall.
- **ROC-AUC & PR-AUC**: Discriminating capacity across variable decision thresholds.
- **Confusion Matrix**: Detailed counts of True Positives, False Positives, True Negatives, and False Negatives.
- **Time-to-Detection (TTD)**: Delay in seconds between the onset of a fault injection scenario and the first anomalous classification flag.
