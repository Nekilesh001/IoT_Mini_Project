# Command Abstraction & Industrial Dispatch

## 1. Supported Commands & Validation

- `SET_MODE`: Sets operating mode (`AUTO`, `MANUAL`, `MAINTENANCE`, `STANDBY`, `OFF`).
- `SET_SAMPLING_INTERVAL`: Validates sampling interval range ($0 < \text{interval} \le 3600\text{s}$).
- `REQUEST_STATE_SYNC`: Dispatches immediate state reconciliation job.
- `SIMULATE_RESTART`: Triggers safe restart simulation.

## 2. Dispatch Path

Commands validate incoming parameters, update the Device Shadow desired state where applicable, generate an asynchronous `ManagementJobRecord`, and write an immutable entry to `management_audit`.
