# Phase 6: Alert Data Models & Schema

## 1. Alert Database Schema (PostgreSQL / SQLite)

Alerts are persisted to the `alerts` relational table with indexed lookup columns and JSON/JSONB measurement snapshots:

```sql
CREATE TABLE alerts (
    alert_id VARCHAR(64) PRIMARY KEY,
    rule_id VARCHAR(64) NOT NULL,
    machine_id VARCHAR(32) NOT NULL,
    machine_type VARCHAR(64) NOT NULL,
    alert_code VARCHAR(32) NOT NULL,
    severity VARCHAR(16) NOT NULL,
    title VARCHAR(128) NOT NULL,
    description VARCHAR(512) NOT NULL,
    status VARCHAR(16) NOT NULL,
    triggered_at TIMESTAMP WITH TIME ZONE NOT NULL,
    acknowledged_at TIMESTAMP WITH TIME ZONE NULL,
    acknowledged_by VARCHAR(64) NULL,
    resolved_at TIMESTAMP WITH TIME ZONE NULL,
    resolution_notes VARCHAR(512) NULL,
    triggering_measurements JSONB NOT NULL,
    current_measurements JSONB NULL,
    occurrence_count INTEGER DEFAULT 1,
    last_occurrence_at TIMESTAMP WITH TIME ZONE NULL
);

CREATE INDEX ix_alerts_machine_id ON alerts(machine_id);
CREATE INDEX ix_alerts_status ON alerts(status);
CREATE INDEX ix_alerts_severity ON alerts(severity);
CREATE INDEX ix_alerts_triggered_at ON alerts(triggered_at);
```

---

## 2. Severity Taxonomy

- **`CRITICAL`**: Requires immediate operator intervention (e.g. thermal runaway, motor jam, severe bearing degradation).
- **`WARNING`**: Operational threshold boundary approached (e.g. low coolant flow, battery $<20\%$).
- **`INFO`**: Diagnostic or advisory event (e.g. routine parameter adjustment, quality fluctuation).

---

## 3. Explainability Schema

Each alert exposes:
- **`title` & `description`**: Plain human-readable explanation.
- **`triggering_measurements`**: Sensor values captured at initial trigger moment.
- **`current_measurements`**: Most recently observed sensor values while the alert remains open.
- **`occurrence_count`**: Number of continuous violation ticks.
