# Final Project Overview — Smart Factory System

## 1. Executive Summary

- **Project Title**: Smart Factory Machine Monitoring & Predictive Maintenance System
- **Repository**: `https://github.com/Nekilesh001/IoT_Mini_Project`
- **Working Branch**: `dev`
- **Core Architecture**: Local-First, Cloud-Optional Industrial IoT (IIoT) Platform
- **Current Milestone**: Phase 13 (Final Documentation, Benchmarking & Demonstration)

## 2. Problem Statement & Objective

Traditional manufacturing operations suffer from unplanned downtime, fragmented protocol ecosystems (Modbus TCP, OPC UA, proprietary MQTT), and fragile cloud-dependent monitoring architectures that fail during network partitions.

This project delivers a complete, production-grade IIoT simulation and predictive maintenance platform that:
1. Simulates 12 heterogeneous factory machines with realistic physics, state machines, and causal degradation mechanisms.
2. Ingests and normalizes multi-protocol telemetry into a decoupled, protocol-agnostic canonical schema.
3. Provides real-time anomaly detection and Remaining Useful Life (RUL) estimation at the edge without target leakage.
4. Manages digital twin device states (Device Shadows) and fleet operations jobs locally.
5. Implements defense-in-depth local security (JWT, RBAC, mTLS, audit logging).
6. Guarantees zero data loss and resilience across 15 failure and outage scenarios.

## 3. System Scope & Subsystems

| Subsystem | Key Technologies | Core Responsibilities |
|---|---|---|
| **Factory Simulator** | Python 3.11+, NumPy, SciPy | 12 heterogeneous machines, dynamic load physics, state transitions, causal wear mechanisms |
| **Protocol Layer** | PyModbus, asyncua, Eclipse Paho MQTT | Modbus TCP servers, OPC UA address spaces, MQTT topics, protocol-specific adapters |
| **Edge Gateway** | Pydantic, Python | Range validation, engineering unit normalization (SI), sequence tracking, deduplication |
| **Storage & Buffer** | PostgreSQL (JSONB), SQLite, SQLAlchemy | Store-and-forward persistent buffer, time-series telemetry table, batch replay worker |
| **Alert Engine** | Python, PostgreSQL | Deterministic threshold rules, hysteresis debounce, cooldown timers, lifecycle states |
| **Machine Learning** | Scikit-Learn, ONNX Runtime, MLflow | 1019 observable temporal features, Isolation Forest anomaly model, HistGradientBoosting RUL model |
| **Device Management** | SQLAlchemy, Python | Digital twin Device Shadows, delta calculation, optimistic locking, fleet jobs, audit trail |
| **Security Layer** | Cryptography, PyJWT, PBKDF2 | Local X.509 PKI, mTLS context, 4-tier RBAC policy, security audit logging, secret scanner |
| **Failure Testing** | Python context managers, SQLite | 15 deterministic failure modes, invariant assertion checkers, recovery metrics tracker |
| **FastAPI Backend** | FastAPI, Uvicorn, Starlette | REST API endpoints, Server-Sent Events (SSE) telemetry/alerts/ML stream, security headers |
| **React Dashboard** | React 19, TypeScript, Vite, Recharts | Machine fleet overview, real-time telemetry charts, alert triage, ML console, device management, security & resilience consoles |
| **Cloud Scaffold** | Python Abstract Interfaces | AWS-ready adapter interfaces (`AWS_ENABLED=false`, `PLANNED / NOT CONNECTED`) |

## 4. Key Architectural Boundaries & Invariants

1. **Anti-Target Leakage**: Machine learning features strictly exclude ground-truth degradation percentages, simulated fault flags, hidden health indicators, and true failure timestamps.
2. **Local-First Independence**: The entire factory floor, data pipeline, ML inference, and management system operates 100% offline without live AWS infrastructure or credentials.
3. **Graceful Degradation**: Failures in ML models or cloud adapters do not disrupt raw telemetry ingestion, database storage, or deterministic rule-based alarms.
4. **Deterministic Invariant Preservation**: Store-and-forward buffering guarantees zero unacknowledged data loss and zero duplicate entries across network partitions or process restarts.
