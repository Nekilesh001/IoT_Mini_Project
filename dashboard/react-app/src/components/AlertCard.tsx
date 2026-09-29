import React, { useState } from "react";
import { Link } from "react-router-dom";
import { AlertItem } from "../types";
import { AlertBadge } from "./AlertBadge";
import { Check, CheckCircle2, Clock, ExternalLink, RefreshCw } from "lucide-react";

interface AlertCardProps {
  alert: AlertItem;
  onAcknowledge?: (alertId: string) => Promise<any>;
  onResolve?: (alertId: string, notes?: string) => Promise<any>;
}

export const AlertCard: React.FC<AlertCardProps> = ({
  alert,
  onAcknowledge,
  onResolve,
}) => {
  const [acting, setActing] = useState(false);

  const isCritical = alert.severity === "CRITICAL";
  const isAcked = alert.status === "ACKNOWLEDGED";
  const isResolved = alert.status === "RESOLVED";

  const handleAck = async (e: React.MouseEvent) => {
    e.preventDefault();
    if (!onAcknowledge) return;
    setActing(true);
    try {
      await onAcknowledge(alert.alert_id);
    } finally {
      setActing(false);
    }
  };

  const handleResolve = async (e: React.MouseEvent) => {
    e.preventDefault();
    if (!onResolve) return;
    setActing(true);
    try {
      await onResolve(alert.alert_id, "Operator resolved issue");
    } finally {
      setActing(false);
    }
  };

  return (
    <div
      style={{
        background: isCritical
          ? "rgba(239, 68, 68, 0.08)"
          : isAcked
          ? "rgba(30, 41, 59, 0.4)"
          : "rgba(249, 115, 22, 0.08)",
        border: `1px solid ${
          isCritical
            ? "rgba(239, 68, 68, 0.35)"
            : isAcked
            ? "rgba(255, 255, 255, 0.08)"
            : "rgba(249, 115, 22, 0.3)"
        }`,
        borderRadius: "10px",
        padding: "16px 20px",
        display: "flex",
        flexDirection: "column",
        gap: "12px",
        transition: "all 0.2s ease",
      }}
    >
      {/* Header */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", flexWrap: "wrap", gap: "10px" }}>
        <div style={{ display: "flex", alignItems: "center", gap: "10px", flexWrap: "wrap" }}>
          <AlertBadge severity={alert.severity} size="sm" />
          <Link
            to={`/machines/${encodeURIComponent(alert.machine_id)}`}
            style={{
              fontSize: "14px",
              fontWeight: 800,
              color: "#38bdf8",
              textDecoration: "none",
              display: "inline-flex",
              alignItems: "center",
              gap: "4px",
            }}
          >
            {alert.machine_id} <ExternalLink size={12} />
          </Link>
          <span style={{ fontSize: "12px", color: "#94a3b8" }}>
            ({alert.machine_type.replace(/_/g, " ")})
          </span>
          <span
            style={{
              fontSize: "11px",
              fontFamily: "monospace",
              color: isAcked ? "#a855f7" : isResolved ? "#10b981" : "#f87171",
              background: "rgba(15, 23, 42, 0.6)",
              padding: "2px 6px",
              borderRadius: "4px",
            }}
          >
            STATUS: {alert.status}
          </span>
        </div>

        <div style={{ display: "flex", alignItems: "center", gap: "8px", fontSize: "11px", color: "#64748b" }}>
          <Clock size={12} />
          <span>{new Date(alert.triggered_at).toLocaleTimeString()}</span>
        </div>
      </div>

      {/* Title & Description */}
      <div>
        <div style={{ fontSize: "14px", fontWeight: 700, color: "#f8fafc" }}>
          {alert.title}
        </div>
        <div style={{ fontSize: "12px", color: "#94a3b8", marginTop: "4px", lineHeight: "1.4" }}>
          {alert.description}
        </div>
      </div>

      {/* Triggering Measurements */}
      <div
        style={{
          background: "rgba(15, 23, 42, 0.6)",
          borderRadius: "6px",
          padding: "8px 12px",
          display: "flex",
          gap: "16px",
          flexWrap: "wrap",
          fontSize: "11px",
        }}
      >
        <span style={{ color: "#64748b", fontWeight: 600 }}>TRIGGER VALUES:</span>
        {Object.entries(alert.triggering_measurements || {}).map(([k, v]) => (
          <span key={k} style={{ color: "#e2e8f0", fontFamily: "monospace" }}>
            <strong>{k}:</strong> {typeof v === "number" ? Number(v).toFixed(2) : String(v)}
          </span>
        ))}
        {alert.occurrence_count > 1 && (
          <span style={{ marginLeft: "auto", color: "#f59e0b", fontWeight: 600 }}>
            Active ({alert.occurrence_count} ticks)
          </span>
        )}
      </div>

      {/* Actions */}
      {!isResolved && (onAcknowledge || onResolve) && (
        <div style={{ display: "flex", justifyContent: "flex-end", gap: "8px", marginTop: "4px" }}>
          {!isAcked && onAcknowledge && (
            <button
              onClick={handleAck}
              disabled={acting}
              style={{
                background: "rgba(168, 85, 247, 0.2)",
                border: "1px solid rgba(168, 85, 247, 0.4)",
                color: "#c084fc",
                padding: "6px 12px",
                borderRadius: "6px",
                fontSize: "11px",
                fontWeight: 600,
                cursor: "pointer",
                display: "inline-flex",
                alignItems: "center",
                gap: "4px",
              }}
            >
              <Check size={12} /> Acknowledge
            </button>
          )}
          {onResolve && (
            <button
              onClick={handleResolve}
              disabled={acting}
              style={{
                background: "rgba(16, 185, 129, 0.2)",
                border: "1px solid rgba(16, 185, 129, 0.4)",
                color: "#34d399",
                padding: "6px 12px",
                borderRadius: "6px",
                fontSize: "11px",
                fontWeight: 600,
                cursor: "pointer",
                display: "inline-flex",
                alignItems: "center",
                gap: "4px",
              }}
            >
              <CheckCircle2 size={12} /> Resolve
            </button>
          )}
        </div>
      )}
    </div>
  );
};
