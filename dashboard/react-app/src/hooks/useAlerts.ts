import { useState, useEffect, useCallback } from "react";
import { AlertItem, AlertSummary } from "../types";
import { alertsApi } from "../api/alerts";

export const useAlerts = () => {
  const [activeAlerts, setActiveAlerts] = useState<AlertItem[]>([]);
  const [summary, setSummary] = useState<AlertSummary | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const fetchAlerts = useCallback(async () => {
    try {
      const [active, sum] = await Promise.all([
        alertsApi.getActiveAlerts(),
        alertsApi.getAlertSummary(),
      ]);
      setActiveAlerts(active);
      setSummary(sum);
      setError(null);
    } catch (err: any) {
      setError(err.message || "Failed to load alerts");
    } finally {
      setLoading(false);
    }
  }, []);

  const acknowledgeAlert = async (alertId: string) => {
    try {
      const updated = await alertsApi.acknowledgeAlert(alertId, "operator");
      setActiveAlerts((prev) =>
        prev.map((a) => (a.alert_id === alertId ? updated : a))
      );
      fetchAlerts();
      return updated;
    } catch (err: any) {
      throw err;
    }
  };

  const resolveAlert = async (alertId: string, notes?: string) => {
    try {
      const updated = await alertsApi.resolveAlert(alertId, notes);
      setActiveAlerts((prev) => prev.filter((a) => a.alert_id !== alertId));
      fetchAlerts();
      return updated;
    } catch (err: any) {
      throw err;
    }
  };

  useEffect(() => {
    fetchAlerts();
    const interval = setInterval(fetchAlerts, 2000);
    return () => clearInterval(interval);
  }, [fetchAlerts]);

  return {
    activeAlerts,
    summary,
    loading,
    error,
    refresh: fetchAlerts,
    acknowledgeAlert,
    resolveAlert,
  };
};
