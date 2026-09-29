import React from "react";

interface ProtocolBadgeProps {
  protocol: string;
}

export const ProtocolBadge: React.FC<ProtocolBadgeProps> = ({ protocol }) => {
  const norm = (protocol || "").toUpperCase();
  const colorMap: Record<string, { bg: string; text: string }> = {
    MODBUS_TCP: { bg: "rgba(59, 130, 246, 0.15)", text: "#60a5fa" },
    OPC_UA: { bg: "rgba(168, 85, 247, 0.15)", text: "#c084fc" },
    MQTT: { bg: "rgba(20, 184, 166, 0.15)", text: "#2dd4bf" },
  };

  const style = colorMap[norm] || { bg: "rgba(100, 116, 139, 0.15)", text: "#94a3b8" };

  return (
    <span
      data-testid={`protocol-badge-${norm}`}
      style={{
        display: "inline-flex",
        alignItems: "center",
        padding: "2px 8px",
        fontSize: "11px",
        fontWeight: 700,
        borderRadius: "4px",
        backgroundColor: style.bg,
        color: style.text,
        border: `1px solid ${style.text}33`,
        letterSpacing: "0.05em",
      }}
    >
      {norm}
    </span>
  );
};
