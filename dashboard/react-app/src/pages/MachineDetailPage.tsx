import React, { useState } from "react";
import { useParams, Link } from "react-router-dom";
import { useMachineDetail } from "../hooks/useMachineDetail";
import { useMachineHistory } from "../hooks/useMachineHistory";
import { StateBadge } from "../components/StateBadge";
import { QualityBadge } from "../components/QualityBadge";
import { ProtocolBadge } from "../components/ProtocolBadge";
import { MetricCard } from "../components/MetricCard";
import { TimeSeriesChart } from "../components/TimeSeriesChart";
import { ArrowLeft, Clock, MapPin, Radio, Hash, Activity } from "lucide-react";

export const MachineDetailPage: React.FC = () => {
  const { machineId } = useParams<{ machineId: string }>();
  const [range, setRange] = useState<string>("15m");

  const { machine, loading: machineLoading, error: machineError } = useMachineDetail(machineId || "");
  const { history, loading: historyLoading, error: historyError } = useMachineHistory(machineId || "", { limit: 100 });

  if (machineLoading) {
    return (
      <div style={{ display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", height: "400px", gap: "16px" }}>
        <div style={{ width: "36px", height: "36px", borderRadius: "50%", border: "3px solid #38bdf8", borderTopColor: "transparent", animation: "spin 1s linear infinite" }} />
        <span style={{ fontSize: "14px", color: "#94a3b8" }}>Loading machine telemetry and specifications...</span>
      </div>
    );
  }

  if (machineError || !machine) {
    return (
      <div
        style={{
          background: "rgba(239, 68, 68, 0.1)",
          border: "1px solid rgba(239, 68, 68, 0.3)",
          borderRadius: "12px",
          padding: "24px",
          color: "#fca5a5",
          textAlign: "center",
        }}
      >
        <div style={{ fontSize: "18px", fontWeight: 700, marginBottom: "8px" }}>Machine Not Found</div>
        <div style={{ fontSize: "13px", color: "#f87171", marginBottom: "16px" }}>{machineError || `No machine with ID '${machineId}'`}</div>
        <Link to="/" style={{ color: "#38bdf8", fontWeight: 600, textDecoration: "none" }}>
          &larr; Return to Fleet Overview
        </Link>
      </div>
    );
  }

  // Create unit map from signals
  const unitMap: Record<string, string> = {};
  for (const s of machine.signals || []) {
    unitMap[s.name] = s.unit;
  }

  const measurements = Object.entries(machine.current_measurements || {});
  const derived = Object.entries(machine.current_derived || {});

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "28px" }}>
      {/* Back button & Title */}
      <div>
        <Link
          to="/"
          style={{
            display: "inline-flex",
            alignItems: "center",
            gap: "6px",
            fontSize: "13px",
            fontWeight: 600,
            color: "#38bdf8",
            textDecoration: "none",
            marginBottom: "12px",
          }}
        >
          <ArrowLeft size={16} /> Back to Fleet
        </Link>

        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", flexWrap: "wrap", gap: "16px" }}>
          <div>
            <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
              <h1 style={{ fontSize: "32px", fontWeight: 800, color: "#f8fafc", margin: 0, letterSpacing: "-0.02em" }}>
                {machine.machine_id}
              </h1>
              <StateBadge state={machine.operating_state} size="lg" />
              <StateBadge state={machine.health_state} size="lg" />
            </div>
            <p style={{ fontSize: "15px", color: "#94a3b8", margin: "6px 0 0 0" }}>
              {machine.machine_type.replace(/_/g, " ")} &bull; {machine.plant_id} / {machine.line_id}
            </p>
          </div>

          <div style={{ display: "flex", gap: "10px", alignItems: "center", flexWrap: "wrap" }}>
            <ProtocolBadge protocol={machine.protocol} />
            <QualityBadge quality={machine.quality} />
          </div>
        </div>
      </div>

      {/* Metadata Bar */}
      <div
        style={{
          background: "rgba(30, 41, 59, 0.4)",
          border: "1px solid rgba(255, 255, 255, 0.08)",
          borderRadius: "10px",
          padding: "16px 20px",
          display: "flex",
          gap: "24px",
          flexWrap: "wrap",
          fontSize: "12px",
          color: "#94a3b8",
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
          <Clock size={16} color="#38bdf8" />
          <span>Latest Event: <strong style={{ color: "#f8fafc", fontFamily: "monospace" }}>{machine.latest_event_time ? new Date(machine.latest_event_time).toLocaleTimeString() : "N/A"}</strong></span>
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
          <Hash size={16} color="#38bdf8" />
          <span>Sequence: <strong style={{ color: "#f8fafc", fontFamily: "monospace" }}>#{machine.sequence}</strong></span>
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
          <Radio size={16} color="#38bdf8" />
          <span>Source: <strong style={{ color: "#f8fafc", fontFamily: "monospace" }}>{machine.source_endpoint || machine.protocol}</strong></span>
        </div>
        {machine.source_address && (
          <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
            <MapPin size={16} color="#38bdf8" />
            <span>Address: <strong style={{ color: "#f8fafc", fontFamily: "monospace" }}>{machine.source_address}</strong></span>
          </div>
        )}
      </div>

      {/* Live Measurements Grid */}
      <section>
        <h2 style={{ fontSize: "18px", fontWeight: 700, color: "#f8fafc", marginBottom: "14px" }}>
          Live Physical Measurements ({measurements.length} Signals)
        </h2>
        {measurements.length === 0 ? (
          <div style={{ background: "rgba(30, 41, 59, 0.4)", padding: "20px", borderRadius: "10px", color: "#64748b", fontStyle: "italic" }}>
            Awaiting live telemetry for this machine...
          </div>
        ) : (
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(200px, 1fr))", gap: "16px" }}>
            {measurements.map(([name, val]) => (
              <MetricCard
                key={name}
                label={name}
                value={val}
                unit={unitMap[name] || ""}
                accentColor="#38bdf8"
              />
            ))}
          </div>
        )}
      </section>

      {/* Derived Physical Metrics (if present) */}
      {derived.length > 0 && (
        <section>
          <h2 style={{ fontSize: "18px", fontWeight: 700, color: "#f8fafc", marginBottom: "14px" }}>
            Derived Operational Metrics
          </h2>
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(200px, 1fr))", gap: "16px" }}>
            {derived.map(([name, val]) => (
              <MetricCard
                key={name}
                label={name}
                value={val}
                accentColor="#34d399"
                description="Calculated at edge"
              />
            ))}
          </div>
        </section>
      )}

      {/* Historical Telemetry Chart */}
      <section>
        <h2 style={{ fontSize: "18px", fontWeight: 700, color: "#f8fafc", marginBottom: "14px" }}>
          Historical Telemetry Trends
        </h2>
        <TimeSeriesChart
          records={history?.records || []}
          availableSignals={history?.available_signals || machine.signals.map((s) => s.name)}
          unitMap={unitMap}
          selectedRange={range}
          onRangeChange={(r) => setRange(r)}
        />
      </section>

      {/* Signal Specification Catalog */}
      <section>
        <h2 style={{ fontSize: "18px", fontWeight: 700, color: "#f8fafc", marginBottom: "14px" }}>
          Signal Catalog Specification
        </h2>
        <div style={{ overflowX: "auto", border: "1px solid rgba(255, 255, 255, 0.08)", borderRadius: "10px" }}>
          <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "12px", textAlign: "left" }}>
            <thead>
              <tr style={{ background: "rgba(30, 41, 59, 0.8)", color: "#94a3b8", borderBottom: "1px solid rgba(255, 255, 255, 0.08)" }}>
                <th style={{ padding: "12px 16px" }}>Signal Name</th>
                <th style={{ padding: "12px 16px" }}>Type</th>
                <th style={{ padding: "12px 16px" }}>Unit</th>
                <th style={{ padding: "12px 16px" }}>Nominal</th>
                <th style={{ padding: "12px 16px" }}>Valid Range</th>
                <th style={{ padding: "12px 16px" }}>Description</th>
              </tr>
            </thead>
            <tbody>
              {machine.signals.map((sig, idx) => (
                <tr
                  key={sig.name}
                  style={{
                    background: idx % 2 === 0 ? "rgba(15, 23, 42, 0.4)" : "rgba(30, 41, 59, 0.2)",
                    borderBottom: "1px solid rgba(255, 255, 255, 0.04)",
                  }}
                >
                  <td style={{ padding: "10px 16px", fontWeight: 600, color: "#f8fafc" }}>{sig.name}</td>
                  <td style={{ padding: "10px 16px", color: "#60a5fa", fontFamily: "monospace" }}>{sig.signal_type}</td>
                  <td style={{ padding: "10px 16px", color: "#38bdf8", fontWeight: 700 }}>{sig.unit}</td>
                  <td style={{ padding: "10px 16px", fontFamily: "monospace" }}>{sig.nominal_value ?? "—"}</td>
                  <td style={{ padding: "10px 16px", color: "#94a3b8", fontFamily: "monospace" }}>
                    {sig.min_value !== null && sig.max_value !== null ? `[${sig.min_value} — ${sig.max_value}]` : "—"}
                  </td>
                  <td style={{ padding: "10px 16px", color: "#64748b" }}>{sig.description}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  );
};
