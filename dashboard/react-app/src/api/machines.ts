import { apiClient } from "./client";
import { MachineOverviewItem, MachineDetail, TelemetryRecord, TelemetryHistory } from "../types";

export async function fetchMachines(): Promise<MachineOverviewItem[]> {
  return apiClient<MachineOverviewItem[]>("/api/machines");
}

export async function fetchMachineDetail(machineId: string): Promise<MachineDetail> {
  return apiClient<MachineDetail>(`/api/machines/${encodeURIComponent(machineId)}`);
}

export async function fetchMachineLatest(machineId: string): Promise<TelemetryRecord> {
  return apiClient<TelemetryRecord>(`/api/machines/${encodeURIComponent(machineId)}/latest`);
}

export interface HistoryParams {
  start?: string;
  end?: string;
  limit?: number;
  signals?: string[];
}

export async function fetchMachineHistory(machineId: string, params: HistoryParams = {}): Promise<TelemetryHistory> {
  const query = new URLSearchParams();
  if (params.start) query.append("start", params.start);
  if (params.end) query.append("end", params.end);
  if (params.limit) query.append("limit", params.limit.toString());
  if (params.signals && params.signals.length > 0) query.append("signals", params.signals.join(","));

  const queryString = query.toString();
  const endpoint = `/api/machines/${encodeURIComponent(machineId)}/history${queryString ? `?${queryString}` : ""}`;
  return apiClient<TelemetryHistory>(endpoint);
}
