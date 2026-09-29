# Alert Engine Integration

## 1. Separation of Concerns: Rules vs. ML

The Smart Factory system clearly distinguishes between two complementary detection mechanisms:
- **Deterministic Rules (`source = 'RULE'`)**: Threshold-based logic (e.g. over-temperature > 95°C, high vibration > 7.0 mm/s) defined in Phase 6.
- **Predictive ML (`source = 'ML'`)**: Multi-variate behavioral anomaly detection and Remaining Useful Life estimation.

## 2. Alert Lifecycle Preservation

The `MLAlertAdapter` (`ml/inference/alert_adapter.py`) feeds ML predictions directly into the existing operational `AlertRepository`:

- **Anomaly Triggers**:
  - Condition: `anomaly_label == ANOMALOUS` or `anomaly_score >= anomaly_alert_threshold` (default: 0.65).
  - Severity: `WARNING`.
  - Alert Code: `ML-ANOM-01`.
  - Lifecycle: Transitions to `OPEN`. Automatically resolves when anomaly score returns below `0.55` (hysteresis).
- **Critical RUL Triggers**:
  - Condition: `predicted_rul_seconds <= rul_critical_threshold_seconds` (default: 600s / 10 minutes).
  - Severity: `CRITICAL`.
  - Alert Code: `ML-RUL-01`.
  - Lifecycle: Transitions to `OPEN`. Automatically resolves when RUL recovers above 900s.
