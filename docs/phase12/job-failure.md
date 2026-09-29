# Phase 12 — Device Management Job Failure & Retry Exhaustion

## Scenario Details
- **Fault Injection**: Target machine fails to process command or offline machine fails heartbeat during job execution.
- **Behavior**: Job engine retries failed execution up to configured `max_retries` (e.g. 3) with backoff interval.
- **Exhaustion**: After exhausting retries, job transitions cleanly from `IN_PROGRESS` to `FAILED`.
- **Audit**: Security and fleet audit logs record failure reason and retry history.
- **Verification Metric**: No infinite retry loop; terminal state reached consistently.
