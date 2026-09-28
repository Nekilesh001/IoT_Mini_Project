# Phase 2: Modbus TCP Simulation & Adapter

## 1. Overview

Modbus TCP exposes industrial telemetry across holding registers (16-bit unsigned integers) mapped to deterministic Unit IDs (Slave IDs).

## 2. Machine & Unit ID Assignments

| Machine ID | Machine Type | Modbus Unit ID | Holding Registers Allocated |
|---|---|---|---|
| `CNC-002` | `CNC_LATHE` | `1` | 13 |
| `CON-001` | `INDUSTRIAL_CONVEYOR` | `2` | 13 |
| `PRS-001` | `INDUSTRIAL_PRESS` | `3` | 13 |
| `CMP-001` | `AIR_COMPRESSOR` | `4` | 13 |
| `CHL-001` | `INDUSTRIAL_CHILLER` | `5` | 13 |

## 3. Register Layout

Registers start at PDU offset `0` (Holding Register 1):

- **Register 0**: `sequence_low` (Bits 0..15)
- **Register 1**: `sequence_high` (Bits 16..31)
- **Register 2**: `operating_state_code` (0=OFF, 1=STARTING, 2=IDLE, 3=RUNNING, 4=WARNING, 5=FAULT, 6=MAINTENANCE, 7=RECOVERY)
- **Register 3..N**: Machine physical signals ordered by the machine profile's signal catalog.

## 4. Signal Encoding & Scaling Rules

- **Float Signals**: Scaled by factor `0.1` (`int(round(value / 0.1))`). Encoded into 16-bit unsigned integers with sign preservation.
- **Integer Signals**: Clamped to `[0, 65535]`.
- **Boolean Signals**: `0` (False) / `1` (True).
- **String/Enum Signals**: Integer state code mapping.

## 5. Server & Adapter Architecture

- **Server Manager**: `ModbusServerManager` uses `pymodbus.server.ModbusTcpServer` and updates live holding registers using `server.context.async_setValues(unit_id, 3, 0, registers)` scheduled on the server's asyncio event loop.
- **Client Adapter**: `ModbusAdapter` connects via `ModbusTcpClient`, reads holding registers for the target Unit ID (`read_holding_registers(address=0, count=N, device_id=unit_id)`), and decodes them into a `ProtocolReading`.
