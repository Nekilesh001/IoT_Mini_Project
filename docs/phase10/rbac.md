# Phase 10 — Role-Based Access Control (RBAC)

## Overview
The RBAC subsystem (`security/rbac.py` and `security/models.py`) provides declarative permission mapping across four hierarchical roles.

## Role Hierarchy & Permission Matrix

| Role | Hierarchy Level | Key Permissions | Excluded Operations |
|---|---|---|---|
| **VIEWER** | Level 1 | `telemetry:read`, `machines:read`, `alerts:read`, `ml:read`, `shadow:read`, `fleet:read`, `jobs:read`, `resilience:read` | Alert acknowledgment, shadow updates, job creation, system administration |
| **OPERATOR** | Level 2 | All VIEWER permissions + `alerts:ack`, `alerts:resolve`, `commands:execute`, `shadow:desired:update`, `shadow:sync`, `jobs:cancel` | Config job creation, OTA deployments, security administration |
| **MAINTAINER** | Level 3 | All OPERATOR permissions + `jobs:config:create`, `jobs:ota:create`, `fleet:metadata:update`, `scenarios:inject`, `resilience:test:run` | User management, certificate generation, security configuration changes |
| **ADMIN** | Level 4 | All Level 1-3 permissions + `security:manage`, `users:manage`, `certificates:manage`, `security:audit:read` | None (Superuser access) |

## Implementation
```python
policy = RBACPolicy()
has_access = policy.has_permission(Role.OPERATOR, Permission.ACK_ALERTS) # True
has_access = policy.has_permission(Role.OPERATOR, Permission.CREATE_CONFIG_JOBS) # False
```
