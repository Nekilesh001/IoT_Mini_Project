import React, { useState, useEffect, useRef } from "react";
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
import { Brain, Cpu, Gauge, Activity, Wrench, Zap, ShieldAlert, CheckCircle2, Clock, BarChart3, Filter } from "lucide-react";
import { MLAnalyticsChart } from "../components/MLAnalyticsChart";

export const MLPage: React.FC = () => {
  const [status, setStatus] = useState<MLSystemStatus | null>(null);
  const [models, setModels] = useState<MLModelInfo[]>([]);
  const [metrics, setMetrics] = useState<MLMetricsSummary | null>(null);
  const [recentInferences, setRecentInferences] = useState<MLInferenceResult[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedMachine, setSelectedMachine] = useState<string>("ALL");
  const [selectedSubsystem, setSelectedSubsystem] = useState<string>("ALL");
  const [liveStreamActive, setLiveStreamActive] = useState<boolean>(false);

  const loadData = async () => {
    try {
      const [statusRes, modelsRes, metricsRes, infRes] = await Promise.all([
        fetchMLStatus(),
        fetchMLModels(),
        fetchMLMetrics(),
        fetchMLInferences(undefined, 40),
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

  // Connect to SSE stream for live ML inference events
  useEffect(() => {
    let eventSource: EventSource | null = null;
    try {
      const url = `${import.meta.env.VITE_API_URL || ""}/api/realtime/telemetry`;
      eventSource = new EventSource(url);

      eventSource.addEventListener("ml_inference", (e: MessageEvent) => {
        try {
          const newInf: MLInferenceResult = JSON.parse(e.data);
          setLiveStreamActive(true);
          setRecentInferences((prev) => {
            // Deduplicate by result_id or machine_id + timestamp
            const exists = prev.some((p) => p.result_id === newInf.result_id);
            if (exists) return prev;
            return [newInf, ...prev.slice(0, 49)];
          });
        } catch {}
      });

      eventSource.onopen = () => setLiveStreamActive(true);
      eventSource.onerror = () => setLiveStreamActive(false);
    } catch {}

    return () => {
      if (eventSource) eventSource.close();
    };
  }, []);

  const filteredInferences = recentInferences.filter((i) => {
    if (selectedMachine !== "ALL" && i.machine_id !== selectedMachine) return false;
    if (selectedSubsystem === "TOOL_WEAR" && !i.machine_id.startsWith("CNC")) return false;
    if (selectedSubsystem === "BEARING_WEAR" && !(i.machine_id.startsWith("PMP") || i.machine_id.startsWith("CMP") || i.machine_id.startsWith("CHL"))) return false;
    if (selectedSubsystem === "ACTUATOR_STRESS" && !i.machine_id.startsWith("ROB")) return false;
    if (selectedSubsystem === "HYDRAULIC_SEAL" && !(i.machine_id.startsWith("PRS") || i.machine_id.startsWith("IMM"))) return false;
    return true;
  });

  const uniqueMachines = Array.from(
    new Set(recentInferences.map((i) => i.machine_id))
  ).sort();

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "28px", maxWidth: "1600px", margin: "0 auto" }}>
      {/* Header */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-end", flexWrap: "wrap", gap: "16px" }}>
        <div>
          <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
            <h1 style={{ fontSize: "28px", fontWeight: 800, margin: 0, color: "#f8fafc", letterSpacing: "-0.02em" }}>
              Edge ML & Predictive Maintenance Console
            </h1>
            <span
              style={{
                display: "inline-flex",
                alignItems: "center",
                gap: "6px",
                padding: "4px 10px",
                borderRadius: "9999px",
                fontSize: "11px",
                fontWeight: 700,
                background: status?.initialized ? "rgba(16, 185, 129, 0.15)" : "rgba(244, 63, 94, 0.15)",
                color: status?.initialized ? "#34d399" : "#f87171",
                border: `1px solid ${status?.initialized ? "rgba(16, 185, 129, 0.3)" : "rgba(244, 63, 94, 0.3)"}`,
              }}
            >
              <span className="live-pulse-dot" />
              {status?.initialized ? "EDGE ENGINE ONLINE" : "OFFLINE"}
            </span>
          </div>
          <p style={{ margin: "6px 0 0 0", color: "#94a3b8", fontSize: "14px" }}>
            Real-time inference subsystem for multi-variate anomaly scoring, continuous Remaining Useful Life (RUL) regression, and component health forecasting.
          </p>
        </div>

        <div style={{ display: "flex", gap: "8px", alignItems: "center" }}>
          <span
            style={{
              padding: "6px 12px",
              borderRadius: "8px",
              fontSize: "12px",
              fontWeight: 700,
              background: "rgba(15, 23, 42, 0.8)",
              color: "#38bdf8",
              border: "1px solid rgba(56, 189, 248, 0.3)",
              fontFamily: "'JetBrains Mono', monospace",
            }}
          >
            BACKEND: {status?.runtime_backend || "ONNX"}
          </span>
        </div>
      </div>

      {error && (
        <div
          style={{
            background: "rgba(244, 63, 94, 0.1)",
            border: "1px solid rgba(244, 63, 94, 0.3)",
            color: "#fca5a5",
            padding: "12px 16px",
            borderRadius: "10px",
            fontSize: "13px",
          }}
        >
          {error}
        </div>
      )}

      {/* Top Stat Cards */}
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))",
          gap: "16px",
        }}
      >
        <div
          style={{
            background: "linear-gradient(135deg, rgba(30, 41, 59, 0.7), rgba(15, 23, 42, 0.8))",
            padding: "18px",
            borderRadius: "12px",
            border: "1px solid rgba(255, 255, 255, 0.08)",
            borderLeft: "3px solid #06b6d4",
          }}
        >
          <div style={{ color: "#94a3b8", fontSize: "11px", fontWeight: 700, letterSpacing: "0.05em" }}>TOTAL INFERENCES</div>
          <div style={{ fontSize: "28px", fontWeight: 800, color: "#f8fafc", marginTop: "4px", fontFamily: "'JetBrains Mono', monospace" }}>
            {metrics?.total_inferences?.toLocaleString() || "0"}
          </div>
          <div style={{ color: "#10b981", fontSize: "11px", marginTop: "4px", fontWeight: 600 }}>
            Success Rate: {metrics?.success_rate_pct || 100}%
          </div>
        </div>

        <div
          style={{
            background: "linear-gradient(135deg, rgba(30, 41, 59, 0.7), rgba(15, 23, 42, 0.8))",
            padding: "18px",
            borderRadius: "12px",
            border: "1px solid rgba(255, 255, 255, 0.08)",
            borderLeft: "3px solid #f59e0b",
          }}
        >
          <div style={{ color: "#94a3b8", fontSize: "11px", fontWeight: 700, letterSpacing: "0.05em" }}>ANOMALY DETECTIONS</div>
          <div style={{ fontSize: "28px", fontWeight: 800, color: "#f59e0b", marginTop: "4px", fontFamily: "'JetBrains Mono', monospace" }}>
            {status?.fleet_summary?.anomalous_inferences_total || 0}
          </div>
          <div style={{ color: "#94a3b8", fontSize: "11px", marginTop: "4px" }}>
            Active: {status?.fleet_summary?.active_anomalous_machines?.length || 0} Machines
          </div>
        </div>

        <div
          style={{
            background: "linear-gradient(135deg, rgba(30, 41, 59, 0.7), rgba(15, 23, 42, 0.8))",
            padding: "18px",
            borderRadius: "12px",
            border: "1px solid rgba(255, 255, 255, 0.08)",
            borderLeft: "3px solid #f43f5e",
          }}
        >
          <div style={{ color: "#94a3b8", fontSize: "11px", fontWeight: 700, letterSpacing: "0.05em" }}>CRITICAL RUL HORIZON</div>
          <div style={{ fontSize: "28px", fontWeight: 800, color: "#f43f5e", marginTop: "4px", fontFamily: "'JetBrains Mono', monospace" }}>
            {status?.fleet_summary?.low_rul_machines?.length || 0}
          </div>
          <div style={{ color: "#94a3b8", fontSize: "11px", marginTop: "4px" }}>
            Machines with &lt;10m life remaining
          </div>
        </div>

        <div
          style={{
            background: "linear-gradient(135deg, rgba(30, 41, 59, 0.7), rgba(15, 23, 42, 0.8))",
            padding: "18px",
            borderRadius: "12px",
            border: "1px solid rgba(255, 255, 255, 0.08)",
            borderLeft: "3px solid #8b5cf6",
          }}
        >
          <div style={{ color: "#94a3b8", fontSize: "11px", fontWeight: 700, letterSpacing: "0.05em" }}>AVG EDGE LATENCY</div>
          <div style={{ fontSize: "28px", fontWeight: 800, color: "#38bdf8", marginTop: "4px", fontFamily: "'JetBrains Mono', monospace" }}>
            {metrics?.total_inference_ms?.mean ? `${metrics.total_inference_ms.mean}ms` : "0.0ms"}
          </div>
          <div style={{ color: "#94a3b8", fontSize: "11px", marginTop: "4px" }}>
            p95: {metrics?.total_inference_ms?.p95 || 0}ms
          </div>
        </div>
      </div>

      {/* Live Visual Analytics & Degradation Trajectory Chart */}
      <MLAnalyticsChart
        inferences={recentInferences}
        selectedMachine={selectedMachine}
        onSelectMachine={(m) => setSelectedMachine(m)}
      />

      {/* Multi-Model Predictive AI Suite Section */}
      <section>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "14px" }}>
          <div>
            <h2 style={{ fontSize: "18px", fontWeight: 700, color: "#f8fafc", margin: 0, display: "flex", alignItems: "center", gap: "8px" }}>
              <Brain size={18} color="#06b6d4" /> Edge Machine Learning Architecture & Subsystem Forecasters
            </h2>
            <span style={{ fontSize: "12px", color: "#94a3b8" }}>
              1,019 physical telemetry features extracted in real-time under strict anti-leakage protection
            </span>
          </div>
        </div>

        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(320px, 1fr))", gap: "16px" }}>
          {/* Model 1: Anomaly Detector */}
          <div
            style={{
              background: "linear-gradient(135deg, rgba(30, 41, 59, 0.75), rgba(15, 23, 42, 0.85))",
              border: "1px solid rgba(255, 255, 255, 0.08)",
              borderRadius: "12px",
              padding: "18px",
              display: "flex",
              flexDirection: "column",
              gap: "10px",
            }}
          >
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
              <span style={{ fontSize: "14px", fontWeight: 800, color: "#f8fafc", display: "flex", alignItems: "center", gap: "6px" }}>
                <Activity size={16} color="#06b6d4" /> Anomaly Detection
              </span>
              <span style={{ fontSize: "10px", padding: "2px 6px", borderRadius: "4px", background: "rgba(6, 182, 212, 0.15)", color: "#38bdf8", fontWeight: 700 }}>
                v1.0.0
              </span>
            </div>
            <div style={{ fontSize: "12px", color: "#94a3b8", lineHeight: 1.4 }}>
              <strong>Algorithm:</strong> Isolation Forest (Unsupervised)<br />
              <strong>Scope:</strong> Evaluates multi-variate process shifts and behavioral drift across all 12 machines.
            </div>
            <div style={{ fontSize: "11px", color: "#64748b", background: "rgba(11, 15, 25, 0.6)", padding: "8px", borderRadius: "6px" }}>
              Input: 1,019 observable temporal features (rolling windows 5, 15, 30, baseline delta)
            </div>
          </div>

          {/* Model 2: RUL Regressor */}
          <div
            style={{
              background: "linear-gradient(135deg, rgba(30, 41, 59, 0.75), rgba(15, 23, 42, 0.85))",
              border: "1px solid rgba(255, 255, 255, 0.08)",
              borderRadius: "12px",
              padding: "18px",
              display: "flex",
              flexDirection: "column",
              gap: "10px",
            }}
          >
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
              <span style={{ fontSize: "14px", fontWeight: 800, color: "#f8fafc", display: "flex", alignItems: "center", gap: "6px" }}>
                <Gauge size={16} color="#10b981" /> Remaining Useful Life (RUL)
              </span>
              <span style={{ fontSize: "10px", padding: "2px 6px", borderRadius: "4px", background: "rgba(16, 185, 129, 0.15)", color: "#34d399", fontWeight: 700 }}>
                v1.0.0
              </span>
            </div>
            <div style={{ fontSize: "12px", color: "#94a3b8", lineHeight: 1.4 }}>
              <strong>Algorithm:</strong> HistGradientBoostingRegressor<br />
              <strong>Scope:</strong> Predicts exact time-to-failure seconds, estimating remaining production horizon.
            </div>
            <div style={{ fontSize: "11px", color: "#64748b", background: "rgba(11, 15, 25, 0.6)", padding: "8px", borderRadius: "6px" }}>
              Performance: 91.1% MAE improvement over baseline, Test MAE = 80.07s
            </div>
          </div>

          {/* Component Forecasters */}
          <div
            style={{
              background: "linear-gradient(135deg, rgba(30, 41, 59, 0.75), rgba(15, 23, 42, 0.85))",
              border: "1px solid rgba(255, 255, 255, 0.08)",
              borderRadius: "12px",
              padding: "18px",
              display: "flex",
              flexDirection: "column",
              gap: "10px",
            }}
          >
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
              <span style={{ fontSize: "14px", fontWeight: 800, color: "#f8fafc", display: "flex", alignItems: "center", gap: "6px" }}>
                <Wrench size={16} color="#f59e0b" /> Component Degradation Forecasts
              </span>
              <span style={{ fontSize: "10px", padding: "2px 6px", borderRadius: "4px", background: "rgba(245, 158, 11, 0.15)", color: "#fbbf24", fontWeight: 700 }}>
                4 Specialized Models
              </span>
            </div>
            <div style={{ fontSize: "12px", color: "#94a3b8", lineHeight: 1.4 }}>
              • <strong>Tool Wear Forecast</strong>: CNC Spindle thermal load & cutting harmonics.<br />
              • <strong>Bearing Fatigue Index</strong>: Pumps, compressors, chillers.<br />
              • <strong>Joint Actuator Stress</strong>: 6-Axis & Welding robotics.<br />
              • <strong>Hydraulic Seal Integrity</strong>: Industrial Presses & Injection Molding.
            </div>
          </div>
        </div>
      </section>

      {/* Latency Breakdown & Model Artifacts */}
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fit, minmax(420px, 1fr))",
          gap: "16px",
        }}
      >
        {/* Latency Breakdown */}
        <div
          style={{
            background: "linear-gradient(135deg, rgba(30, 41, 59, 0.7), rgba(15, 23, 42, 0.8))",
            padding: "20px",
            borderRadius: "12px",
            border: "1px solid rgba(255, 255, 255, 0.08)",
          }}
        >
          <h3 style={{ fontSize: "15px", fontWeight: 700, margin: "0 0 16px 0", color: "#f8fafc" }}>
            Real-Time Edge Latency Breakdown
          </h3>
          <div style={{ display: "flex", flexDirection: "column", gap: "14px" }}>
            <div>
              <div style={{ display: "flex", justifyContent: "space-between", fontSize: "12px", marginBottom: "6px", color: "#cbd5e1" }}>
                <span>1. Feature Extraction (1,019 features)</span>
                <span style={{ fontFamily: "'JetBrains Mono', monospace" }}>{metrics?.feature_generation_ms?.mean || 0}ms (p95: {metrics?.feature_generation_ms?.p95 || 0}ms)</span>
              </div>
              <div style={{ height: "6px", background: "rgba(15, 23, 42, 0.8)", borderRadius: "9999px", overflow: "hidden" }}>
                <div style={{ height: "100%", width: "70%", background: "#06b6d4", borderRadius: "9999px" }} />
              </div>
            </div>

            <div>
              <div style={{ display: "flex", justifyContent: "space-between", fontSize: "12px", marginBottom: "6px", color: "#cbd5e1" }}>
                <span>2. Isolation Forest Anomaly Scoring</span>
                <span style={{ fontFamily: "'JetBrains Mono', monospace" }}>{metrics?.anomaly_inference_ms?.mean || 0}ms (p95: {metrics?.anomaly_inference_ms?.p95 || 0}ms)</span>
              </div>
              <div style={{ height: "6px", background: "rgba(15, 23, 42, 0.8)", borderRadius: "9999px", overflow: "hidden" }}>
                <div style={{ height: "100%", width: "15%", background: "#f59e0b", borderRadius: "9999px" }} />
              </div>
            </div>

            <div>
              <div style={{ display: "flex", justifyContent: "space-between", fontSize: "12px", marginBottom: "6px", color: "#cbd5e1" }}>
                <span>3. HistGBM RUL Regression</span>
                <span style={{ fontFamily: "'JetBrains Mono', monospace" }}>{metrics?.rul_inference_ms?.mean || 0}ms (p95: {metrics?.rul_inference_ms?.p95 || 0}ms)</span>
              </div>
              <div style={{ height: "6px", background: "rgba(15, 23, 42, 0.8)", borderRadius: "9999px", overflow: "hidden" }}>
                <div style={{ height: "100%", width: "15%", background: "#10b981", borderRadius: "9999px" }} />
              </div>
            </div>
          </div>
        </div>

        {/* Model Bundle Catalog */}
        <div
          style={{
            background: "linear-gradient(135deg, rgba(30, 41, 59, 0.7), rgba(15, 23, 42, 0.8))",
            padding: "20px",
            borderRadius: "12px",
            border: "1px solid rgba(255, 255, 255, 0.08)",
          }}
        >
          <h3 style={{ fontSize: "15px", fontWeight: 700, margin: "0 0 16px 0", color: "#f8fafc" }}>
            Loaded Model Artifacts
          </h3>
          <div style={{ display: "flex", flexDirection: "column", gap: "10px" }}>
            {models.length > 0 ? (
              models.map((m) => (
                <div
                  key={m.model_name}
                  style={{
                    background: "rgba(15, 23, 42, 0.8)",
                    padding: "12px 14px",
                    borderRadius: "8px",
                    border: "1px solid rgba(255, 255, 255, 0.05)",
                  }}
                >
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                    <span style={{ fontWeight: 700, color: "#f8fafc", fontSize: "13px" }}>{m.model_name}</span>
                    <span
                      style={{
                        fontSize: "11px",
                        padding: "2px 6px",
                        borderRadius: "4px",
                        background: "rgba(56, 189, 248, 0.15)",
                        color: "#38bdf8",
                        fontWeight: 700,
                      }}
                    >
                      {m.version}
                    </span>
                  </div>
                  <div style={{ fontSize: "11px", color: "#94a3b8", marginTop: "4px", fontFamily: "'JetBrains Mono', monospace" }}>
                    Type: {m.model_type} | Features: {m.num_features} | Backend: {m.runtime_backend}
                  </div>
                </div>
              ))
            ) : (
              <div style={{ fontSize: "12px", color: "#94a3b8", fontStyle: "italic" }}>
                Initializing models via Edge ModelLoader...
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Real-time Fleet Predictions Table */}
      <div
        style={{
          background: "linear-gradient(135deg, rgba(30, 41, 59, 0.7), rgba(15, 23, 42, 0.8))",
          padding: "20px",
          borderRadius: "14px",
          border: "1px solid rgba(255, 255, 255, 0.08)",
        }}
      >
        <div
          style={{
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
            marginBottom: "16px",
            flexWrap: "wrap",
            gap: "10px",
          }}
        >
          <div>
            <h2 style={{ fontSize: "17px", fontWeight: 700, margin: 0, color: "#f8fafc", display: "flex", alignItems: "center", gap: "8px" }}>
              <Activity size={18} color="#06b6d4" /> Fleet Real-Time Inference Stream
            </h2>
            <span style={{ fontSize: "12px", color: "#64748b" }}>
              Live scoring updates from background edge pipeline
            </span>
          </div>

          <div style={{ display: "flex", gap: "10px", alignItems: "center", flexWrap: "wrap" }}>
            <div style={{ display: "flex", gap: "6px", alignItems: "center" }}>
              <label style={{ fontSize: "12px", color: "#94a3b8" }}>Filter Machine:</label>
              <select
                value={selectedMachine}
                onChange={(e) => setSelectedMachine(e.target.value)}
                style={{
                  background: "rgba(15, 23, 42, 0.9)",
                  border: "1px solid rgba(255, 255, 255, 0.1)",
                  color: "#f8fafc",
                  padding: "6px 10px",
                  borderRadius: "6px",
                  fontSize: "12px",
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

            <div style={{ display: "flex", gap: "6px", alignItems: "center" }}>
              <label style={{ fontSize: "12px", color: "#94a3b8" }}>Subsystem:</label>
              <select
                value={selectedSubsystem}
                onChange={(e) => setSelectedSubsystem(e.target.value)}
                style={{
                  background: "rgba(15, 23, 42, 0.9)",
                  border: "1px solid rgba(255, 255, 255, 0.1)",
                  color: "#f8fafc",
                  padding: "6px 10px",
                  borderRadius: "6px",
                  fontSize: "12px",
                }}
              >
                <option value="ALL">All Diagnostics</option>
                <option value="TOOL_WEAR">Tool Wear (CNC)</option>
                <option value="BEARING_WEAR">Bearing Health (Pumps/Compressors)</option>
                <option value="ACTUATOR_STRESS">Joint Stress (Robots)</option>
                <option value="HYDRAULIC_SEAL">Hydraulics (Presses/Molding)</option>
              </select>
            </div>
          </div>
        </div>

        <div style={{ overflowX: "auto" }}>
          <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "12px", textAlign: "left" }}>
            <thead>
              <tr style={{ borderBottom: "1px solid rgba(255, 255, 255, 0.08)", color: "#94a3b8", background: "rgba(15, 23, 42, 0.5)" }}>
                <th style={{ padding: "10px 12px" }}>MACHINE</th>
                <th style={{ padding: "10px 12px" }}>STATUS</th>
                <th style={{ padding: "10px 12px" }}>ANOMALY RISK</th>
                <th style={{ padding: "10px 12px" }}>ANOMALY STATE</th>
                <th style={{ padding: "10px 12px" }}>PREDICTED RUL</th>
                <th style={{ padding: "10px 12px" }}>SUBSYSTEM HEALTH</th>
                <th style={{ padding: "10px 12px" }}>LATENCY</th>
                <th style={{ padding: "10px 12px" }}>TIMESTAMP</th>
              </tr>
            </thead>
            <tbody>
              {filteredInferences.length === 0 ? (
                <tr>
                  <td colSpan={8} style={{ textAlign: "center", padding: "24px", color: "#64748b" }}>
                    {loading ? "Streaming live inference predictions..." : "No inference records matching filter"}
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

                  // Compute component health estimate
                  let subLabel = "Nominal";
                  let subColor = "#10b981";
                  if (inf.machine_id.startsWith("CNC")) {
                    subLabel = isAnom ? "Tool Wear Warning" : "Tool Edge Normal";
                    subColor = isAnom ? "#f59e0b" : "#10b981";
                  } else if (inf.machine_id.startsWith("PMP") || inf.machine_id.startsWith("CMP") || inf.machine_id.startsWith("CHL")) {
                    subLabel = isAnom ? "Bearing Fatigue High" : "Bearing Nominal";
                    subColor = isAnom ? "#f43f5e" : "#10b981";
                  } else if (inf.machine_id.startsWith("ROB")) {
                    subLabel = isAnom ? "Joint Actuator Stress" : "Actuators Healthy";
                    subColor = isAnom ? "#f59e0b" : "#10b981";
                  }

                  return (
                    <tr key={inf.result_id} style={{ borderBottom: "1px solid rgba(255, 255, 255, 0.04)" }}>
                      <td style={{ padding: "10px 12px", fontWeight: 700, color: "#f8fafc" }}>
                        {inf.machine_id}
                        <span style={{ fontSize: "10px", color: "#64748b", display: "block" }}>
                          {inf.machine_type}
                        </span>
                      </td>

                      <td style={{ padding: "10px 12px" }}>
                        <span
                          style={{
                            padding: "2px 8px",
                            borderRadius: "4px",
                            fontSize: "10px",
                            fontWeight: 700,
                            background:
                              inf.status === "READY"
                                ? "rgba(16, 185, 129, 0.15)"
                                : "rgba(245, 158, 11, 0.15)",
                            color: inf.status === "READY" ? "#34d399" : "#fbbf24",
                          }}
                        >
                          {inf.status}
                        </span>
                      </td>

                      <td style={{ padding: "10px 12px", minWidth: "140px" }}>
                        <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                          <span style={{ minWidth: "38px", fontWeight: 700, color: isAnom ? "#f87171" : "#cbd5e1", fontFamily: "'JetBrains Mono', monospace" }}>
                            {(score * 100).toFixed(1)}%
                          </span>
                          <div style={{ flex: 1, height: "6px", background: "rgba(15, 23, 42, 0.8)", borderRadius: "9999px", overflow: "hidden" }}>
                            <div
                              style={{
                                height: "100%",
                                width: `${Math.min(100, Math.max(5, score * 100))}%`,
                                background: isAnom ? "#f43f5e" : score > 0.4 ? "#f59e0b" : "#10b981",
                                borderRadius: "9999px",
                              }}
                            />
                          </div>
                        </div>
                      </td>

                      <td style={{ padding: "10px 12px" }}>
                        <span
                          style={{
                            padding: "3px 8px",
                            borderRadius: "9999px",
                            fontSize: "11px",
                            fontWeight: 700,
                            background: isAnom ? "rgba(244, 63, 94, 0.2)" : "rgba(16, 185, 129, 0.15)",
                            color: isAnom ? "#f87171" : "#34d399",
                            border: `1px solid ${isAnom ? "rgba(244, 63, 94, 0.4)" : "rgba(16, 185, 129, 0.3)"}`,
                          }}
                        >
                          {inf.anomaly_label}
                        </span>
                      </td>

                      <td style={{ padding: "10px 12px", fontWeight: 700, color: isLowRul ? "#f43f5e" : "#f8fafc", fontFamily: "'JetBrains Mono', monospace" }}>
                        {inf.predicted_rul_seconds !== null && inf.predicted_rul_seconds !== undefined
                          ? `${inf.predicted_rul_minutes?.toFixed(1)} min (${inf.predicted_rul_seconds?.toFixed(0)}s)`
                          : "Warming up..."}
                      </td>

                      <td style={{ padding: "10px 12px", color: subColor, fontWeight: 600 }}>
                        {subLabel}
                      </td>

                      <td style={{ padding: "10px 12px", color: "#94a3b8", fontFamily: "'JetBrains Mono', monospace" }}>
                        {inf.latency_ms?.total_inference_ms?.toFixed(2) || "0.00"} ms
                      </td>

                      <td style={{ padding: "10px 12px", color: "#64748b", fontSize: "11px", fontFamily: "'JetBrains Mono', monospace" }}>
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
