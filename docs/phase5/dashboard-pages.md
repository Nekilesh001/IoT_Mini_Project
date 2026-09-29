# Dashboard Pages & Views — Phase 5

This document describes the views, components, and user interactions implemented in the Phase 5 React application.

---

## 1. Overview Page (`/`)

The primary operations landing page for plant engineers and floor supervisors.

```
+-----------------------------------------------------------------------------------+
| Total Machines: 12 | Running: 10 | Warning: 1 | Fault: 1 | Maint: 0 | Live SSE: OK    |
+-----------------------------------------------------------------------------------+
| [Line Filter: ALL | LINE_1 | LINE_2 | LINE_3]  [Protocol Filter: ALL | Modbus | OPC UA | MQTT] |
+-----------------------------------------------------------------------------------+
|  [ CNC-001 ]        [ AGV-001 ]          [ CHILLER-001 ]      [ ROBOT-001 ]       |
|  Status: RUNNING    Status: RUNNING      Status: WARNING      Status: RUNNING     |
|  Protocol: Modbus   Protocol: MQTT       Protocol: OPC UA     Protocol: Modbus    |
|  Spindle: 3200 RPM  Battery: 88.5%       Supply Temp: 6.2°C   Joint 1: 45.2°      |
|  Temp: 42.1°C       Speed: 1.2 m/s       Return Temp: 11.8°C  Torque: 34.1 Nm     |
|  Seq: 450 | Good    Seq: 450 | Good      Seq: 450 | Good      Seq: 450 | Good     |
+-----------------------------------------------------------------------------------+
```

### Key Elements:
- **Factory Summary Cards**: Display Total Fleet, Active Running, Warning, Fault, and Maintenance metrics.
- **Filter Toolbar**: Instant filtering by Production Line and Industrial Protocol.
- **12-Machine Grid**: Machine cards customized with domain-specific live metrics (e.g. CNC shows spindle RPM and temperatures, AGVs show battery SOC and speeds, Chillers show temperatures and flow rates).
- **Navigation**: Clicking any card routes directly to the detailed telemetry view for that machine.

---

## 2. Machine Detail Page (`/machines/:machineId`)

Deep inspection page for an individual machine asset.

```
+-----------------------------------------------------------------------------------+
| <-- Back to Overview | CNC-001 (CNC Mill) | Line 1 - Plant 1 | Status: RUNNING (GOOD) |
+-----------------------------------------------------------------------------------+
| LIVE MEASUREMENTS                                                                 |
| [ Spindle Speed: 3200.5 RPM ] [ Spindle Temp: 42.8 °C ] [ Vibration: 0.045 g ]   |
| [ Feed Rate: 850.0 mm/min   ] [ Coolant Flow: 14.2 L/min] [ Power: 4.85 kW ]      |
+-----------------------------------------------------------------------------------+
| HISTORICAL TRENDS                                                                 |
| Range: [5 min | 15 min | 1 hour | 24 hours]   Signals: [x] Spindle Speed [x] Temp |
|                                                                                   |
|  RPM                                                                              |
| 3500 |              /\____/\                                                      |
| 3000 | ___________/        \__________                                            |
| 2500 |                                                                            |
|      +--------------------------------+                                           |
|       10:00        10:05        10:10                                             |
+-----------------------------------------------------------------------------------+
| ASSET SIGNAL CATALOG & PROVENANCE                                                 |
| - Protocol: MODBUS_TCP                                                            |
| - Ingestion Time: 2026-09-29T10:10:00.120Z                                        |
| - Source Adapter: modbus_edge_adapter                                             |
| - Ground Truth Leakage: NONE DETECTED                                             |
+-----------------------------------------------------------------------------------+
```

### Key Elements:
- **Real-Time Header**: Asset ID, machine type, plant/line hierarchy, current state, health rating, and telemetry quality tag.
- **Live Measurement Cards**: Auto-populated from the machine's active signal catalog with engineering units.
- **Interactive Time-Series Chart**:
  - Time range selector (`5m`, `15m`, `1h`, `24h`).
  - Multi-signal selector toggles individual measurements.
  - Responsive SVG rendering with auto-scaling min/max bounds and hover tooltips.
- **Asset Metadata & Catalog**: Full signal catalog showing signal keys, display names, and types.

---

## 3. Protocol Health Page (`/protocols`)

Operational health and connectivity status across industrial protocol adapters.

### Key Elements:
- **Protocol Status Cards**: Dedicated cards for **Modbus TCP**, **OPC UA**, and **MQTT**.
- **Metrics**: Displays connection status (`HEALTHY`, `DEGRADED`, `DISCONNECTED`), managed machine count (4 machines per protocol), and timestamp of the last recorded telemetry packet.
- **Quick Links**: Direct navigation to machines monitored under each specific protocol adapter.
