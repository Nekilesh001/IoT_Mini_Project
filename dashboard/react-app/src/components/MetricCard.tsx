import React from "react";

interface MetricCardProps {
  label: string;
  value: any;
  unit?: string;
  description?: string;
  accentColor?: string;
}

export const MetricCard: React.FC<MetricCardProps> = ({
  label,
  value,
  unit = "",
  description,
  accentColor = "#38bdf8",
}) => {
  const formattedValue =
    typeof value === "number"
      ? Number.isInteger(value)
        ? value.toLocaleString()
        : value.toFixed(2)
      : value !== undefined && value !== null
      ? String(value)
      : "—";

  const cleanLabel = label.replace(/_/g, " ").toUpperCase();

  return (
    <div
      style={{
        background: "rgba(30, 41, 59, 0.6)",
        backdropFilter: "blur(8px)",
        border: "1px solid rgba(255, 255, 255, 0.08)",
        borderRadius: "10px",
        padding: "16px",
        display: "flex",
        flexDirection: "column",
        justifyContent: "space-between",
        minWidth: "160px",
        boxShadow: "0 4px 12px rgba(0, 0, 0, 0.2)",
      }}
    >
      <div style={{ fontSize: "11px", fontWeight: 600, color: "#94a3b8", letterSpacing: "0.05em", marginBottom: "8px" }}>
        {cleanLabel}
      </div>
      <div style={{ display: "flex", alignItems: "baseline", gap: "6px" }}>
        <span style={{ fontSize: "24px", fontWeight: 700, color: "#f8fafc", fontFamily: "monospace" }}>
          {formattedValue}
        </span>
        {unit && (
          <span style={{ fontSize: "12px", fontWeight: 600, color: accentColor }}>
            {unit}
          </span>
        )}
      </div>
      {description && (
        <div style={{ fontSize: "11px", color: "#64748b", marginTop: "6px", lineHeight: 1.3 }}>
          {description}
        </div>
      )}
    </div>
  );
};
