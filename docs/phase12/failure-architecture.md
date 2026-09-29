# Phase 12 — Failure & Resilience Architecture

## Overview
Phase 12 introduces deterministic failure injection, automated invariant checking, and recovery verification for edge-first manufacturing deployments.

```
+-----------------------------------------------------------------------------+
|                       Failure & Resilience Architecture                     |
|                                                                             |
|   +---------------------------------------------------------------------+   |
|   |                        Failure Injector                             |   |
|   |   - Intercepts MQTT, DB, Adapters, ML, Alerts, Jobs, Network        |   |
|   +---------------------------------------------------------------------+   |
|                                     |                                       |
|                                     v                                       |
|   +---------------------------------------------------------------------+   |
|   |                        Scenario Runner                              |   |
|   |   - Executes 15 deterministic failure/recovery lifecycle scenarios  |   |
|   +---------------------------------------------------------------------+   |
|                                     |                                       |
|             +-----------------------+-----------------------+               |
|             v                                               v               |
|   +-----------------------+                       +---------------------+   |
|   | Invariant Assertions  |                       |  Metrics Collector  |   |
|   | - Zero data loss      |                       | - Detection Latency |   |
|   | - Deduplication check |                       | - Recovery Duration |   |
|   | - ML isolation        |                       | - Buffered/Replayed |   |
|   | - Ground truth guard  |                       | - Error Rates       |   |
|   +-----------------------+                       +---------------------+   |
+-----------------------------------------------------------------------------+
```

## Core Resilience Mechanisms
1. **Store-and-Forward Buffering**: When the event bus or storage database is unavailable, telemetry is placed into persistent SQLite buffering.
2. **Deterministic Replay**: On component recovery, buffered batches are replayed in order, marking records delivered with zero data loss.
3. **Graceful ML Degradation**: If ONNX models fail or feature schemas mismatch, the edge fallback path preserves real-time ingestion and deterministic rule-based alerts.
4. **Target Leakage Shielding**: Failure reports and resilience metrics NEVER expose simulator-only degradation percentages or hidden failure timestamps.
