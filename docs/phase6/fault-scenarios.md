# Phase 6: Fault Scenario Definitions & Catalog

## 1. Fault Taxonomy

Phase 6 implements the standard industrial fault taxonomy:

| Taxonomy Category | Description | Scope in Phase 6 |
|---|---|---|
| `MACHINE_FAULT` | Physical machine wear, mechanical obstruction, thermal overload, hydraulic loss | Fully Implemented |
| `SENSOR_FAULT` | Sensor optical degradation, dropout, latency, measurement drift | Fully Implemented |
| `PROTOCOL_FAULT` | Protocol-level timeouts, bad packets, frame crc errors | Controlled Hooks (Phase 2) |
| `NETWORK_FAULT` | Network connection drop, high jitter, packet loss | Controlled Hooks (Phase 2) |
| `EDGE_FAULT` | Processing queue backlog, buffer persistence rollover | Controlled Hooks (Phase 3/4) |
| `CLOUD_FAULT` | Cloud endpoint disconnection, sync delay | Deferred to Cloud Phases |

---

## 2. Standard Machine Fault Catalog

The `FaultScenarioManager` provides 10 standardized scenarios across all factory machine types:

| Machine ID | Machine Type | Scenario ID | Fault Type | Progressive? | Target Condition | Key Symptom |
|---|---|---|---|---|---|---|
| `PMP-001` | `INDUSTRIAL_PUMP` | `PUMP_BEARING_WEAR` | `MACHINE_FAULT` | Yes | `bearing_wear` | Vibration $X$ surge, bearing temp rise |
| `CON-001` | `INDUSTRIAL_CONVEYOR` | `CONVEYOR_BELT_JAM` | `MACHINE_FAULT` | No | `jammed` | Drive motor current surge ($>24\text{ A}$), belt stall |
| `CNC-001` | `CNC_MACHINING_CENTER` | `CNC_SPINDLE_OVERHEAT` | `MACHINE_FAULT` | Yes | `spindle_overheat` | Spindle temperature rise ($>65\text{ }^\circ\text{C}$), vibration anomaly |
| `CHL-001` | `INDUSTRIAL_CHILLER` | `CHILLER_LOW_FLOW` | `MACHINE_FAULT` | Yes | `low_flow` | Coolant flow drop ($<60\text{ L/min}$), supply temp rise |
| `AGV-001` | `AUTONOMOUS_MOBILE_ROBOT` | `AGV_LOW_BATTERY` | `MACHINE_FAULT` | Yes | `low_battery` | Battery SOC drop ($<20\%$), navigation alert |
| `CMP-001` | `AIR_COMPRESSOR` | `COMPRESSOR_FILTER_CLOG`| `MACHINE_FAULT` | Yes | `filter_clog` | Discharge element temperature spike ($>110\text{ }^\circ\text{C}$) |
| `ROB-001` | `INDUSTRIAL_ROBOT_6AXIS`| `ROBOT_JOINT_OVERLOAD` | `MACHINE_FAULT` | No | `joint_overload` | Joint 1 torque overload ($>180\text{ Nm}$) |
| `IMM-001` | `INJECTION_MOLDING_MACHINE`| `IMM_COOLING_FAILURE` | `MACHINE_FAULT` | Yes | `cooling_failure` | Mold temperature escalation, cycle time delay |
| `PRS-001` | `INDUSTRIAL_PRESS` | `PRESS_PRESSURE_LOSS` | `MACHINE_FAULT` | No | `pressure_loss` | Hydraulic pressure decay below minimum tonnage |
| `VIS-001` | `VISION_INSPECTION_STATION`| `VISION_CAMERA_DROPOUT`| `SENSOR_FAULT` | No | `sensor_dropout` | Camera latency, image capture timeout |

---

## 3. Scenario Lifecycle Management

```
[CREATED] ---> start() ---> [ACTIVE] ---> advance() (Progressive wear increments)
                              |
                              +---> stop() ---> [RESOLVED] (Conditions removed, baseline restored)
```
