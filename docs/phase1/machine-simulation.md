# Phase 1 — Machine Simulation & State Model

## 12-Machine Catalog & Protocol Metadata

The factory simulator manages 12 heterogeneous machines with the following configuration and protocol metadata:

| Machine ID | Machine Class | Protocol Metadata |
| :--- | :--- | :--- |
| **CNC-001** | CNC_MACHINING_CENTER | OPC_UA |
| **CNC-002** | CNC_LATHE | MODBUS_TCP |
| **ROB-001** | INDUSTRIAL_ROBOT_6AXIS | OPC_UA |
| **ROB-002** | WELDING_ROBOT | MQTT |
| **CON-001** | INDUSTRIAL_CONVEYOR | MODBUS_TCP |
| **PRS-001** | INDUSTRIAL_PRESS | MODBUS_TCP |
| **IMM-001** | INJECTION_MOLDING_MACHINE | OPC_UA |
| **CMP-001** | AIR_COMPRESSOR | MODBUS_TCP |
| **PMP-001** | INDUSTRIAL_PUMP | MQTT |
| **VIS-001** | VISION_INSPECTION_STATION | OPC_UA |
| **AGV-001** | AUTONOMOUS_MOBILE_ROBOT | MQTT |
| **CHL-001** | INDUSTRIAL_CHILLER | MODBUS_TCP |

---

## Operating State Machine & Transitions

Machines support 8 operating states: `OFF`, `STARTING`, `IDLE`, `RUNNING`, `WARNING`, `FAULT`, `MAINTENANCE`, `RECOVERY`.

### Transition Rules
- `OFF` -> `STARTING`
- `STARTING` -> `IDLE`, `RUNNING`, `FAULT`
- `IDLE` -> `RUNNING`, `OFF`, `MAINTENANCE`, `FAULT`
- `RUNNING` -> `IDLE`, `WARNING`, `FAULT`, `MAINTENANCE`
- `WARNING` -> `RUNNING`, `FAULT`, `MAINTENANCE`, `IDLE`
- `FAULT` -> `RECOVERY`, `MAINTENANCE`
- `MAINTENANCE` -> `RECOVERY`, `OFF`, `IDLE`
- `RECOVERY` -> `IDLE`, `RUNNING`, `OFF`, `FAULT`

Invalid state transitions raise `InvalidStateTransitionError`.

---

## Causal Physics & Degradation Mechanics

Telemetry signals are derived logically from operating state, load percentage, operating time, and continuous degradation level (0-100%).

- **Load Dependence**: Spindle speed, motor currents, joint torques, hydraulic pressures, and throughput rates scale with load percentage.
- **Correlated Degradation**: Wear increases thermal build-up and mechanical vibration RMS across correlated sensors simultaneously (e.g., bearing degradation increases both vibration X/Y and bearing temperature).
- **Fault Injection Hooks**: Methods `apply_condition(name, severity)` and `inject_internal_condition(name, params)` allow external scenario controllers to simulate filter clogs, bearing wear, jam states, and thermal spikes.
