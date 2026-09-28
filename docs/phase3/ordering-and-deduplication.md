# Phase 3: Ordering & Deduplication Engine

## 1. Sequence Tracking

- Sequence counters are tracked per `machineId` independently.
- Expected behavior:
  - `sequence == last_seq + 1`: `ACCEPTED` (Continuous stream).
  - `sequence > last_seq + 1`: `ACCEPTED` (Flags `gap_detected = True` and records `gap_size`).
  - `sequence == last_seq`: `DUPLICATE` (Duplicate sequence rejection).
  - `sequence < last_seq`: `OUT_OF_ORDER` (Out-of-order rejection).

## 2. Event ID Deduplication

- Every ingested event ID (`eventId`) is registered in a bounded ring buffer (default 1000 items).
- Re-submission of an existing `eventId` is tagged as `DUPLICATE`.
