# Limitations & Phase Boundaries

## 1. Local-First Scope

- **Cloud Connection Inactive**: AWS IoT Core, AWS IoT Device Shadow, AWS IoT Jobs, and AWS Fleet Indexing are scaffolded with interfaces only; no live AWS calls or credentials are used.
- **Simulated Firmware (OTA)**: `OTA_SIMULATION` jobs simulate version transitions and metadata updates without flashing real physical device hardware.
- **Single-Node Execution**: In this phase, jobs are executed in-process or via local worker processes. Distributed multi-node job dispatch will be expanded in future scaling phases.
