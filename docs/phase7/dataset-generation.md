# Phase 7: Dataset Generation & Telemetry Sources

## 1. Overview

Phase 7 implements two telemetry collection backends behind a unified interface `BaseTelemetryCollector`:

1. **`SimulatorDatasetGenerator`** ([`ml/data/simulator_dataset.py`](file:///d:/ONE_DATA/IoT_mini/ml/data/simulator_dataset.py)): Runs the deterministic multi-machine physics simulator across extended time horizons with orchestrated fault and maintenance schedules.
2. **`PostgresTelemetryCollector`** ([`ml/data/postgres_dataset.py`](file:///d:/ONE_DATA/IoT_mini/ml/data/postgres_dataset.py)): Queries historical telemetry persisted in PostgreSQL or SQLite from live factory ingestion runs.

---

## 2. Deterministic Simulation Strategy

To ensure sufficient historical depth, heterogeneous machine coverage, and varied operational dynamics, `SimulatorDatasetGenerator` steps the existing `FactorySimulator` for 7200 seconds (2 hours of simulated factory time at 1.0s resolution, with 10.0s telemetry emission interval).

### Machine Coverage

The simulation covers all 12 factory machines:
- `CNC-001`, `CNC-002` (CNC Milling / Machining Centers)
- `ROBOT-001`, `ROBOT-002` (6-Axis Articulated Robots)
- `PRESS-001` (Hydraulic Stamping Press)
- `KILN-001` (High-Temperature Industrial Kiln)
- `AGV-001`, `AGV-002` (Automated Guided Vehicles)
- `PACK-001` (Packaging Machine)
- `PUMP-001`, `PUMP-002` (Coolant & Fluid Pumps)
- `COMP-001` (Air Compressor)

### Injected Fault Schedules

| Time Interval (s) | Target Machine | Injected Scenario | Manifestation |
| :--- | :--- | :--- | :--- |
| **800 – 1600** | `CNC-001` | Spindle Bearing Degradation | Rising vibration RMS, elevated spindle temperature, increased motor current |
| **2000 – 2800** | `ROBOT-001` | Joint 2 & 3 Mechanical Backlash | Position tracking error, high joint torque, increased servo temperature |
| **3200 – 4000** | `PRESS-001` | Hydraulic Pressure Decay | Declining main hydraulic pressure, cycling relief valve, oil heating |
| **4400 – 5200** | `KILN-001` | Thermal Runaway / Element Failure | Zone 1 & 2 thermal spike, thermocouple fluctuation, power surge |
| **5600 – 6400** | `PUMP-001` | Cavitation & Impeller Wear | Discharge pressure drop, cavitation vibration frequency, flow rate decay |

After each fault window, maintenance/recovery is executed to restore nominal machine dynamics, producing clean cyclic transitions between normal, degraded, fault, and recovered operating states.

---

## 3. Ground-Truth Target Label Construction

Targets are derived in [`ml/data/labels.py`](file:///d:/ONE_DATA/IoT_mini/ml/data/labels.py) using offline simulation logs:

1. **`target_is_anomaly`** (Binary integer `0` or `1`):
   Set to `1` during active fault injection intervals or when simulator health index drops below 70%. Set to `0` during nominal baseline periods.
2. **`target_rul_seconds`** (Continuous float):
   Calculated using a piecewise linear degradation model:
   - When healthy: capped at `max_rul_seconds` (default: 3600.0s).
   - When degrading towards failure: linearly decreases to 0 at the failure event timestamp.
   - During active fault state: set to 0.0s.
   - Post-recovery: resets to nominal baseline ceiling.

Both target columns are stored in separate target DataFrames or files (`target_is_anomaly.parquet`, `target_rul.parquet`) and **strictly excluded from all feature matrices**.
