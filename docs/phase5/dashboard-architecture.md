# Dashboard Architecture — Phase 5 React Application

This document outlines the design principles, architecture, component hierarchy, and design system of the Phase 5 React dashboard application.

---

## 1. Design Principles & Aesthetics

The dashboard is built as an **Industrial Operations Console**:
- **Industrial Dark Theme**: High-contrast, slate-gray palette (`#0B0F19`, `#111827`, `#1F2937`) engineered for control-room monitoring and reduced visual fatigue.
- **Heterogeneous Machine Handling**: Rejects universal measurement assumptions. CNC, AGV, Chiller, Robot Arm, and Molding machines display their respective engineering telemetry and units.
- **Live Reactivity**: Telemetry, machine state, quality indicators, and trend graphs update seamlessly via Server-Sent Events without full-page reloads.
- **Accessibility & Clarity**: State badges (RUNNING, IDLE, WARNING, FAULT, MAINTENANCE, OFF) utilize distinct icons, high-contrast text, and border styling rather than relying solely on color.

---

## 2. Technology Stack

- **Framework**: React 19 + TypeScript
- **Build Tool**: Vite 7
- **Routing**: React Router 7 (`react-router-dom`)
- **Icons**: Lucide React
- **Styling**: Vanilla CSS Design System with CSS variables and utility classes
- **Charts**: Custom responsive SVG-based time-series charts with auto-scaling axes, hover tooltips, and multi-signal support.

---

## 3. Directory Structure

```
dashboard/react-app/
├── package.json
├── tsconfig.json
├── vite.config.ts
├── index.html
├── src/
│   ├── main.tsx
│   ├── App.tsx
│   ├── index.css
│   ├── types/
│   │   └── index.ts          # TypeScript domain models and schemas
│   ├── api/
│   │   ├── client.ts         # Axios/Fetch HTTP client abstraction
│   │   ├── factory.ts        # Factory and Protocol API endpoints
│   │   └── machines.ts       # Machine and Telemetry API endpoints
│   ├── hooks/
│   │   ├── useFactorySummary.ts
│   │   ├── useMachines.ts
│   │   ├── useMachineDetail.ts
│   │   ├── useMachineHistory.ts
│   │   └── useRealtimeTelemetry.ts
│   ├── components/
│   │   ├── Layout.tsx        # Top navbar, sidebar, realtime status bar
│   │   ├── MetricCard.tsx    # Operational summary cards
│   │   ├── MachineCard.tsx   # Fleet overview machine card
│   │   ├── StateBadge.tsx    # Industrial state indicator
│   │   ├── QualityBadge.tsx  # Telemetry quality tag (GOOD, BAD, STALE...)
│   │   ├── ProtocolBadge.tsx # Modbus, OPC UA, MQTT tags
│   │   └── TimeSeriesChart.tsx # Dynamic SVG time-series visualizer
│   ├── pages/
│   │   ├── OverviewPage.tsx      # Factory overview + 12-machine grid
│   │   ├── MachineDetailPage.tsx # Deep inspection + live + trend charts
│   │   └── ProtocolHealthPage.tsx # Modbus/OPC UA/MQTT health dashboard
│   └── test/
│       ├── setup.ts
│       ├── MachineCard.test.tsx
│       ├── MetricCard.test.tsx
│       ├── StateBadge.test.tsx
│       └── ProtocolHealthPage.test.tsx
```

---

## 4. State Management & Data Flow

- **Zero Heavyweight Store**: Data management uses React hooks (`useFactorySummary`, `useMachines`, `useRealtimeTelemetry`) combined with local component state.
- **Decoupled API Client**: All HTTP requests are channeled through `src/api/`, abstracting backend URLs and response transformations.
- **Component Hierarchy**:
  - `App` $\to$ `Layout` (Sidebar + Header + Status Bar) $\to$ `Routes`:
    - `/` $\to$ `OverviewPage` (MetricCards + MachineCard Grid)
    - `/machines/:machineId` $\to$ `MachineDetailPage` (Live telemetry + Signal Catalog + TimeSeriesChart)
    - `/protocols` $\to$ `ProtocolHealthPage` (Protocol Cards + Adapter Status)
