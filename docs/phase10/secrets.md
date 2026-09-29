# Phase 10 — Secrets Management & Hygiene

## Secrets Architecture

The secrets subsystem (`security/secrets.py`) enforces strict separation between application code and environment-specific secrets.

### Key Capabilities

1. **Environment-Driven Configuration**: Secrets are resolved from environment variables or `.env` files using `python-dotenv`.
2. **Typed Security Configuration (`SecurityConfig`)**: Validates mandatory secrets, token expiration intervals, TLS/mTLS parameters, and local bootstrap user profiles.
3. **Automated Secret Hygiene Scanner (`security/validation.py`)**:
   - Regex and entropy-based scanning across workspace source files (`.py`, `.ts`, `.tsx`, `.json`, `.yaml`, `.env.example`).
   - Detects AWS access keys (`AKIA...`), generic API keys, private key blocks (`BEGIN PRIVATE KEY`), and hard-coded passwords.
   - Command: `python -m security.validation` produces clean PASS/FAIL reporting without logging detected secret values.
4. **Zero-Leakage Masking**:
   - Helper `mask_secret(val)` redacts strings (`********`) to prevent accidental logging in exception handlers or audit trails.

## Configuration Template (`.env.example`)

```bash
# Security & Secret Settings (Placeholders Only)
DATABASE_URL=sqlite:///./data/telemetry_dev.db
MQTT_USERNAME=edge_worker
MQTT_PASSWORD=
API_SECRET=
JWT_SECRET=
JWT_ALGORITHM=HS256
JWT_EXPIRATION_MINUTES=60

TLS_ENABLED=false
MTLS_ENABLED=false
CA_CERT_PATH=certs/ca/ca.crt
SERVER_CERT_PATH=certs/server/server.crt
SERVER_KEY_PATH=certs/server/server.key
CLIENT_CERT_PATH=certs/clients/client.crt
CLIENT_KEY_PATH=certs/clients/client.key

BOOTSTRAP_ADMIN_USERNAME=admin
BOOTSTRAP_ADMIN_PASSWORD=
```
