import { useState, useEffect, useCallback } from "react";
import { FactorySummary } from "../types";
import { fetchFactorySummary } from "../api/factory";

export function useFactorySummary(pollIntervalMs = 5000) {
  const [summary, setSummary] = useState<FactorySummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadSummary = useCallback(async () => {
    try {
      const data = await fetchFactorySummary();
      setSummary(data);
      setError(null);
    } catch (err: any) {
      setError(err?.message || "Failed to load factory summary");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadSummary();
    const interval = setInterval(loadSummary, pollIntervalMs);
    return () => clearInterval(interval);
  }, [loadSummary, pollIntervalMs]);

  return { summary, loading, error, refresh: loadSummary };
}
