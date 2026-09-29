# Job Management & Execution Engine

## 1. Job Lifecycle & State Machine

```mermaid
stateDiagram-v2
    [*] --> PENDING: create_job()
    PENDING --> IN_PROGRESS: start_job()
    IN_PROGRESS --> SUCCEEDED: complete_job()
    IN_PROGRESS --> PENDING: fail_job() [attempt < max_attempts]
    IN_PROGRESS --> FAILED: fail_job() [attempt >= max_attempts]
    PENDING --> CANCELLED: cancel_job()
    IN_PROGRESS --> CANCELLED: cancel_job()
    SUCCEEDED --> [*]
    FAILED --> [*]
    CANCELLED --> [*]
```

## 2. Job Types

- `CONFIG_UPDATE`: Pushes desired configuration parameters to target machine shadow.
- `COMMAND`: Executes one-off administrative action.
- `OTA_SIMULATION`: Simulates staged firmware rollout and version bumping.
- `RESTART_SIMULATION`: Triggers controlled restart simulation.
- `SYNC_STATE`: Synchronizes reported state from desired state.

## 3. Retries & Attempt Logging

Each execution attempt generates a dedicated `JobAttemptRecord` in `job_attempts` storing start timestamp, completion timestamp, attempt number, status (`IN_PROGRESS`, `FAILED`, `SUCCEEDED`), and error details.
