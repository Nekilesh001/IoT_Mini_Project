# Phase 2: OPC UA Simulation & Adapter

## 1. Overview

OPC UA provides object-oriented industrial information modeling. Machines and their signals are represented as a structured node hierarchy in the server address space.

## 2. Machine Node Structure

OPC UA is assigned to:
- `CNC-001` (`CNC_MACHINING_CENTER`)
- `ROB-001` (`INDUSTRIAL_ROBOT_6AXIS`)
- `IMM-001` (`INJECTION_MOLDING_MACHINE`)
- `VIS-001` (`VISION_INSPECTION_STATION`)

### Hierarchy

```
Root
 └── Objects
      └── Factory
           └── Plant_01
                └── Line_A
                     └── CNC-001
                          ├── sequence (UInt32)
                          ├── operating_state (String)
                          ├── spindle_speed_rpm (Double)
                          ├── spindle_load_pct (Double)
                          └── ...
```

## 3. Deterministic Node IDs

Node IDs follow the deterministic namespace convention (`ns=2`):
`ns=2;s=Factory/Plant_01/Line_A/{machine_id}/{signal_name}`

Header variables:
- `ns=2;s=Factory/Plant_01/Line_A/{machine_id}/sequence`
- `ns=2;s=Factory/Plant_01/Line_A/{machine_id}/operating_state`

## 4. Server & Adapter Architecture

- **Server Manager**: `OPCUAServerManager` utilizes `asyncua.Server` to instantiate the information model and update node variables asynchronously when `update_from_telemetry()` is invoked.
- **Client Adapter**: `OPCUAAdapter` connects via `asyncua.Client`, reads node values by deterministic string IDs, and constructs `ProtocolReading` instances.
