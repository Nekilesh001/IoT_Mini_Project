# Management Audit Trail

## 1. Auditable Actions

Every management action records an immutable audit log entry in the `management_audit` table:
- `SHADOW_DESIRED_UPDATED`
- `SHADOW_REPORTED_UPDATED`
- `SHADOW_SYNCED`
- `DEVICE_REGISTERED`
- `DEVICE_UPDATED`
- `CONNECTIVITY_CHANGED`
- `JOB_CREATED`
- `JOB_STARTED`
- `JOB_COMPLETED`
- `JOB_FAILED`
- `JOB_RETRIED`
- `JOB_CANCELLED`
- `COMMAND_EXECUTED`

## 2. Audit Record Fields

- `event_id`: Unique identifier
- `machine_id`: Machine target
- `action`: AuditAction enum
- `actor`: `LOCAL_UI`, `LOCAL_SERVICE`, `SYSTEM`, `CLI`, `TEST`
- `timestamp`: UTC timestamp
- `before_state`: State snapshot prior to action
- `after_state`: State snapshot resulting from action
- `result`: Execution outcome payload
- `error`: Error message if action failed
