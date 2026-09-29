import { useState, useEffect, useCallback } from "react";
import { MachineOverviewItem, RealtimeTelemetryEvent } from "../types";
import { fetchMachines } from "../api/machines";
import { useRealtimeTelemetry } from "./useRealtimeTelemetry";

export function useMachines() {
  const [machines, setMachines] = useState<MachineOverviewItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadMachines = useCallback(async () => {
    try {
      const data = await fetchMachines();
      setMachines(data);
      setError(null);
    } catch (err: any) {
      setError(err?.message || "Failed to load machines");
    } finally {
      setLoading(false);
    }
  }, []);

  const handleRealtimeEvent = useCallback((event: RealtimeTelemetryEvent) => {
    setMachines((prev) =>
      prev.map((m) => {
        if (m.machine_id === event.machine_id) {
          const updatedKeyMeas = { ...m.key_measurements, ...event.measurements };
          return {
            ...m,
            operating_state: event.operating_state,
            health_state: event.health_state,
            quality: event.quality,
            sequence: event.sequence,
            latest_event_time: event.event_time,
            key_measurements: updatedKeyMeas,
          };
        }
        return m;
      })
    );
  }, []);

  const { status: realtimeStatus } = useRealtimeTelemetry(handleRealtimeEvent);

  useEffect(() => {
    loadMachines();
  }, [loadMachines]);

  return { machines, loading, error, realtimeStatus, refresh: loadMachines };
}
