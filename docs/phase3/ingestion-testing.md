# Phase 3: Edge Ingestion Testing Strategy

## 1. Test Suite Structure

The Edge Ingestion test suite consists of 9 test modules located in `tests/edge/`:

1. `test_canonical_model.py`: Canonical schema validation, serialization, and deserialization.
2. `test_validation.py`: Machine identity, datatype, and engineering range bounds.
3. `test_normalization.py`: Unit conversion calculations and unsupported conversion rejections.
4. `test_quality.py`: Quality code precedence rules and staleness detection.
5. `test_sequence.py`: Monotonic sequence ordering and gap metric tracking.
6. `test_duplicates.py`: Duplicate sequence and eventId detection.
7. `test_ingestion_service.py`: Pipeline execution across heterogeneous machine types.
8. `test_ground_truth_isolation.py`: Strict isolation asserting zero ground-truth fields in canonical payloads.
9. `test_edge_protocol_integration.py`: End-to-end integration across Modbus TCP, OPC UA, and MQTT.

## 2. Test Commands

```bash
# Run Phase 3 Edge tests
python -m pytest tests/edge/ -v

# Run entire system test suite (Phase 1 + Phase 2 + Phase 3)
python -m pytest tests/simulator/ tests/protocols/ tests/edge/ -v
```
