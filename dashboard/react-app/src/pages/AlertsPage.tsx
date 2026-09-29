import React, { useState, useEffect } from "react";
import { useAlerts } from "../hooks/useAlerts";
import { alertsApi } from "../api/alerts";
import { AlertItem, FaultScenario } from "../types";
import { MetricCard } from "../components/MetricCard";
import { AlertCard } from "../components/AlertCard";
import { ActiveAlertsPanel } from "../components/ActiveAlertsPanel";
import {
  ShieldAlert,
  Play,
  Square,
  Filter,
  Search,
  AlertTriangle,
  History,
  Activity,
  Zap,
} from "lucide-react";

export const AlertsPage: React.FC = () => {
  const { activeAlerts, summary, loading, acknowledgeAlert, resolveAlert, refresh } =
    useAlerts();

  const [allAlerts, setAllAlerts] = useState<AlertItem[]>([]);
  const [scenarios, setScenarios] = useState<FaultScenario[]>([]);
  const [selectedSeverity, setSelectedSeverity] = useState<string>("ALL");
  const [selectedStatus, setSelectedStatus] = useState<string>("ALL");
  const [triggeringScenario, setTriggeringScenario] = useState<string | null>(null);

  const fetchHistory = async () => {
    try {
      const data = await alertsApi.getAlerts({ limit: 100 });
      setAllAlerts(data);
    } catch (e) {
      console.error("Failed to load alert history", e);
    }
  };

  const fetchScenarios = async () => {
    try {
      const scens = await alertsApi.getScenarios();
      setScenarios(scens);
    } catch (e) {
      console.error("Failed to load fault scenarios", e);
    }
  };

  useEffect(() => {
    fetchHistory();
    fetchScenarios();
    const intv = setInterval(() => {
      fetchHistory();
      fetchScenarios();
    }, 2500);
    return () => clearInterval(intv);
  }, []);

  const handleStartScenario = async (scenarioId: string) => {
    setTriggeringScenario(scenarioId);
    try {
      await alertsApi.startScenario(scenarioId);
      await fetchScenarios();
      refresh();
    } finally {
      setTriggeringScenario(null);
    }
  };

  const handleStopScenario = async (scenarioId: string) => {
    setTriggeringScenario(scenarioId);
    try {
      await alertsApi.stopScenario(scenarioId);
      await fetchScenarios();
      refresh();
    } finally {
      setTriggeringScenario(null);
    }
  };

  const filteredHistory = allAlerts.filter((a) => {
    const matchSev = selectedSeverity === "ALL" || a.severity === selectedSeverity;
    const matchStat = selectedStatus === "ALL" || a.status === selectedStatus;
    return matchSev && matchStat;
  });

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "28px" }}>
      {/* Page Header */}
      <div>
        <div style={{ display: "flex", alignItems: "center", gap: "8px", color: "#f87171", fontSize: "12px", fontWeight: 700, textTransform: "uppercase", letterSpacing: "0.08em", marginBottom: "4px" }}>
          <ShieldAlert size={14} /> Operations & Safety Monitoring
        </div>
        <h1 style={{ fontSize: "28px", fontWeight: 800, color: "#f8fafc", margin: 0, letterSpacing: "-0.02em" }}>
          Alerts & Fault Management
        </h1>
        <p style={{ fontSize: "14px", color: "#94a3b8", margin: "6px 0 0 0" }}>
          Rule-based operational alarms, threshold violations, and simulation fault injection console.
        </p>
      </div>

      {/* Summary KPI Cards */}
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))",
          gap: "16px",
        }}
      >
        <MetricCard label="Active Alerts" value={summary?.active_total || 0} accentColor="#ef4444" description="Un-resolved alarms" />
        <MetricCard label="Critical" value={summary?.critical_count || 0} accentColor="#f87171" description="Immediate safety/loss" />
        <MetricCard label="Warning" value={summary?.warning_count || 0} accentColor="#fb923c" description="Degradation / bounds" />
        <MetricCard label="Acknowledged" value={summary?.acknowledged_total || 0} accentColor="#c084fc" description="Operator in-progress" />
        <MetricCard label="Total History" value={summary?.total_historical_alerts || 0} accentColor="#38bdf8" description="All-time recorded" />
      </div>

      {/* Active Alerts Panel */}
      <section>
        <h2 style={{ fontSize: "18px", fontWeight: 700, color: "#f8fafc", marginBottom: "14px", display: "flex", alignItems: "center", gap: "8px" }}>
          <Activity size={18} color="#f87171" /> Active Operational Alarms
        </h2>
        <ActiveAlertsPanel
          alerts={activeAlerts}
          summary={summary}
          onAcknowledge={acknowledgeAlert}
          onResolve={resolveAlert}
        />
      </section>

      {/* Interactive Fault Scenario Injection Console */}
      <section
        style={{
          background: "rgba(30, 41, 59, 0.4)",
          border: "1px solid rgba(255, 255, 255, 0.08)",
          borderRadius: "12px",
          padding: "24px",
          display: "flex",
          flexDirection: "column",
          gap: "16px",
        }}
      >
        <div>
          <h2 style={{ fontSize: "18px", fontWeight: 700, color: "#f8fafc", margin: 0, display: "flex", alignItems: "center", gap: "8px" }}>
            <Zap size={18} color="#38bdf8" /> Fault Injection Testing Console
          </h2>
          <p style={{ fontSize: "13px", color: "#94a3b8", margin: "4px 0 0 0" }}>
            Trigger realistic physical anomalies on the factory floor to verify edge propagation and rule-based alert generation.
          </p>
        </div>

        <div
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(auto-fill, minmax(300px, 1fr))",
            gap: "14px",
          }}
        >
          {scenarios.map((scen) => {
            const isActive = scen.state === "ACTIVE";
            const isPending = triggeringScenario === scen.scenario_id;

            return (
              <div
                key={scen.scenario_id}
                style={{
                  background: isActive ? "rgba(239, 68, 68, 0.1)" : "rgba(15, 23, 42, 0.6)",
                  border: `1px solid ${isActive ? "rgba(239, 68, 68, 0.4)" : "rgba(255, 255, 255, 0.06)"}`,
                  borderRadius: "8px",
                  padding: "16px",
                  display: "flex",
                  flexDirection: "column",
                  justifyContent: "space-between",
                  gap: "12px",
                }}
              >
                <div>
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "6px" }}>
                    <span style={{ fontSize: "14px", fontWeight: 700, color: "#f8fafc" }}>
                      {scen.title}
                    </span>
                    <span
                      style={{
                        fontSize: "10px",
                        fontWeight: 700,
                        padding: "2px 6px",
                        borderRadius: "4px",
                        color: isActive ? "#f87171" : "#64748b",
                        background: isActive ? "rgba(239, 68, 68, 0.2)" : "rgba(255, 255, 255, 0.05)",
                      }}
                    >
                      {isActive ? "ACTIVE" : "IDLE"}
                    </span>
                  </div>
                  <div style={{ fontSize: "11px", color: "#38bdf8", fontWeight: 600 }}>
                    Target: {scen.machine_id} ({scen.machine_type.replace(/_/g, " ")})
                  </div>
                  <div style={{ fontSize: "12px", color: "#94a3b8", marginTop: "6px", lineHeight: "1.3" }}>
                    {scen.description}
                  </div>
                </div>

                <div style={{ display: "flex", justifyContent: "flex-end" }}>
                  {isActive ? (
                    <button
                      onClick={() => handleStopScenario(scen.scenario_id)}
                      disabled={isPending}
                      style={{
                        background: "#10b981",
                        color: "#fff",
                        border: "none",
                        padding: "6px 14px",
                        borderRadius: "6px",
                        fontSize: "12px",
                        fontWeight: 600,
                        cursor: "pointer",
                        display: "inline-flex",
                        alignItems: "center",
                        gap: "6px",
                      }}
                    >
                      <Square size={12} /> Clear Fault (Recover)
                    </button>
                  ) : (
                    <button
                      onClick={() => handleStartScenario(scen.scenario_id)}
                      disabled={isPending}
                      style={{
                        background: "#ef4444",
                        color: "#fff",
                        border: "none",
                        padding: "6px 14px",
                        borderRadius: "6px",
                        fontSize: "12px",
                        fontWeight: 600,
                        cursor: "pointer",
                        display: "inline-flex",
                        alignItems: "center",
                        gap: "6px",
                      }}
                    >
                      <Play size={12} /> Inject Fault
                    </button>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      </section>

      {/* Historical Audit Log */}
      <section style={{ display: "flex", flexDirection: "column", gap: "14px" }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: "12px" }}>
          <h2 style={{ fontSize: "18px", fontWeight: 700, color: "#f8fafc", margin: 0, display: "flex", alignItems: "center", gap: "8px" }}>
            <History size={18} color="#38bdf8" /> Alert Audit & Resolution Log ({filteredHistory.length})
          </h2>

          <div style={{ display: "flex", gap: "10px", alignItems: "center" }}>
            {/* Severity Filter */}
            <select
              value={selectedSeverity}
              onChange={(e) => setSelectedSeverity(e.target.value)}
              style={{
                background: "rgba(15, 23, 42, 0.8)",
                border: "1px solid rgba(255, 255, 255, 0.1)",
                borderRadius: "6px",
                color: "#f8fafc",
                fontSize: "12px",
                padding: "6px 10px",
                outline: "none",
                cursor: "pointer",
              }}
            >
              <option value="ALL">All Severities</option>
              <option value="CRITICAL">Critical</option>
              <option value="WARNING">Warning</option>
              <option value="INFO">Info</option>
            </select>

            {/* Status Filter */}
            <select
              value={selectedStatus}
              onChange={(e) => setSelectedStatus(e.target.value)}
              style={{
                background: "rgba(15, 23, 42, 0.8)",
                border: "1px solid rgba(255, 255, 255, 0.1)",
                borderRadius: "6px",
                color: "#f8fafc",
                fontSize: "12px",
                padding: "6px 10px",
                outline: "none",
                cursor: "pointer",
              }}
            >
              <option value="ALL">All Statuses</option>
              <option value="OPEN">Open</option>
              <option value="ACKNOWLEDGED">Acknowledged</option>
              <option value="RESOLVED">Resolved</option>
            </select>
          </div>
        </div>

        {filteredHistory.length === 0 ? (
          <div style={{ background: "rgba(30, 41, 59, 0.3)", padding: "32px", borderRadius: "8px", textAlign: "center", color: "#64748b" }}>
            No matching alert history records found.
          </div>
        ) : (
          <div style={{ display: "flex", flexDirection: "column", gap: "10px" }}>
            {filteredHistory.map((alert) => (
              <AlertCard
                key={alert.alert_id}
                alert={alert}
                onAcknowledge={acknowledgeAlert}
                onResolve={resolveAlert}
              />
            ))}
          </div>
        )}
      </section>
    </div>
  );
};
