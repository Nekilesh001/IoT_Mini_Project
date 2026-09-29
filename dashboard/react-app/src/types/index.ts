/**
 * Frontend TypeScript Domain Models.
 */

export interface SignalMetadata {
  name: string;
  signal_type: string;
  unit: string;
  min_value?: number | null;
  max_value?: number | null;
  nominal_value?: any;
  description: string;
}

export interface MachineOverviewItem {
  machine_id: string;
  machine_type: string;
  protocol: string;
  plant_id: string;
  line_id: string;
  operating_state: string;
  health_state: string;
  quality: string;
  sequence: number;
  latest_event_time?: string | null;
  key_measurements: Record<string, any>;
}

export interface MachineDetail {
  machine_id: string;
  machine_type: string;
  protocol: string;
  plant_id: string;
  line_id: string;
  operating_state: string;
  health_state: string;
  quality: string;
  sequence: number;
  latest_event_time?: string | null;
  latest_ingestion_time?: string | null;
  source_endpoint?: string | null;
  source_address?: string | null;
  signals: SignalMetadata[];
  current_measurements: Record<string, any>;
  current_derived: Record<string, any>;
}

export interface ProtocolHealthItem {
  protocol: string;
  status: string;
  endpoint: string;
  assigned_machines: string[];
  last_seen?: string | null;
}

export interface FactorySummary {
  total_machines: number;
  states: {
    running: number;
    idle: number;
    starting: number;
    stopping: number;
    maintenance: number;
    off: number;
  };
  health: {
    healthy: number;
    warning: number;
    critical: number;
  };
  protocols: ProtocolHealthItem[];
  total_telemetry_records: number;
  latest_event_time?: string | null;
}

export interface TelemetryRecord {
  event_id: string;
  schema_version: string;
  event_type: string;
  plant_id: string;
  line_id: string;
  machine_id: string;
  machine_type: string;
  protocol: string;
  endpoint?: string | null;
  source_address: string;
  event_time: string;
  ingestion_time: string;
  sequence: number;
  operating_state: string;
  health_state: string;
  quality: string;
  measurements: Record<string, any>;
  derived?: Record<string, any> | null;
  ml?: Record<string, any> | null;
  received_at?: string | null;
}

export interface TelemetryHistory {
  machine_id: string;
  total_records: number;
  records: TelemetryRecord[];
  available_signals: string[];
}

export interface RealtimeTelemetryEvent {
  event_type?: string;
  machine_id: string;
  machine_type: string;
  protocol: string;
  event_id: string;
  sequence: number;
  event_time: string;
  operating_state: string;
  health_state: string;
  quality: string;
  measurements: Record<string, any>;
  derived?: Record<string, any> | null;
}

export type AlertSeverity = "INFO" | "WARNING" | "CRITICAL";
export type AlertStatus = "OPEN" | "ACKNOWLEDGED" | "RESOLVED";

export interface AlertItem {
  alert_id: string;
  rule_id: string;
  machine_id: string;
  machine_type: string;
  alert_code: string;
  severity: AlertSeverity;
  title: string;
  description: string;
  status: AlertStatus;
  triggered_at: string;
  acknowledged_at?: string | null;
  acknowledged_by?: string | null;
  resolved_at?: string | null;
  resolution_notes?: string | null;
  triggering_measurements: Record<string, any>;
  current_measurements?: Record<string, any> | null;
  occurrence_count: number;
  last_occurrence_at?: string | null;
}

export interface AlertSummary {
  active_total: number;
  open_total: number;
  acknowledged_total: number;
  critical_count: number;
  warning_count: number;
  info_count: number;
  active_machines_count: number;
  active_machines: string[];
  total_historical_alerts: number;
  timestamp: string;
}

export interface FaultScenario {
  scenario_id: string;
  machine_id: string;
  machine_type: string;
  fault_type: string;
  fault_code: string;
  title: string;
  description: string;
  severity: AlertSeverity;
  is_progressive: boolean;
  duration_ticks?: number | null;
  state: "IDLE" | "ACTIVE" | "RESOLVED";
  current_tick: number;
  start_time?: string | null;
  end_time?: string | null;
}

