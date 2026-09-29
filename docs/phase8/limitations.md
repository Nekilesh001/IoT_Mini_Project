# Engineering Assumptions & Limitations

## 1. Safety and Certification Disclaimer

This software is developed for research, benchmarking, and architectural simulation.

> **CRITICAL SAFETY NOTE**:
> 1. Machine learning anomaly scores and RUL estimates **MUST NOT** be used to control safety-critical industrial equipment directly.
> 2. ML predictions **DO NOT** replace hardwired Emergency Stop (E-Stop) circuits, SIL-rated safety PLCs, or certified industrial protection systems.
> 3. Predictions serve as advisory diagnostic indicators for human operators and maintenance planning.

## 2. Simulation-Derived ML Limitations

1. **Synthetic Dynamics**: Models were trained on synthetic physical simulations incorporating idealized mathematical degradation curves. Real-world machinery exhibits unmodeled mechanical harmonics, ambient thermal shifts, and non-linear wear characteristics.
2. **Warm-Up Latency**: Features utilizing 30-sample rolling windows require initial historical observations before reaching steady-state statistical maturity.
3. **Feature Generation Overhead**: In Python, extracting 1,019 rolling features per sample takes ~650ms on a single CPU core. In industrial high-frequency edge deployments (e.g. > 100Hz vibration sampling), feature extraction would typically be compiled into native Rust/C++ or accelerated via SIMD DSP hardware.
