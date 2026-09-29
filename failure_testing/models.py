"""
Failure Testing Domain Models & Enums.
Defines failure scenario types, injection parameters, execution outcomes, and recovery metrics.
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class FailureScenarioType(str, Enum):
    """Catalog of 15 systematic local failure scenarios."""
    MQTT_OUTAGE = "MQTT_OUTAGE"
    DATABASE_OUTAGE = "DATABASE_OUTAGE"
    STORAGE_PRESSURE = "STORAGE_PRESSURE"
    PROTOCOL_FAILURE = "PROTOCOL_FAILURE"
    INVALID_TELEMETRY = "INVALID_TELEMETRY"
    DUPLICATE_TELEMETRY = "DUPLICATE_TELEMETRY"
    OUT_OF_ORDER_TELEMETRY = "OUT_OF_ORDER_TELEMETRY"
    STALE_TELEMETRY = "STALE_TELEMETRY"
    ML_MODEL_LOAD_FAILURE = "ML_MODEL_LOAD_FAILURE"
    ML_INFERENCE_FAILURE = "ML_INFERENCE_FAILURE"
    ALERT_PERSISTENCE_FAILURE = "ALERT_PERSISTENCE_FAILURE"
    API_DEPENDENCY_FAILURE = "API_DEPENDENCY_FAILURE"
    DEVICE_JOB_FAILURE = "DEVICE_JOB_FAILURE"
    NETWORK_INTERRUPTION = "NETWORK_INTERRUPTION"
    SERVICE_RESTART_RECOVERY = "SERVICE_RESTART_RECOVERY"


class FailureTarget(str, Enum):
    """System component targeted by the failure injector."""
    EVENT_BUS = "EVENT_BUS"
    PRIMARY_DATABASE = "PRIMARY_DATABASE"
    STORE_AND_FORWARD_BUFFER = "STORE_AND_FORWARD_BUFFER"
    PROTOCOL_ADAPTER = "PROTOCOL_ADAPTER"
    EDGE_INGESTION = "EDGE_INGESTION"
    ML_INFERENCE = "ML_INFERENCE"
    ALERT_ENGINE = "ALERT_ENGINE"
    DEVICE_JOB_ENGINE = "DEVICE_JOB_ENGINE"
    REST_API = "REST_API"


class FailureInjectionConfig(BaseModel):
    """Configuration parameters for a failure injection scenario."""
    scenario_type: FailureScenarioType
    target_component: FailureTarget
    target_machine_id: Optional[str] = None
    duration_seconds: float = 2.0
    parameters: Dict[str, Any] = Field(default_factory=dict)
    auto_recover: bool = True


class RecoveryMetrics(BaseModel):
    """Observable recovery performance metrics captured during failure testing."""
    detection_latency_ms: float = 0.0
    recovery_latency_ms: float = 0.0
    buffered_events_count: int = 0
    replayed_events_count: int = 0
    lost_events_count: int = 0
    duplicate_persisted_count: int = 0
    job_retries_count: int = 0
    ml_downtime_seconds: float = 0.0
    alert_downtime_seconds: float = 0.0


class ScenarioResult(BaseModel):
    """Outcome and assertion record of an executed failure scenario."""
    scenario_type: FailureScenarioType
    scenario_name: str
    target_component: FailureTarget
    target_machine_id: Optional[str] = None
    status: str = "PASSED"  # PASSED / FAILED / ERROR
    start_time: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    end_time: Optional[datetime] = None
    duration_seconds: float = 0.0
    expected_behavior: str = ""
    observed_behavior: str = ""
    metrics: RecoveryMetrics = Field(default_factory=RecoveryMetrics)
    assertions_passed: List[str] = Field(default_factory=list)
    assertions_failed: List[str] = Field(default_factory=list)
    error_message: Optional[str] = None
    notes: Optional[str] = None
