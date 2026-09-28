# Phase 3: Unit Normalization

## 1. Normalization Standard

Edge telemetry enforces canonical engineering units:
- **Temperature**: Celsius (`°C`)
- **Pressure**: Bar (`BAR`)
- **Rotational Velocity**: Revolutions per minute (`RPM`)
- **Linear Velocity**: Meters per second (`m/s`) or `mm/s`
- **Current / Voltage / Power**: Amperes (`A`), Volts (`V`), Kilowatts (`kW`)
- **Flow Rate**: Cubic meters per hour (`m³/h`) or `L/min`

## 2. Deterministic Conversion Registry

Conversions are executed explicitly when specified in signal metadata:
- `°F` → `°C`: `(v - 32) * 5 / 9`
- `PSI` → `BAR`: `v * 0.0689476`
- `KPA` → `BAR`: `v * 0.01`
- `L/MIN` → `M³/H`: `v * 0.06`
- `W` → `KW`: `v / 1000.0`

Heuristic guessing based on variable name substrings is strictly disallowed.
