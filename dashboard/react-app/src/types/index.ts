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

export type MLAnomalyLabel = "NORMAL" | "ANOMALOUS" | "UNKNOWN";
export type MLInferenceStatus = "NOT_READY" | "READY" | "DEGRADED" | "ERROR";

export interface MLInferenceResult {
  result_id: string;
  machine_id: string;
  machine_type: string;
  event_time?: string | null;
  inference_time?: string | null;
  anomaly_score?: number | null;
  raw_anomaly_score?: number | null;
  anomaly_label: MLAnomalyLabel;
  predicted_rul_seconds?: number | null;
  predicted_rul_minutes?: number | null;
  predicted_rul_hours?: number | null;
  anomaly_model_name?: string | null;
  anomaly_model_version?: string | null;
  rul_model_name?: string | null;
  rul_model_version?: string | null;
  feature_manifest_version?: string;
  feature_count?: number;
  runtime_backend: string;
  status: MLInferenceStatus;
  latency_ms: {
    feature_generation_ms: number;
    anomaly_inference_ms: number;
    rul_inference_ms: number;
    total_inference_ms: number;
  };
  error_code?: string | null;
  error_message?: string | null;
}

export interface MLModelInfo {
  model_name: string;
  model_type: string;
  version: string;
  num_features: number;
  loaded_at: string;
  runtime_backend: string;
  hyperparameters?: Record<string, any>;
}

export interface MLLatencyStats {
  count: number;
  mean: number;
  median: number;
  p95: number;
  max: number;
}

export interface MLMetricsSummary {
  total_inferences: number;
  successful_inferences: number;
  failed_inferences: number;
  success_rate_pct: number;
  feature_generation_ms: MLLatencyStats;
  anomaly_inference_ms: MLLatencyStats;
  rul_inference_ms: MLLatencyStats;
  total_inference_ms: MLLatencyStats;
}

export interface MLSystemStatus {
  enabled: boolean;
  initialized: boolean;
  runtime_backend: string;
  onnx_enabled: boolean;
  min_warmup_samples: number;
  anomaly_model: {
    name: string;
    version: string;
    loaded: boolean;
  };
  rul_model: {
    name: string;
    version: string;
    loaded: boolean;
  };
  active_machine_buffers: string[];
  metrics: MLMetricsSummary;
  fleet_summary?: {
    total_inferences: number;
    anomalous_inferences_total: number;
    monitored_machines_count: number;
    active_anomalous_machines: string[];
    low_rul_machines: string[];
  };
}

export interface ExternalIoTDevice {
  device_id: string;
  device_type: string;
  device_class: string;
  plant_id: string;
  line_id: string;
  description: string;
  hardware: string;
  firmware_version: string;
  ingress_broker: string;
  telemetry_topic: string;
  command_topic: string;
  connection_status: "ONLINE" | "STALE" | "OFFLINE";
  last_seen?: string | null;
  latest_temperature_c?: number | null;
  latest_humidity_pct?: number | null;
  latest_sequence?: number | null;
  actuator_state?: {
    type?: string;
    state?: string;
  } | null;
  control_state?: {
    mode?: string;
    alertThresholdC?: number;
    normalThresholdC?: number;
  } | null;
}

export interface WokwiBridgeStatus {
  enabled: boolean;
  connected: boolean;
  health: string;
  broker: string;
  port: number;
  telemetry_topic: string;
  command_topic: string;
  received_count: number;
  rejected_count: number;
  reconnect_count: number;
  last_message_time?: string | null;
  last_error?: string | null;
  queue_size: number;
}

