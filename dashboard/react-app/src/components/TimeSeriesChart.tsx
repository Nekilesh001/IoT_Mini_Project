import React, { useState, useMemo } from "react";
import { TelemetryRecord } from "../types";

interface TimeSeriesChartProps {
  records: TelemetryRecord[];
  availableSignals: string[];
  unitMap?: Record<string, string>;
  selectedRange?: string;
  onRangeChange?: (range: string) => void;
}

const PALETTE = [
  "#38bdf8", // Sky Blue
  "#34d399", // Emerald Green
  "#f472b6", // Rose Pink
  "#fbbf24", // Amber Yellow
  "#a78bfa", // Purple
  "#fb923c", // Orange
  "#2dd4bf", // Teal
  "#818cf8", // Indigo
];

export const TimeSeriesChart: React.FC<TimeSeriesChartProps> = ({
  records,
  availableSignals,
  unitMap = {},
  selectedRange = "15m",
  onRangeChange,
}) => {
  // Default to selecting the first 3 signals
  const [selectedSignals, setSelectedSignals] = useState<string[]>(() =>
    availableSignals.slice(0, 3)
  );
  const [hoverIndex, setHoverIndex] = useState<number | null>(null);

  const toggleSignal = (sig: string) => {
    setSelectedSignals((prev) =>
      prev.includes(sig) ? (prev.length > 1 ? prev.filter((s) => s !== sig) : prev) : [...prev, sig]
    );
  };

  // Extract series data
  const chartData = useMemo(() => {
    if (!records || records.length === 0) return [];
    return records.map((r, i) => {
      const point: Record<string, any> = {
        index: i,
        timeStr: r.event_time ? new Date(r.event_time).toLocaleTimeString() : `#${r.sequence}`,
        sequence: r.sequence,
      };
      for (const sig of availableSignals) {
        const val = r.measurements?.[sig];
        point[sig] = typeof val === "number" ? val : null;
      }
      return point;
    });
  }, [records, availableSignals]);

  // Compute min/max bounds across selected signals
  const { minY, maxY } = useMemo(() => {
    let min = Infinity;
    let max = -Infinity;
    for (const point of chartData) {
      for (const sig of selectedSignals) {
        const val = point[sig];
        if (typeof val === "number" && !isNaN(val)) {
          if (val < min) min = val;
          if (val > max) max = val;
        }
      }
    }
    if (min === Infinity || max === -Infinity) {
      return { minY: 0, maxY: 100 };
    }
    const padding = (max - min) * 0.1 || 1.0;
    return {
      minY: min - padding,
      maxY: max + padding,
    };
  }, [chartData, selectedSignals]);

  // Dimensions
  const width = 800;
  const height = 320;
  const padLeft = 60;
  const padRight = 30;
  const padTop = 20;
  const padBottom = 40;

  const innerW = width - padLeft - padRight;
  const innerH = height - padTop - padBottom;

  const scaleX = (idx: number) => {
    if (chartData.length <= 1) return padLeft + innerW / 2;
    return padLeft + (idx / (chartData.length - 1)) * innerW;
  };

  const scaleY = (val: number) => {
    if (maxY === minY) return padTop + innerH / 2;
    return padTop + innerH - ((val - minY) / (maxY - minY)) * innerH;
  };

  return (
    <div
      style={{
        background: "rgba(15, 23, 42, 0.7)",
        backdropFilter: "blur(12px)",
        border: "1px solid rgba(255, 255, 255, 0.08)",
        borderRadius: "12px",
        padding: "20px",
        display: "flex",
        flexDirection: "column",
        gap: "16px",
      }}
    >
      {/* Chart Controls Bar */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: "12px" }}>
        {/* Signal selection toggles */}
        <div style={{ display: "flex", gap: "8px", flexWrap: "wrap", alignItems: "center" }}>
          <span style={{ fontSize: "12px", fontWeight: 600, color: "#94a3b8" }}>Signals:</span>
          {availableSignals.map((sig, idx) => {
            const isSelected = selectedSignals.includes(sig);
            const color = PALETTE[idx % PALETTE.length];
            return (
              <button
                key={sig}
                onClick={() => toggleSignal(sig)}
                style={{
                  background: isSelected ? `${color}22` : "rgba(30, 41, 59, 0.4)",
                  border: `1px solid ${isSelected ? color : "rgba(255, 255, 255, 0.1)"}`,
                  color: isSelected ? color : "#94a3b8",
                  padding: "4px 10px",
                  borderRadius: "6px",
                  fontSize: "11px",
                  fontWeight: 600,
                  cursor: "pointer",
                  transition: "all 0.15s ease",
                  display: "flex",
                  alignItems: "center",
                  gap: "6px",
                }}
              >
                <span
                  style={{
                    width: "8px",
                    height: "8px",
                    borderRadius: "50%",
                    backgroundColor: isSelected ? color : "#64748b",
                  }}
                />
                {sig.replace(/_/g, " ")}
              </button>
            );
          })}
        </div>

        {/* Time range selector */}
        {onRangeChange && (
          <div style={{ display: "flex", gap: "4px", background: "rgba(30, 41, 59, 0.6)", padding: "3px", borderRadius: "8px" }}>
            {["5m", "15m", "1h", "All"].map((rng) => (
              <button
                key={rng}
                onClick={() => onRangeChange(rng)}
                style={{
                  background: selectedRange.toLowerCase() === rng.toLowerCase() ? "#38bdf8" : "transparent",
                  color: selectedRange.toLowerCase() === rng.toLowerCase() ? "#0f172a" : "#94a3b8",
                  border: "none",
                  padding: "4px 10px",
                  borderRadius: "6px",
                  fontSize: "11px",
                  fontWeight: 700,
                  cursor: "pointer",
                }}
              >
                {rng}
              </button>
            ))}
          </div>
        )}
      </div>

      {/* SVG Plot Canvas */}
      {chartData.length === 0 ? (
        <div style={{ height: "240px", display: "flex", alignItems: "center", justifyContent: "center", color: "#64748b", fontStyle: "italic" }}>
          No historical telemetry records available in selected range.
        </div>
      ) : (
        <div style={{ position: "relative", width: "100%", overflowX: "auto" }}>
          <svg
            viewBox={`0 0 ${width} ${height}`}
            style={{ width: "100%", height: "auto", display: "block" }}
            onMouseLeave={() => setHoverIndex(null)}
          >
            {/* Grid lines */}
            {[0, 0.25, 0.5, 0.75, 1].map((ratio) => {
              const y = padTop + innerH * ratio;
              const val = maxY - ratio * (maxY - minY);
              return (
                <g key={ratio}>
                  <line
                    x1={padLeft}
                    y1={y}
                    x2={width - padRight}
                    y2={y}
                    stroke="rgba(255, 255, 255, 0.06)"
                    strokeDasharray="4 4"
                  />
                  <text
                    x={padLeft - 8}
                    y={y + 4}
                    fill="#64748b"
                    fontSize="10"
                    textAnchor="end"
                    fontFamily="monospace"
                  >
                    {val.toFixed(1)}
                  </text>
                </g>
              );
            })}

            {/* X-axis labels */}
            {chartData.map((d, i) => {
              // Show label at beginning, 1/3, 2/3, and end
              const step = Math.max(1, Math.floor(chartData.length / 4));
              if (i % step === 0 || i === chartData.length - 1) {
                const x = scaleX(i);
                return (
                  <text
                    key={i}
                    x={x}
                    y={height - 12}
                    fill="#64748b"
                    fontSize="10"
                    textAnchor="middle"
                    fontFamily="monospace"
                  >
                    {d.timeStr}
                  </text>
                );
              }
              return null;
            })}

            {/* Signal Curves */}
            {selectedSignals.map((sig) => {
              const sigIdx = availableSignals.indexOf(sig);
              const color = PALETTE[sigIdx % PALETTE.length];

              const points: string[] = [];
              chartData.forEach((d, i) => {
                const val = d[sig];
                if (typeof val === "number" && !isNaN(val)) {
                  points.push(`${scaleX(i)},${scaleY(val)}`);
                }
              });

              if (points.length === 0) return null;

              return (
                <g key={sig}>
                  <polyline
                    fill="none"
                    stroke={color}
                    strokeWidth="2.5"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    points={points.join(" ")}
                  />
                  {points.map((pt, i) => {
                    const [px, py] = pt.split(",").map(Number);
                    return (
                      <circle
                        key={i}
                        cx={px}
                        cy={py}
                        r="3"
                        fill={color}
                        onMouseEnter={() => setHoverIndex(i)}
                        style={{ cursor: "pointer" }}
                      />
                    );
                  })}
                </g>
              );
            })}

            {/* Hover cursor & guide */}
            {hoverIndex !== null && chartData[hoverIndex] && (
              <g>
                <line
                  x1={scaleX(hoverIndex)}
                  y1={padTop}
                  x2={scaleX(hoverIndex)}
                  y2={padTop + innerH}
                  stroke="#e2e8f0"
                  strokeWidth="1.5"
                  strokeDasharray="2 2"
                />
              </g>
            )}
          </svg>

          {/* Tooltip Overlay */}
          {hoverIndex !== null && chartData[hoverIndex] && (
            <div
              style={{
                position: "absolute",
                top: "10px",
                right: "10px",
                background: "rgba(15, 23, 42, 0.9)",
                backdropFilter: "blur(8px)",
                border: "1px solid rgba(255, 255, 255, 0.15)",
                borderRadius: "8px",
                padding: "10px 14px",
                fontSize: "12px",
                boxShadow: "0 8px 20px rgba(0, 0, 0, 0.4)",
                pointerEvents: "none",
                minWidth: "180px",
              }}
            >
              <div style={{ fontWeight: 700, color: "#f8fafc", marginBottom: "4px" }}>
                {chartData[hoverIndex].timeStr} (Seq #{chartData[hoverIndex].sequence})
              </div>
              {selectedSignals.map((sig) => {
                const sigIdx = availableSignals.indexOf(sig);
                const color = PALETTE[sigIdx % PALETTE.length];
                const val = chartData[hoverIndex][sig];
                return (
                  <div key={sig} style={{ display: "flex", justifyContent: "space-between", gap: "12px", color }}>
                    <span>{sig.replace(/_/g, " ")}:</span>
                    <span style={{ fontWeight: 700, fontFamily: "monospace" }}>
                      {typeof val === "number" ? val.toFixed(2) : "N/A"} {unitMap[sig] || ""}
                    </span>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      )}
    </div>
  );
};
