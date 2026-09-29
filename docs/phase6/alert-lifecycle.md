# Phase 6: Alert Lifecycle & State Transitions

## 1. Alert Lifecycle State Machine

```
              +-------------------------------------+
              |                                     |
              v                                     |
+--------------------------+                        |
|           OPEN           |                        |
+--------------------------+                        |
              |                                     |
    acknowledge_alert()                             |
              |                                     |
              v                                     |
+--------------------------+                        |
|       ACKNOWLEDGED       |                        |
+--------------------------+                        |
              |                                     |
       resolve_alert()                       resolve_alert()
              |                                     |
              +------------------+------------------+
                                 |
                                 v
                    +--------------------------+
                    |         RESOLVED         |
                    +--------------------------+
```

---

## 2. Transition Rules and Validation

1. **`OPEN -> ACKNOWLEDGED`**: Operator confirms receipt of operational warning. Records `acknowledged_at` timestamp and `acknowledged_by` operator ID.
2. **`ACKNOWLEDGED -> RESOLVED`**: Machine condition clears (hysteresis) or operator completes repair. Records `resolved_at` and `resolution_notes`.
3. **`OPEN -> RESOLVED`**: Automatic recovery when measurement drops below hysteresis clear threshold without manual acknowledgment.
4. **Invalid Transitions**:
   - `RESOLVED -> OPEN` or `RESOLVED -> ACKNOWLEDGED` raises `ValueError`.
   - Re-acknowledging or re-resolving an already resolved alert is strictly rejected.
