# Phase 12 — PostgreSQL / Storage Database Outage & Recovery

## Scenario Details
- **Fault Injection**: PostgreSQL or SQLite primary storage throws `ConnectionError` or write lock timeout.
- **Behavior**: Ingestion workers place incoming canonical telemetry into the local SQLite store-and-forward queue.
- **Recovery**: As database comes back online, a background replay worker batches undelivered records into the primary storage table.
- **Verification Metric**: Zero telemetry records lost; storage deduplication prevents duplicate rows.
