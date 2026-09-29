# Phase 6: Fault Injection and Alerting Architecture

## 1. Architectural Overview

The Phase 6 subsystem introduces systematic, deterministic fault injection and rule-based operational alerting into the Smart Factory platform. The architecture strictly maintains separation between simulator degradation mechanics, protocol communication, edge canonical normalization, rule evaluation, and alert persistence.

```
+-------------------------------------------------------------------------+
|                         Simulation Layer (Phase 1)                      |
|  [BaseMachine Physics] <--- [FaultScenarioManager] (Controlled Injections)
+-------------------------------------------------------------------------+
                                    |
                                    v
+-------------------------------------------------------------------------+
|                         Protocol Layer (Phase 2)                        |
|       [OPC UA Server]       [Modbus TCP Server]       [MQTT Broker]      |
+-------------------------------------------------------------------------+
                                    |
                                    v
+-------------------------------------------------------------------------+
|                           Edge Layer (Phase 3)                          |
|         [Protocol Adapters] -> [Edge Ingestion Engine & Validator]      |
|                       -> Canonical Telemetry (Strict Non-Leakage)        |
+-------------------------------------------------------------------------+
                                    |
                                    v
+-------------------------------------------------------------------------+
|                           Alerting Engine (Phase 6)                     |
|         [Rule Evaluator] (Threshold, RoC, Stale, Missing, Composite)    |
|         [Alert Engine]   (Deduplication, Cooldown, Hysteresis)          |
|         [Alert Repository] -> PostgreSQL / SQLite (`alerts` table)      |
+-------------------------------------------------------------------------+
                                    |
                                    v
+-------------------------------------------------------------------------+
|                      Operational API & UI (Phase 5/6)                   |
|         [FastAPI REST API & SSE Broadcast Service]                      |
|         [React Dashboard: Active Alerts Panel, Console, Ack/Resolve]    |
+-------------------------------------------------------------------------+
```

---

## 2. Strict Safety Boundary

> [!IMPORTANT]
> **Safety Notice**: This project is an educational and architectural simulation of an industrial IoT system.
> Real-world factory safety functions (Emergency Stops, Safety PLCs, Hardware Interlocks, ISO 13849 Safety Relays) operate completely outside and independent of cloud and edge telemetry software.
> The alerting engine in this application is designed solely for operational monitoring, diagnostic visibility, and predictive maintenance demonstration.

---

## 3. Strict Ground-Truth Isolation & Non-Leakage

To ensure explainability and prevent future ML target leakage:
1. **Hidden Simulator Variables Excluded**: Simulation ground-truth variables (such as `degradation_level`, `hidden_wear_counter`, `active_conditions`, and internal `scenario_id`) are strictly confined to the simulator.
2. **Canonical Telemetry Purity**: Canonical telemetry payloads contain only observed sensor measurements and edge-validated states.
3. **Deterministic Explainability**: Every alert is derived strictly from observable telemetry measurements (e.g. `vibration_x_mm_s > 4.5 mm/s`).
