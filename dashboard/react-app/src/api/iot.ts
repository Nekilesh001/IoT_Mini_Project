/**
 * API client functions for External IoT Devices and Wokwi Bridge.
 */

import { ExternalIoTDevice, WokwiBridgeStatus } from "../types";

const API_BASE = import.meta.env.VITE_API_URL || "";

export async function fetchExternalIoTDevices(): Promise<ExternalIoTDevice[]> {
  const response = await fetch(`${API_BASE}/api/iot-devices`);
  if (!response.ok) {
    throw new Error(`Failed to fetch external IoT devices: ${response.statusText}`);
  }
  return response.json();
}

export async function fetchExternalIoTDevice(deviceId: string): Promise<ExternalIoTDevice> {
  const response = await fetch(`${API_BASE}/api/iot-devices/${deviceId}`);
  if (!response.ok) {
    throw new Error(`Failed to fetch device ${deviceId}: ${response.statusText}`);
  }
  return response.json();
}

export async function fetchExternalIoTHistory(deviceId: string, limit: number = 50): Promise<any[]> {
  const response = await fetch(`${API_BASE}/api/iot-devices/${deviceId}/history?limit=${limit}`);
  if (!response.ok) {
    throw new Error(`Failed to fetch history for ${deviceId}: ${response.statusText}`);
  }
  return response.json();
}

export async function fetchWokwiBridgeStatus(): Promise<WokwiBridgeStatus> {
  const response = await fetch(`${API_BASE}/api/iot-devices/bridge/status`);
  if (!response.ok) {
    throw new Error(`Failed to fetch Wokwi bridge status: ${response.statusText}`);
  }
  return response.json();
}
