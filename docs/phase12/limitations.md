# Phase 12 — Failure Testing Scope & Limitations

## Scope & Boundaries

1. **Local Deterministic Injections**: Failure injections are performed using in-process interceptors, SQLite mock outages, and Python exception wrappers. They do not simulate hardware kernel panics or power outages.
2. **Phase 11 AWS Boundary**: Cloud IoT Core network partition tests are not executed because Phase 11 remains `PLANNED / NOT CONNECTED`.
3. **No Target Leakage**: All tests strictly verify that simulator ground truth parameters (e.g. `degradation_pct`) remain isolated from failure logs, telemetry payloads, and metrics.
