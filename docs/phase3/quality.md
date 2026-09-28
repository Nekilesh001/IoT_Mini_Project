# Phase 3: Quality Assessment Engine

## 1. Quality Codes

- `GOOD`: Valid reading within calibrated physical limits and fresh timestamp.
- `BAD`: Unparseable datatype, malformed structure, or protocol framing error.
- `STALE`: Telemetry timestamp age exceeds configured freshness threshold (default 60s).
- `MISSING`: Configured required measurement missing from incoming payload.
- `OUT_OF_RANGE`: Measurement violates physical sensor bounds (`min_value` / `max_value`).
- `ESTIMATED`: Value explicitly imputed during transient signal loss.

## 2. Precedence Evaluation Hierarchy

Top-level event quality is evaluated hierarchically:
`BAD` > `OUT_OF_RANGE` > `MISSING` > `STALE` > `ESTIMATED` > `GOOD`
