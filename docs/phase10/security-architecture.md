# Phase 10 — Security Architecture

## Overview
The Smart Factory Security Architecture provides defense-in-depth controls designed specifically for local, edge-first industrial IoT deployments. The system secures credentials, machine-to-edge communication, REST API management, and administrative workflows without introducing mandatory cloud dependencies or blocking offline local development.

```
+-----------------------------------------------------------------------------+
|                          Security Perimeter                                 |
|                                                                             |
|  +--------------------+        mTLS / TLS         +----------------------+  |
|  |  Factory Machines  | ------------------------> | Protocol Adapters &  |  |
|  | (PMP/CNC/ROB/ENV)  |   X.509 Client Certs      | Local MQTT Broker    |  |
|  +--------------------+                           +----------------------+  |
|                                                              |              |
|                                                              v              |
|  +--------------------+    Bearer JWT + RBAC      +----------------------+  |
|  | React Dashboard /  | ------------------------> | Edge FastAPI Gateway |  |
|  | Management Clients |   Correlation ID Tracking | & Security Middlew.  |  |
|  +--------------------+                           +----------------------+  |
|                                                              |              |
|                                                              v              |
|  +--------------------+                           +----------------------+  |
|  |  Security Audit    | <======================== | RBAC Enforcement &   |  |
|  |  Log (Masked)      |    Action / Denial Events | Secret Scrubbing     |  |
|  +--------------------+                           +----------------------+  |
+-----------------------------------------------------------------------------+
```

## Security Principles & Boundaries

1. **Local-First Independence**: All cryptographic operations, X.509 certificate generation, JWT signing, RBAC evaluations, and secret validations execute purely in-process or against local files. No AWS Cognito, Secrets Manager, or IAM connection is required.
2. **Deterministic Role-Based Access Control (RBAC)**: Hierarchical roles (`VIEWER`, `OPERATOR`, `MAINTAINER`, `ADMIN`) strictly partition telemetry reads, alert acknowledgments, shadow state modifications, job submissions, and audit trail inspection.
3. **Secret Hygiene & Zero-Leakage**: High-entropy strings, passwords, private keys, and tokens are scrubbed from log files, error responses, and audit records. Automated scanner validates absence of committed secrets.
4. **Dual Mode Communication**: Supports both standard insecure development mode (`TLS_ENABLED=false`) and cryptographically verified mTLS mode (`TLS_ENABLED=true`, `MTLS_ENABLED=true`) without breaking existing workflows.
5. **Machine Learning Leakage Preservation**: Security logs, error responses, and audit events strictly exclude ground-truth degradation counters, hidden health labels, and simulated fault parameters.
