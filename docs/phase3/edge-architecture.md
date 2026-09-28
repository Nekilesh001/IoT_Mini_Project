# Phase 3: Edge Ingestion Architecture

## 1. Overview

Phase 3 establishes the protocol-agnostic Edge Ingestion Pipeline that consumes `ProtocolReading` instances emitted by Modbus TCP, OPC UA, and MQTT adapters and transforms them into validated, normalized, quality-tagged, ordered, and deduplicated `CanonicalTelemetry` records.

```
+-------------------------------------------------------------------------+
|                  Phase 2 Protocol Adapters                              |
|   - Modbus TCP Adapter (Holding Register Array)                         |
|   - OPC UA Adapter (Typed Variant Nodes)                                |
|   - MQTT Adapter (JSON PubSub Payloads)                                 |
+-------------------------------------------------------------------------+
                                    |
                                    v (ProtocolReading)
+-------------------------------------------------------------------------+
|                  Phase 3 Edge Ingestion Pipeline                        |
|                                                                         |
|   1. Profile & Identity Resolver (Machine validation & metadata)        |
|   2. Schema & Range Validator (Machine-aware SignalDefinitions)         |
|   3. Unit Normalizer (Deterministic physical unit standard)             |
|   4. Quality Assessment Engine (GOOD, BAD, STALE, OUT_OF_RANGE, etc.)   |
|   5. Sequence & Duplicate Tracker (Per-machine monotonically ordered)   |
|   6. Edge Derived Metrics Calculator (Simple deterministic formulas)    |
|   7. Canonical Telemetry Builder (Standard JSON Envelope)               |
+-------------------------------------------------------------------------+
                                    |
                                    v (CanonicalTelemetry / IngestionResult)
+-------------------------------------------------------------------------+
|             Phase 4 Local Event Bus & Storage (Deferred)                |
+-------------------------------------------------------------------------+
```

## 2. Ingestion Result Model

Every ingestion operation returns an explicit `IngestionResult` object containing:
- `status`: `ACCEPTED`, `DUPLICATE`, `OUT_OF_ORDER`, `INVALID`, `REJECTED`
- `canonical_telemetry`: Populated `CanonicalTelemetry` object when accepted
- `errors`: List of validation / schema / routing errors
- `warnings`: Uncatalogued signals or non-fatal missing optional attributes
- `metrics`: Sequence gap size, latency, processing counters
