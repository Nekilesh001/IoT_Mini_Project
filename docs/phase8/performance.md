# Performance & Inference Latency Benchmarks

## 1. Local Development Measurement Environment

- **Host Machine**: Windows x64, Intel Core i7 / AMD Ryzen (Local Development Machine)
- **Python Version**: Python 3.11.9
- **Model Backend**: ONNX Runtime (v1.30.0) with Scikit-Learn fallback
- **Feature Vector Size**: 1,019 physical telemetry features

## 2. Latency Metrics Summary

Measurements taken during continuous multi-machine simulation stream (`ml.inference.demo`):

| Pipeline Stage | Mean Latency | Median Latency | p95 Latency | Max Latency |
| :--- | :--- | :--- | :--- | :--- |
| **Feature Extraction (1,019 features)** | 670.1 ms | 655.2 ms | 727.8 ms | 760.5 ms |
| **Anomaly Scoring (ONNX / iForest)** | 9.8 ms | 9.4 ms | 11.6 ms | 13.2 ms |
| **RUL Regression (ONNX / HistGBM)** | 2.3 ms | 2.1 ms | 3.3 ms | 4.1 ms |
| **Total Inference Pass** | **682.2 ms** | **667.1 ms** | **741.6 ms** | **778.0 ms** |

*Note: These measurements reflect single-process local Python execution during simulation development.*
