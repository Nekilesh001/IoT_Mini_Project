# Phase 10 — Security Audit Trail

## Overview
The security audit subsystem (`security/audit.py`) records all authentication attempts, authorization denials, cryptographic events, and administrative actions with automated secret scrubbing.

## Audit Record Schema

```json
{
  "event_id": "aud-8b2b7190-67c4-49c9-94ea-630df2b79eb4",
  "timestamp": "2026-09-29T16:50:00.000000Z",
  "event_type": "AUTHORIZATION_FAILURE",
  "actor": "operator",
  "role": "OPERATOR",
  "action": "security:audit:read",
  "machine_id": null,
  "result": "DENIED",
  "ip_address": "127.0.0.1",
  "details": {
    "path": "/api/security/audit",
    "method": "GET"
  }
}
```

## Security Invariants
1. **Zero-Secret Logging**: Passwords, raw JWT tokens, cryptographic private keys, and API secrets are strictly scrubbed before persistence.
2. **Deterministic Append-Only History**: In-memory ring buffer (up to 1,000 entries) and SQLite-backed persistence store audit events.
3. **RBAC Guarded**: Audit trail endpoints require `ADMIN` or authorized operational roles (`security:audit:read`).
