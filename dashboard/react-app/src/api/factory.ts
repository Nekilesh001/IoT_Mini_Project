import { apiClient } from "./client";
import { FactorySummary, ProtocolHealthItem } from "../types";

export async function fetchFactorySummary(): Promise<FactorySummary> {
  return apiClient<FactorySummary>("/api/factory/summary");
}

export async function fetchProtocolHealth(): Promise<{ protocols: ProtocolHealthItem[]; total_protocols: number; online_protocols: number }> {
  return apiClient<{ protocols: ProtocolHealthItem[]; total_protocols: number; online_protocols: number }>("/api/protocols/health");
}
