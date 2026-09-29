# Phase 4 — Telemetry Repository & Query Layer

## 1. Overview

The `TelemetryRepository` encapsulates all database operations, providing clean query abstractions for future Phase 5 REST APIs and analytics while keeping transport protocols completely decoupled from storage logic.

## 2. API Interface

```python
class TelemetryRepository:
    def insert(self, canonical: CanonicalTelemetry) -> bool:
        """Idempotently insert single record. Returns False on duplicate without crashing."""

    def insert_many(self, telemetry_list: List[CanonicalTelemetry]) -> int:
        """Batch insert records idempotently. Returns count of newly inserted items."""

    def get_by_event_id(self, event_id: str) -> Optional[TelemetryRecord]:
        """Fetch record by exact event ID."""

    def get_latest_by_machine(self, machine_id: str) -> Optional[TelemetryRecord]:
        """Fetch latest telemetry record for a machine by sequence."""

    def get_machine_history(self, machine_id: str, limit: int = 100) -> List[TelemetryRecord]:
        """Fetch recent history for machine ordered by event_time descending."""

    def count_by_machine(self, machine_id: str) -> int:
        """Count total persisted records for a given machine."""

    def query_time_range(self, machine_id: str, start_time: datetime, end_time: datetime) -> List[TelemetryRecord]:
        """Query time range ordered ascending for analytical trends."""
```

## 3. Session & Connection Management

Sessions are managed using scoped SQLAlchemy session factories (`scoped_session` or context-managed sessions), ensuring:
- Immediate commit on success and rollback on exceptions.
- No dangling connection leaks.
- Engine pooling suitable for concurrent API reads and subscriber writes.
