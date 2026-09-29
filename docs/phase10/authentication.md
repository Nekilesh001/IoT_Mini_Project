# Phase 10 — Local Authentication

## Overview
The authentication subsystem (`security/auth.py`) implements a local, cryptographically secure JSON Web Token (JWT) workflow designed for on-premise industrial gateways without external identity providers.

## Key Features

1. **Bootstrap Developer Accounts**:
   - Initialized from environment variables (`ADMIN_USERNAME`, `OPERATOR_USERNAME`, `MAINTAINER_USERNAME`, `VIEWER_USERNAME`).
   - Passwords hashed using PBKDF2-HMAC-SHA256 with 100,000 iterations.
2. **JWT Token Lifecycle**:
   - Signature algorithm: `HS256`.
   - Claims: `sub` (username), `role` (Role enum), `jti` (unique token ID), `iat` (issued at), `exp` (expiration).
   - Configurable TTL (default: 60 minutes).
3. **Endpoint Contracts**:
   - `POST /api/auth/login`: Authenticates user and returns Bearer token payload.
   - `GET /api/auth/me`: Decodes active token and returns user details and permission set.
