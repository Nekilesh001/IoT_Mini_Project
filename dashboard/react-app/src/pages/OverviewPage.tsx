import React, { useState, useEffect } from "react";
import { useFactorySummary } from "../hooks/useFactorySummary";
import { useMachines } from "../hooks/useMachines";
import { useAlerts } from "../hooks/useAlerts";
import { useRealtimeTelemetry } from "../hooks/useRealtimeTelemetry";
import { fetchMLStatus } from "../api/ml";
import { MLSystemStatus } from "../types";
import { MachineCard } from "../components/MachineCard";
import { MetricCard } from "../components/MetricCard";
import { ActiveAlertsPanel } from "../components/ActiveAlertsPanel";
import { Activity, AlertOctagon, ShieldAlert, Cpu, Radio, Sparkles, CheckCircle2 } from "lucide-react";

export const OverviewPage: React.FC = () => {
  const { summary, loading: summaryLoading, error: summaryError, refresh: refreshSummary } = useFactorySummary();
  const { machines, loading: machinesLoading, error: machinesError } = useMachines();
  const { activeAlerts, summary: alertSummary, acknowledgeAlert, resolveAlert } = useAlerts();
  const { latestEvents, status: streamStatus } = useRealtimeTelemetry();
  const [mlStatus, setMlStatus] = useState<MLSystemStatus | null>(null);

  useEffect(() => {
    fetchMLStatus().then(setMlStatus).catch(() => {});
    const interval = setInterval(() => {
      fetchMLStatus().then(setMlStatus).catch(() => {});
    }, 3000);
    return () => clearInterval(interval);
  }, []);

  if (summaryLoading && machinesLoading) {
    return (
      <div style={{ display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", height: "400px", gap: "16px" }}>
        <div style={{ width: "40px", height: "40px", borderRadius: "50%", border: "3px solid #06b6d4", borderTopColor: "transparent", animation: "spin 1s linear infinite" }} />
        <span style={{ fontSize: "14px", color: "#94a3b8" }}>Connecting to Smart Factory Telemetry Ingestion Engine...</span>
      </div>
    );
  }

  if (summaryError && machinesError) {
    return (
      <div
        className="glass-panel"
        style={{
          padding: "32px",
          color: "#fca5a5",
          textAlign: "center",
          maxWidth: "600px",
          margin: "40px auto",
          borderColor: "rgba(244, 63, 94, 0.4)",
        }}
      >
        <AlertOctagon size={36} color="#f43f5e" style={{ margin: "0 auto 12px auto" }} />
        <div style={{ fontSize: "18px", fontWeight: 800, marginBottom: "8px", color: "#fff" }}>Backend Service Disconnected</div>
        <div style={{ fontSize: "13px", color: "#f87171", marginBottom: "20px" }}>{summaryError}</div>
        <button
          onClick={() => refreshSummary()}
          style={{
            background: "linear-gradient(135deg, #e11d48, #f43f5e)",
            color: "#fff",
            border: "none",
            padding: "10px 20px",
            borderRadius: "8px",
            fontWeight: 700,
            cursor: "pointer",
            boxShadow: "0 0 15px rgba(244, 63, 94, 0.4)",
          }}
        >
          Retry Connection
        </button>
      </div>
    );
  }

  const states = summary?.states || { running: 0, idle: 0, starting: 0, stopping: 0, maintenance: 0, off: 0 };

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "28px" }}>
      {/* Title Bar with Live SSE Indicator */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-end", flexWrap: "wrap", gap: "16px" }}>
        <div>
          <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
            <h1 style={{ fontSize: "28px", fontWeight: 800, color: "#f8fafc", margin: 0, letterSpacing: "-0.02em" }}>
              Plant Operations & Fleet Telemetry
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
                background: streamStatus === "connected" ? "rgba(16, 185, 129, 0.15)" : "rgba(245, 158, 11, 0.15)",
                color: streamStatus === "connected" ? "#34d399" : "#fbbf24",
                border: `1px solid ${streamStatus === "connected" ? "rgba(16, 185, 129, 0.3)" : "rgba(245, 158, 11, 0.3)"}`,
              }}
            >
              <span className="live-pulse-dot" />
              {streamStatus === "connected" ? "LIVE SSE STREAM" : "CONNECTING"}
            </span>
          </div>
          <p style={{ fontSize: "14px", color: "#94a3b8", margin: "6px 0 0 0" }}>
            Real-time physical telemetry, edge ML predictive maintenance, and multi-protocol monitoring across 12 production nodes.
          </p>
        </div>

        <div style={{ display: "flex", gap: "12px", alignItems: "center", flexWrap: "wrap" }}>
          <div
            style={{
              background: "rgba(15, 23, 42, 0.7)",
              border: "1px solid rgba(255, 255, 255, 0.08)",
              borderRadius: "8px",
              padding: "6px 12px",
              fontSize: "12px",
              color: "#94a3b8",
            }}
          >
            Total Records: <strong style={{ color: "#38bdf8", fontFamily: "'JetBrains Mono', monospace" }}>{summary?.total_telemetry_records.toLocaleString() || 0}</strong>
          </div>
        </div>
      </div>

      {/* Summary Metrics Grid */}
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))",
          gap: "16px",
        }}
      >
        <MetricCard label="Total Equipment" value={summary?.total_machines || 12} accentColor="#06b6d4" />
        <MetricCard label="Active Running" value={states.running} accentColor="#10b981" description="Full Production" />
        <MetricCard label="Operational Alerts" value={alertSummary?.active_total || 0} accentColor={alertSummary && alertSummary.active_total > 0 ? "#f43f5e" : "#10b981"} description={alertSummary && alertSummary.active_total > 0 ? `${alertSummary.critical_count} Critical` : "Nominal"} />
        <MetricCard label="ML Anomalies" value={mlStatus?.fleet_summary?.active_anomalous_machines?.length || 0} accentColor={mlStatus?.fleet_summary?.active_anomalous_machines?.length ? "#f59e0b" : "#10b981"} description="Isolation Forest" />
        <MetricCard label="Critical RUL" value={mlStatus?.fleet_summary?.low_rul_machines?.length || 0} accentColor={mlStatus?.fleet_summary?.low_rul_machines?.length ? "#f43f5e" : "#10b981"} description="HistGBM <10m" />
        <MetricCard label="Edge Latency" value={mlStatus?.metrics?.total_inference_ms?.mean ? `${mlStatus.metrics.total_inference_ms.mean}ms` : "0.0ms"} accentColor="#8b5cf6" description={mlStatus?.runtime_backend || "ONNX"} />
      </div>

      {/* Active Operational Alarms */}
      <section>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "12px" }}>
          <h2 style={{ fontSize: "17px", fontWeight: 700, color: "#f8fafc", margin: 0, display: "flex", alignItems: "center", gap: "8px" }}>
            <ShieldAlert size={18} color={activeAlerts.length > 0 ? "#f87171" : "#10b981"} /> Live Operational Alarms & Degradation Events
          </h2>
          <span style={{ fontSize: "12px", color: "#64748b" }}>
            Real-time rule & ML threshold evaluations
          </span>
        </div>
        <ActiveAlertsPanel
          alerts={activeAlerts}
          summary={alertSummary}
          onAcknowledge={acknowledgeAlert}
          onResolve={resolveAlert}
        />
      </section>

      {/* Machine Fleet Grid */}
      <section>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "16px" }}>
          <div>
            <h2 style={{ fontSize: "18px", fontWeight: 700, color: "#f8fafc", margin: 0 }}>
              Production Fleet Status (12 Equipment Nodes)
            </h2>
            <span style={{ fontSize: "12px", color: "#64748b" }}>
              Live telemetry updates in real time via Server-Sent Events (SSE)
            </span>
          </div>
        </div>

        <div
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(auto-fill, minmax(340px, 1fr))",
            gap: "20px",
          }}
        >
          {machines.map((machine) => (
            <MachineCard
              key={machine.machine_id}
              machine={machine}
              liveEvent={latestEvents[machine.machine_id]}
            />
          ))}
        </div>
      </section>
    </div>
  );
};
