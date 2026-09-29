import React, { useEffect, useState, useRef } from "react";
import { Link } from "react-router-dom";
import { MachineOverviewItem, RealtimeTelemetryEvent } from "../types";
import { StateBadge } from "./StateBadge";
import { ProtocolBadge } from "./ProtocolBadge";
import { QualityBadge } from "./QualityBadge";
import { Activity, Gauge, Zap, Wrench, ShieldAlert, Cpu, CheckCircle } from "lucide-react";

interface MachineCardProps {
  machine: MachineOverviewItem;
  liveEvent?: RealtimeTelemetryEvent;
}

export const MachineCard: React.FC<MachineCardProps> = ({ machine, liveEvent }) => {
  const [isUpdated, setIsUpdated] = useState(false);
  const prevSeqRef = useRef<number>(machine.sequence);

  // Merge live SSE event if available
  const currentSequence = liveEvent?.sequence ?? machine.sequence;
  const currentOperatingState = liveEvent?.operating_state ?? machine.operating_state;
  const currentHealthState = liveEvent?.health_state ?? machine.health_state;
  const currentQuality = liveEvent?.quality ?? machine.quality;
  const currentMeasurements = liveEvent?.measurements ?? machine.key_measurements ?? {};
  const currentEventTime = liveEvent?.event_time ?? machine.latest_event_time;

  useEffect(() => {
    if (liveEvent && liveEvent.sequence !== prevSeqRef.current) {
      prevSeqRef.current = liveEvent.sequence;
      setIsUpdated(true);
      const timer = setTimeout(() => setIsUpdated(false), 900);
      return () => clearTimeout(timer);
    }
  }, [liveEvent]);

  const measurementEntries = Object.entries(currentMeasurements).slice(0, 4);

  // Compute component degradation / predictive indicator
  let componentWearLabel = "Component Health";
  let componentWearVal = 98;
  let componentIcon = Gauge;

  if (machine.machine_type.includes("CNC")) {
    componentWearLabel = "Tool Wear Forecast";
    const toolWear = (currentMeasurements["tool_wear_pct"] as number) ?? (currentMeasurements["spindle_temperature_c"] ? Math.min(100, (currentMeasurements["spindle_temperature_c"] as number) * 0.9) : 15);
    componentWearVal = Math.round(100 - toolWear);
    componentIcon = Wrench;
  } else if (machine.machine_type.includes("PUMP") || machine.machine_type.includes("COMPRESSOR") || machine.machine_type.includes("CHILLER")) {
    componentWearLabel = "Bearing Life Forecast";
    const vib = (currentMeasurements["vibration_rms_mm_s"] as number) ?? 1.2;
    componentWearVal = Math.max(10, Math.round(100 - (vib * 12)));
    componentIcon = Activity;
  } else if (machine.machine_type.includes("ROBOT")) {
    componentWearLabel = "Joint Actuator Stress";
    const temp = (currentMeasurements["joint_1_temp_c"] as number) ?? 40;
    componentWearVal = Math.max(15, Math.round(100 - (temp * 0.8)));
    componentIcon = Zap;
  } else if (machine.machine_type.includes("PRESS") || machine.machine_type.includes("MOLDING")) {
    componentWearLabel = "Hydraulic Seal Health";
    const press = (currentMeasurements["hydraulic_pressure_bar"] as number) ?? 140;
    componentWearVal = Math.max(20, Math.round(Math.min(100, (press / 180) * 100)));
    componentIcon = Gauge;
  }

  const getWearColor = (val: number) => {
    if (val > 70) return "#10b981"; // Emerald healthy
    if (val > 40) return "#f59e0b"; // Amber warning
    return "#f43f5e"; // Rose critical
  };

  return (
    <Link
      to={`/machines/${encodeURIComponent(machine.machine_id)}`}
      style={{ textDecoration: "none", color: "inherit", display: "block" }}
    >
      <div
        data-testid={`machine-card-${machine.machine_id}`}
        style={{
          background: "linear-gradient(145deg, rgba(30, 41, 59, 0.75), rgba(15, 23, 42, 0.85))",
          backdropFilter: "blur(12px)",
          border: isUpdated ? "1px solid #06b6d4" : "1px solid rgba(255, 255, 255, 0.08)",
          borderRadius: "14px",
          padding: "20px",
          transition: "all 0.25s cubic-bezier(0.4, 0, 0.2, 1)",
          cursor: "pointer",
          display: "flex",
          flexDirection: "column",
          gap: "14px",
          boxShadow: isUpdated ? "0 0 24px rgba(6, 182, 212, 0.25)" : "0 6px 20px rgba(0, 0, 0, 0.35)",
          position: "relative",
          overflow: "hidden",
        }}
        onMouseEnter={(e) => {
          e.currentTarget.style.borderColor = "rgba(6, 182, 212, 0.5)";
          e.currentTarget.style.transform = "translateY(-3px)";
          e.currentTarget.style.boxShadow = "0 14px 28px rgba(0, 0, 0, 0.45)";
        }}
        onMouseLeave={(e) => {
          e.currentTarget.style.borderColor = isUpdated ? "#06b6d4" : "rgba(255, 255, 255, 0.08)";
          e.currentTarget.style.transform = "translateY(0)";
          e.currentTarget.style.boxShadow = isUpdated ? "0 0 24px rgba(6, 182, 212, 0.25)" : "0 6px 20px rgba(0, 0, 0, 0.35)";
        }}
      >
        {/* Top Accent Light */}
        <div
          style={{
            position: "absolute",
            top: 0,
            left: 0,
            right: 0,
            height: "2px",
            background: currentHealthState === "HEALTHY" 
              ? "linear-gradient(90deg, transparent, #10b981, transparent)"
              : currentHealthState === "WARNING"
              ? "linear-gradient(90deg, transparent, #f59e0b, transparent)"
              : "linear-gradient(90deg, transparent, #f43f5e, transparent)",
          }}
        />

        {/* Header */}
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", gap: "10px" }}>
          <div>
            <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
              <div
                style={{
                  width: "28px",
                  height: "28px",
                  borderRadius: "6px",
                  background: "rgba(6, 182, 212, 0.15)",
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  border: "1px solid rgba(6, 182, 212, 0.3)",
                }}
              >
                <Cpu size={15} color="#38bdf8" />
              </div>
              <span style={{ fontSize: "17px", fontWeight: 800, color: "#f8fafc", letterSpacing: "0.02em" }}>
                {machine.machine_id}
              </span>
              {isUpdated && (
                <span className="live-pulse-dot" title="Live stream update" />
              )}
            </div>
            <div style={{ fontSize: "11px", fontWeight: 600, color: "#94a3b8", marginTop: "4px" }}>
              {machine.machine_type.replace(/_/g, " ")}
            </div>
          </div>
          <StateBadge state={currentOperatingState} size="sm" />
        </div>

        {/* Protocol & Sequence Chips */}
        <div style={{ display: "flex", gap: "6px", alignItems: "center", flexWrap: "wrap" }}>
          <ProtocolBadge protocol={machine.protocol} />
          <QualityBadge quality={currentQuality} />
          <span
            style={{
              fontSize: "10px",
              color: "#64748b",
              fontFamily: "'JetBrains Mono', monospace",
              marginLeft: "auto",
              padding: "2px 6px",
              background: "rgba(15, 23, 42, 0.6)",
              borderRadius: "4px",
              border: "1px solid rgba(255, 255, 255, 0.05)",
            }}
          >
            Seq #{currentSequence}
          </span>
        </div>

        {/* Live Key Sensor Matrix */}
        <div
          style={{
            background: "rgba(11, 15, 25, 0.7)",
            borderRadius: "10px",
            padding: "12px",
            border: "1px solid rgba(255, 255, 255, 0.04)",
            display: "grid",
            gridTemplateColumns: measurementEntries.length > 2 ? "1fr 1fr" : "1fr",
            gap: "10px",
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
                  <span
                    style={{
                      fontSize: "9px",
                      color: "#64748b",
                      textTransform: "uppercase",
                      letterSpacing: "0.05em",
                      fontWeight: 700,
                    }}
                  >
                    {key.replace(/_/g, " ")}
                  </span>
                  <span
                    className={isUpdated ? "telemetry-updated" : ""}
                    style={{
                      fontSize: "14px",
                      fontWeight: 700,
                      color: "#f1f5f9",
                      fontFamily: "'JetBrains Mono', monospace",
                      marginTop: "1px",
                    }}
                  >
                    {formattedVal}
                  </span>
                </div>
              );
            })
          ) : (
            <div style={{ fontSize: "12px", color: "#64748b", fontStyle: "italic", textAlign: "center", padding: "6px" }}>
              Awaiting live telemetry stream...
            </div>
          )}
        </div>

        {/* Component Health & Predictive Forecast Meter */}
        <div style={{ display: "flex", flexDirection: "column", gap: "4px" }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
            <span style={{ fontSize: "11px", fontWeight: 600, color: "#94a3b8", display: "flex", alignItems: "center", gap: "4px" }}>
              <Wrench size={12} color={getWearColor(componentWearVal)} /> {componentWearLabel}
            </span>
            <span style={{ fontSize: "11px", fontWeight: 700, color: getWearColor(componentWearVal), fontFamily: "'JetBrains Mono', monospace" }}>
              {componentWearVal}%
            </span>
          </div>
          <div style={{ width: "100%", height: "4px", background: "rgba(255, 255, 255, 0.08)", borderRadius: "9999px", overflow: "hidden" }}>
            <div
              style={{
                width: `${componentWearVal}%`,
                height: "100%",
                background: getWearColor(componentWearVal),
                borderRadius: "9999px",
                transition: "width 0.4s ease-in-out",
              }}
            />
          </div>
        </div>

        {/* Footer info */}
        <div
          style={{
            display: "flex",
            justifyContent: "space-between",
            fontSize: "10px",
            color: "#64748b",
            borderTop: "1px solid rgba(255, 255, 255, 0.04)",
            paddingTop: "8px",
          }}
        >
          <span>{machine.plant_id} / {machine.line_id}</span>
          <span style={{ fontFamily: "'JetBrains Mono', monospace" }}>
            {currentEventTime ? new Date(currentEventTime).toLocaleTimeString() : "Live streaming"}
          </span>
        </div>
      </div>
    </Link>
  );
};
