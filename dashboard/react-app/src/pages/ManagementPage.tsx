import React, { useState, useEffect } from "react";
import { apiClient } from "../api/client";
import {
  Server,
  Layers,
  RefreshCw,
  Play,
  CheckCircle2,
  XCircle,
  Clock,
  AlertTriangle,
  Sliders,
  Send,
  Zap,
} from "lucide-react";

interface FleetDevice {
  machine_id: string;
  machine_type: string;
  protocol: string;
  connectivity: string;
  management_state: string;
  software_version: string;
  firmware_version: string;
  config_version: string;
  metadata: Record<string, any>;
  last_seen: string | null;
}

interface FleetSummary {
  total_machines: number;
  online_count: number;
  offline_count: number;
  degraded_count: number;
  active_jobs_count: number;
  pending_sync_count: number;
}

interface DeviceShadow {
  device_id: string;
  desired_state: Record<string, any>;
  reported_state: Record<string, any>;
  delta: Record<string, any>;
  version: number;
  is_sync_pending: boolean;
  updated_at: string;
}

interface ManagementJob {
  job_id: string;
  machine_id: string;
  job_type: string;
  payload: Record<string, any>;
  status: string;
  attempt: number;
  max_attempts: number;
  error?: string | null;
  result?: Record<string, any> | null;
  created_at: string;
}

