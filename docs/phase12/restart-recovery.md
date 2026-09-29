# Phase 12 — Service Restart During Buffered Operations

## Scenario Details
- **Fault Injection**: System simulates immediate process crash or restart while 50+ messages remain unacknowledged in the store-and-forward queue.
- **Behavior**: Process shuts down without waiting for downstream acknowledgments. On process reboot, `PersistentBuffer` scans local SQLite table `buffered_events` for `delivered=0`.
- **Recovery**: Replay worker resumes delivering undelivered messages to upstream/downstream endpoints.
- **Verification Metric**: 100% recovery of buffered messages across process restart boundaries.
