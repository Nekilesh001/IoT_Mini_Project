# Local Persistence & Backends

## 1. Database Schema

The local backend persists state across 5 tables defined in `device_management/repository.py`:
1. `device_shadow`: Stores `desired_state`, `reported_state`, `version`, `updated_at`.
2. `fleet_devices`: Stores metadata, versions, connectivity state, and last seen timestamps.
3. `management_jobs`: Stores job definitions, payloads, statuses, and retry attempt counters.
4. `job_attempts`: Detailed execution records for every attempt.
5. `management_audit`: Immutable audit trail logs.

## 2. Storage Engine Compatibility

Fully compatible with SQLite (`sqlite:///:memory:` for tests, local SQLite file) and PostgreSQL (`postgresql+psycopg2://` for production) with native JSON/JSONB support.
