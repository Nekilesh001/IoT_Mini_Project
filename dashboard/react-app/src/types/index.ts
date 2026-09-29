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
