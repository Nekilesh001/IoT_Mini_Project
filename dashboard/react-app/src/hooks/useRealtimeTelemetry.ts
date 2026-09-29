import { useEffect, useState, useRef, useCallback } from "react";
import { RealtimeTelemetryEvent } from "../types";

export type ConnectionStatus = "connecting" | "connected" | "disconnected" | "error";

export function useRealtimeTelemetry(onEventReceived?: (event: RealtimeTelemetryEvent) => void) {
  const [status, setStatus] = useState<ConnectionStatus>("connecting");
  const [latestEvents, setLatestEvents] = useState<Record<string, RealtimeTelemetryEvent>>({});
  const [lastHeartbeat, setLastHeartbeat] = useState<Date | null>(null);
  const seenSequences = useRef<Map<string, number>>(new Map());
  const callbackRef = useRef(onEventReceived);
  callbackRef.current = onEventReceived;

  useEffect(() => {
    let eventSource: EventSource | null = null;
    let isCancelled = false;

    const connect = () => {
      setStatus("connecting");
      const url = `${import.meta.env.VITE_API_URL || ""}/api/realtime/telemetry`;
      eventSource = new EventSource(url);

      eventSource.onopen = () => {
        if (!isCancelled) {
          setStatus("connected");
        }
      };

      eventSource.onmessage = (e) => {
        if (isCancelled || !e.data) return;
        try {
          const event: RealtimeTelemetryEvent = JSON.parse(e.data);
          const prevSeq = seenSequences.current.get(event.machine_id) || 0;

          if (event.sequence >= prevSeq) {
            seenSequences.current.set(event.machine_id, event.sequence);
            setLatestEvents((prev) => ({
              ...prev,
              [event.machine_id]: event,
            }));
            if (callbackRef.current) {
              callbackRef.current(event);
            }
          }
          setLastHeartbeat(new Date());
        } catch {
          // Heartbeat comment or non-json message
          setLastHeartbeat(new Date());
        }
      };

      eventSource.onerror = () => {
        if (!isCancelled) {
          setStatus("error");
          eventSource?.close();
          // Auto-reconnect after 3 seconds
          setTimeout(() => {
            if (!isCancelled) connect();
          }, 3000);
        }
      };
    };

    connect();

    return () => {
      isCancelled = true;
      if (eventSource) {
        eventSource.close();
      }
    };
  }, []);

  return { status, latestEvents, lastHeartbeat };
}
