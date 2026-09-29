import React, { useState, useEffect } from "react";
import { Activity, Play, CheckCircle2, XCircle, AlertTriangle, RefreshCw, Layers, Database, Cpu, Radio, ShieldCheck } from "lucide-react";

interface ResilienceStatus {
  event_bus: string;
  primary_database: string;
  ml_inference: string;
  alert_engine: string;
  protocol_adapters: string;
  buffer_queue: string;
  active_injected_faults: string[];
}

interface ScenarioResult {
  scenario_type: string;
  scenario_name: string;
  target_component: string;
  status: "PASSED" | "FAILED" | "DEGRADED";
  duration_seconds: number;
  expected_behavior: string;
  observed_behavior: string;
  assertions_passed: string[];
  assertions_failed: string[];
}

export const ResiliencePage: React.FC = () => {
  const [resilienceStatus, setResilienceStatus] = useState<ResilienceStatus | null>(null);
  const [results, setResults] = useState<ScenarioResult[]>([]);
  const [loading, setLoading] = useState(false);
  const [runningTests, setRunningTests] = useState(false);

  const fetchStatusAndResults = async () => {
    setLoading(true);
    try {
      const [statusRes, resultsRes] = await Promise.all([
        fetch("/api/resilience/status"),
        fetch("/api/resilience/results"),
      ]);

      if (statusRes.ok) {
        setResilienceStatus(await statusRes.json());
      }
      if (resultsRes.ok) {
        setResults(await resultsRes.json());
      }
    } catch (e) {
      console.error("Failed to load resilience data", e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchStatusAndResults();
  }, []);

  const handleRunAllTests = async () => {
    setRunningTests(true);
    try {
      const token = localStorage.getItem("factory_auth_token");
      const headers: Record<string, string> = { "Content-Type": "application/json" };
      if (token) {
        headers["Authorization"] = `Bearer ${token}`;
      }

      const res = await fetch("/api/resilience/run", {
        method: "POST",
        headers,
        body: JSON.stringify({}),
      });

      if (res.ok) {
        const data = await res.json();
        setResults(data);
      }
    } catch (e) {
      console.error("Failed to execute failure tests", e);
    } finally {
      setRunningTests(false);
      fetchStatusAndResults();
    }
  };

  const getStatusBadge = (statusStr: string) => {
    const isHealthy = statusStr === "HEALTHY" || statusStr === "ACTIVE" || statusStr === "PASSED";
    const isDegraded = statusStr === "DEGRADED" || statusStr === "WARNING";
    const bg = isHealthy ? "rgba(16, 185, 129, 0.15)" : isDegraded ? "rgba(245, 158, 11, 0.15)" : "rgba(239, 68, 68, 0.15)";
    const color = isHealthy ? "#10b981" : isDegraded ? "#f59e0b" : "#ef4444";
    return (
      <span style={{ padding: "4px 10px", borderRadius: "9999px", fontSize: "11px", fontWeight: 700, background: bg, color }}>
        {statusStr}
      </span>
    );
  };

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "28px" }}>
      {/* Title & Actions */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: "16px" }}>
        <div>
          <h1 style={{ fontSize: "28px", fontWeight: 800, color: "#f8fafc", margin: 0, letterSpacing: "-0.02em" }}>
            Pipeline Resilience & Recovery
          </h1>
          <p style={{ fontSize: "14px", color: "#94a3b8", margin: "6px 0 0 0" }}>
            Deterministic failure injection, store-and-forward buffer replay, and invariant verification.
          </p>
        </div>

        <button
          onClick={handleRunAllTests}
          disabled={runningTests}
          style={{
            display: "inline-flex",
            alignItems: "center",
            gap: "8px",
            padding: "10px 18px",
            borderRadius: "8px",
            border: "none",
            background: "linear-gradient(135deg, #0284c7, #38bdf8)",
            color: "#0f172a",
            fontWeight: 800,
            fontSize: "13px",
            cursor: runningTests ? "not-allowed" : "pointer",
            boxShadow: "0 0 16px rgba(56, 189, 248, 0.3)",
          }}
        >
          {runningTests ? <RefreshCw size={16} className="animate-spin" /> : <Play size={16} />}
          {runningTests ? "Running Injections..." : "Run Failure Verification Suite"}
        </button>
      </div>

      {/* Component Health Grid */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))", gap: "14px" }}>
        <div style={{ background: "rgba(30, 41, 59, 0.5)", border: "1px solid rgba(255, 255, 255, 0.08)", borderRadius: "10px", padding: "16px" }}>
          <div style={{ display: "flex", alignItems: "center", gap: "8px", color: "#38bdf8", marginBottom: "6px" }}>
            <Radio size={16} />
            <span style={{ fontSize: "12px", fontWeight: 600 }}>MQTT Event Bus</span>
          </div>
          <div>{getStatusBadge(resilienceStatus?.event_bus || "HEALTHY")}</div>
        </div>

        <div style={{ background: "rgba(30, 41, 59, 0.5)", border: "1px solid rgba(255, 255, 255, 0.08)", borderRadius: "10px", padding: "16px" }}>
          <div style={{ display: "flex", alignItems: "center", gap: "8px", color: "#60a5fa", marginBottom: "6px" }}>
            <Database size={16} />
            <span style={{ fontSize: "12px", fontWeight: 600 }}>PostgreSQL Primary</span>
          </div>
          <div>{getStatusBadge(resilienceStatus?.primary_database || "HEALTHY")}</div>
        </div>

        <div style={{ background: "rgba(30, 41, 59, 0.5)", border: "1px solid rgba(255, 255, 255, 0.08)", borderRadius: "10px", padding: "16px" }}>
          <div style={{ display: "flex", alignItems: "center", gap: "8px", color: "#c084fc", marginBottom: "6px" }}>
            <Cpu size={16} />
            <span style={{ fontSize: "12px", fontWeight: 600 }}>ML Inference</span>
          </div>
          <div>{getStatusBadge(resilienceStatus?.ml_inference || "HEALTHY")}</div>
        </div>

        <div style={{ background: "rgba(30, 41, 59, 0.5)", border: "1px solid rgba(255, 255, 255, 0.08)", borderRadius: "10px", padding: "16px" }}>
          <div style={{ display: "flex", alignItems: "center", gap: "8px", color: "#f59e0b", marginBottom: "6px" }}>
            <Layers size={16} />
            <span style={{ fontSize: "12px", fontWeight: 600 }}>Store-and-Forward</span>
          </div>
          <div>{getStatusBadge(resilienceStatus?.buffer_queue || "ACTIVE")}</div>
        </div>
      </div>

      {/* Test Results Table */}
      <div style={{ background: "rgba(30, 41, 59, 0.5)", border: "1px solid rgba(255, 255, 255, 0.08)", borderRadius: "12px", padding: "24px" }}>
        <h2 style={{ fontSize: "16px", fontWeight: 700, color: "#f8fafc", margin: "0 0 16px 0", display: "flex", alignItems: "center", gap: "8px" }}>
          <ShieldCheck size={18} color="#10b981" /> End-to-End Failure & Recovery Verification Results
        </h2>

        <div style={{ overflowX: "auto" }}>
          <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "12px", textAlign: "left" }}>
            <thead>
              <tr style={{ borderBottom: "1px solid rgba(255, 255, 255, 0.1)", color: "#94a3b8" }}>
                <th style={{ padding: "10px" }}>Scenario</th>
                <th style={{ padding: "10px" }}>Target</th>
                <th style={{ padding: "10px" }}>Result</th>
                <th style={{ padding: "10px" }}>Duration</th>
                <th style={{ padding: "10px" }}>Observed Recovery Behavior</th>
              </tr>
            </thead>
            <tbody>
              {results.length > 0 ? (
                results.map((res) => (
                  <tr key={res.scenario_name} style={{ borderBottom: "1px solid rgba(255, 255, 255, 0.04)", color: "#e2e8f0" }}>
                    <td style={{ padding: "10px", fontWeight: 700, color: "#f8fafc" }}>{res.scenario_name}</td>
                    <td style={{ padding: "10px", fontFamily: "monospace", color: "#94a3b8" }}>{res.target_component}</td>
                    <td style={{ padding: "10px" }}>{getStatusBadge(res.status)}</td>
                    <td style={{ padding: "10px", fontFamily: "monospace" }}>{res.duration_seconds.toFixed(3)}s</td>
                    <td style={{ padding: "10px", color: "#cbd5e1", maxWidth: "450px" }}>{res.observed_behavior}</td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan={5} style={{ padding: "20px", textAlign: "center", color: "#64748b" }}>
                    Click "Run Failure Verification Suite" to execute test suite.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
