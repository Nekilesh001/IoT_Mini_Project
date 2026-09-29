# Device Shadow State Management

## 1. Concept & Data Model

The `DeviceShadowState` represents the digital twin state of a factory machine:
- **`desired_state`**: Target operating parameters (e.g. `sampling_interval_sec`, `operating_mode`, `eco_mode`) set by operators or automated workflows.
- **`reported_state`**: Actual state acknowledged and confirmed by the machine.
- **`delta`**: Automatically calculated difference representing pending synchronization.
- **`version`**: Monotonically increasing version counter supporting optimistic concurrency validation.

## 2. Delta Computation Logic

A delta key exists whenever a property in `desired_state` is missing or has a different value in `reported_state`:

$$\text{Delta} = \{k: v \mid k \in \text{desired}, \text{reported}[k] \neq v\}$$

When $\text{Delta} = \emptyset$, `is_sync_pending = False`.

## 3. Optimistic Concurrency Control

When submitting a desired state update with `expected_version`, if the current shadow version differs, the update is rejected with `VersionConflictError` (HTTP 409 Conflict), preventing race conditions across concurrent operators.
