import React from "react";
import { AlertSeverity } from "../types";
import { AlertOctagon, AlertTriangle, Info } from "lucide-react";

interface AlertBadgeProps {
  severity: AlertSeverity | string;
  size?: "sm" | "md" | "lg";
}

export const AlertBadge: React.FC<AlertBadgeProps> = ({ severity, size = "md" }) => {
  const sev = String(severity).toUpperCase();

  let bg = "rgba(100, 116, 139, 0.2)";
  let border = "rgba(100, 116, 139, 0.4)";
  let color = "#94a3b8";
  let icon = <Info size={size === "sm" ? 12 : 14} />;

  if (sev === "CRITICAL") {
    bg = "rgba(239, 68, 68, 0.2)";
    border = "rgba(239, 68, 68, 0.5)";
    color = "#f87171";
    icon = <AlertOctagon size={size === "sm" ? 12 : 14} />;
  } else if (sev === "WARNING") {
    bg = "rgba(249, 115, 22, 0.2)";
    border = "rgba(249, 115, 22, 0.5)";
    color = "#fb923c";
    icon = <AlertTriangle size={size === "sm" ? 12 : 14} />;
  } else if (sev === "INFO") {
    bg = "rgba(56, 189, 248, 0.2)";
    border = "rgba(56, 189, 248, 0.4)";
    color = "#38bdf8";
    icon = <Info size={size === "sm" ? 12 : 14} />;
  }

  const fontSize = size === "sm" ? "10px" : size === "lg" ? "13px" : "11px";
  const padding = size === "sm" ? "2px 6px" : size === "lg" ? "6px 12px" : "4px 8px";

  return (
    <span
      style={{
        display: "inline-flex",
        alignItems: "center",
        gap: "4px",
        background: bg,
        border: `1px solid ${border}`,
        color,
        borderRadius: "4px",
        padding,
        fontSize,
        fontWeight: 700,
        textTransform: "uppercase",
        letterSpacing: "0.04em",
      }}
    >
      {icon}
      {sev}
    </span>
  );
};
