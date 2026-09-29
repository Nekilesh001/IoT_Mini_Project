import React, { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import { fetchProtocolHealth } from "../api/factory";
import { ProtocolHealthItem } from "../types";
import { Radio, CheckCircle2, Clock, Server, ArrowRight } from "lucide-react";

export const ProtocolHealthPage: React.FC = () => {
  const [protocols, setProtocols] = useState<ProtocolHealthItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchProtocolHealth()
      .then((data) => {
        setProtocols(data.protocols);
        setError(null);
      })
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <div style={{ display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", height: "400px", gap: "16px" }}>
        <div style={{ width: "36px", height: "36px", borderRadius: "50%", border: "3px solid #38bdf8", borderTopColor: "transparent", animation: "spin 1s linear infinite" }} />
        <span style={{ fontSize: "14px", color: "#94a3b8" }}>Loading protocol statuses...</span>
      </div>
    );
  }

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "32px" }}>
      <div>
        <h1 style={{ fontSize: "28px", fontWeight: 800, color: "#f8fafc", margin: 0, letterSpacing: "-0.02em" }}>
          Industrial Protocol Gateway Status
        </h1>
        <p style={{ fontSize: "14px", color: "#94a3b8", margin: "6px 0 0 0" }}>
          Live status and machine assignments for industrial communication layers.
        </p>
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(340px, 1fr))", gap: "20px" }}>
        {protocols.map((proto) => {
          const isOnline = proto.status === "ONLINE";
          const accentColor = proto.protocol === "MODBUS_TCP" ? "#60a5fa" : proto.protocol === "OPC_UA" ? "#c084fc" : "#2dd4bf";

          return (
            <div
              key={proto.protocol}
              style={{
                background: "rgba(30, 41, 59, 0.5)",
                backdropFilter: "blur(10px)",
                border: "1px solid rgba(255, 255, 255, 0.08)",
                borderRadius: "12px",
                padding: "24px",
                display: "flex",
                flexDirection: "column",
                gap: "18px",
                boxShadow: "0 4px 16px rgba(0, 0, 0, 0.25)",
              }}
            >
              {/* Header */}
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
                  <div style={{ padding: "8px", borderRadius: "8px", background: `${accentColor}22`, color: accentColor }}>
                    <Radio size={22} />
                  </div>
                  <div style={{ fontSize: "18px", fontWeight: 800, color: "#f8fafc" }}>
                    {proto.protocol}
                  </div>
                </div>

                <span
                  style={{
                    display: "inline-flex",
                    alignItems: "center",
                    gap: "6px",
                    padding: "4px 10px",
                    fontSize: "11px",
                    fontWeight: 700,
                    borderRadius: "9999px",
                    backgroundColor: isOnline ? "rgba(16, 185, 129, 0.15)" : "rgba(245, 158, 11, 0.15)",
                    color: isOnline ? "#10b981" : "#f59e0b",
                    border: `1px solid ${isOnline ? "#10b98144" : "#f59e0b44"}`,
                  }}
                >
                  <span style={{ width: "6px", height: "6px", borderRadius: "50%", backgroundColor: isOnline ? "#10b981" : "#f59e0b" }} />
                  {proto.status}
                </span>
              </div>

              {/* Endpoint info */}
              <div style={{ display: "flex", flexDirection: "column", gap: "8px", fontSize: "12px", color: "#94a3b8" }}>
                <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                  <Server size={14} color="#64748b" />
                  <span>Endpoint: <strong style={{ color: "#e2e8f0", fontFamily: "monospace" }}>{proto.endpoint}</strong></span>
                </div>
                <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                  <Clock size={14} color="#64748b" />
                  <span>Last Seen: <strong style={{ color: "#e2e8f0" }}>{proto.last_seen ? new Date(proto.last_seen).toLocaleTimeString() : "Awaiting telemetry"}</strong></span>
                </div>
              </div>

              {/* Assigned Machines */}
              <div>
                <div style={{ fontSize: "12px", fontWeight: 600, color: "#94a3b8", marginBottom: "8px" }}>
                  Assigned Equipment ({proto.assigned_machines.length} Machines):
                </div>
                <div style={{ display: "flex", gap: "6px", flexWrap: "wrap" }}>
                  {proto.assigned_machines.map((mId) => (
                    <Link
                      key={mId}
                      to={`/machines/${mId}`}
                      style={{
                        background: "rgba(15, 23, 42, 0.6)",
                        border: "1px solid rgba(255, 255, 255, 0.1)",
                        borderRadius: "6px",
                        padding: "4px 10px",
                        color: "#38bdf8",
                        textDecoration: "none",
                        fontSize: "12px",
                        fontWeight: 700,
                        fontFamily: "monospace",
                        display: "inline-flex",
                        alignItems: "center",
                        gap: "4px",
                      }}
                    >
                      {mId}
                      <ArrowRight size={12} />
                    </Link>
                  ))}
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
