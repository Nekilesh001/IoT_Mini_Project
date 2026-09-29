# Fleet Management & Machine Indexing

## 1. Scope & Inventory

The `FleetManager` coordinates inventory records for all 12 heterogeneous machines in the factory catalog:
- **Identity & Type**: `machine_id`, `machine_type` (CNC, Robot, Pump, Chiller, etc.)
- **Protocol**: OPC UA, Modbus TCP, MQTT
- **Connectivity State**: `ONLINE`, `OFFLINE`, `DEGRADED`, `UNKNOWN`
- **Management State**: `ACTIVE`, `MAINTENANCE`, `UNPROVISIONED`, `QUARANTINED`, `DECOMMISSIONED`
- **Version Tracking**: `software_version`, `firmware_version`, `config_version`
- **Telemetry Health**: `last_seen` timestamp

## 2. Fleet Summary Aggregations

Aggregates operational counts across connectivity states, protocol distributions, machine types, pending shadow deltas, and active management jobs for high-level operations consoles.
