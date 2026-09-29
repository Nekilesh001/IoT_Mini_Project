# Testing & Verification Strategy

## 1. Test Suite Coverage

- `tests/device_management/test_shadow.py`: Shadow desired/reported updates, delta computation, version incrementation, optimistic concurrency error handling, and synchronization.
- `tests/device_management/test_fleet.py`: Fleet machine registration, catalog queries, connectivity state tracking, metadata patching, and fleet summary aggregations.
- `tests/device_management/test_jobs.py`: Full job lifecycle state transitions (`PENDING -> IN_PROGRESS -> SUCCEEDED/FAILED/CANCELLED`), retry policies, max attempt enforcement, and attempt history records.
- `tests/device_management/test_commands.py`: Industrial command validation, shadow updating, job scheduling, and audit logging.
- `tests/device_management/test_repository.py`: CRUD operations across all 5 ORM tables on SQLite/PostgreSQL.
- `tests/device_management/test_api.py`: FastAPI REST API endpoints.
- `tests/device_management/test_aws_scaffold.py`: Cloud interface conformance, AWS scaffold instantiation, disabled-by-default verification.

## 2. Test Execution

```bash
pytest tests/device_management/ -v
python -m device_management.demo
```
