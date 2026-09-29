/**
 * Edge ML API Client for FastAPI backend.
 */

import { apiClient } from "./client";
import {
  MLInferenceResult,
  MLModelInfo,
  MLSystemStatus,
  MLMetricsSummary,
} from "../types";

export async function fetchMLStatus(): Promise<MLSystemStatus> {
  return apiClient<MLSystemStatus>("/api/ml/status");
}

export async function fetchMLModels(): Promise<MLModelInfo[]> {
  return apiClient<MLModelInfo[]>("/api/ml/models");
}

export async function fetchMLMetrics(): Promise<MLMetricsSummary> {
  return apiClient<MLMetricsSummary>("/api/ml/metrics");
}

export async function fetchFleetMLSummary(): Promise<any> {
  return apiClient<any>("/api/ml/fleet-summary");
}

export async function fetchMachineLatestML(machineId: string): Promise<MLInferenceResult> {
  return apiClient<MLInferenceResult>(`/api/ml/machines/${machineId}`);
}

export async function fetchMLInferences(machineId?: string, limit: number = 50): Promise<MLInferenceResult[]> {
  const query = machineId ? `?machine_id=${machineId}&limit=${limit}` : `?limit=${limit}`;
  return apiClient<MLInferenceResult[]>(`/api/ml/inferences${query}`);
}
