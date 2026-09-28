# Phase 1 — Factory Simulation Core Architecture

## Overview & Architectural Decoupling

The **Factory Simulation Core** implements an offline, object-oriented physics engine for the 12 heterogeneous smart factory machines. It enforces strict separation between:

1. **Machine Behaviour**: Physics, load dynamics, process models, and wear degradation curves.
2. **Machine State / Physics**: State transitions (`OperatingState` and `HealthState`).
3. **Telemetry Snapshot**: Internal data object holding public measurements and isolated ground-truth metadata.

```
+---------------------+      +------------------------+      +--------------------+
| Machine Behaviour   | ---> | Machine State / Physics| ---> | Telemetry Snapshot |
| (Physics Engine)    |      | (Operating & Health)   |      | (Internal Object)  |
+---------------------+      +------------------------+      +--------------------+
```

---

## Domain Model & Package Architecture

The `simulator` package is organized into modular submodules:

- **`simulator.core`**: `domain.py` (Enums, `MachineProfile`, `TelemetrySnapshot`, `SimulationGroundTruth`) and `machine.py` (`BaseMachine`).
- **`simulator.states`**: `state_machine.py` (`MachineStateMachine` managing state transitions).
- **`simulator.degradation`**: `degradation_model.py` (`DegradationModel` managing continuous wear and fault hooks).
- **`simulator.process_models`**: `base.py` (`MachineBehaviorStrategy`) and `strategies.py` (strategy algorithms for all 12 machines).
- **`simulator.runtime`**: `factory_runtime.py` (`FactorySimulator` managing the 12 machines).
- **`simulator.scenarios`**: `scenarios.py` (deterministic scenario execution).
- **`simulator.config`**: `machines.json` and `simulation.json` (structured machine profiles and parameters).

---

## Target Leakage Prevention & Ground-Truth Isolation

Simulator internal ground-truth data (`degradation_level`, `scenario_id`, `fault_label`, `active_conditions`, `hidden_wear_counter`) is held in a separate `SimulationGroundTruth` object. 

When snapshots are converted to public payloads for downstream ingestion via `TelemetrySnapshot.to_dict(include_ground_truth=False)`, ground-truth fields are completely excluded to guarantee zero target leakage in ML feature extraction.
