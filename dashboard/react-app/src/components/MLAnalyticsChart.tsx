import React, { useState, useMemo } from "react";
import { MLInferenceResult } from "../types";
import { Activity, Gauge, TrendingDown, Layers, AlertTriangle, ShieldCheck } from "lucide-react";

interface MLAnalyticsChartProps {
  inferences: MLInferenceResult[];
  selectedMachine?: string;
  onSelectMachine?: (machineId: string) => void;
}

export const MLAnalyticsChart: React.FC<MLAnalyticsChartProps> = ({
  inferences,
  selectedMachine = "ALL",
  onSelectMachine,
}) => {
  const [viewMode, setViewMode] = useState<"ANOMALY" | "RUL" | "COMBINED">("COMBINED");
  const [hoverIndex, setHoverIndex] = useState<number | null>(null);

  // Filter inferences by machine and sort chronologically (oldest -> newest)
  const machineInferences = useMemo(() => {
    const filtered = selectedMachine === "ALL" 
      ? inferences 
      : inferences.filter((i) => i.machine_id === selectedMachine);
    
    return [...filtered].reverse().slice(-40); // Last 40 chronological data points
  }, [inferences, selectedMachine]);

  // SVG Chart dimensions
  const width = 900;
  const height = 300;
  const padLeft = 60;
  const padRight = 60;
  const padTop = 30;
  const padBottom = 40;

  const innerW = width - padLeft - padRight;
  const innerH = height - padTop - padBottom;

  const scaleX = (idx: number) => {
    if (machineInferences.length <= 1) return padLeft + innerW / 2;
    return padLeft + (idx / (machineInferences.length - 1)) * innerW;
  };

  // Anomaly Scale [0.0 - 1.0]
  const scaleYAnomaly = (val: number) => {
    return padTop + innerH - Math.max(0, Math.min(1, val)) * innerH;
  };

  // RUL Scale [0 - maxRUL]
  const maxRulMinutes = useMemo(() => {
    let max = 60;
    for (const inf of machineInferences) {
      if (inf.predicted_rul_minutes && inf.predicted_rul_minutes > max) {
        max = inf.predicted_rul_minutes;
      }
    }
    return Math.ceil(max / 10) * 10 || 60;
  }, [machineInferences]);

  const scaleYRul = (val: number) => {
    const clamped = Math.max(0, Math.min(maxRulMinutes, val));
    return padTop + innerH - (clamped / maxRulMinutes) * innerH;
  };

  // Generate SVG path for Anomaly Scores
  const anomalyPath = useMemo(() => {
    if (machineInferences.length === 0) return "";
    return machineInferences.reduce((acc, inf, i) => {
      const x = scaleX(i);
      const score = inf.anomaly_score ?? 0.15;
      const y = scaleYAnomaly(score);
      return i === 0 ? `M ${x} ${y}` : `${acc} L ${x} ${y}`;
    }, "");
  }, [machineInferences]);

  // Generate Area Fill for Anomaly Scores
  const anomalyArea = useMemo(() => {
    if (!anomalyPath || machineInferences.length === 0) return "";
    const startX = scaleX(0);
    const endX = scaleX(machineInferences.length - 1);
    const bottomY = padTop + innerH;
    return `${anomalyPath} L ${endX} ${bottomY} L ${startX} ${bottomY} Z`;
  }, [anomalyPath, machineInferences]);

  // Generate SVG path for RUL
  const rulPath = useMemo(() => {
    if (machineInferences.length === 0) return "";
    return machineInferences.reduce((acc, inf, i) => {
      const x = scaleX(i);
      const rul = inf.predicted_rul_minutes ?? 60.0;
      const y = scaleYRul(rul);
      return i === 0 ? `M ${x} ${y}` : `${acc} L ${x} ${y}`;
    }, "");
  }, [machineInferences, maxRulMinutes]);

  const activePoint = hoverIndex !== null && machineInferences[hoverIndex] ? machineInferences[hoverIndex] : null;

  return (
    <div
      style={{
        background: "linear-gradient(145deg, rgba(30, 41, 59, 0.75), rgba(15, 23, 42, 0.85))",
        backdropFilter: "blur(16px)",
        border: "1px solid rgba(255, 255, 255, 0.08)",
        borderRadius: "14px",
        padding: "20px 24px",
        boxShadow: "0 10px 30px -10px rgba(0, 0, 0, 0.5)",
        display: "flex",
        flexDirection: "column",
        gap: "18px",
      }}
    >
      {/* Chart Header & Controls */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: "12px" }}>
        <div>
          <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
            <Activity size={18} color="#06b6d4" />
            <h3 style={{ fontSize: "16px", fontWeight: 800, color: "#f8fafc", margin: 0 }}>
              Live Edge ML Model Analytics & Degradation Trajectory
            </h3>
          </div>
          <p style={{ fontSize: "12px", color: "#94a3b8", margin: "4px 0 0 0" }}>
            Real-time multi-variate anomaly score trends vs. remaining operational life horizon
          </p>
        </div>

        {/* View Switchers */}
        <div style={{ display: "flex", gap: "8px", alignItems: "center" }}>
          <div style={{ display: "flex", background: "rgba(15, 23, 42, 0.8)", padding: "3px", borderRadius: "8px", border: "1px solid rgba(255, 255, 255, 0.08)" }}>
            <button
              onClick={() => setViewMode("COMBINED")}
              style={{
                background: viewMode === "COMBINED" ? "rgba(6, 182, 212, 0.2)" : "transparent",
                color: viewMode === "COMBINED" ? "#38bdf8" : "#94a3b8",
                border: viewMode === "COMBINED" ? "1px solid rgba(6, 182, 212, 0.4)" : "1px solid transparent",
                padding: "4px 10px",
                borderRadius: "6px",
                fontSize: "11px",
                fontWeight: 700,
                cursor: "pointer",
                display: "flex",
                alignItems: "center",
                gap: "4px",
              }}
            >
              <Layers size={13} /> Dual Stream
            </button>
            <button
              onClick={() => setViewMode("ANOMALY")}
              style={{
                background: viewMode === "ANOMALY" ? "rgba(245, 158, 11, 0.2)" : "transparent",
                color: viewMode === "ANOMALY" ? "#fbbf24" : "#94a3b8",
                border: viewMode === "ANOMALY" ? "1px solid rgba(245, 158, 11, 0.4)" : "1px solid transparent",
                padding: "4px 10px",
                borderRadius: "6px",
                fontSize: "11px",
                fontWeight: 700,
                cursor: "pointer",
                display: "flex",
                alignItems: "center",
                gap: "4px",
              }}
            >
              <Activity size={13} /> Anomaly Score
            </button>
            <button
              onClick={() => setViewMode("RUL")}
              style={{
                background: viewMode === "RUL" ? "rgba(16, 185, 129, 0.2)" : "transparent",
                color: viewMode === "RUL" ? "#34d399" : "#94a3b8",
                border: viewMode === "RUL" ? "1px solid rgba(16, 185, 129, 0.4)" : "1px solid transparent",
                padding: "4px 10px",
                borderRadius: "6px",
                fontSize: "11px",
                fontWeight: 700,
                cursor: "pointer",
                display: "flex",
                alignItems: "center",
                gap: "4px",
              }}
            >
              <Gauge size={13} /> RUL Countdown
            </button>
          </div>
        </div>
      </div>

      {/* Main SVG Visualization */}
      <div style={{ position: "relative", width: "100%", overflowX: "auto" }}>
        {machineInferences.length === 0 ? (
          <div style={{ height: "260px", display: "flex", alignItems: "center", justifyContent: "center", color: "#64748b", fontStyle: "italic", fontSize: "13px" }}>
            Awaiting streaming ML inference results from background edge engine...
          </div>
        ) : (
          <svg
            viewBox={`0 0 ${width} ${height}`}
            style={{ width: "100%", height: "auto", minWidth: "650px", overflow: "visible" }}
            onMouseLeave={() => setHoverIndex(null)}
          >
            <defs>
              {/* Anomaly Gradient */}
              <linearGradient id="anomalyGradient" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor="#f43f5e" stopOpacity="0.4" />
                <stop offset="60%" stopColor="#f59e0b" stopOpacity="0.15" />
                <stop offset="100%" stopColor="#10b981" stopOpacity="0.0" />
              </linearGradient>

              {/* RUL Gradient */}
              <linearGradient id="rulGradient" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor="#38bdf8" stopOpacity="0.3" />
                <stop offset="100%" stopColor="#38bdf8" stopOpacity="0.0" />
              </linearGradient>
            </defs>

            {/* Grid Lines */}
            {[0, 0.25, 0.5, 0.75, 1.0].map((ratio) => {
              const y = padTop + innerH * (1 - ratio);
              return (
                <g key={ratio}>
                  <line
                    x1={padLeft}
                    y1={y}
                    x2={padLeft + innerW}
                    y2={y}
                    stroke="rgba(255, 255, 255, 0.05)"
                    strokeDasharray="4 4"
                  />
                  {/* Left Y-Axis Label (Anomaly Risk) */}
                  {(viewMode === "ANOMALY" || viewMode === "COMBINED") && (
                    <text
                      x={padLeft - 8}
                      y={y + 4}
                      textAnchor="end"
                      fill="#94a3b8"
                      fontSize="10px"
                      fontFamily="'JetBrains Mono', monospace"
                    >
                      {`${Math.round(ratio * 100)}%`}
                    </text>
                  )}
                  {/* Right Y-Axis Label (RUL Minutes) */}
                  {(viewMode === "RUL" || viewMode === "COMBINED") && (
                    <text
                      x={padLeft + innerW + 8}
                      y={y + 4}
                      textAnchor="start"
                      fill="#38bdf8"
                      fontSize="10px"
                      fontFamily="'JetBrains Mono', monospace"
                    >
                      {`${Math.round(ratio * maxRulMinutes)}m`}
                    </text>
                  )}
                </g>
              );
            })}

            {/* 65% Anomaly Threshold Reference Line */}
            {(viewMode === "ANOMALY" || viewMode === "COMBINED") && (
              <g>
                <line
                  x1={padLeft}
                  y1={scaleYAnomaly(0.65)}
                  x2={padLeft + innerW}
                  y2={scaleYAnomaly(0.65)}
                  stroke="#f43f5e"
                  strokeWidth="1.5"
                  strokeDasharray="6 3"
                  opacity="0.75"
                />
                <text
                  x={padLeft + innerW - 10}
                  y={scaleYAnomaly(0.65) - 6}
                  textAnchor="end"
                  fill="#f87171"
                  fontSize="10px"
                  fontWeight="700"
                  fontFamily="'JetBrains Mono', monospace"
                >
                  65% ANOMALY TRIGGER THRESHOLD
                </text>
              </g>
            )}

            {/* 10m RUL Critical Horizon Line */}
            {(viewMode === "RUL" || viewMode === "COMBINED") && (
              <g>
                <line
                  x1={padLeft}
                  y1={scaleYRul(10)}
                  x2={padLeft + innerW}
                  y2={scaleYRul(10)}
                  stroke="#f59e0b"
                  strokeWidth="1"
                  strokeDasharray="4 4"
                  opacity="0.6"
                />
              </g>
            )}

            {/* Anomaly Score Area & Line */}
            {(viewMode === "ANOMALY" || viewMode === "COMBINED") && (
              <>
                <path d={anomalyArea} fill="url(#anomalyGradient)" />
                <path d={anomalyPath} fill="none" stroke="#f59e0b" strokeWidth="2.5" />
              </>
            )}

            {/* RUL Line */}
            {(viewMode === "RUL" || viewMode === "COMBINED") && (
              <path d={rulPath} fill="none" stroke="#38bdf8" strokeWidth="2.5" strokeDasharray={viewMode === "COMBINED" ? "5 2" : "none"} />
            )}

            {/* Interactive Data Points & Hover Triggers */}
            {machineInferences.map((inf, i) => {
              const x = scaleX(i);
              const score = inf.anomaly_score ?? 0.15;
              const yAnom = scaleYAnomaly(score);
              const isHovered = hoverIndex === i;
              const isAnom = inf.anomaly_label === "ANOMALOUS";

              return (
                <g key={inf.result_id || i}>
                  {/* Transparent hover capture column */}
                  <rect
                    x={x - (innerW / machineInferences.length) / 2}
                    y={padTop}
                    width={innerW / machineInferences.length}
                    height={innerH}
                    fill="transparent"
                    onMouseEnter={() => setHoverIndex(i)}
                    style={{ cursor: "pointer" }}
                  />

                  {/* Anomaly Dot */}
                  {(viewMode === "ANOMALY" || viewMode === "COMBINED") && (
                    <circle
                      cx={x}
                      cy={yAnom}
                      r={isHovered ? 6 : isAnom ? 4.5 : 3}
                      fill={isAnom ? "#f43f5e" : "#10b981"}
                      stroke="#0f172a"
                      strokeWidth="2"
                    />
                  )}
                </g>
              );
            })}

            {/* Vertical Cursor Line */}
            {hoverIndex !== null && (
              <line
                x1={scaleX(hoverIndex)}
                y1={padTop}
                x2={scaleX(hoverIndex)}
                y2={padTop + innerH}
                stroke="#38bdf8"
                strokeWidth="1.5"
                strokeDasharray="2 2"
              />
            )}
          </svg>
        )}

        {/* Hover Tooltip Overlay */}
        {activePoint && hoverIndex !== null && (
          <div
            style={{
              position: "absolute",
              top: "10px",
              left: `${Math.min(75, Math.max(15, (scaleX(hoverIndex) / width) * 100))}%`,
              transform: "translateX(-50%)",
              background: "rgba(15, 23, 42, 0.95)",
              border: "1px solid #06b6d4",
              borderRadius: "10px",
              padding: "10px 14px",
              boxShadow: "0 10px 25px rgba(0, 0, 0, 0.6)",
              pointerEvents: "none",
              fontSize: "12px",
              zIndex: 10,
              minWidth: "200px",
            }}
          >
            <div style={{ display: "flex", justifyContent: "space-between", fontWeight: 800, color: "#f8fafc", borderBottom: "1px solid rgba(255, 255, 255, 0.1)", paddingBottom: "4px", marginBottom: "6px" }}>
              <span>{activePoint.machine_id}</span>
              <span style={{ fontSize: "10px", color: "#94a3b8", fontFamily: "'JetBrains Mono', monospace" }}>
                {activePoint.event_time ? new Date(activePoint.event_time).toLocaleTimeString() : ""}
              </span>
            </div>
            <div style={{ display: "flex", justifyContent: "space-between", color: "#f59e0b", marginBottom: "3px" }}>
              <span>Anomaly Risk:</span>
              <strong style={{ fontFamily: "'JetBrains Mono', monospace" }}>
                {activePoint.anomaly_score !== null && activePoint.anomaly_score !== undefined ? `${(activePoint.anomaly_score * 100).toFixed(1)}%` : "N/A"}
              </strong>
            </div>
            <div style={{ display: "flex", justifyContent: "space-between", color: "#38bdf8", marginBottom: "3px" }}>
              <span>Predicted RUL:</span>
              <strong style={{ fontFamily: "'JetBrains Mono', monospace" }}>
                {activePoint.predicted_rul_minutes !== null && activePoint.predicted_rul_minutes !== undefined ? `${activePoint.predicted_rul_minutes.toFixed(1)}m` : "Warming"}
              </strong>
            </div>
            <div style={{ display: "flex", justifyContent: "space-between", color: "#94a3b8", fontSize: "11px" }}>
              <span>Inference Latency:</span>
              <span style={{ fontFamily: "'JetBrains Mono', monospace" }}>
                {activePoint.latency_ms?.total_inference_ms?.toFixed(2) || "0.00"}ms
              </span>
            </div>
          </div>
        )}
      </div>

      {/* Legend & Summary Footer */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", borderTop: "1px solid rgba(255, 255, 255, 0.05)", paddingTop: "12px", fontSize: "12px", flexWrap: "wrap", gap: "10px" }}>
        <div style={{ display: "flex", gap: "16px", alignItems: "center" }}>
          <div style={{ display: "flex", alignItems: "center", gap: "6px" }}>
            <span style={{ width: "12px", height: "3px", background: "#f59e0b", borderRadius: "2px" }} />
            <span style={{ color: "#cbd5e1" }}>Isolation Forest Anomaly Score (%)</span>
          </div>
          <div style={{ display: "flex", alignItems: "center", gap: "6px" }}>
            <span style={{ width: "12px", height: "3px", background: "#38bdf8", borderBottom: "2px dashed #38bdf8" }} />
            <span style={{ color: "#cbd5e1" }}>HistGBM Predicted RUL (Minutes)</span>
          </div>
        </div>

        <div style={{ color: "#64748b", fontFamily: "'JetBrains Mono', monospace" }}>
          Showing latest {machineInferences.length} stream evaluations
        </div>
      </div>
    </div>
  );
};
