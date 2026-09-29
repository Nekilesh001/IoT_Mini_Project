# Multi-Protocol Integration & Normalization Matrix

## Protocol Ingestion & Decoupling Architecture

```
+-------------------------------------------------------------------------+
|                           Protocol Layer                                |
|                                                                         |
|  [Modbus TCP Server]     [OPC UA Server]       [MQTT Broker]            |
|       (Port 5020)          (Port 4840)          (Port 1883)             |
|            |                    |                    |                  |
|            v                    v                    v                  |
|  [Modbus Adapter]        [OPC UA Adapter]      [MQTT Adapter]           |
|            |                    |                    |                  |
|            +--------------------+--------------------+                  |
|                                 |                                       |
|                                 v (ProtocolReading Object)              |
|                   +---------------------------+                         |
|                   |  Edge Ingestion Service   |                         |
|                   | - Range Validation        |                         |
|                   | - Unit Normalization (SI) |                         |
|                   | - Deduplication (Seq/ID)  |                         |
|                   +---------------------------+                         |
|                                 |                                       |
|                                 v                                       |
|                   [Canonical Telemetry JSON]                            |
|             (Completely Protocol-Agnostic Envelope)                     |
+-------------------------------------------------------------------------+
```

## Protocol Matrix

| Protocol | Simulated Port | Machines Connected | Payload Format | Adapter Implementation | Failure / Reconnection Handling |
|---|:---:|---|---|---|---|
| **Modbus TCP** | `5020` | `CNC-002`, `CON-001`, `PRS-001`, `CMP-001`, `CHL-001` | 16-bit Holding Registers (Scaled Integers) | [`protocols/modbus/`](file:///D:/ONE_DATA/IoT_mini/protocols/modbus/) | Automatic retry with exponential backoff (1s–30s); flags machine `DEGRADED` on timeout |
| **OPC UA** | `4840` | `CNC-001`, `ROB-001`, `IMM-001`, `VIS-001` | Structured Node Variables (`ns=2;s=...`) | [`protocols/opcua/`](file:///D:/ONE_DATA/IoT_mini/protocols/opcua/) | Session keepalive watchdog; auto-reconnects and re-subscribes node monitoring |
| **MQTT** | `1883` | `ROB-002`, `PMP-001`, `AGV-001` | UTF-8 JSON topic messages (`factory/{id}/telemetry`) | [`protocols/mqtt/`](file:///D:/ONE_DATA/IoT_mini/protocols/mqtt/) | QoS 1 publishing; local store-and-forward queue buffering on broker disconnect |
