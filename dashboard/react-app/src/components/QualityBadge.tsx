import React from "react";

interface QualityBadgeProps {
  quality: string;
}

export const QualityBadge: React.FC<QualityBadgeProps> = ({ quality }) => {
  const norm = (quality || "GOOD").toUpperCase();
  const colorMap: Record<string, { bg: string; text: string }> = {
    GOOD: { bg: "rgba(16, 185, 129, 0.15)", text: "#10b981" },
    BAD: { bg: "rgba(239, 68, 68, 0.15)", text: "#ef4444" },
    STALE: { bg: "rgba(245, 158, 11, 0.15)", text: "#f59e0b" },
    MISSING: { bg: "rgba(244, 63, 94, 0.15)", text: "#f43f5e" },
    OUT_OF_RANGE: { bg: "rgba(249, 115, 22, 0.15)", text: "#f97316" },
    ESTIMATED: { bg: "rgba(59, 130, 246, 0.15)", text: "#3b82f6" },
  };

  const style = colorMap[norm] || colorMap.GOOD;

  return (
    <span
      data-testid={`quality-badge-${norm}`}
      style={{
        display: "inline-flex",
        alignItems: "center",
        padding: "2px 8px",
        fontSize: "11px",
        fontWeight: 600,
        borderRadius: "4px",
        backgroundColor: style.bg,
        color: style.text,
        border: `1px solid ${style.text}44`,
        letterSpacing: "0.02em",
      }}
    >
      QUALITY: {norm}
    </span>
  );
};
