# AGENTS.md — Agent Guidelines & Execution Rules

This document outlines mandatory instructions for AI coding agents operating on the **Smart Factory Machine Monitoring and Predictive Maintenance System** codebase.

---

## 1. Mandatory Pre-Execution Checklist

Before executing any code changes or file creations, every agent MUST:

1. **Read [PROJECT_SPECIFICATION.md](PROJECT_SPECIFICATION.md)** to understand the overall architecture, telemetry schema, protocol abstraction, machine state models, and security principles.
2. **Read [PHASE_STATUS.md](PHASE_STATUS.md)** to check current phase status, completed tasks, and active requirements.
3. **Verify Git Branch**: Confirm active working branch is `dev`. **NEVER work or push directly on `main`**.

---

## 2. Core Execution Constraints

- **Architecture Freeze**: Treat the architecture documented in `PROJECT_SPECIFICATION.md` as frozen unless the prompt explicitly instructs an architectural change.
- **Strict Scope Control**: Implement ONLY the specific task or phase requested. Do NOT implement future phases prematurely.
- **No Unrelated Refactoring**: Avoid refactoring working components outside the explicit scope of the current task.
- **Protocol Abstraction**: Maintain strict decoupling between machine behavior simulation and protocol server/adapter implementations (`Machine Behaviour -> Protocol Server/Publisher -> Protocol Adapter -> Canonical Telemetry`).
- **Protocol-Agnostic Edge**: Downstream edge ingestion, validation, normalization, signal-specific filtering/deduplication, rules, and ML inference pipelines MUST remain completely agnostic of source protocols.
- **Local-First Independence**: All features must function fully offline without requiring active AWS infrastructure.

---

## 3. Machine Simulation & Target Leakage Rules

- **Behavior-Driven Physics**: Simulators must derive telemetry from underlying state, operating load, environmental conditions, and degradation mechanisms — NOT isolated random number generation.
- **Prevent Target Leakage**: ML feature extraction MUST strictly exclude simulator ground-truth variables, hidden degradation counters, simulated fault flags, simulator-derived health labels, and existing ML predictions. Only raw/normalized physical measurements, envelope metadata, and engineered operational features may be passed into ML feature vectors or production edge inference.

---

## 4. Security & Secret Handling

- **Zero Secret Commits**: NEVER commit API keys, private keys, certificates with private keys, database passwords, or AWS credentials to version control.
- **Environment Separation**: Always pull configuration and credentials from environment variables or local `.env` files (documented via `.env.example`).

---

## 5. Development & Git Workflow

- **Branch Usage**: All development, experiments, testing, and documentation must take place on the `dev` branch.
- **Commit Messages**: Use structured commit types (`feat:`, `fix:`, `test:`, `docs:`, `refactor:`, `chore:`).
- **PR Flow**: Merge into `main` strictly via reviewed Pull Requests after full verification.

---

## 6. Testing & Quality Requirements

- Write unit/integration tests for all implemented behavior and components.
- Run tests and verify success before completing any task.
- Update project documentation (`PHASE_STATUS.md`, `README.md`, etc.) whenever progress or schemas change.

---

## 7. Reporting & Stop Criteria

Upon completing a task, the agent MUST report:
1. **Files Created / Modified** (with file links)
2. **Tests Executed** and exact test results
3. **Assumptions Made** during execution
4. **Unresolved Architectural Decisions** or risks

Once reporting is complete, **STOP immediately** and await user review.
