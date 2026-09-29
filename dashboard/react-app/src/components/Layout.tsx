import React from "react";
import { Link, useLocation } from "react-router-dom";
import { LayoutDashboard, Cpu, Activity, Radio, ShieldAlert, RefreshCw } from "lucide-react";
import { useRealtimeTelemetry } from "../hooks/useRealtimeTelemetry";

interface LayoutProps {
  children: React.ReactNode;
}

export const Layout: React.FC<LayoutProps> = ({ children }) => {
  const location = useLocation();
  const { status, lastHeartbeat } = useRealtimeTelemetry();

  const navItems = [
    { path: "/", label: "Overview", icon: LayoutDashboard },
    { path: "/machines", label: "Machines Grid", icon: Cpu },
    { path: "/alerts", label: "Alerts & Faults", icon: ShieldAlert },
    { path: "/protocols", label: "Protocol Health", icon: Radio },
  ];


  return (
    <div style={{ display: "flex", minHeight: "100vh", background: "#090d16", color: "#f8fafc" }}>
      {/* Sidebar */}
      <aside
        style={{
          width: "260px",
          background: "rgba(15, 23, 42, 0.95)",
          borderRight: "1px solid rgba(255, 255, 255, 0.08)",
          display: "flex",
          flexDirection: "column",
          padding: "24px 16px",
          flexShrink: 0,
        }}
      >
        {/* Brand */}
        <div style={{ display: "flex", alignItems: "center", gap: "12px", padding: "0 8px 24px 8px", borderBottom: "1px solid rgba(255, 255, 255, 0.08)" }}>
          <div
            style={{
              width: "36px",
              height: "36px",
              borderRadius: "8px",
              background: "linear-gradient(135deg, #0284c7, #38bdf8)",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              boxShadow: "0 0 12px rgba(56, 189, 248, 0.4)",
            }}
          >
            <Activity size={20} color="#0f172a" />
          </div>
          <div>
            <div style={{ fontSize: "14px", fontWeight: 800, letterSpacing: "0.04em", color: "#f8fafc" }}>
              SMART FACTORY
            </div>
            <div style={{ fontSize: "11px", color: "#38bdf8", fontWeight: 600, letterSpacing: "0.02em" }}>
              IIoT Operations Console
            </div>
          </div>
        </div>

        {/* Navigation */}
        <nav style={{ display: "flex", flexDirection: "column", gap: "6px", marginTop: "24px", flex: 1 }}>
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = location.pathname === item.path || (item.path === "/machines" && location.pathname.startsWith("/machines/"));
            return (
              <Link
                key={item.path}
                to={item.path}
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: "12px",
                  padding: "10px 14px",
                  borderRadius: "8px",
                  textDecoration: "none",
                  fontSize: "13px",
                  fontWeight: 600,
                  color: isActive ? "#38bdf8" : "#94a3b8",
                  background: isActive ? "rgba(56, 189, 248, 0.12)" : "transparent",
                  border: isActive ? "1px solid rgba(56, 189, 248, 0.25)" : "1px solid transparent",
                  transition: "all 0.15s ease",
                }}
              >
                <Icon size={18} />
                {item.label}
              </Link>
            );
          })}
        </nav>

        {/* Realtime Connection Status Pill */}
        <div
          style={{
            background: "rgba(15, 23, 42, 0.8)",
            border: "1px solid rgba(255, 255, 255, 0.08)",
            borderRadius: "8px",
            padding: "12px",
            display: "flex",
            flexDirection: "column",
            gap: "6px",
          }}
        >
          <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
            <span style={{ fontSize: "11px", fontWeight: 600, color: "#94a3b8" }}>SSE Stream</span>
            <div style={{ display: "flex", alignItems: "center", gap: "6px" }}>
              <span
                style={{
                  width: "8px",
                  height: "8px",
                  borderRadius: "50%",
                  backgroundColor: status === "connected" ? "#10b981" : status === "connecting" ? "#f59e0b" : "#ef4444",
                  boxShadow: status === "connected" ? "0 0 8px #10b981" : "none",
                }}
              />
              <span style={{ fontSize: "11px", fontWeight: 700, textTransform: "uppercase", color: status === "connected" ? "#10b981" : "#f59e0b" }}>
                {status}
              </span>
            </div>
          </div>
          {lastHeartbeat && (
            <div style={{ fontSize: "10px", color: "#64748b" }}>
              Last event: {lastHeartbeat.toLocaleTimeString()}
            </div>
          )}
        </div>
      </aside>

      {/* Main Content Area */}
      <main style={{ flex: 1, display: "flex", flexDirection: "column", overflowY: "auto" }}>
        <header
          style={{
            height: "64px",
            borderBottom: "1px solid rgba(255, 255, 255, 0.08)",
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            padding: "0 32px",
            background: "rgba(15, 23, 42, 0.5)",
            backdropFilter: "blur(8px)",
          }}
        >
          <div style={{ fontSize: "14px", fontWeight: 600, color: "#94a3b8" }}>
            PLANT_01 &bull; PRODUCTION LINE_A &bull; 12 MACHINES ACTIVE
          </div>
          <div style={{ display: "flex", alignItems: "center", gap: "16px", fontSize: "12px", color: "#64748b" }}>
            <span style={{ fontFamily: "monospace" }}>{new Date().toLocaleDateString()}</span>
          </div>
        </header>

        <div style={{ padding: "32px", maxWidth: "1600px", width: "100%", margin: "0 auto", boxSizing: "border-box" }}>
          {children}
        </div>
      </main>
    </div>
  );
};
