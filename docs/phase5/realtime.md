# Real-Time Telemetry Streaming Architecture — Phase 5

This document describes the design, mechanics, and frontend consumption of the real-time Server-Sent Events (SSE) telemetry pipeline.

---

## 1. Overview & Mechanics

To provide live, low-latency factory floor updates without requiring heavyweight message brokers (Redis, Kafka) or complex bidirectional WebSocket framing, Phase 5 implements a lightweight, local **Server-Sent Events (SSE)** telemetry stream at `GET /api/realtime/telemetry`.

```
[ Phase 4 Storage Worker ]
             |
             v (persists records)
    [ PostgreSQL DB ]
             |
             v (reads records with sequence > last_seen)
    [ RealtimeService.stream_telemetry() ]
             |
             v (yields SSE data chunks)
    [ FastAPI /api/realtime/telemetry ]
             |
             | text/event-stream
             v
    [ React useRealtimeTelemetry Hook (EventSource) ]
             |
             +---> Live Factory Summary Badge
             +---> Machine Cards Live Values
             +---> Live Trend Charts
```

---

## 2. Server-Side Implementation (`RealtimeService`)

The backend streaming generator runs within `api.services.realtime_service`:

- **Connection Initialization**:
  - Sets SSE headers: `Content-Type: text/event-stream`, `Cache-Control: no-cache`, `Connection: keep-alive`.
  - Initializes tracking state (`last_sequences: Dict[str, int]`) for all 12 machines using the latest committed database sequence numbers.
- **Poll & Yield Loop**:
  - Periodically executes an indexed query retrieving the latest record for each machine.
  - Compares the record's `sequence` number against `last_sequences[machine_id]`.
  - If a strictly newer sequence is detected:
    1. Formats the payload omitting simulator ground truth.
    2. Updates `last_sequences[machine_id]`.
    3. Yields an SSE event chunk:
       ```
       event: telemetry
       data: {"eventId": "...", "machineId": "CNC-001", "sequence": 142, "eventTime": "2026-09-29T10:00:00Z", "operatingState": "RUNNING", "healthState": "NORMAL", "quality": "GOOD", "measurements": {...}}

       ```
- **Disconnection Handling**:
  - Listens for `asyncio.CancelledError` or client socket drops.
  - Automatically breaks the generator loop and closes database session handles cleanly.

---

## 3. Frontend Consumption (`useRealtimeTelemetry`)

The React frontend consumes the stream via a custom hook (`dashboard/react-app/src/hooks/useRealtimeTelemetry.ts`):

- **Native `EventSource` API**: Connects to `http://127.0.0.1:8000/api/realtime/telemetry`.
- **Deduplication**:
  - Tracks seen `eventId` and sequence numbers to eliminate duplicate rendering.
- **Connection Lifecycle Management**:
  - Manages `isConnected`, `isReconnecting`, and error states.
  - Automatically initiates exponential backoff reconnects upon transient connection drops.
- **State Propagation**:
  - Updates local machine card metrics.
  - Updates factory summary cards without full-page reloads.
  - Appends live data points to active time-series charts.
