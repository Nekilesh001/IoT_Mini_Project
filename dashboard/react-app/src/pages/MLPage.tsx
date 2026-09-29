import React, { useState, useEffect } from "react";
import {
  fetchMLStatus,
  fetchMLModels,
  fetchMLMetrics,
  fetchMLInferences,
} from "../api/ml";
import {
  MLSystemStatus,
  MLModelInfo,
  MLMetricsSummary,
  MLInferenceResult,
} from "../types";

export const MLPage: React.FC = () => {
  const [status, setStatus] = useState<MLSystemStatus | null>(null);
  const [models, setModels] = useState<MLModelInfo[]>([]);
  const [metrics, setMetrics] = useState<MLMetricsSummary | null>(null);
  const [recentInferences, setRecentInferences] = useState<MLInferenceResult[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedMachine, setSelectedMachine] = useState<string>("ALL");

  const loadData = async () => {
    try {
      const [statusRes, modelsRes, metricsRes, infRes] = await Promise.all([
        fetchMLStatus(),
        fetchMLModels(),
        fetchMLMetrics(),
        fetchMLInferences(undefined, 30),
      ]);
      setStatus(statusRes);
      setModels(modelsRes);
      setMetrics(metricsRes);
      setRecentInferences(infRes);
      setError(null);
    } catch (err: any) {
      setError(err?.message || "Failed to load Edge ML telemetry");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
    const interval = setInterval(loadData, 3000);
    return () => clearInterval(interval);
  }, []);

  const filteredInferences =
    selectedMachine === "ALL"
      ? recentInferences
      : recentInferences.filter((i) => i.machine_id === selectedMachine);

  const uniqueMachines = Array.from(
    new Set(recentInferences.map((i) => i.machine_id))
  ).sort();

  return (
    <div className="ml-page-container" style={{ padding: "1.5rem", maxWidth: "1600px", margin: "0 auto" }}>
      {/* Header */}
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          marginBottom: "1.5rem",
          flexWrap: "wrap",
          gap: "1rem",
        }}
      >
        <div>
          <h1 style={{ fontSize: "1.75rem", fontWeight: 700, margin: 0, color: "#f8fafc" }}>
            Edge ML & Predictive Maintenance Console
          </h1>
          <p style={{ margin: "0.25rem 0 0 0", color: "#94a3b8", fontSize: "0.95rem" }}>
            Real-time edge inference for unsupervised anomaly detection and continuous Remaining Useful Life (RUL) regression
          </p>
        </div>

        <div style={{ display: "flex", gap: "0.75rem", alignItems: "center" }}>
          <span
            style={{
              display: "inline-flex",
              alignItems: "center",
              gap: "0.4rem",
              padding: "0.35rem 0.75rem",
              borderRadius: "9999px",
              fontSize: "0.85rem",
              fontWeight: 600,
              background: status?.initialized ? "rgba(34, 197, 94, 0.15)" : "rgba(239, 68, 68, 0.15)",
              color: status?.initialized ? "#4ade80" : "#f87171",
              border: `1px solid ${status?.initialized ? "rgba(34, 197, 94, 0.3)" : "rgba(239, 68, 68, 0.3)"}`,
            }}
          >
            <span
              style={{
                width: "8px",
                height: "8px",
                borderRadius: "50%",
                background: status?.initialized ? "#22c55e" : "#ef4444",
              }}
            />
            {status?.initialized ? "ML ENGINE ACTIVE" : "ML ENGINE OFFLINE"}
          </span>

          <span
            style={{
              padding: "0.35rem 0.75rem",
              borderRadius: "6px",
              fontSize: "0.85rem",
              fontWeight: 600,
              background: "#1e293b",
              color: "#38bdf8",
              border: "1px solid #334155",
            }}
          >
            RUNTIME: {status?.runtime_backend || "SKLEARN"}
          </span>
        </div>
      </div>

      {error && (
        <div
          style={{
            background: "rgba(239, 68, 68, 0.1)",
            border: "1px solid rgba(239, 68, 68, 0.3)",
            color: "#fca5a5",
            padding: "0.75rem 1rem",
            borderRadius: "8px",
            marginBottom: "1.5rem",
            fontSize: "0.9rem",
          }}
        >
          {error}
        </div>
      )}

      {/* Top Stat Cards */}
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fit, minmax(240px, 1fr))",
          gap: "1rem",
          marginBottom: "1.5rem",
        }}
      >
        <div style={{ background: "#1e293b", padding: "1.25rem", borderRadius: "10px", border: "1px solid #334155" }}>
          <div style={{ color: "#94a3b8", fontSize: "0.85rem", fontWeight: 500 }}>TOTAL INFERENCES</div>
          <div style={{ fontSize: "1.85rem", fontWeight: 700, color: "#f8fafc", marginTop: "0.25rem" }}>
            {metrics?.total_inferences?.toLocaleString() || "0"}
          </div>
          <div style={{ color: "#4ade80", fontSize: "0.8rem", marginTop: "0.25rem" }}>
            Success Rate: {metrics?.success_rate_pct || 100}%
          </div>
        </div>

        <div style={{ background: "#1e293b", padding: "1.25rem", borderRadius: "10px", border: "1px solid #334155" }}>
          <div style={{ color: "#94a3b8", fontSize: "0.85rem", fontWeight: 500 }}>ANOMALY DETECTIONS</div>
          <div style={{ fontSize: "1.85rem", fontWeight: 700, color: "#f59e0b", marginTop: "0.25rem" }}>
            {status?.fleet_summary?.anomalous_inferences_total || 0}
          </div>
          <div style={{ color: "#94a3b8", fontSize: "0.8rem", marginTop: "0.25rem" }}>
            Active Anomalous: {status?.fleet_summary?.active_anomalous_machines?.length || 0} Machines
          </div>
        </div>

        <div style={{ background: "#1e293b", padding: "1.25rem", borderRadius: "10px", border: "1px solid #334155" }}>
          <div style={{ color: "#94a3b8", fontSize: "0.85rem", fontWeight: 500 }}>LOW RUL ALERTS (&lt;30m)</div>
          <div style={{ fontSize: "1.85rem", fontWeight: 700, color: "#ef4444", marginTop: "0.25rem" }}>
            {status?.fleet_summary?.low_rul_machines?.length || 0}
          </div>
          <div style={{ color: "#94a3b8", fontSize: "0.8rem", marginTop: "0.25rem" }}>
            Critical Maintenance Warning
          </div>
        </div>

        <div style={{ background: "#1e293b", padding: "1.25rem", borderRadius: "10px", border: "1px solid #334155" }}>
          <div style={{ color: "#94a3b8", fontSize: "0.85rem", fontWeight: 500 }}>AVG INFERENCE LATENCY</div>
          <div style={{ fontSize: "1.85rem", fontWeight: 700, color: "#38bdf8", marginTop: "0.25rem" }}>
            {metrics?.total_inference_ms?.mean ? `${metrics.total_inference_ms.mean}ms` : "0.0ms"}
          </div>
          <div style={{ color: "#94a3b8", fontSize: "0.8rem", marginTop: "0.25rem" }}>
            p95: {metrics?.total_inference_ms?.p95 || 0}ms | Max: {metrics?.total_inference_ms?.max || 0}ms
          </div>
        </div>
      </div>

      {/* Latency & Model Catalog Row */}
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fit, minmax(400px, 1fr))",
          gap: "1.5rem",
          marginBottom: "1.5rem",
        }}
      >
        {/* Latency Breakdown Card */}
        <div style={{ background: "#1e293b", padding: "1.25rem", borderRadius: "10px", border: "1px solid #334155" }}>
          <h2 style={{ fontSize: "1.1rem", fontWeight: 600, margin: "0 0 1rem 0", color: "#f8fafc" }}>
            Real-Time Latency Breakdown
          </h2>
          <div style={{ display: "flex", flexDirection: "column", gap: "0.85rem" }}>
            <div>
              <div style={{ display: "flex", justifyContent: "space-between", fontSize: "0.85rem", marginBottom: "0.25rem", color: "#cbd5e1" }}>
                <span>Feature Generation (1019 signals)</span>
                <span>{metrics?.feature_generation_ms?.mean || 0}ms (p95: {metrics?.feature_generation_ms?.p95 || 0}ms)</span>
              </div>
              <div style={{ height: "6px", background: "#0f172a", borderRadius: "3px", overflow: "hidden" }}>
                <div style={{ height: "100%", width: "65%", background: "#38bdf8", borderRadius: "3px" }} />
              </div>
            </div>

            <div>
              <div style={{ display: "flex", justifyContent: "space-between", fontSize: "0.85rem", marginBottom: "0.25rem", color: "#cbd5e1" }}>
                <span>Isolation Forest Anomaly Scoring</span>
                <span>{metrics?.anomaly_inference_ms?.mean || 0}ms (p95: {metrics?.anomaly_inference_ms?.p95 || 0}ms)</span>
              </div>
              <div style={{ height: "6px", background: "#0f172a", borderRadius: "3px", overflow: "hidden" }}>
                <div style={{ height: "100%", width: "20%", background: "#f59e0b", borderRadius: "3px" }} />
              </div>
            </div>

            <div>
              <div style={{ display: "flex", justifyContent: "space-between", fontSize: "0.85rem", marginBottom: "0.25rem", color: "#cbd5e1" }}>
                <span>RUL HistGradientBoosting Regression</span>
                <span>{metrics?.rul_inference_ms?.mean || 0}ms (p95: {metrics?.rul_inference_ms?.p95 || 0}ms)</span>
              </div>
              <div style={{ height: "6px", background: "#0f172a", borderRadius: "3px", overflow: "hidden" }}>
                <div style={{ height: "100%", width: "15%", background: "#10b981", borderRadius: "3px" }} />
              </div>
            </div>
          </div>
        </div>

        {/* Model Bundle Catalog Card */}
        <div style={{ background: "#1e293b", padding: "1.25rem", borderRadius: "10px", border: "1px solid #334155" }}>
          <h2 style={{ fontSize: "1.1rem", fontWeight: 600, margin: "0 0 1rem 0", color: "#f8fafc" }}>
            Loaded Model Bundles
          </h2>
          <div style={{ display: "flex", flexDirection: "column", gap: "0.75rem" }}>
            {models.map((m) => (
              <div
                key={m.model_name}
                style={{
                  background: "#0f172a",
                  padding: "0.85rem 1rem",
                  borderRadius: "8px",
                  border: "1px solid #334155",
                }}
              >
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                  <span style={{ fontWeight: 600, color: "#f8fafc" }}>{m.model_name}</span>
                  <span
                    style={{
                      fontSize: "0.75rem",
                      padding: "0.2rem 0.5rem",
                      borderRadius: "4px",
                      background: "rgba(56, 189, 248, 0.15)",
                      color: "#38bdf8",
                    }}
                  >
                    {m.version}
                  </span>
                </div>
                <div style={{ fontSize: "0.8rem", color: "#94a3b8", marginTop: "0.35rem" }}>
                  Type: {m.model_type} | Features: {m.num_features} | Runtime: {m.runtime_backend}
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Real-time Fleet Predictions Table */}
      <div style={{ background: "#1e293b", padding: "1.25rem", borderRadius: "10px", border: "1px solid #334155" }}>
        <div
          style={{
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
            marginBottom: "1rem",
            flexWrap: "wrap",
            gap: "0.5rem",
          }}
        >
          <h2 style={{ fontSize: "1.1rem", fontWeight: 600, margin: 0, color: "#f8fafc" }}>
            Fleet Real-Time Inference Stream
          </h2>

          <div style={{ display: "flex", gap: "0.5rem", alignItems: "center" }}>
            <label style={{ fontSize: "0.85rem", color: "#94a3b8" }}>Filter Machine:</label>
            <select
              value={selectedMachine}
              onChange={(e) => setSelectedMachine(e.target.value)}
              style={{
                background: "#0f172a",
                border: "1px solid #334155",
                color: "#f8fafc",
                padding: "0.35rem 0.65rem",
                borderRadius: "6px",
                fontSize: "0.85rem",
              }}
            >
              <option value="ALL">All Machines</option>
              {uniqueMachines.map((m) => (
                <option key={m} value={m}>
                  {m}
                </option>
              ))}
            </select>
          </div>
        </div>

        <div style={{ overflowX: "auto" }}>
          <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "0.85rem", textAlign: "left" }}>
            <thead>
              <tr style={{ borderBottom: "1px solid #334155", color: "#94a3b8" }}>
                <th style={{ padding: "0.75rem 0.5rem" }}>MACHINE</th>
                <th style={{ padding: "0.75rem 0.5rem" }}>STATUS</th>
                <th style={{ padding: "0.75rem 0.5rem" }}>ANOMALY RISK</th>
                <th style={{ padding: "0.75rem 0.5rem" }}>ANOMALY STATE</th>
                <th style={{ padding: "0.75rem 0.5rem" }}>PREDICTED RUL</th>
                <th style={{ padding: "0.75rem 0.5rem" }}>LATENCY</th>
                <th style={{ padding: "0.75rem 0.5rem" }}>TIME</th>
              </tr>
            </thead>
            <tbody>
              {filteredInferences.length === 0 ? (
                <tr>
                  <td colSpan={7} style={{ textAlign: "center", padding: "2rem", color: "#64748b" }}>
                    {loading ? "Streaming real-time telemetry..." : "No ML inference records found"}
                  </td>
                </tr>
              ) : (
                filteredInferences.map((inf) => {
                  const isAnom = inf.anomaly_label === "ANOMALOUS";
                  const score = inf.anomaly_score ?? 0;
                  const isLowRul =
                    inf.predicted_rul_seconds !== null &&
                    inf.predicted_rul_seconds !== undefined &&
                    inf.predicted_rul_seconds < 1800;

                  return (
                    <tr key={inf.result_id} style={{ borderBottom: "1px solid rgba(51, 65, 85, 0.5)" }}>
                      <td style={{ padding: "0.75rem 0.5rem", fontWeight: 600, color: "#f8fafc" }}>
                        {inf.machine_id}
                        <span style={{ fontSize: "0.75rem", color: "#64748b", display: "block" }}>
                          {inf.machine_type}
                        </span>
                      </td>

                      <td style={{ padding: "0.75rem 0.5rem" }}>
                        <span
                          style={{
                            padding: "0.2rem 0.5rem",
                            borderRadius: "4px",
                            fontSize: "0.75rem",
                            fontWeight: 600,
                            background:
                              inf.status === "READY"
                                ? "rgba(34, 197, 94, 0.1)"
                                : "rgba(234, 179, 8, 0.1)",
                            color: inf.status === "READY" ? "#4ade80" : "#facc15",
                          }}
                        >
                          {inf.status}
                        </span>
                      </td>

                      <td style={{ padding: "0.75rem 0.5rem", minWidth: "140px" }}>
                        <div style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
                          <span style={{ minWidth: "35px", fontWeight: 600, color: isAnom ? "#f87171" : "#cbd5e1" }}>
                            {(score * 100).toFixed(1)}%
                          </span>
                          <div style={{ flex: 1, height: "6px", background: "#0f172a", borderRadius: "3px", overflow: "hidden" }}>
                            <div
                              style={{
                                height: "100%",
                                width: `${Math.min(100, Math.max(5, score * 100))}%`,
                                background: isAnom ? "#ef4444" : score > 0.4 ? "#f59e0b" : "#10b981",
                                borderRadius: "3px",
                              }}
                            />
                          </div>
                        </div>
                      </td>

                      <td style={{ padding: "0.75rem 0.5rem" }}>
                        <span
                          style={{
                            padding: "0.2rem 0.55rem",
                            borderRadius: "9999px",
                            fontSize: "0.75rem",
                            fontWeight: 600,
                            background: isAnom ? "rgba(239, 68, 68, 0.2)" : "rgba(34, 197, 94, 0.15)",
                            color: isAnom ? "#f87171" : "#4ade80",
                            border: `1px solid ${isAnom ? "rgba(239, 68, 68, 0.4)" : "rgba(34, 197, 94, 0.3)"}`,
                          }}
                        >
                          {inf.anomaly_label}
                        </span>
                      </td>

                      <td style={{ padding: "0.75rem 0.5rem", fontWeight: 600, color: isLowRul ? "#f87171" : "#f8fafc" }}>
                        {inf.predicted_rul_seconds !== null && inf.predicted_rul_seconds !== undefined
                          ? `${inf.predicted_rul_minutes?.toFixed(1)} min (${inf.predicted_rul_seconds?.toFixed(0)}s)`
                          : "Warming up..."}
                      </td>

                      <td style={{ padding: "0.75rem 0.5rem", color: "#94a3b8" }}>
                        {inf.latency_ms?.total_inference_ms?.toFixed(2) || "0.00"} ms
                      </td>

                      <td style={{ padding: "0.75rem 0.5rem", color: "#64748b", fontSize: "0.8rem" }}>
                        {inf.event_time ? new Date(inf.event_time).toLocaleTimeString() : "--"}
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
