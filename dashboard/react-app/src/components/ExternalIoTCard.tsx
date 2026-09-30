import React, { useState, useEffect } from "react";
import { ExternalIoTDevice, RealtimeTelemetryEvent } from "../types";
import { Radio, Thermometer, Droplets, Cpu, Sparkles, Activity, Clock, ShieldCheck, Zap } from "lucide-react";

interface ExternalIoTCardProps {
  device: ExternalIoTDevice;
  liveEvent?: RealtimeTelemetryEvent;
}

export const ExternalIoTCard: React.FC<ExternalIoTCardProps> = ({ device, liveEvent }) => {
  const [history, setHistory] = useState<Array<{ time: string; temp: number; hum: number }>>([]);

  // Extract latest dynamic measurements from live SSE event or initial device state
  const rawMeasurements = liveEvent?.measurements || {};
  const tempRaw = rawMeasurements.temperature_c ?? rawMeasurements.temperatureC ?? device.latest_temperature_c;
  const humRaw = rawMeasurements.humidity_pct ?? rawMeasurements.humidityPct ?? device.latest_humidity_pct;
  const currentTemp = typeof tempRaw === "number" ? tempRaw : null;
  const currentHum = typeof humRaw === "number" ? humRaw : null;
  const sequence = liveEvent?.sequence ?? device.latest_sequence ?? 0;
  const eventTime = liveEvent?.event_time ?? device.last_seen;

  // Append new telemetry points to the local history for the mini trend line
  useEffect(() => {
    if (currentTemp !== null && currentHum !== null) {
      const timeStr = eventTime ? new Date(eventTime).toLocaleTimeString() : new Date().toLocaleTimeString();
      setHistory((prev) => {
        const next = [...prev, { time: timeStr, temp: currentTemp, hum: currentHum }];
        return next.slice(-20); // Keep last 20 data points for sparkline
      });
    }
  }, [currentTemp, currentHum, sequence, eventTime]);

  // Determine connection badge & freshness
  const isLive = Boolean(liveEvent);
  const status = isLive ? "ONLINE" : (device.connection_status || "OFFLINE");
  const isOnline = status === "ONLINE";

  // Temperature status classification
  const isCriticalTemp = currentTemp !== null && currentTemp >= 35.0;
  const isWarningTemp = currentTemp !== null && currentTemp >= 30.0;
  const tempColor = isCriticalTemp ? "#f43f5e" : isWarningTemp ? "#fbbf24" : "#38bdf8";

  // Actuator LED state
  const actuatorState = device.actuator_state?.state || (isWarningTemp ? "ON" : "OFF");

  return (
    <div
      className="glass-panel"
      style={{
        padding: "20px 24px",
        background: "linear-gradient(135deg, rgba(15, 23, 42, 0.85), rgba(30, 41, 59, 0.7))",
        border: "1px solid rgba(6, 182, 212, 0.3)",
        borderRadius: "14px",
        boxShadow: "0 8px 32px rgba(0, 0, 0, 0.35)",
        position: "relative",
        overflow: "hidden",
      }}
    >
      {/* Top Banner & Header */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: "16px" }}>
        <div>
          <div style={{ display: "flex", alignItems: "center", gap: "8px", marginBottom: "4px" }}>
            <span
              style={{
                display: "inline-flex",
                alignItems: "center",
                gap: "4px",
                padding: "2px 8px",
                borderRadius: "6px",
                fontSize: "10px",
                fontWeight: 800,
                letterSpacing: "0.05em",
                background: "rgba(6, 182, 212, 0.15)",
                color: "#22d3ee",
                border: "1px solid rgba(6, 182, 212, 0.4)",
              }}
            >
              <Radio size={12} />
              EXTERNAL IOT NODE
            </span>
            <span
              style={{
                display: "inline-flex",
                alignItems: "center",
                gap: "4px",
                padding: "2px 8px",
                borderRadius: "6px",
                fontSize: "10px",
                fontWeight: 700,
                background: "rgba(148, 163, 184, 0.1)",
                color: "#94a3b8",
              }}
            >
              <Cpu size={12} />
              Raspberry Pi Pico W
            </span>
          </div>
          <h3 style={{ fontSize: "20px", fontWeight: 800, color: "#f8fafc", margin: 0 }}>
            {device.device_id}
          </h3>
          <span style={{ fontSize: "12px", color: "#94a3b8" }}>
            Ambient Environment Sensor (DHT22) &bull; {device.plant_id} / {device.line_id}
          </span>
        </div>

        {/* Live Status Badge */}
        <div style={{ display: "flex", flexDirection: "column", alignItems: "flex-end", gap: "6px" }}>
          <span
            style={{
              display: "inline-flex",
              alignItems: "center",
              gap: "6px",
              padding: "4px 10px",
              borderRadius: "9999px",
              fontSize: "11px",
              fontWeight: 700,
              background: isOnline ? "rgba(16, 185, 129, 0.15)" : "rgba(148, 163, 184, 0.15)",
              color: isOnline ? "#34d399" : "#94a3b8",
              border: `1px solid ${isOnline ? "rgba(16, 185, 129, 0.3)" : "rgba(148, 163, 184, 0.2)"}`,
            }}
          >
            <span
              style={{
                width: "8px",
                height: "8px",
                borderRadius: "50%",
                background: isOnline ? "#10b981" : "#64748b",
                boxShadow: isOnline ? "0 0 8px #10b981" : "none",
                animation: isOnline ? "pulse 2s infinite" : "none",
              }}
            />
            {status}
          </span>
          <span style={{ fontSize: "10px", color: "#64748b", fontFamily: "'JetBrains Mono', monospace" }}>
            Seq #{sequence}
          </span>
        </div>
      </div>

      {/* Primary Metrics Grid */}
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "1fr 1fr",
          gap: "14px",
          marginBottom: "16px",
        }}
      >
        {/* Temperature Card */}
        <div
          style={{
            background: "rgba(15, 23, 42, 0.6)",
            border: `1px solid ${isWarningTemp ? "rgba(245, 158, 11, 0.4)" : "rgba(56, 189, 248, 0.2)"}`,
            borderRadius: "10px",
            padding: "14px",
            display: "flex",
            flexDirection: "column",
            gap: "4px",
          }}
        >
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
            <span style={{ fontSize: "11px", fontWeight: 700, color: "#94a3b8", textTransform: "uppercase", display: "flex", alignItems: "center", gap: "5px" }}>
              <Thermometer size={14} color={tempColor} />
              Temperature
            </span>
            {isWarningTemp && (
              <span style={{ fontSize: "9px", fontWeight: 800, padding: "1px 6px", borderRadius: "4px", background: "rgba(245, 158, 11, 0.2)", color: "#fbbf24" }}>
                {isCriticalTemp ? "CRITICAL" : "HIGH"}
              </span>
            )}
          </div>
          <div style={{ display: "flex", alignItems: "baseline", gap: "4px" }}>
            <span style={{ fontSize: "26px", fontWeight: 900, color: tempColor, fontFamily: "'JetBrains Mono', monospace" }}>
              {currentTemp !== null ? currentTemp.toFixed(1) : "--.-"}
            </span>
            <span style={{ fontSize: "14px", fontWeight: 700, color: "#94a3b8" }}>°C</span>
          </div>
          <span style={{ fontSize: "10px", color: "#64748b" }}>
            Threshold: &ge;30°C Warn / &ge;35°C Crit
          </span>
        </div>

        {/* Humidity Card */}
        <div
          style={{
            background: "rgba(15, 23, 42, 0.6)",
            border: "1px solid rgba(16, 185, 129, 0.2)",
            borderRadius: "10px",
            padding: "14px",
            display: "flex",
            flexDirection: "column",
            gap: "4px",
          }}
        >
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
            <span style={{ fontSize: "11px", fontWeight: 700, color: "#94a3b8", textTransform: "uppercase", display: "flex", alignItems: "center", gap: "5px" }}>
              <Droplets size={14} color="#34d399" />
              Rel. Humidity
            </span>
          </div>
          <div style={{ display: "flex", alignItems: "baseline", gap: "4px" }}>
            <span style={{ fontSize: "26px", fontWeight: 900, color: "#34d399", fontFamily: "'JetBrains Mono', monospace" }}>
              {currentHum !== null ? currentHum.toFixed(1) : "--.-"}
            </span>
            <span style={{ fontSize: "14px", fontWeight: 700, color: "#94a3b8" }}>%</span>
          </div>
          <span style={{ fontSize: "10px", color: "#64748b" }}>
            DHT22 Range: 0–100% RH
          </span>
        </div>
      </div>

      {/* Mini Trend Line Sparkline */}
      {history.length > 1 && (
        <div style={{ marginBottom: "14px" }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "6px" }}>
            <span style={{ fontSize: "11px", fontWeight: 700, color: "#94a3b8", display: "flex", alignItems: "center", gap: "4px" }}>
              <Activity size={12} color="#06b6d4" /> Live Ingress Stream ({history.length} samples)
            </span>
            <span style={{ fontSize: "10px", color: "#64748b", fontFamily: "'JetBrains Mono', monospace" }}>
              {history[history.length - 1]?.time}
            </span>
          </div>
          <div
            style={{
              height: "40px",
              background: "rgba(15, 23, 42, 0.5)",
              borderRadius: "6px",
              padding: "4px 8px",
              display: "flex",
              alignItems: "flex-end",
              gap: "3px",
              overflow: "hidden",
            }}
          >
            {history.map((pt, idx) => {
              // Normalize temp between 20°C and 45°C
              const heightPct = Math.min(100, Math.max(15, ((pt.temp - 20) / 25) * 100));
              const barColor = pt.temp >= 35 ? "#f43f5e" : pt.temp >= 30 ? "#fbbf24" : "#06b6d4";
              return (
                <div
                  key={idx}
                  title={`Time: ${pt.time} | Temp: ${pt.temp}°C | Hum: ${pt.hum}%`}
                  style={{
                    flex: 1,
                    height: `${heightPct}%`,
                    background: barColor,
                    borderRadius: "2px",
                    opacity: 0.6 + (idx / history.length) * 0.4,
                    transition: "height 0.3s ease",
                  }}
                />
              );
            })}
          </div>
        </div>
      )}

      {/* Footer Details: Actuator, Ingress Broker & Firmware */}
      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          paddingTop: "12px",
          borderTop: "1px solid rgba(255, 255, 255, 0.06)",
          fontSize: "11px",
          color: "#94a3b8",
          flexWrap: "wrap",
          gap: "8px",
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: "6px" }}>
          <Zap size={13} color={actuatorState === "ON" ? "#fbbf24" : "#64748b"} />
          <span>LED Actuator: </span>
          <strong style={{ color: actuatorState === "ON" ? "#fbbf24" : "#94a3b8" }}>{actuatorState}</strong>
          <span style={{ color: "#64748b" }}>({device.control_state?.mode || "AUTO"})</span>
        </div>

        <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
          <span>
            Broker: <strong style={{ color: "#38bdf8", fontFamily: "'JetBrains Mono', monospace" }}>{device.ingress_broker || "broker.hivemq.com"}</strong>
          </span>
          <span>
            FW: <strong style={{ color: "#cbd5e1" }}>{device.firmware_version || "0.1.0"}</strong>
          </span>
        </div>
      </div>
    </div>
  );
};
