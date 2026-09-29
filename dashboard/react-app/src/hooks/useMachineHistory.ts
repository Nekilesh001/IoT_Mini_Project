import { useState, useEffect, useCallback } from "react";
import { TelemetryHistory, TelemetryRecord, RealtimeTelemetryEvent } from "../types";
import { fetchMachineHistory, HistoryParams } from "../api/machines";
import { useRealtimeTelemetry } from "./useRealtimeTelemetry";

export function useMachineHistory(machineId: string, params: HistoryParams = {}) {
  const [history, setHistory] = useState<TelemetryHistory | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadHistory = useCallback(async () => {
    if (!machineId) return;
    try {
      setLoading(true);
      const data = await fetchMachineHistory(machineId, params);
      setHistory(data);
      setError(null);
    } catch (err: any) {
      setError(err?.message || "Failed to load telemetry history");
    } finally {
      setLoading(false);
    }
  }, [machineId, params.start, params.end, params.limit, params.signals?.join(",")]);

  const handleRealtimeEvent = useCallback(
    (event: RealtimeTelemetryEvent) => {
      if (event.machine_id === machineId) {
        setHistory((prev) => {
          if (!prev) return prev;
          const newRecord: TelemetryRecord = {
            event_id: event.event_id,
            schema_version: "1.0.0",
            event_type: "TELEMETRY",
            plant_id: "PLANT_01",
            line_id: "LINE_A",
            machine_id: event.machine_id,
            machine_type: event.machine_type,
            protocol: event.protocol,
            source_address: "",
            event_time: event.event_time,
            ingestion_time: event.event_time,
            sequence: event.sequence,
            operating_state: event.operating_state,
            health_state: event.health_state,
            quality: event.quality,
            measurements: event.measurements,
            derived: event.derived,
          };
          const updatedRecords = [...prev.records, newRecord].slice(-100);
          return {
            ...prev,
            total_records: updatedRecords.length,
            records: updatedRecords,
          };
        });
      }
    },
    [machineId]
  );

  useRealtimeTelemetry(handleRealtimeEvent);

  useEffect(() => {
    loadHistory();
  }, [loadHistory]);

  return { history, loading, error, refresh: loadHistory };
}
