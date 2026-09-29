import React from "react";

interface StateBadgeProps {
  state: string;
  size?: "sm" | "md" | "lg";
}

export const StateBadge: React.FC<StateBadgeProps> = ({ state, size = "md" }) => {
  const normalized = (state || "OFF").toUpperCase();

  const colorMap: Record<string, { bg: string; text: string; dot: string; label: string }> = {
    RUNNING: { bg: "rgba(16, 185, 129, 0.15)", text: "#10b981", dot: "#10b981", label: "RUNNING" },
    IDLE: { bg: "rgba(6, 182, 212, 0.15)", text: "#06b6d4", dot: "#06b6d4", label: "IDLE" },
    STARTING: { bg: "rgba(245, 158, 11, 0.15)", text: "#f59e0b", dot: "#f59e0b", label: "STARTING" },
    STOPPING: { bg: "rgba(245, 158, 11, 0.15)", text: "#f59e0b", dot: "#f59e0b", label: "STOPPING" },
    MAINTENANCE: { bg: "rgba(168, 85, 247, 0.15)", text: "#a855f7", dot: "#a855f7", label: "MAINTENANCE" },
    FAULT: { bg: "rgba(239, 68, 68, 0.15)", text: "#ef4444", dot: "#ef4444", label: "FAULT" },
    CRITICAL: { bg: "rgba(239, 68, 68, 0.15)", text: "#ef4444", dot: "#ef4444", label: "CRITICAL" },
    WARNING: { bg: "rgba(249, 115, 22, 0.15)", text: "#f97316", dot: "#f97316", label: "WARNING" },
    HEALTHY: { bg: "rgba(16, 185, 129, 0.15)", text: "#10b981", dot: "#10b981", label: "HEALTHY" },
    OFF: { bg: "rgba(100, 116, 139, 0.15)", text: "#94a3b8", dot: "#64748b", label: "OFF" },
  };

  const style = colorMap[normalized] || colorMap.OFF;
  const padding = size === "sm" ? "2px 8px" : size === "lg" ? "6px 14px" : "4px 10px";
  const fontSize = size === "sm" ? "11px" : size === "lg" ? "14px" : "12px";

  return (
    <span
      data-testid={`state-badge-${normalized}`}
      style={{
        display: "inline-flex",
        alignItems: "center",
        gap: "6px",
        padding,
        fontSize,
        fontWeight: 600,
        borderRadius: "9999px",
        backgroundColor: style.bg,
        color: style.text,
        border: `1px solid ${style.text}33`,
        textTransform: "uppercase",
        letterSpacing: "0.05em",
      }}
    >
      <span
        style={{
          width: size === "sm" ? "6px" : "8px",
          height: size === "sm" ? "6px" : "8px",
          borderRadius: "50%",
          backgroundColor: style.dot,
          boxShadow: normalized === "RUNNING" ? `0 0 6px ${style.dot}` : "none",
        }}
      />
      {style.label}
    </span>
  );
};
