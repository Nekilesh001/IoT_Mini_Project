import React from "react";
import { Link } from "react-router-dom";
import { MachineOverviewItem } from "../types";
import { StateBadge } from "./StateBadge";
import { ProtocolBadge } from "./ProtocolBadge";
import { QualityBadge } from "./QualityBadge";

interface MachineCardProps {
  machine: MachineOverviewItem;
}

export const MachineCard: React.FC<MachineCardProps> = ({ machine }) => {
  const measurementEntries = Object.entries(machine.key_measurements || {}).slice(0, 4);

  return (
    <Link
      to={`/machines/${encodeURIComponent(machine.machine_id)}`}
      style={{
        textDecoration: "none",
        color: "inherit",
        display: "block",
      }}
    >
      <div
        data-testid={`machine-card-${machine.machine_id}`}
        style={{
          background: "rgba(30, 41, 59, 0.5)",
          backdropFilter: "blur(10px)",
          border: "1px solid rgba(255, 255, 255, 0.08)",
          borderRadius: "12px",
          padding: "20px",
          transition: "all 0.2s cubic-bezier(0.4, 0, 0.2, 1)",
          cursor: "pointer",
          display: "flex",
          flexDirection: "column",
          gap: "14px",
          boxShadow: "0 4px 16px rgba(0, 0, 0, 0.25)",
        }}
        onMouseEnter={(e) => {
          e.currentTarget.style.borderColor = "rgba(56, 189, 248, 0.4)";
          e.currentTarget.style.transform = "translateY(-2px)";
          e.currentTarget.style.boxShadow = "0 8px 24px rgba(0, 0, 0, 0.35)";
        }}
        onMouseLeave={(e) => {
          e.currentTarget.style.borderColor = "rgba(255, 255, 255, 0.08)";
          e.currentTarget.style.transform = "translateY(0)";
          e.currentTarget.style.boxShadow = "0 4px 16px rgba(0, 0, 0, 0.25)";
        }}
      >
        {/* Header */}
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", gap: "10px" }}>
          <div>
            <div style={{ fontSize: "18px", fontWeight: 800, color: "#f8fafc", letterSpacing: "0.02em" }}>
              {machine.machine_id}
            </div>
            <div style={{ fontSize: "12px", fontWeight: 500, color: "#94a3b8", marginTop: "2px" }}>
              {machine.machine_type.replace(/_/g, " ")}
            </div>
          </div>
          <StateBadge state={machine.operating_state} size="sm" />
        </div>

        {/* Badges & Meta */}
        <div style={{ display: "flex", gap: "8px", alignItems: "center", flexWrap: "wrap" }}>
          <ProtocolBadge protocol={machine.protocol} />
          <QualityBadge quality={machine.quality} />
          <span style={{ fontSize: "11px", color: "#64748b", fontFamily: "monospace", marginLeft: "auto" }}>
            Seq #{machine.sequence}
          </span>
        </div>

        {/* Dynamic Key Measurements */}
        <div
          style={{
            background: "rgba(15, 23, 42, 0.6)",
            borderRadius: "8px",
            padding: "12px",
            display: "grid",
            gridTemplateColumns: measurementEntries.length > 2 ? "1fr 1fr" : "1fr",
            gap: "8px",
          }}
        >
          {measurementEntries.length > 0 ? (
            measurementEntries.map(([key, val]) => {
              const formattedVal =
                typeof val === "number"
                  ? Number.isInteger(val)
                    ? val.toString()
                    : val.toFixed(1)
                  : String(val);
              return (
                <div key={key} style={{ display: "flex", flexDirection: "column" }}>
                  <span style={{ fontSize: "10px", color: "#64748b", textTransform: "uppercase", letterSpacing: "0.04em" }}>
                    {key.replace(/_/g, " ")}
                  </span>
                  <span style={{ fontSize: "14px", fontWeight: 700, color: "#e2e8f0", fontFamily: "monospace" }}>
                    {formattedVal}
                  </span>
                </div>
              );
            })
          ) : (
            <div style={{ fontSize: "12px", color: "#64748b", fontStyle: "italic", textAlign: "center" }}>
              Awaiting telemetry stream...
            </div>
          )}
        </div>

        {/* Footer info */}
        <div style={{ display: "flex", justifyContent: "space-between", fontSize: "11px", color: "#64748b" }}>
          <span>{machine.plant_id} / {machine.line_id}</span>
          <span>
            {machine.latest_event_time
              ? new Date(machine.latest_event_time).toLocaleTimeString()
              : "No recent event"}
          </span>
        </div>
      </div>
    </Link>
  );
};
