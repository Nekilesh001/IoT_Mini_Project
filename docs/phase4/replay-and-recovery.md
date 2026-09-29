# Phase 4 — Replay & Recovery Mechanism

## 1. Replay Worker Execution

The `ReplayWorker` operates asynchronously in the background to drain queued events from `PersistentBuffer`.

### Selection & Ordering
Events are fetched in deterministic chronological order:
```sql
SELECT * FROM buffer_events
WHERE (status = 'PENDING' OR status = 'IN_FLIGHT') AND next_retry_at <= :now
ORDER BY created_at ASC, machine_id ASC, sequence ASC
LIMIT :batch_size;
```

This ensures events are replayed in chronological order per machine.

## 2. Exponential Backoff & Failure Handling

To avoid overwhelming recovered brokers or entering tight CPU loops during sustained outages, failed replay attempts apply exponential backoff:

$$\text{delay} = \min(\text{max\_delay}, \text{initial\_delay} \times 2^{\text{retry\_count}})$$

- **Default Initial Delay**: 1.0 second
- **Default Max Delay**: 60.0 seconds
- **Default Max Retries**: 10 attempts

## 3. Replay Flow

1. Replay worker selects up to `batch_size` pending events.
2. Events are marked `IN_FLIGHT`.
3. If `publisher` is available, worker re-publishes to MQTT.
4. If direct `repository` mode is configured, worker re-persists directly to DB.
5. On confirmed success, events are marked `DELIVERED` and purged.
6. On error, `mark_retry_failed()` calculates `next_retry_at` and records the error.
