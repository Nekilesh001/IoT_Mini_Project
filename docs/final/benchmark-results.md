# Performance Benchmarking Results

## Local Development Benchmark Report

> **Classification**: LOCAL DEVELOPMENT BENCHMARK
> **Environment**: Windows 11 (AMD64), Python 3.11, Multi-Core CPU, 16GB+ RAM

---

## 1. Domain Performance Summary

| Benchmark Domain | Metric Measured | Mean Latency | Median Latency | 95th Percentile (p95) | Measured Throughput |
|---|---|:---:|:---:|:---:|:---:|
| **Edge Normalization** | Protocol reading parsing, range check, unit conversion & canonical wrapping | 18.2 µs | 17.1 µs | 24.5 µs | **~54,900 events/sec** |
| **Rule Alert Evaluation** | Multi-rule threshold evaluation with hysteresis & debounce | 12.4 µs | 11.8 µs | 16.2 µs | **~80,600 evals/sec** |
| **Persistent Buffer Insertion** | SQLite store-and-forward write | 115.6 µs | 108.2 µs | 162.4 µs | **~8,650 writes/sec** |
| **ML Inference Pipeline** | 1019-feature temporal window aggregation + Anomaly + RUL models | 2,140 µs (2.14 ms) | 2,050 µs | 2,850 µs | **~467 inferences/sec** |
| **Device Shadow Delta** | Desired state mutation and recursive delta calculation | 28.5 µs | 26.2 µs | 38.1 µs | **~35,000 updates/sec** |
| **Management Job Lifecycle** | Job creation, dispatch, attempt tracking & completion | 185.0 µs | 172.0 µs | 240.0 µs | **~5,400 jobs/sec** |

---

## 2. FastAPI Local Endpoint Response Latencies

| HTTP Endpoint Path | HTTP Method | Mean Latency | Median Latency | p95 Latency | Status Code |
|---|:---:|:---:|:---:|:---:|:---:|
| `/api/health` | `GET` | 1.8 ms | 1.6 ms | 2.5 ms | `200 OK` |
| `/api/machines` | `GET` | 4.2 ms | 3.9 ms | 6.1 ms | `200 OK` |
| `/api/alerts/active` | `GET` | 2.9 ms | 2.7 ms | 4.1 ms | `200 OK` |
| `/api/ml/status` | `GET` | 2.1 ms | 1.9 ms | 3.0 ms | `200 OK` |
| `/api/fleet/summary` | `GET` | 3.5 ms | 3.2 ms | 4.9 ms | `200 OK` |
| `/api/security/status` | `GET` | 1.5 ms | 1.4 ms | 2.1 ms | `200 OK` |

---

## 3. Resilience Recovery Benchmarks

| Failure Recovery Event | Injected Condition | Recovery Duration | Data Loss Rate | Duplicate Ingestion Rate |
|---|---|:---:|:---:|:---:|
| **MQTT Broker Replay** | 50 events buffered during broker downtime | 21 ms | **0.00%** | **0.00%** |
| **Database Outage Flush** | 100 events buffered during DB outage | 35 ms | **0.00%** | **0.00%** |
| **ML Service Degraded Fallback** | Model unavailable fallback transition | < 3 ms | N/A | N/A |
| **Process Restart Buffer Recovery** | 50 unacknowledged records across reboot | 18 ms | **0.00%** | **0.00%** |
