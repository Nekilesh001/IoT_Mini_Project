# Phase 6: React Dashboard Alert Console & Components

## 1. Overview Page Additions

- **Active Alerts Banner & Panel**: Visually prominent display of all un-resolved factory alerts with severity badges, machine badges, triggering sensor readings, and direct `Acknowledge` action buttons.
- **Factory Status Cards**: Summary counters for `Critical Alerts`, `Warnings`, `Open`, and `Acknowledged` alerts with realtime live pulse indicators.

---

## 2. Dedicated Alerts Page (`/alerts`)

- **KPI Summary Grid**: 4 summary metric cards showing active totals, criticals, warnings, and machines with open violations.
- **Fault Injection Control Panel**: Quick-trigger demo buttons to simulate standard faults (Pump Bearing Wear, Conveyor Belt Jam, CNC Thermal Runaway, Chiller Low Flow, AGV Low Battery).
- **Interactive Alert Console**: Filter by status (`ALL`, `OPEN`, `ACKNOWLEDGED`, `RESOLVED`) and severity (`ALL`, `CRITICAL`, `WARNING`, `INFO`).
- **Explainability View**: Displays the exact sensor measurement that violated the configured rule and the current live measurement value.

---

## 3. Machine Detail Page Integration

- **Machine Alerts Panel**: Displays historical and active alerts specifically filtered for the selected machine node.
- **State & Health Synchronization**: Dynamic state badges update seamlessly alongside real-time alert event propagation via SSE.
