# Phase 10 — API Security & Hardening Middleware

## Overview
Edge FastAPI endpoints are hardened against standard web attack vectors via security middleware (`security/middleware.py`).

## Hardening Headers

| Header | Configured Value | Purpose |
|---|---|---|
| `X-Content-Type-Options` | `nosniff` | Prevents MIME-type sniffing |
| `X-Frame-Options` | `DENY` | Mitigates clickjacking attacks |
| `Referrer-Policy` | `strict-origin-when-cross-origin` | Protects origin leakage in HTTP referrers |
| `X-Correlation-ID` | Generated UUID / Propagated | Distributed tracing across edge pipeline |
| `Cache-Control` | `no-store, max-age=0` (on sensitive endpoints) | Prevents caching of sensitive credentials |

## REST API Security Endpoints

- `POST /api/auth/login`: Authenticate with username/password, receives JWT access token.
- `GET /api/auth/me`: Inspect authenticated caller identity, role, and permission list.
- `GET /api/security/status`: Inspect TLS, mTLS, and RBAC operational status.
- `GET /api/security/audit`: Inspect security audit trail events (Requires `ADMIN` or `security:audit:read`).
- `POST /api/security/validate-secrets`: Execute on-demand secret hygiene scanner (Requires `ADMIN`).