export const ManagementPage: React.FC = () => {
  const [devices, setDevices] = useState<FleetDevice[]>([]);
  const [summary, setSummary] = useState<FleetSummary | null>(null);
  const [selectedMachine, setSelectedMachine] = useState<string>("CNC-001");
  const [shadow, setShadow] = useState<DeviceShadow | null>(null);
  const [jobs, setJobs] = useState<ManagementJob[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [actionLoading, setActionLoading] = useState<boolean>(false);
  const [message, setMessage] = useState<{ text: string; type: "success" | "error" } | null>(null);

  // Form state for creating jobs
  const [jobType, setJobType] = useState<string>("CONFIG_UPDATE");
  const [operatingMode, setOperatingMode] = useState<string>("AUTO");
  const [samplingInterval, setSamplingInterval] = useState<number>(2.0);

  const fetchFleet = async () => {
    try {
      const [devs, sum, jbs] = await Promise.all([
        apiClient<FleetDevice[]>("/api/devices"),
        apiClient<FleetSummary>("/api/fleet/summary"),
        apiClient<ManagementJob[]>("/api/jobs?limit=20"),
      ]);
      setDevices(devs);
      setSummary(sum);
      setJobs(jbs);
      if (devs.length > 0 && !devs.find((d) => d.machine_id === selectedMachine)) {
        setSelectedMachine(devs[0].machine_id);
      }
    } catch (err: any) {
      console.error("Failed to load fleet data:", err);
    } finally {
      setLoading(false);
    }
  };

  const fetchShadow = async (mId: string) => {
    try {
      const sh = await apiClient<DeviceShadow>(`/api/devices/${mId}/shadow`);
      setShadow(sh);
    } catch (err: any) {
      console.error("Failed to load shadow:", err);
    }
  };

  useEffect(() => {
    fetchFleet();
    const interval = setInterval(fetchFleet, 5000);
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    if (selectedMachine) {
      fetchShadow(selectedMachine);
    }
  }, [selectedMachine]);

  const handleCreateConfigJob = async (e: React.FormEvent) => {
    e.preventDefault();
    setActionLoading(true);
    setMessage(null);
    try {
      const payload: Record<string, any> = {
        desired: {
          operating_mode: operatingMode,
          sampling_interval_sec: samplingInterval,
        },
        config_version: "1.2.0",
      };

      const newJob = await apiClient<ManagementJob>("/api/jobs", {
        method: "POST",
        body: JSON.stringify({
          machine_id: selectedMachine,
          job_type: jobType,
          payload,
          max_attempts: 3,
        }),
      });

      // Automatically trigger execution in local demo mode
      await apiClient(`/api/jobs/${newJob.job_id}/execute`, { method: "POST" });

      setMessage({ text: `Job ${newJob.job_id} dispatched and executed successfully!`, type: "success" });
      await fetchFleet();
      await fetchShadow(selectedMachine);
    } catch (err: any) {
      setMessage({ text: err?.message || "Failed to dispatch job", type: "error" });
    } finally {
      setActionLoading(false);
    }
  };

  const handleSyncShadow = async () => {
    if (!selectedMachine) return;
    setActionLoading(true);
    try {
      await apiClient(`/api/devices/${selectedMachine}/shadow/sync`, { method: "POST" });
      setMessage({ text: `Device shadow synchronized for ${selectedMachine}!`, type: "success" });
      await fetchShadow(selectedMachine);
      await fetchFleet();
    } catch (err: any) {
      setMessage({ text: err?.message || "Failed to sync shadow", type: "error" });
    } finally {
      setActionLoading(false);
    }
  };

  return (
    <div style={{ padding: "24px", maxWidth: "1400px", margin: "0 auto" }}>
      {/* Header */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "24px" }}>
        <div>
          <h1 style={{ fontSize: "24px", fontWeight: 700, margin: 0, color: "#f8fafc" }}>
            Fleet & Device Management
          </h1>
          <p style={{ fontSize: "14px", color: "#94a3b8", margin: "4px 0 0 0" }}>
            Local Device Shadow digital twins, configuration rollout jobs, and firmware state sync.
          </p>
        </div>
        <button
          onClick={() => {
            fetchFleet();
            if (selectedMachine) fetchShadow(selectedMachine);
          }}
          style={{
            display: "flex",
            alignItems: "center",
            gap: "8px",
            background: "rgba(30, 41, 59, 0.8)",
            border: "1px solid rgba(255, 255, 255, 0.1)",
            padding: "8px 16px",
            borderRadius: "6px",
            color: "#f8fafc",
            cursor: "pointer",
          }}
        >
          <RefreshCw size={16} /> Refresh
        </button>
      </div>

      {/* KPI Cards */}
      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))",
          gap: "16px",
          marginBottom: "24px",
        }}
      >
        <div style={{ background: "rgba(15, 23, 42, 0.8)", border: "1px solid rgba(255, 255, 255, 0.08)", padding: "16px", borderRadius: "8px" }}>
          <div style={{ fontSize: "12px", color: "#94a3b8", textTransform: "uppercase" }}>Total Machines</div>
          <div style={{ fontSize: "24px", fontWeight: 700, color: "#38bdf8", marginTop: "4px" }}>
            {summary?.total_machines ?? 12}
          </div>
        </div>
        <div style={{ background: "rgba(15, 23, 42, 0.8)", border: "1px solid rgba(255, 255, 255, 0.08)", padding: "16px", borderRadius: "8px" }}>
          <div style={{ fontSize: "12px", color: "#94a3b8", textTransform: "uppercase" }}>Online Fleet</div>
          <div style={{ fontSize: "24px", fontWeight: 700, color: "#4ade80", marginTop: "4px" }}>
            {summary?.online_count ?? 12}
          </div>
        </div>
        <div style={{ background: "rgba(15, 23, 42, 0.8)", border: "1px solid rgba(255, 255, 255, 0.08)", padding: "16px", borderRadius: "8px" }}>
          <div style={{ fontSize: "12px", color: "#94a3b8", textTransform: "uppercase" }}>Pending Sync Deltas</div>
          <div style={{ fontSize: "24px", fontWeight: 700, color: "#facc15", marginTop: "4px" }}>
            {summary?.pending_sync_count ?? 0}
          </div>
        </div>
        <div style={{ background: "rgba(15, 23, 42, 0.8)", border: "1px solid rgba(255, 255, 255, 0.08)", padding: "16px", borderRadius: "8px" }}>
          <div style={{ fontSize: "12px", color: "#94a3b8", textTransform: "uppercase" }}>Active Jobs</div>
          <div style={{ fontSize: "24px", fontWeight: 700, color: "#a855f7", marginTop: "4px" }}>
            {summary?.active_jobs_count ?? 0}
          </div>
        </div>
      </div>

      {message && (
        <div
          style={{
            padding: "12px 16px",
            borderRadius: "6px",
            marginBottom: "20px",
            background: message.type === "success" ? "rgba(34, 197, 94, 0.15)" : "rgba(239, 68, 68, 0.15)",
            border: `1px solid ${message.type === "success" ? "rgba(34, 197, 94, 0.4)" : "rgba(239, 68, 68, 0.4)"}`,
            color: message.type === "success" ? "#4ade80" : "#f87171",
            display: "flex",
            alignItems: "center",
            gap: "8px",
          }}
        >
          {message.type === "success" ? <CheckCircle2 size={18} /> : <AlertTriangle size={18} />}
          <span>{message.text}</span>
        </div>
      )}

      {/* Main Grid: Machine Selector & Shadow on Left, Jobs & Actions on Right */}
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "24px" }}>
        {/* Left Column: Fleet Selection & Device Shadow */}
        <div style={{ display: "flex", flexDirection: "column", gap: "24px" }}>
          {/* Machine Inventory Table */}
          <div style={{ background: "rgba(15, 23, 42, 0.8)", border: "1px solid rgba(255, 255, 255, 0.08)", borderRadius: "8px", padding: "16px" }}>
            <h2 style={{ fontSize: "16px", fontWeight: 600, margin: "0 0 16px 0", color: "#f8fafc", display: "flex", alignItems: "center", gap: "8px" }}>
              <Server size={18} color="#38bdf8" /> Factory Fleet Devices
            </h2>
            <div style={{ overflowX: "auto", maxHeight: "280px" }}>
              <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "13px" }}>
                <thead>
                  <tr style={{ borderBottom: "1px solid rgba(255, 255, 255, 0.1)", color: "#94a3b8", textAlign: "left" }}>
                    <th style={{ padding: "8px" }}>Machine</th>
                    <th style={{ padding: "8px" }}>Protocol</th>
                    <th style={{ padding: "8px" }}>Status</th>
                    <th style={{ padding: "8px" }}>FW / Config</th>
                    <th style={{ padding: "8px" }}>Action</th>
                  </tr>
                </thead>
                <tbody>
                  {devices.map((d) => (
                    <tr
                      key={d.machine_id}
                      style={{
                        borderBottom: "1px solid rgba(255, 255, 255, 0.04)",
                        background: selectedMachine === d.machine_id ? "rgba(56, 189, 248, 0.1)" : "transparent",
                      }}
                    >
                      <td style={{ padding: "8px", fontWeight: 600, color: "#f8fafc" }}>{d.machine_id}</td>
                      <td style={{ padding: "8px", color: "#94a3b8" }}>{d.protocol}</td>
                      <td style={{ padding: "8px" }}>
                        <span
                          style={{
                            padding: "2px 8px",
                            borderRadius: "4px",
                            fontSize: "11px",
                            fontWeight: 600,
                            background: d.connectivity === "ONLINE" ? "rgba(34, 197, 94, 0.2)" : "rgba(239, 68, 68, 0.2)",
                            color: d.connectivity === "ONLINE" ? "#4ade80" : "#f87171",
                          }}
                        >
                          {d.connectivity}
                        </span>
                      </td>
                      <td style={{ padding: "8px", color: "#cbd5e1", fontSize: "12px" }}>
                        {d.firmware_version} / v{d.config_version}
                      </td>
                      <td style={{ padding: "8px" }}>
                        <button
                          onClick={() => setSelectedMachine(d.machine_id)}
                          style={{
                            padding: "4px 8px",
                            borderRadius: "4px",
                            background: selectedMachine === d.machine_id ? "#0284c7" : "rgba(255, 255, 255, 0.08)",
                            border: "none",
                            color: "#f8fafc",
                            cursor: "pointer",
                            fontSize: "12px",
                          }}
                        >
                          Inspect
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* Device Shadow View */}
          <div style={{ background: "rgba(15, 23, 42, 0.8)", border: "1px solid rgba(255, 255, 255, 0.08)", borderRadius: "8px", padding: "16px" }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "16px" }}>
              <h2 style={{ fontSize: "16px", fontWeight: 600, margin: 0, color: "#f8fafc", display: "flex", alignItems: "center", gap: "8px" }}>
                <Layers size={18} color="#38bdf8" /> Shadow State: {selectedMachine}
              </h2>
              {shadow && (
                <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                  <span style={{ fontSize: "12px", color: "#94a3b8" }}>v{shadow.version}</span>
                  {shadow.is_sync_pending ? (
                    <span style={{ padding: "2px 8px", borderRadius: "4px", background: "rgba(234, 179, 8, 0.2)", color: "#facc15", fontSize: "11px", fontWeight: 600 }}>
                      Sync Pending
                    </span>
                  ) : (
                    <span style={{ padding: "2px 8px", borderRadius: "4px", background: "rgba(34, 197, 94, 0.2)", color: "#4ade80", fontSize: "11px", fontWeight: 600 }}>
                      In Sync
                    </span>
                  )}
                </div>
              )}
            </div>

            {shadow ? (
              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "12px" }}>
                <div style={{ background: "rgba(0, 0, 0, 0.3)", padding: "12px", borderRadius: "6px" }}>
                  <div style={{ fontSize: "12px", fontWeight: 600, color: "#38bdf8", marginBottom: "8px" }}>
                    Desired State
                  </div>
                  <pre style={{ fontSize: "12px", color: "#cbd5e1", margin: 0, whiteSpace: "pre-wrap" }}>
                    {JSON.stringify(shadow.desired_state, null, 2)}
                  </pre>
                </div>
                <div style={{ background: "rgba(0, 0, 0, 0.3)", padding: "12px", borderRadius: "6px" }}>
                  <div style={{ fontSize: "12px", fontWeight: 600, color: "#4ade80", marginBottom: "8px" }}>
                    Reported State
                  </div>
                  <pre style={{ fontSize: "12px", color: "#cbd5e1", margin: 0, whiteSpace: "pre-wrap" }}>
                    {JSON.stringify(shadow.reported_state, null, 2)}
                  </pre>
                </div>
              </div>
            ) : (
              <div style={{ color: "#94a3b8", fontSize: "13px" }}>Loading shadow...</div>
            )}

            {shadow && shadow.is_sync_pending && (
              <div style={{ marginTop: "12px", display: "flex", justifyContent: "flex-end" }}>
                <button
                  onClick={handleSyncShadow}
                  disabled={actionLoading}
                  style={{
                    padding: "6px 14px",
                    borderRadius: "6px",
                    background: "#0284c7",
                    border: "none",
                    color: "#f8fafc",
                    fontSize: "13px",
                    fontWeight: 600,
                    cursor: "pointer",
                    display: "flex",
                    alignItems: "center",
                    gap: "6px",
                  }}
                >
                  <Zap size={14} /> Synchronize Reported State
                </button>
              </div>
            )}
          </div>
        </div>

        {/* Right Column: Create Management Job & Job History */}
        <div style={{ display: "flex", flexDirection: "column", gap: "24px" }}>
          {/* Create Job Form */}
          <div style={{ background: "rgba(15, 23, 42, 0.8)", border: "1px solid rgba(255, 255, 255, 0.08)", borderRadius: "8px", padding: "16px" }}>
            <h2 style={{ fontSize: "16px", fontWeight: 600, margin: "0 0 16px 0", color: "#f8fafc", display: "flex", alignItems: "center", gap: "8px" }}>
              <Sliders size={18} color="#a855f7" /> Create Management Job
            </h2>
            <form onSubmit={handleCreateConfigJob} style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
              <div>
                <label style={{ fontSize: "12px", color: "#94a3b8", display: "block", marginBottom: "4px" }}>
                  Target Machine
                </label>
                <select
                  value={selectedMachine}
                  onChange={(e) => setSelectedMachine(e.target.value)}
                  style={{
                    width: "100%",
                    padding: "8px",
                    borderRadius: "6px",
                    background: "rgba(30, 41, 59, 0.8)",
                    border: "1px solid rgba(255, 255, 255, 0.1)",
                    color: "#f8fafc",
                    fontSize: "13px",
                  }}
                >
                  {devices.map((d) => (
                    <option key={d.machine_id} value={d.machine_id}>
                      {d.machine_id} ({d.machine_type})
                    </option>
                  ))}
                </select>
              </div>

              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "12px" }}>
                <div>
                  <label style={{ fontSize: "12px", color: "#94a3b8", display: "block", marginBottom: "4px" }}>
                    Job Type
                  </label>
                  <select
                    value={jobType}
                    onChange={(e) => setJobType(e.target.value)}
                    style={{
                      width: "100%",
                      padding: "8px",
                      borderRadius: "6px",
                      background: "rgba(30, 41, 59, 0.8)",
                      border: "1px solid rgba(255, 255, 255, 0.1)",
                      color: "#f8fafc",
                      fontSize: "13px",
                    }}
                  >
                    <option value="CONFIG_UPDATE">CONFIG_UPDATE</option>
                    <option value="OTA_SIMULATION">OTA_SIMULATION</option>
                    <option value="RESTART_SIMULATION">RESTART_SIMULATION</option>
                    <option value="SYNC_STATE">SYNC_STATE</option>
                  </select>
                </div>

                <div>
                  <label style={{ fontSize: "12px", color: "#94a3b8", display: "block", marginBottom: "4px" }}>
                    Operating Mode
                  </label>
                  <select
                    value={operatingMode}
                    onChange={(e) => setOperatingMode(e.target.value)}
                    style={{
                      width: "100%",
                      padding: "8px",
                      borderRadius: "6px",
                      background: "rgba(30, 41, 59, 0.8)",
                      border: "1px solid rgba(255, 255, 255, 0.1)",
                      color: "#f8fafc",
                      fontSize: "13px",
                    }}
                  >
                    <option value="AUTO">AUTO</option>
                    <option value="MANUAL">MANUAL</option>
                    <option value="MAINTENANCE">MAINTENANCE</option>
                    <option value="STANDBY">STANDBY</option>
                  </select>
                </div>
              </div>

              <div>
                <label style={{ fontSize: "12px", color: "#94a3b8", display: "block", marginBottom: "4px" }}>
                  Sampling Interval (Seconds)
                </label>
                <input
                  type="number"
                  step="0.5"
                  min="0.5"
                  max="60"
                  value={samplingInterval}
                  onChange={(e) => setSamplingInterval(parseFloat(e.target.value))}
                  style={{
                    width: "100%",
                    padding: "8px",
                    borderRadius: "6px",
                    background: "rgba(30, 41, 59, 0.8)",
                    border: "1px solid rgba(255, 255, 255, 0.1)",
                    color: "#f8fafc",
                    fontSize: "13px",
                    boxSizing: "border-box",
                  }}
                />
              </div>

              <button
                type="submit"
                disabled={actionLoading}
                style={{
                  marginTop: "8px",
                  padding: "10px",
                  borderRadius: "6px",
                  background: "linear-gradient(135deg, #0284c7, #38bdf8)",
                  border: "none",
                  color: "#0f172a",
                  fontWeight: 700,
                  fontSize: "14px",
                  cursor: "pointer",
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  gap: "8px",
                }}
              >
                <Send size={16} /> Dispatch & Execute Job
              </button>
            </form>
          </div>

          {/* Recent Jobs History Table */}
          <div style={{ background: "rgba(15, 23, 42, 0.8)", border: "1px solid rgba(255, 255, 255, 0.08)", borderRadius: "8px", padding: "16px" }}>
            <h2 style={{ fontSize: "16px", fontWeight: 600, margin: "0 0 16px 0", color: "#f8fafc", display: "flex", alignItems: "center", gap: "8px" }}>
              <Clock size={18} color="#facc15" /> Recent Management Jobs
            </h2>
            <div style={{ overflowX: "auto", maxHeight: "280px" }}>
              <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "13px" }}>
                <thead>
                  <tr style={{ borderBottom: "1px solid rgba(255, 255, 255, 0.1)", color: "#94a3b8", textAlign: "left" }}>
                    <th style={{ padding: "8px" }}>Job ID</th>
                    <th style={{ padding: "8px" }}>Target</th>
                    <th style={{ padding: "8px" }}>Type</th>
                    <th style={{ padding: "8px" }}>Status</th>
                    <th style={{ padding: "8px" }}>Attempts</th>
                  </tr>
                </thead>
                <tbody>
                  {jobs.map((j) => (
                    <tr key={j.job_id} style={{ borderBottom: "1px solid rgba(255, 255, 255, 0.04)" }}>
                      <td style={{ padding: "8px", color: "#38bdf8", fontFamily: "monospace" }}>{j.job_id}</td>
                      <td style={{ padding: "8px", fontWeight: 600, color: "#f8fafc" }}>{j.machine_id}</td>
                      <td style={{ padding: "8px", color: "#94a3b8", fontSize: "12px" }}>{j.job_type}</td>
                      <td style={{ padding: "8px" }}>
                        <span
                          style={{
                            padding: "2px 8px",
                            borderRadius: "4px",
                            fontSize: "11px",
                            fontWeight: 600,
                            background:
                              j.status === "SUCCEEDED"
                                ? "rgba(34, 197, 94, 0.2)"
                                : j.status === "FAILED"
                                ? "rgba(239, 68, 68, 0.2)"
                                : "rgba(234, 179, 8, 0.2)",
                            color:
                              j.status === "SUCCEEDED"
                                ? "#4ade80"
                                : j.status === "FAILED"
                                ? "#f87171"
                                : "#facc15",
                          }}
                        >
                          {j.status}
                        </span>
                      </td>
                      <td style={{ padding: "8px", color: "#cbd5e1" }}>
                        {j.attempt} / {j.max_attempts}
                      </td>
                    </tr>
                  ))}
                  {jobs.length === 0 && (
                    <tr>
                      <td colSpan={5} style={{ padding: "16px", textAlign: "center", color: "#94a3b8" }}>
                        No management jobs dispatched yet.
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
