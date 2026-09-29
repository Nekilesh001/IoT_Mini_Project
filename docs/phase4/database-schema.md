# Phase 4 — Database Schema & Heterogeneous Storage

## 1. Table: `telemetry_records`

Operational telemetry is persisted in a relational schema with JSON/JSONB support for heterogeneous machine signals.

| Column | Type | Constraints / Details |
|---|---|---|
| `event_id` | VARCHAR(64) | PRIMARY KEY |
| `schema_version` | VARCHAR(16) | NOT NULL, default '1.0.0' |
| `event_type` | VARCHAR(32) | NOT NULL, default 'TELEMETRY' |
| `plant_id` | VARCHAR(32) | NOT NULL, Index |
| `line_id` | VARCHAR(32) | NOT NULL, Index |
| `machine_id` | VARCHAR(64) | NOT NULL, Index |
| `machine_type` | VARCHAR(64) | NOT NULL |
| `protocol` | VARCHAR(32) | NOT NULL |
| `endpoint` | VARCHAR(256) | NULL |
| `source_address` | VARCHAR(256) | NOT NULL |
| `event_time` | TIMESTAMPTZ | NOT NULL, Index |
| `ingestion_time` | TIMESTAMPTZ | NOT NULL |
| `sequence` | BIGINT | NOT NULL, Index |
| `operating_state` | VARCHAR(32) | NOT NULL, default 'RUNNING' |
| `health_state` | VARCHAR(32) | NOT NULL, default 'HEALTHY' |
| `quality` | VARCHAR(32) | NOT NULL, default 'GOOD' |
| `measurements` | JSONB / JSON | NOT NULL (heterogeneous sensor key-value map) |
| `derived` | JSONB / JSON | NULL (computed physical metrics) |
| `ml` | JSONB / JSON | NULL (operational feature metadata) |
| `received_at` | TIMESTAMPTZ | NOT NULL, default `NOW()` |

## 2. Uniqueness & Indexes

- **Composite Unique Constraint**: `uq_telemetry_machine_sequence (machine_id, sequence)` — prevents duplicate sequence insertions per machine.
- **Index**: `ix_telemetry_machine_event_time (machine_id, event_time)` — optimizes single-machine time-series range scans.
- **Index**: `ix_telemetry_plant_line_event_time (plant_id, line_id, event_time)` — enables line/plant-wide aggregation queries.
- **Index**: `ix_telemetry_event_type_event_time (event_type, event_time)` — facilitates event-type filtering.

## 3. Heterogeneous Measurement Rationale

Rather than defining a sparse relational table with hundreds of nullable columns for 12 distinct machine profiles (e.g. CNC Lathe spindle speed vs AGV battery state of charge vs Chiller COP), `measurements` uses PostgreSQL `JSONB` (`JSON` on SQLite). This preserves exact physical signals per machine without schema migrations when introducing new equipment.
