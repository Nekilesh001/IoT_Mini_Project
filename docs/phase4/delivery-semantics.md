# Phase 4 — Delivery Semantics & Idempotency

## 1. At-Least-Once Delivery

In distributed IoT edge networks with store-and-forward retransmissions and MQTT QoS 1, claiming *exactly-once* transport delivery is unrealistic due to potential network partition acknowledgments.

Phase 4 explicitly implements:
$$\textbf{At-Least-Once Transport Delivery} + \textbf{Idempotent Database Persistence}$$

## 2. Idempotency Guarantees

Idempotency is enforced at multiple layers:

1. **Database Constraints**:
   - Primary Key: `event_id`
   - Unique Constraint: `(machine_id, sequence)`
2. **Conflict Resolution Strategy**:
   - `TelemetryRepository.insert()` checks for existing `event_id` or `(machine_id, sequence)`.
   - Repeated delivery of identical payloads is safely ignored (`return False`) without raising unhandled exceptions or duplicating records.
3. **Consumer Decoupling**:
   - Subscribing consumers record duplicates in internal operational metrics (`duplicate_count`) and continue processing without stalling the MQTT event stream.
