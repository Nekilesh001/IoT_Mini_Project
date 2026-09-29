import { useState, useEffect, useCallback } from "react";
import { MachineDetail, RealtimeTelemetryEvent } from "../types";
import { fetchMachineDetail } from "../api/machines";
import { useRealtimeTelemetry } from "./useRealtimeTelemetry";

export function useMachineDetail(machineId: string) {
  const [machine, setMachine] = useState<MachineDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadMachine = useCallback(async () => {
    if (!machineId) return;
    try {
      setLoading(true);
      const data = await fetchMachineDetail(machineId);
      setMachine(data);
      setError(null);
    } catch (err: any) {
      setError(err?.message || `Failed to load details for ${machineId}`);
    } finally {
      setLoading(false);
    }
  }, [machineId]);

  const handleRealtimeEvent = useCallback(
    (event: RealtimeTelemetryEvent) => {
      if (event.machine_id === machineId) {
        setMachine((prev) => {
          if (!prev) return prev;
          return {
            ...prev,
            operating_state: event.operating_state,
            health_state: event.health_state,
            quality: event.quality,
            sequence: event.sequence,
            latest_event_time: event.event_time,
            current_measurements: { ...prev.current_measurements, ...event.measurements },
            current_derived: event.derived ? { ...prev.current_derived, ...event.derived } : prev.current_derived,
          };
        });
      }
    },
    [machineId]
  );

  useRealtimeTelemetry(handleRealtimeEvent);

  useEffect(() => {
    loadMachine();
  }, [loadMachine]);

  return { machine, loading, error, refresh: loadMachine };
}
