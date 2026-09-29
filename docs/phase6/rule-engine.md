# Phase 6: Rule-Based Alert Engine

## 1. Rule Engine Concept

The Rule Engine evaluates validated canonical telemetry packets against explicit, machine-aware rules to produce deterministic, explainable operational alerts.

```
CanonicalTelemetry ---> [RuleEvaluator] ---> [AlertEngine] ---> Active Alert Management / PostgreSQL
```

---

## 2. Rule Types Supported

1. **`THRESHOLD`**: Direct relational comparison (`>`, `<`, `>=`, `<=`, `==`, `!=`) against numerical sensor measurements.
   - Example: `spindle_temperature_c > 65.0`
2. **`RATE_OF_CHANGE`**: Computes the first derivative $\frac{\Delta V}{\Delta t}$ of a physical signal across successive telemetry ticks.
   - Example: `\Delta spindle_temperature_c / \Delta t > 15.0 ^\circ C / s`
3. **`MISSING_SIGNAL`**: Triggers when expected signal channels are absent from the payload or flagged as `MISSING`.
4. **`STALE_SIGNAL`**: Triggers when telemetry quality is degraded (`STALE`, `BAD`, `OUT_OF_RANGE`).
5. **`STATE`**: Evaluates operating state transitions (e.g., transition to `FAULT` or `EMERGENCY_STOP`).
6. **`COMPOSITE`**: Evaluates multiple simultaneous conditions on distinct signal channels.
   - Example: `supply_temperature_c > 18.0` AND `coolant_flow_rate_l_min < 60.0`.

---

## 3. Cooldown, Deduplication, and Hysteresis

### Cooldown
Prevents repeated alert creation on consecutive ticks while the fault condition persists. Configurable per rule via `cooldown_seconds`.

### Deduplication
Alerts are indexed by the natural key `(machine_id, rule_id)`. When an active alert exists for a key:
- A new database row is NOT inserted.
- The existing record's `occurrence_count` is incremented.
- `current_measurements` and `last_occurrence_at` are updated.

### Hysteresis
To prevent alert flapping near threshold boundaries, rules define separate `threshold` and `clear_threshold` values.
- **Trigger**: Value crosses `threshold` (e.g. Pump vibration $> 4.5\text{ mm/s}$).
- **Hysteresis Zone**: Value remains between $4.5$ and $3.0\text{ mm/s}$ (alert remains active).
- **Auto-Clear**: Value drops below `clear_threshold` ($< 3.0\text{ mm/s}$), transitioning the alert to `RESOLVED`.
