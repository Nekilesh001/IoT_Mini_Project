# Phase 10 — Security Testing & Verification

## Test Matrix

The test suite in `tests/security/` verifies all security controls:

1. `test_secrets.py`: Environment resolution, mandatory secret enforcement, safe masking, and regex secret hygiene scanning.
2. `test_certificates.py`: Local X.509 CA generation, CSR signing, certificate validation, expiration rejection, and SAN checking.
3. `test_auth.py`: PBKDF2 password hashing, valid/invalid login flows, JWT token creation, negative expiry rejection, and signature decoding.
4. `test_rbac.py`: Role hierarchy enforcement across `VIEWER`, `OPERATOR`, `MAINTAINER`, and `ADMIN`.
5. `test_api_security.py`: HTTP security headers, bearer token validation, correlation ID propagation, and 403 Forbidden denial on unauthorized audit endpoints.

## CLI Execution
```bash
# Run standalone security demo
python -m security.demo

# Run secret hygiene scanner
python -m security.validation

# Run automated pytest security suite
python -m pytest tests/security -v
```
