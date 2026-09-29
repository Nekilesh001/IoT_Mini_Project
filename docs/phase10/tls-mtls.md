# Phase 10 — Local TLS & Mutual TLS (mTLS)

## Overview
The system provides a local X.509 PKI toolkit (`security/certificates.py` and `security/mtls.py`) enabling cryptographic authentication and encryption between edge devices, adapters, and local MQTT brokers.

## PKI Capabilities

1. **Local Certificate Authority (CA)**:
   - Self-signed X.509 Root CA generation with RSA 2048/4096-bit keys.
   - CA key usage: `keyCertSign`, `cRLSign`.
2. **Server & Client Certificate Issuance**:
   - Certificate Signing Requests (CSR) signed by local CA.
   - Subject Alternative Names (SAN) support for `localhost`, `127.0.0.1`, and machine identifiers (e.g. `PMP-001`).
3. **Chain & Revocation/Expiry Verification**:
   - Expiration checking against current system time.
   - Cryptographic signature validation against CA public certificate.
   - Hostname/SAN verification against connection target.
4. **Local SSLContext Builder**:
   - Creates Python `ssl.SSLContext` configured for TLSv1.2/TLSv1.3 with client certificate validation (`ssl.CERT_REQUIRED`).

## Safe Storage & Git Hygiene
Generated keys and certificates are written exclusively to `certs/` (`certs/ca/`, `certs/server/`, `certs/clients/`), which is ignored by `.gitignore` to prevent secret leakage.
