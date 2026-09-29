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
  accentColor = "#06b6d4",
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
        background: "linear-gradient(135deg, rgba(30, 41, 59, 0.7), rgba(15, 23, 42, 0.8))",
        backdropFilter: "blur(12px)",
        border: "1px solid rgba(255, 255, 255, 0.08)",
        borderLeft: `3px solid ${accentColor}`,
        borderRadius: "12px",
        padding: "16px 18px",
        display: "flex",
        flexDirection: "column",
        justifyContent: "space-between",
        minWidth: "160px",
        boxShadow: "0 6px 16px rgba(0, 0, 0, 0.3)",
        transition: "all 0.2s ease",
      }}
      onMouseEnter={(e) => {
        e.currentTarget.style.borderColor = accentColor;
        e.currentTarget.style.transform = "translateY(-2px)";
      }}
      onMouseLeave={(e) => {
        e.currentTarget.style.borderColor = "rgba(255, 255, 255, 0.08)";
        e.currentTarget.style.borderLeft = `3px solid ${accentColor}`;
        e.currentTarget.style.transform = "translateY(0)";
      }}
    >
      <div style={{ fontSize: "10px", fontWeight: 700, color: "#94a3b8", letterSpacing: "0.06em", marginBottom: "8px" }}>
        {cleanLabel}
      </div>
      <div style={{ display: "flex", alignItems: "baseline", gap: "6px" }}>
        <span style={{ fontSize: "24px", fontWeight: 800, color: "#f8fafc", fontFamily: "'JetBrains Mono', monospace", letterSpacing: "-0.02em" }}>
          {formattedValue}
        </span>
        {unit && (
          <span style={{ fontSize: "12px", fontWeight: 700, color: accentColor, fontFamily: "'JetBrains Mono', monospace" }}>
            {unit}
          </span>
        )}
      </div>
      {description && (
        <div style={{ fontSize: "11px", color: "#64748b", marginTop: "6px", fontWeight: 500 }}>
          {description}
        </div>
      )}
    </div>
  );
};
