# Phase 2: Protocol Mappings Specification

## 1. 12-Machine Protocol Allocation Matrix

| Machine ID | Machine Type | Protocol | Addressing Reference |
|---|---|---|---|
| `CNC-001` | `CNC_MACHINING_CENTER` | **OPC UA** | `ns=2;s=Factory/Plant_01/Line_A/CNC-001` |
| `CNC-002` | `CNC_LATHE` | **Modbus TCP** | `Unit ID: 1`, `Holding Registers: 0..12` |
| `ROB-001` | `INDUSTRIAL_ROBOT_6AXIS` | **OPC UA** | `ns=2;s=Factory/Plant_01/Line_A/ROB-001` |
| `ROB-002` | `WELDING_ROBOT` | **MQTT** | `factory/PLANT_01/LINE_A/ROB-002/telemetry` |
| `CON-001` | `INDUSTRIAL_CONVEYOR` | **Modbus TCP** | `Unit ID: 2`, `Holding Registers: 0..12` |
| `PRS-001` | `INDUSTRIAL_PRESS` | **Modbus TCP** | `Unit ID: 3`, `Holding Registers: 0..12` |
| `IMM-001` | `INJECTION_MOLDING_MACHINE` | **OPC UA** | `ns=2;s=Factory/Plant_01/Line_A/IMM-001` |
| `CMP-001` | `AIR_COMPRESSOR` | **Modbus TCP** | `Unit ID: 4`, `Holding Registers: 0..12` |
| `PMP-001` | `INDUSTRIAL_PUMP` | **MQTT** | `factory/PLANT_01/LINE_A/PMP-001/telemetry` |
| `VIS-001` | `VISION_INSPECTION_STATION` | **OPC UA** | `ns=2;s=Factory/Plant_01/Line_A/VIS-001` |
| `AGV-001` | `AUTONOMOUS_MOBILE_ROBOT` | **MQTT** | `factory/PLANT_01/LINE_A/AGV-001/telemetry` |
| `CHL-001` | `INDUSTRIAL_CHILLER` | **Modbus TCP** | `Unit ID: 5`, `Holding Registers: 0..12` |

## 2. Decoupled Mapping Models

- **Modbus**: `ModbusSignalMapper` translates between signals and 16-bit register arrays with fixed scale factors (0.1 for floats).
- **OPC UA**: `OPCUASignalMapper` translates between signals, node string IDs, and OPC UA variant data types (`Double`, `Int64`, `Boolean`, `String`).
- **MQTT**: `MQTTSignalMapper` formats topics and serializes JSON dictionaries.
