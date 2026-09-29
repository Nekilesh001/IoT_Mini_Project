import React from "react";
import { AlertItem, AlertSummary } from "../types";
import { AlertCard } from "./AlertCard";
import { AlertOctagon, CheckCircle2, ShieldAlert } from "lucide-react";

interface ActiveAlertsPanelProps {
  alerts: AlertItem[];
  summary?: AlertSummary | null;
  onAcknowledge?: (alertId: string) => Promise<any>;
  onResolve?: (alertId: string, notes?: string) => Promise<any>;
}

export const ActiveAlertsPanel: React.FC<ActiveAlertsPanelProps> = ({
  alerts,
  summary,
  onAcknowledge,
  onResolve,
}) => {
  if (alerts.length === 0) {
    return (
      <div
        style={{
          background: "rgba(16, 185, 129, 0.06)",
          border: "1px solid rgba(16, 185, 129, 0.2)",
          borderRadius: "12px",
          padding: "20px 24px",
          display: "flex",
          alignItems: "center",
          gap: "14px",
          color: "#34d399",
        }}
      >
        <CheckCircle2 size={24} color="#10b981" />
        <div>
          <div style={{ fontSize: "14px", fontWeight: 700, color: "#f8fafc" }}>
            All Systems Operating Normally
          </div>
          <div style={{ fontSize: "12px", color: "#94a3b8", marginTop: "2px" }}>
            No active un-resolved threshold violations across the 12 equipment nodes.
          </div>
        </div>
      </div>
    );
  }

  const criticalCount = alerts.filter((a) => a.severity === "CRITICAL").length;
  const warningCount = alerts.filter((a) => a.severity === "WARNING").length;

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
      {/* Active Alert Banner */}
      <div
        style={{
          background: criticalCount > 0 ? "rgba(239, 68, 68, 0.15)" : "rgba(249, 115, 22, 0.12)",
          border: `1px solid ${criticalCount > 0 ? "rgba(239, 68, 68, 0.4)" : "rgba(249, 115, 22, 0.4)"}`,
          borderRadius: "12px",
          padding: "16px 20px",
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          flexWrap: "wrap",
          gap: "12px",
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
          <AlertOctagon size={24} color={criticalCount > 0 ? "#f87171" : "#fb923c"} />
          <div>
            <div style={{ fontSize: "15px", fontWeight: 800, color: "#f8fafc" }}>
              Active Operational Alerts ({alerts.length})
            </div>
            <div style={{ fontSize: "12px", color: "#cbd5e1", marginTop: "2px" }}>
              {criticalCount} Critical &bull; {warningCount} Warning &bull; Immediate operator attention required
            </div>
          </div>
        </div>
      </div>

      {/* Alert Cards List */}
      <div style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
        {alerts.map((alert) => (
          <AlertCard
            key={alert.alert_id}
            alert={alert}
            onAcknowledge={onAcknowledge}
            onResolve={onResolve}
          />
        ))}
      </div>
    </div>
  );
};
