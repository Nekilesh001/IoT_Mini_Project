# Phase 3: Machine-Aware Validation

## 1. Validation Logic

The `TelemetryValidator` enforces machine-aware validation against Phase 1 `MachineProfile` definitions:

1. **Machine Identity Check**: Asserts the `machine_id` exists in the registered factory configuration.
2. **Type Consistency**: Verifies that `reading.machine_type` matches `profile.machine_type`.
3. **Protocol Consistency**: Verifies that `reading.protocol` aligns with configured `profile.protocol_metadata`.
4. **Signal Catalog Enforcement**:
   - Compares incoming keys against `profile.signals`.
   - Checks signal datatype (`FLOAT`, `INT`, `BOOL`, `STRING`, `ENUM`).
   - Validates engineering bounds (`min_value <= value <= max_value`).
   - Tags out-of-range signals with `QualityCode.OUT_OF_RANGE`.
   - Tags type mismatch or malformed values with `QualityCode.BAD`.
   - Flags missing signals with `QualityCode.MISSING`.
