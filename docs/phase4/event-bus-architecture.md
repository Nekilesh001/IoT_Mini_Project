# Phase 4 — Event Bus & Storage Architecture

## 1. Overview

Phase 4 establishes the local operational data and event distribution plane for the **Smart Factory Machine Monitoring and Predictive Maintenance System**. It decouples edge canonicalization (Phase 3) from downstream query APIs, dashboard visualization, and future analytics through a local event bus and durable storage engine.

```mermaid
flowchart TD
    CT[Canonical Telemetry (Phase 3)] --> PUB[Canonical Telemetry Publisher]
    PUB -->|MQTT Publish| EB[Local MQTT Event Bus]
    PUB -->|Outage Fallback| PB[(Persistent Buffer SQLite)]
    
    EB --> SUB[Canonical Telemetry Consumer]
    SUB --> REPO[Telemetry Repository]
    REPO --> PG[(PostgreSQL / SQLite Operational DB)]
    
    PB --> RW[Replay Worker]
    RW -->|Recovery Drain| PUB
    RW -->|Direct Persistence| REPO
```

## 2. Key Responsibilities

1. **Transport Isolation**: Serialized Phase 3 `CanonicalTelemetry` events are published over a local MQTT broker using structured, deterministic topic hierarchies.
2. **Operational Persistence**: Events are ingested by subscribers and stored idempotently in a time-series operational database using PostgreSQL JSONB (or SQLite for local dev).
3. **Store-and-Forward Buffering**: If the MQTT broker or PostgreSQL database is unavailable, telemetry events are queued into a local, crash-resilient SQLite buffer.
4. **Deterministic Replay**: When the transport or storage layer recovers, a background replay worker drains buffered events with exponential backoff and delivers them in deterministic order (`created_at`, `machine_id`, `sequence`).
5. **Repository Abstraction**: Provides clean, testable interfaces (`TelemetryRepository`) for time-range queries, machine history, latest snapshots, and counts.
