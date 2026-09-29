# Phase 4 — Testing & Quality Assurance

## 1. Test Architecture

The Phase 4 test suite covers model mapping, database repository queries, idempotency, buffer durability, exponential backoff replay, MQTT publisher/consumer integration, and full pipeline roundtrip across Modbus, OPC UA, and MQTT machine types.

```
tests/
├── storage/
│   ├── test_models.py           # SQLAlchemy ORM mapping & JSON/JSONB serialization
│   ├── test_repository.py       # Time-series queries, latest record, counts
│   ├── test_idempotency.py      # Duplicate event_id & (machine_id, seq) protection
│   ├── test_buffer.py           # SQLite persistent buffer state transitions
│   └── test_replay.py           # Replay worker batching & backoff logic
├── event_bus/
│   ├── test_topic_mapping.py    # Canonical topic construction & parsing
│   ├── test_publisher.py        # Publisher connection & fallback buffering
│   ├── test_consumer.py         # Consumer parsing, persistence, malformed JSON safety
│   └── test_mqtt_failures.py    # Simulated broker outage, buffering & replay recovery
└── integration/
    ├── test_phase4_pipeline.py  # End-to-end Modbus/OPC UA/MQTT ingestion to DB
    └── test_restart_recovery.py # Buffer durability across process restart & replay
```

## 2. Running Test Suite

```bash
# Run Phase 4 Storage tests
python -m pytest tests/storage/ -v

# Run Phase 4 Event Bus tests
python -m pytest tests/event_bus/ -v

# Run Phase 4 Integration tests
python -m pytest tests/integration/ -v

# Run Complete Repository Test Suite (Phase 1, 2, 3, 4)
python -m pytest -v
```

## 3. Running the Phase 4 Outage & Recovery Demo

```bash
python -m storage.demo
```
