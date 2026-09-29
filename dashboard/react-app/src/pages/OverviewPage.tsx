import { useState, useEffect } from "react";
import { useFactorySummary } from "../hooks/useFactorySummary";
import { useMachines } from "../hooks/useMachines";
import { useAlerts } from "../hooks/useAlerts";
import { fetchMLStatus } from "../api/ml";
import { MLSystemStatus } from "../types";
import { MachineCard } from "../components/MachineCard";
import { MetricCard } from "../components/MetricCard";
import { ActiveAlertsPanel } from "../components/ActiveAlertsPanel";
import { Activity, CheckCircle2, AlertTriangle, AlertOctagon, Wrench, PowerOff, Database, ShieldAlert, Brain } from "lucide-react";

export const OverviewPage: React.FC = () => {
  const { summary, loading: summaryLoading, error: summaryError, refresh: refreshSummary } = useFactorySummary();
  const { machines, loading: machinesLoading, error: machinesError } = useMachines();
  const { activeAlerts, summary: alertSummary, acknowledgeAlert, resolveAlert } = useAlerts();
  const [mlStatus, setMlStatus] = useState<MLSystemStatus | null>(null);

  useEffect(() => {
    fetchMLStatus().then(setMlStatus).catch(() => {});
    const interval = setInterval(() => {
      fetchMLStatus().then(setMlStatus).catch(() => {});
    }, 4000);
    return () => clearInterval(interval);
  }, []);


  if (summaryLoading && machinesLoading) {
    return (
      <div style={{ display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", height: "400px", gap: "16px" }}>
        <div style={{ width: "36px", height: "36px", borderRadius: "50%", border: "3px solid #38bdf8", borderTopColor: "transparent", animation: "spin 1s linear infinite" }} />
        <span style={{ fontSize: "14px", color: "#94a3b8" }}>Connecting to Smart Factory API...</span>
      </div>
    );
  }

  if (summaryError && machinesError) {
    return (
      <div
        style={{
          background: "rgba(239, 68, 68, 0.1)",
          border: "1px solid rgba(239, 68, 68, 0.3)",
          borderRadius: "12px",
          padding: "24px",
          color: "#fca5a5",
          textAlign: "center",
        }}
      >
        <AlertOctagon size={32} style={{ margin: "0 auto 12px auto" }} />
        <div style={{ fontSize: "16px", fontWeight: 700, marginBottom: "6px" }}>API Connection Error</div>
        <div style={{ fontSize: "13px", color: "#f87171", marginBottom: "16px" }}>{summaryError}</div>
        <button
          onClick={() => refreshSummary()}
          style={{ background: "#ef4444", color: "#fff", border: "none", padding: "8px 16px", borderRadius: "6px", fontWeight: 600, cursor: "pointer" }}
        >
          Retry Connection
        </button>
      </div>
    );
  }

  const states = summary?.states || { running: 0, idle: 0, starting: 0, stopping: 0, maintenance: 0, off: 0 };
  const health = summary?.health || { healthy: 0, warning: 0, critical: 0 };

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "32px" }}>
      {/* Title Bar */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-end", flexWrap: "wrap", gap: "16px" }}>
        <div>
          <h1 style={{ fontSize: "28px", fontWeight: 800, color: "#f8fafc", margin: 0, letterSpacing: "-0.02em" }}>
            Plant Overview & Machine Fleet
          </h1>
          <p style={{ fontSize: "14px", color: "#94a3b8", margin: "6px 0 0 0" }}>
            Real-time telemetry and operational state for 12 heterogeneous production machines.
          </p>
        </div>
        <div style={{ display: "flex", gap: "8px", alignItems: "center" }}>
          <span style={{ fontSize: "12px", color: "#64748b" }}>
            Total Stored Telemetry: <strong style={{ color: "#38bdf8", fontFamily: "monospace" }}>{summary?.total_telemetry_records.toLocaleString() || 0}</strong> records
          </span>
        </div>
      </div>

      {/* Summary Metrics Banner */}
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))",
          gap: "16px",
        }}
      >
        <MetricCard label="Total Machines" value={summary?.total_machines || 12} accentColor="#38bdf8" />
        <MetricCard label="Running" value={states.running} accentColor="#10b981" description="Active production" />
        <MetricCard label="Active Alerts" value={alertSummary?.active_total || 0} accentColor={alertSummary && alertSummary.active_total > 0 ? "#ef4444" : "#10b981"} description={alertSummary && alertSummary.active_total > 0 ? `${alertSummary.critical_count} Critical` : "Normal operation"} />
        <MetricCard label="ML Anomalies" value={mlStatus?.fleet_summary?.active_anomalous_machines?.length || 0} accentColor={mlStatus?.fleet_summary?.active_anomalous_machines?.length ? "#f59e0b" : "#10b981"} description="Isolation Forest" />
        <MetricCard label="Critical RUL" value={mlStatus?.fleet_summary?.low_rul_machines?.length || 0} accentColor={mlStatus?.fleet_summary?.low_rul_machines?.length ? "#ef4444" : "#10b981"} description="<30m Remaining" />
        <MetricCard label="ML Latency" value={mlStatus?.metrics?.total_inference_ms?.mean ? `${mlStatus.metrics.total_inference_ms.mean}ms` : "0.0ms"} accentColor="#818cf8" description={mlStatus?.runtime_backend || "SKLEARN"} />
      </div>

      {/* Active Operational Alarms */}
      <section>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "12px" }}>
          <h2 style={{ fontSize: "18px", fontWeight: 700, color: "#f8fafc", margin: 0, display: "flex", alignItems: "center", gap: "8px" }}>
            <ShieldAlert size={18} color={activeAlerts.length > 0 ? "#f87171" : "#10b981"} /> Live Operational Alarms
          </h2>
          <span style={{ fontSize: "12px", color: "#64748b" }}>
            Real-time rule-based threshold evaluation
          </span>
        </div>
        <ActiveAlertsPanel
          alerts={activeAlerts}
          summary={alertSummary}
          onAcknowledge={acknowledgeAlert}
          onResolve={resolveAlert}
        />
      </section>

      {/* Machine Status Grid */}

      <section>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "16px" }}>
          <h2 style={{ fontSize: "18px", fontWeight: 700, color: "#f8fafc", margin: 0 }}>
            Machine Fleet (12 Equipment Nodes)
          </h2>
          <span style={{ fontSize: "12px", color: "#64748b" }}>
            Click card for live signals & historical trends
          </span>
        </div>

        <div
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(auto-fill, minmax(320px, 1fr))",
            gap: "20px",
          }}
        >
          {machines.map((machine) => (
            <MachineCard key={machine.machine_id} machine={machine} />
          ))}
        </div>
      </section>
    </div>
  );
};
