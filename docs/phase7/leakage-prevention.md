# Phase 7: Ground-Truth Isolation & Anti-Leakage Controls

## 1. The Leakage Problem in Industrial IoT

In industrial simulation and digital twins, the simulator possesses perfect internal knowledge of fault states, component degradation counters, and exact time-to-failure milestones. If any of these internal variables are accidentally included in feature extraction or if future observations leak into historical features, machine learning models will exhibit artificially perfect accuracy during training but completely fail in real-world deployment where internal ground-truth is unobservable.

---

## 2. Leakage Defense Architecture

Phase 7 implements multiple deterministic boundaries to guarantee zero ground-truth leakage:

```
┌────────────────────────────────────────────────────────┐
│               SIMULATOR GROUND TRUTH                   │
│  - degradation_pct                                     │
│  - health_index                                        │
│  - fault_state / active_faults                         │
│  - remaining_useful_life_seconds                       │
│  - simulated_failure_timestamp                         │
└──────────────────────────┬─────────────────────────────┘
                           │
       ====================╪==================== [PHYSICAL BOUNDARY]
                           │  Allowed ONLY for Target Labeling
                           ▼
┌────────────────────────────────────────────────────────┐
│             OFFLINE TRAINING TARGET BUILDER            │
│  - target_is_anomaly (Binary classification target)    │
│  - target_rul_seconds (Continuous regression target)   │
└──────────────────────────┬─────────────────────────────┘
                           │
       ====================╪==================== [STRICT AIRGAP]
                           │  FORBIDDEN FROM FEATURE MATRIX
                           ✕
┌────────────────────────────────────────────────────────┐
│             CANONICAL OBSERVABLE TELEMETRY             │
│  - Physical sensor readings (temperature, vibration)   │
│  - Operating state, signal quality indicator           │
└──────────────────────────┬─────────────────────────────┘
                           │
                           ▼
┌────────────────────────────────────────────────────────┐
│               FEATURE EXTRACTION ENGINE                │
│  - Backward-looking rolling windows only               │
│  - Automated regex validation against forbidden terms  │
│  - Raises TargetLeakageError on any violation          │
└────────────────────────────────────────────────────────┘
```

---

## 3. Forbidden Prohibited Patterns

In [`ml/features/validation.py`](file:///d:/ONE_DATA/IoT_mini/ml/features/validation.py), every candidate feature column is checked against `PROHIBITED_LEAKAGE_PATTERNS`:

```python
PROHIBITED_LEAKAGE_PATTERNS = [
    r"target",
    r"label",
    r"ground_truth",
    r"hidden",
    r"degradation_pct",
    r"degradation_factor",
    r"wear_counter",
    r"health_index",
    r"health_pct",
    r"fault_injected",
    r"fault_active",
    r"fault_scenario",
    r"failure_timestamp",
    r"failure_imminent",
    r"rul_remaining",
    r"true_rul",
    r"prediction",
    r"alert_history",
]
```

If any column matches any prohibited pattern, `validate_feature_names()` immediately raises a fatal `TargetLeakageError`.

---

## 4. Chronological Splitting Rules

To prevent temporal leakage (where future patterns leak into past validation windows), all splits are strictly chronological:
- **Train Split (60%)**: $t \in [t_{0}, t_{60\%}]$
- **Validation Split (20%)**: $t \in (t_{60\%}, t_{80\%}]$
- **Test Split (20%)**: $t \in (t_{80\%}, t_{100\%}]$

Splitting is performed independently per machine using timestamps, ensuring that the test set always represents unseen future operating periods.
