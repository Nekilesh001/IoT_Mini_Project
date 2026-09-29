import React, { useState } from "react";
import { useMachines } from "../hooks/useMachines";
import { MachineCard } from "../components/MachineCard";
import { Search, Filter, Cpu, Radio, Activity, AlertOctagon } from "lucide-react";

export const MachinesPage: React.FC = () => {
  const { machines, loading, error } = useMachines();
  const [searchTerm, setSearchTerm] = useState("");
  const [selectedLine, setSelectedLine] = useState<string>("ALL");
  const [selectedProtocol, setSelectedProtocol] = useState<string>("ALL");
  const [selectedState, setSelectedState] = useState<string>("ALL");

  if (loading) {
    return (
      <div style={{ display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", height: "400px", gap: "16px" }}>
        <div style={{ width: "36px", height: "36px", borderRadius: "50%", border: "3px solid #38bdf8", borderTopColor: "transparent", animation: "spin 1s linear infinite" }} />
        <span style={{ fontSize: "14px", color: "#94a3b8" }}>Loading machine fleet...</span>
      </div>
    );
  }

  if (error) {
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
        <AlertOctagon size={32} style={{ margin: "0 auto 12px auto" }} />
        <div style={{ fontSize: "16px", fontWeight: 700, marginBottom: "6px" }}>API Connection Error</div>
        <div style={{ fontSize: "13px", color: "#f87171" }}>{error}</div>
      </div>
    );
  }

  // Extract unique lines and protocols
  const lines = ["ALL", ...Array.from(new Set(machines.map((m) => m.line_id)))];
  const protocols = ["ALL", ...Array.from(new Set(machines.map((m) => m.protocol)))];
  const states = ["ALL", "RUNNING", "IDLE", "WARNING", "FAULT", "MAINTENANCE"];

  // Filter machines
  const filteredMachines = machines.filter((m) => {
    const matchesSearch =
      m.machine_id.toLowerCase().includes(searchTerm.toLowerCase()) ||
      m.machine_type.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesLine = selectedLine === "ALL" || m.line_id === selectedLine;
    const matchesProtocol = selectedProtocol === "ALL" || m.protocol === selectedProtocol;
    const matchesState = selectedState === "ALL" || m.operating_state.toUpperCase() === selectedState.toUpperCase();
    return matchesSearch && matchesLine && matchesProtocol && matchesState;
  });

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "24px" }}>
      {/* Page Header */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-end", flexWrap: "wrap", gap: "16px" }}>
        <div>
          <div style={{ display: "flex", alignItems: "center", gap: "8px", color: "#38bdf8", fontSize: "12px", fontWeight: 700, textTransform: "uppercase", letterSpacing: "0.08em", marginBottom: "4px" }}>
            <Cpu size={14} /> Equipment Inventory
          </div>
          <h1 style={{ fontSize: "28px", fontWeight: 800, color: "#f8fafc", margin: 0, letterSpacing: "-0.02em" }}>
            Machine Fleet Grid
          </h1>
          <p style={{ fontSize: "14px", color: "#94a3b8", margin: "6px 0 0 0" }}>
            Real-time status, protocol mapping, and live sensor values for all factory machines.
          </p>
        </div>
        <div style={{ display: "flex", gap: "8px", alignItems: "center" }}>
          <span style={{ fontSize: "12px", color: "#64748b" }}>
            Showing <strong style={{ color: "#38bdf8", fontFamily: "monospace" }}>{filteredMachines.length}</strong> of {machines.length} machines
          </span>
        </div>
      </div>

      {/* Search & Filter Toolbar */}
      <div
        style={{
          background: "rgba(30, 41, 59, 0.4)",
          border: "1px solid rgba(255, 255, 255, 0.08)",
          borderRadius: "12px",
          padding: "16px 20px",
          display: "flex",
          flexWrap: "wrap",
          gap: "16px",
          alignItems: "center",
          justifyContent: "space-between",
        }}
      >
        {/* Search input */}
        <div style={{ display: "flex", alignItems: "center", gap: "8px", background: "rgba(15, 23, 42, 0.6)", border: "1px solid rgba(255, 255, 255, 0.1)", borderRadius: "8px", padding: "8px 12px", minWidth: "240px", flex: "1" }}>
          <Search size={16} color="#64748b" />
          <input
            type="text"
            placeholder="Search by Machine ID or Type (e.g. CNC, AGV)..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            style={{
              background: "transparent",
              border: "none",
              outline: "none",
              color: "#f8fafc",
              fontSize: "13px",
              width: "100%",
            }}
          />
        </div>

        {/* Filter dropdowns */}
        <div style={{ display: "flex", gap: "12px", flexWrap: "wrap", alignItems: "center" }}>
          {/* Line Filter */}
          <div style={{ display: "flex", alignItems: "center", gap: "6px" }}>
            <span style={{ fontSize: "12px", color: "#94a3b8" }}>Line:</span>
            <select
              value={selectedLine}
              onChange={(e) => setSelectedLine(e.target.value)}
              style={{
                background: "rgba(15, 23, 42, 0.8)",
                border: "1px solid rgba(255, 255, 255, 0.1)",
                borderRadius: "6px",
                color: "#f8fafc",
                fontSize: "12px",
                padding: "6px 10px",
                outline: "none",
                cursor: "pointer",
              }}
            >
              {lines.map((l) => (
                <option key={l} value={l}>
                  {l}
                </option>
              ))}
            </select>
          </div>

          {/* Protocol Filter */}
          <div style={{ display: "flex", alignItems: "center", gap: "6px" }}>
            <span style={{ fontSize: "12px", color: "#94a3b8" }}>Protocol:</span>
            <select
              value={selectedProtocol}
              onChange={(e) => setSelectedProtocol(e.target.value)}
              style={{
                background: "rgba(15, 23, 42, 0.8)",
                border: "1px solid rgba(255, 255, 255, 0.1)",
                borderRadius: "6px",
                color: "#f8fafc",
                fontSize: "12px",
                padding: "6px 10px",
                outline: "none",
                cursor: "pointer",
              }}
            >
              {protocols.map((p) => (
                <option key={p} value={p}>
                  {p}
                </option>
              ))}
            </select>
          </div>

          {/* State Filter */}
          <div style={{ display: "flex", alignItems: "center", gap: "6px" }}>
            <span style={{ fontSize: "12px", color: "#94a3b8" }}>State:</span>
            <select
              value={selectedState}
              onChange={(e) => setSelectedState(e.target.value)}
              style={{
                background: "rgba(15, 23, 42, 0.8)",
                border: "1px solid rgba(255, 255, 255, 0.1)",
                borderRadius: "6px",
                color: "#f8fafc",
                fontSize: "12px",
                padding: "6px 10px",
                outline: "none",
                cursor: "pointer",
              }}
            >
              {states.map((s) => (
                <option key={s} value={s}>
                  {s}
                </option>
              ))}
            </select>
          </div>
        </div>
      </div>

      {/* Machine Cards Grid */}
      {filteredMachines.length === 0 ? (
        <div
          style={{
            background: "rgba(30, 41, 59, 0.3)",
            borderRadius: "12px",
            border: "1px dashed rgba(255, 255, 255, 0.1)",
            padding: "48px",
            textAlign: "center",
            color: "#94a3b8",
          }}
        >
          <p style={{ fontSize: "16px", fontWeight: 600, color: "#f8fafc", marginBottom: "8px" }}>
            No matching machines found
          </p>
          <p style={{ fontSize: "13px", color: "#64748b", margin: 0 }}>
            Try resetting your search query or filter selection.
          </p>
        </div>
      ) : (
        <div
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(auto-fill, minmax(320px, 1fr))",
            gap: "20px",
          }}
        >
          {filteredMachines.map((machine) => (
            <MachineCard key={machine.machine_id} machine={machine} />
          ))}
        </div>
      )}
    </div>
  );
};
