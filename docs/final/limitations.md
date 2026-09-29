# System Scope, Assumptions & Engineering Limitations

## 1. Simulation Context
- **Synthetic Physics**: Sensor telemetry, wear rates, and degradation equations are derived from deterministic and stochastic mathematical models. They simulate realistic behavior for software and ML validation, but do not replace hardware testing on physical machines.
- **Safety Control Disclaimer**: This platform is an educational engineering simulation and software architecture demonstration. It is **not** a certified industrial safety control system (SIL / IEC 61508 / ISO 13849).

## 2. Machine Learning Boundaries
- **Simulated Training Distribution**: Isolation Forest and HistGradientBoosting models are trained on simulated 7,200-second factory run datasets. Real-world machine variance, vibration harmonics, and novel physical failure modes would require domain adaptation and field retraining.
- **Target Leakage Strict Isolation**: True RUL and degradation percentages are strictly excluded from runtime edge inference.

## 3. Local-First Security Scope
- **Development-Grade PKI**: Local X.509 certificate generation is designed for on-premise development, testing, and isolated factory gateways. It does not integrate with an enterprise Public Key Infrastructure (PKI) or hardware HSM modules.
- **In-Process Token Signing**: JWT tokens use local symmetric HMAC keys (`HS256`). Production enterprise deployments should adopt asymmetric RSA/ECDSA signing with key rotation.

## 4. Resilience & Chaos Limitations
- **In-Process Deterministic Injection**: Chaos and failure scenarios test software resilience, queue buffering, circuit breakers, and deduplication logic. They do not simulate hardware kernel panics, physical cable severing, or bare-metal power loss.

## 5. AWS Cloud Boundary
- **Scaffolding Only**: Phase 11 remains `PLANNED / NOT CONNECTED`. No live AWS infrastructure, IoT Core brokers, or cloud credentials exist or are required.
