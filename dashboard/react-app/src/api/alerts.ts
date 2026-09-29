import { apiClient } from "./client";
import { AlertItem, AlertSummary, FaultScenario } from "../types";

export const alertsApi = {
  getAlerts: async (params?: {
    machine_id?: string;
    severity?: string;
    status?: string;
    start?: string;
    end?: string;
    limit?: number;
  }): Promise<AlertItem[]> => {
    const query = new URLSearchParams();
    if (params?.machine_id) query.set("machine_id", params.machine_id);
    if (params?.severity) query.set("severity", params.severity);
    if (params?.status) query.set("status", params.status);
    if (params?.start) query.set("start", params.start);
    if (params?.end) query.set("end", params.end);
    if (params?.limit) query.set("limit", params.limit.toString());
    const qs = query.toString();
    return apiClient<AlertItem[]>(`/api/alerts${qs ? `?${qs}` : ""}`);
  },

  getActiveAlerts: async (limit: number = 100): Promise<AlertItem[]> => {
    return apiClient<AlertItem[]>(`/api/alerts/active?limit=${limit}`);
  },

  getAlertSummary: async (): Promise<AlertSummary> => {
    return apiClient<AlertSummary>("/api/alerts/summary");
  },

  getAlertById: async (alertId: string): Promise<AlertItem> => {
    return apiClient<AlertItem>(`/api/alerts/${encodeURIComponent(alertId)}`);
  },

  getMachineAlerts: async (
    machineId: string,
    limit: number = 50
  ): Promise<AlertItem[]> => {
    return apiClient<AlertItem[]>(
      `/api/machines/${encodeURIComponent(machineId)}/alerts?limit=${limit}`
    );
  },

  acknowledgeAlert: async (
    alertId: string,
    acknowledgedBy: string = "operator"
  ): Promise<AlertItem> => {
    return apiClient<AlertItem>(
      `/api/alerts/${encodeURIComponent(alertId)}/acknowledge`,
      {
        method: "POST",
        body: JSON.stringify({ acknowledged_by: acknowledgedBy }),
      }
    );
  },

  resolveAlert: async (
    alertId: string,
    resolutionNotes: string = "Resolved by operator"
  ): Promise<AlertItem> => {
    return apiClient<AlertItem>(
      `/api/alerts/${encodeURIComponent(alertId)}/resolve`,
      {
        method: "POST",
        body: JSON.stringify({ resolution_notes: resolutionNotes }),
      }
    );
  },

  getScenarios: async (): Promise<FaultScenario[]> => {
    return apiClient<FaultScenario[]>("/api/scenarios");
  },

  startScenario: async (scenarioId: string): Promise<FaultScenario> => {
    return apiClient<FaultScenario>(
      `/api/scenarios/${encodeURIComponent(scenarioId)}/start`,
      { method: "POST" }
    );
  },

  stopScenario: async (scenarioId: string): Promise<FaultScenario> => {
    return apiClient<FaultScenario>(
      `/api/scenarios/${encodeURIComponent(scenarioId)}/stop`,
      { method: "POST" }
    );
  },
};
