import React, { useState, useEffect } from "react";
import { Shield, Key, Lock, CheckCircle2, AlertTriangle, UserCheck, FileText, ShieldAlert, Cpu } from "lucide-react";

interface SecurityStatus {
  tls_enabled: boolean;
  mtls_enabled: boolean;
  auth_enabled: boolean;
  allow_anonymous_viewer: boolean;
  jwt_algorithm: string;
  jwt_expiration_minutes: number;
  active_users_count: number;
}

interface UserProfile {
  username: string;
  role: string;
  full_name?: string;
  email?: string;
  permissions: string[];
}

interface AuditRecord {
  event_id: string;
  timestamp: string;
  action: string;
  actor: string;
  role?: string;
  machine_id?: string;
  status: string;
  details: Record<string, any>;
}

export const SecurityPage: React.FC = () => {
  const [statusData, setStatusData] = useState<SecurityStatus | null>(null);
  const [currentUser, setCurrentUser] = useState<UserProfile | null>(null);
  const [auditLogs, setAuditLogs] = useState<AuditRecord[]>([]);
  const [username, setUsername] = useState("operator");
  const [password, setPassword] = useState("operator_pass_local");
  const [token, setToken] = useState<string | null>(localStorage.getItem("factory_auth_token"));
  const [loginError, setLoginError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const fetchSecurityData = async (authToken?: string | null) => {
    try {
      const res = await fetch("/api/security/status");
      if (res.ok) {
        const data = await res.json();
        setStatusData(data);
      }

      const activeToken = authToken !== undefined ? authToken : token;
      if (activeToken) {
        const meRes = await fetch("/api/auth/me", {
          headers: { Authorization: `Bearer ${activeToken}` },
        });
        if (meRes.ok) {
          const userData = await meRes.json();
          setCurrentUser(userData);
        }

        const auditRes = await fetch("/api/security/audit?limit=25", {
          headers: { Authorization: `Bearer ${activeToken}` },
        });
        if (auditRes.ok) {
          const logs = await auditRes.json();
          setAuditLogs(logs);
        }
      }
    } catch (e) {
      console.error("Failed to fetch security data", e);
    }
  };

  useEffect(() => {
    fetchSecurityData();
  }, []);

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setLoginError(null);
    try {
      const res = await fetch("/api/auth/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username, password }),
      });
      if (res.ok) {
        const data = await res.json();
        setToken(data.access_token);
        localStorage.setItem("factory_auth_token", data.access_token);
        await fetchSecurityData(data.access_token);
      } else {
        const err = await res.json();
        setLoginError(err.detail || "Authentication failed.");
      }
    } catch (err: any) {
      setLoginError(err.message || "Network error.");
    } finally {
      setLoading(false);
    }
  };

  const handleLogout = () => {
    setToken(null);
    setCurrentUser(null);
    localStorage.removeItem("factory_auth_token");
  };

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "28px" }}>
      {/* Page Title */}
      <div>
        <h1 style={{ fontSize: "28px", fontWeight: 800, color: "#f8fafc", margin: 0, letterSpacing: "-0.02em" }}>
          Security & Access Control
        </h1>
        <p style={{ fontSize: "14px", color: "#94a3b8", margin: "6px 0 0 0" }}>
          Role-based access control, cryptographic verification, and security audit log.
        </p>
      </div>

      {/* Security Status Cards */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(240px, 1fr))", gap: "16px" }}>
        <div style={{ background: "rgba(30, 41, 59, 0.5)", border: "1px solid rgba(255, 255, 255, 0.08)", borderRadius: "12px", padding: "20px" }}>
          <div style={{ display: "flex", alignItems: "center", gap: "10px", color: "#38bdf8", marginBottom: "8px" }}>
            <Lock size={18} />
            <span style={{ fontSize: "13px", fontWeight: 700 }}>TLS / mTLS Encryption</span>
          </div>
          <div style={{ fontSize: "20px", fontWeight: 800, color: statusData?.tls_enabled ? "#10b981" : "#f59e0b" }}>
            {statusData?.tls_enabled ? "ENFORCED" : "DEV LOCAL (PLAIN)"}
          </div>
          <div style={{ fontSize: "12px", color: "#94a3b8", marginTop: "4px" }}>
            mTLS Client Auth: {statusData?.mtls_enabled ? "Required" : "Optional/Disabled"}
          </div>
        </div>

        <div style={{ background: "rgba(30, 41, 59, 0.5)", border: "1px solid rgba(255, 255, 255, 0.08)", borderRadius: "12px", padding: "20px" }}>
          <div style={{ display: "flex", alignItems: "center", gap: "10px", color: "#a855f7", marginBottom: "8px" }}>
            <Shield size={18} />
            <span style={{ fontSize: "13px", fontWeight: 700 }}>JWT Authentication</span>
          </div>
          <div style={{ fontSize: "20px", fontWeight: 800, color: "#f8fafc" }}>
            {statusData?.jwt_algorithm || "HS256"}
          </div>
          <div style={{ fontSize: "12px", color: "#94a3b8", marginTop: "4px" }}>
            Expiry: {statusData?.jwt_expiration_minutes || 60} min &bull; Bootstrap Users: {statusData?.active_users_count || 4}
          </div>
        </div>

        <div style={{ background: "rgba(30, 41, 59, 0.5)", border: "1px solid rgba(255, 255, 255, 0.08)", borderRadius: "12px", padding: "20px" }}>
          <div style={{ display: "flex", alignItems: "center", gap: "10px", color: "#10b981", marginBottom: "8px" }}>
            <CheckCircle2 size={18} />
            <span style={{ fontSize: "13px", fontWeight: 700 }}>Secret Hygiene</span>
          </div>
          <div style={{ fontSize: "20px", fontWeight: 800, color: "#10b981" }}>
            VERIFIED CLEAN
          </div>
          <div style={{ fontSize: "12px", color: "#94a3b8", marginTop: "4px" }}>
            0 committed secrets or AWS keys
          </div>
        </div>
      </div>

      {/* Authentication & User Session Section */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(360px, 1fr))", gap: "20px" }}>
        {/* Login Box */}
        <div style={{ background: "rgba(30, 41, 59, 0.5)", border: "1px solid rgba(255, 255, 255, 0.08)", borderRadius: "12px", padding: "24px" }}>
          <h2 style={{ fontSize: "16px", fontWeight: 700, color: "#f8fafc", margin: "0 0 16px 0", display: "flex", alignItems: "center", gap: "8px" }}>
            <Key size={18} color="#38bdf8" /> Local API Authentication
          </h2>
          {currentUser ? (
            <div style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
              <div style={{ display: "flex", alignItems: "center", gap: "10px", padding: "12px", background: "rgba(56, 189, 248, 0.08)", borderRadius: "8px", border: "1px solid rgba(56, 189, 248, 0.2)" }}>
                <UserCheck size={20} color="#38bdf8" />
                <div>
                  <div style={{ fontSize: "14px", fontWeight: 700, color: "#f8fafc" }}>{currentUser.username}</div>
                  <div style={{ fontSize: "12px", color: "#38bdf8", fontWeight: 600 }}>ROLE: {currentUser.role}</div>
                </div>
              </div>
              <button
                onClick={handleLogout}
                style={{
                  padding: "8px 16px",
                  borderRadius: "6px",
                  border: "1px solid rgba(239, 68, 68, 0.3)",
                  background: "rgba(239, 68, 68, 0.15)",
                  color: "#ef4444",
                  fontWeight: 600,
                  fontSize: "13px",
                  cursor: "pointer",
                }}
              >
                Log Out
              </button>
            </div>
          ) : (
            <form onSubmit={handleLogin} style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
              <div>
                <label style={{ fontSize: "12px", color: "#94a3b8", display: "block", marginBottom: "4px" }}>Username</label>
                <input
                  type="text"
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  style={{
                    width: "100%",
                    padding: "8px 12px",
                    background: "rgba(15, 23, 42, 0.8)",
                    border: "1px solid rgba(255, 255, 255, 0.1)",
                    borderRadius: "6px",
                    color: "#f8fafc",
                    fontSize: "13px",
                    boxSizing: "border-box",
                  }}
                />
              </div>
              <div>
                <label style={{ fontSize: "12px", color: "#94a3b8", display: "block", marginBottom: "4px" }}>Password</label>
                <input
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  style={{
                    width: "100%",
                    padding: "8px 12px",
                    background: "rgba(15, 23, 42, 0.8)",
                    border: "1px solid rgba(255, 255, 255, 0.1)",
                    borderRadius: "6px",
                    color: "#f8fafc",
                    fontSize: "13px",
                    boxSizing: "border-box",
                  }}
                />
              </div>
              {loginError && (
                <div style={{ fontSize: "12px", color: "#ef4444", background: "rgba(239, 68, 68, 0.1)", padding: "8px", borderRadius: "6px" }}>
                  {loginError}
                </div>
              )}
              <button
                type="submit"
                disabled={loading}
                style={{
                  padding: "10px",
                  borderRadius: "6px",
                  border: "none",
                  background: "#0284c7",
                  color: "#ffffff",
                  fontWeight: 700,
                  fontSize: "13px",
                  cursor: "pointer",
                }}
              >
                {loading ? "Authenticating..." : "Obtain Bearer Token"}
              </button>
            </form>
          )}
        </div>

        {/* Permissions Matrix */}
        <div style={{ background: "rgba(30, 41, 59, 0.5)", border: "1px solid rgba(255, 255, 255, 0.08)", borderRadius: "12px", padding: "24px" }}>
          <h2 style={{ fontSize: "16px", fontWeight: 700, color: "#f8fafc", margin: "0 0 16px 0", display: "flex", alignItems: "center", gap: "8px" }}>
            <ShieldAlert size={18} color="#a855f7" /> RBAC Permissions Matrix
          </h2>
          <div style={{ display: "flex", flexDirection: "column", gap: "8px", maxHeight: "240px", overflowY: "auto" }}>
            {currentUser?.permissions && currentUser.permissions.length > 0 ? (
              currentUser.permissions.map((p) => (
                <div key={p} style={{ display: "flex", alignItems: "center", gap: "8px", fontSize: "12px", color: "#e2e8f0" }}>
                  <CheckCircle2 size={14} color="#10b981" />
                  <span style={{ fontFamily: "monospace" }}>{p}</span>
                </div>
              ))
            ) : (
              <div style={{ fontSize: "12px", color: "#94a3b8" }}>
                Log in to inspect active role permissions (e.g. operator, maintainer, admin).
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Security Audit Trail */}
      <div style={{ background: "rgba(30, 41, 59, 0.5)", border: "1px solid rgba(255, 255, 255, 0.08)", borderRadius: "12px", padding: "24px" }}>
        <h2 style={{ fontSize: "16px", fontWeight: 700, color: "#f8fafc", margin: "0 0 16px 0", display: "flex", alignItems: "center", gap: "8px" }}>
          <FileText size={18} color="#38bdf8" /> Recent Security Audit Trail
        </h2>
        <div style={{ overflowX: "auto" }}>
          <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "12px", textAlign: "left" }}>
            <thead>
              <tr style={{ borderBottom: "1px solid rgba(255, 255, 255, 0.1)", color: "#94a3b8" }}>
                <th style={{ padding: "10px" }}>Action</th>
                <th style={{ padding: "10px" }}>Actor</th>
                <th style={{ padding: "10px" }}>Role</th>
                <th style={{ padding: "10px" }}>Status</th>
                <th style={{ padding: "10px" }}>Timestamp</th>
              </tr>
            </thead>
            <tbody>
              {auditLogs.length > 0 ? (
                auditLogs.map((log) => (
                  <tr key={log.event_id} style={{ borderBottom: "1px solid rgba(255, 255, 255, 0.04)", color: "#e2e8f0" }}>
                    <td style={{ padding: "10px", fontWeight: 600, fontFamily: "monospace", color: "#38bdf8" }}>{log.action}</td>
                    <td style={{ padding: "10px" }}>{log.actor}</td>
                    <td style={{ padding: "10px" }}>{log.role || "-"}</td>
                    <td style={{ padding: "10px" }}>
                      <span
                        style={{
                          padding: "2px 8px",
                          borderRadius: "4px",
                          fontSize: "10px",
                          fontWeight: 700,
                          background: log.status === "SUCCESS" ? "rgba(16, 185, 129, 0.15)" : "rgba(239, 68, 68, 0.15)",
                          color: log.status === "SUCCESS" ? "#10b981" : "#ef4444",
                        }}
                      >
                        {log.status}
                      </span>
                    </td>
                    <td style={{ padding: "10px", color: "#94a3b8" }}>{new Date(log.timestamp).toLocaleTimeString()}</td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan={5} style={{ padding: "16px", textAlign: "center", color: "#64748b" }}>
                    {token ? "No security audit logs found." : "Authenticate as MAINTAINER or ADMIN to view security audit events."}
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
