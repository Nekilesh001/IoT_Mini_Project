# Phase 10 — API & Service Authorization

## Overview
Authorization (`security/authorization.py`) enforces server-side permission checks on all incoming REST requests, SSE streams, and internal service calls.

## FastAPI Authorization Dependencies

FastAPI endpoints declare authorization requirements via dependency injection:

```python
from fastapi import Depends
from security.authorization import require_permission, get_current_user
from security.models import Permission, User

@router.post("/jobs/config")
async def create_config_job(
    request: JobCreateRequest,
    current_user: User = Depends(require_permission(Permission.CREATE_CONFIG_JOBS)),
):
    ...
```

## Error Handling & Audit Integration
When an unauthorized request occurs:
1. An HTTP `403 Forbidden` status code is returned with `{"detail": "Permission denied: <permission_name> required."}`.
2. A security audit event (`SecurityAuditEventType.AUTHORIZATION_FAILURE`) is dispatched to `SecurityAuditService`.
3. No stack traces, secrets, or internal system paths are exposed to the client.
