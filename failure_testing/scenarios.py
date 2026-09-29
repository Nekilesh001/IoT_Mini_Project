"""
Failure Scenario Catalog Definitions.
Maps all 15 failure scenarios to their target components, expected behaviors, and execution parameters.
"""

from typing import Any, Dict, List
from failure_testing.models import (
    FailureScenarioType,
    FailureTarget,
    FailureInjectionConfig,
)

SCENARIO_DEFINITIONS: Dict[FailureScenarioType, Dict[str, Any]] = {
    FailureScenarioType.MQTT_OUTAGE: {
        "name": "MQTT Event Bus Outage",
        "target": FailureTarget.EVENT_BUS,
        "expected": "Telemetry generation continues; local store-and-forward buffer stores unroutable messages; automatic replay on broker reconnection without data loss.",
    },
    FailureScenarioType.DATABASE_OUTAGE: {
        "name": "Primary PostgreSQL Database Outage",
        "target": FailureTarget.PRIMARY_DATABASE,
        "expected": "Ingestion continues; events are safely buffered in local SQLite buffer; replay worker handles retry backoff; database recovery triggers full replay with zero loss.",
    },
    FailureScenarioType.STORAGE_PRESSURE: {
        "name": "Storage Pressure & Disk Failure Simulation",
        "target": FailureTarget.STORE_AND_FORWARD_BUFFER,
        "expected": "Buffer reaches high water mark; oldest unacked events prioritized or backpressure applied; alerts generated for storage degradation.",
    },
    FailureScenarioType.PROTOCOL_FAILURE: {
        "name": "Single Protocol Adapter Failure (e.g. PMP-001 MQTT)",
        "target": FailureTarget.PROTOCOL_ADAPTER,
        "expected": "Affected machine transitions to DEGRADED/OFFLINE; remaining 11 machines across Modbus/OPC UA continue streaming without interruption; recovery restores adapter.",
    },
    FailureScenarioType.INVALID_TELEMETRY: {
        "name": "Invalid Telemetry Injection (Missing/Out-of-Range Fields)",
        "target": FailureTarget.EDGE_INGESTION,
        "expected": "Edge quality validator tags readings as BAD/UNCERTAIN; invalid data is excluded from ML feature buffers and primary storage; pipeline does not crash.",
    },
    FailureScenarioType.DUPLICATE_TELEMETRY: {
        "name": "Duplicate Telemetry Injection (Replayed Event IDs)",
        "target": FailureTarget.EDGE_INGESTION,
        "expected": "Deduplication engine detects duplicate event_id and sequence numbers; duplicates are dropped and not double-inserted into the database.",
    },
    FailureScenarioType.OUT_OF_ORDER_TELEMETRY: {
        "name": "Out-of-Order Telemetry Sequence Injection",
        "target": FailureTarget.EDGE_INGESTION,
        "expected": "Sequence tracking detects out-of-order sequence index; temporal feature buffer sorts telemetry chronologically before ML inference.",
    },
    FailureScenarioType.STALE_TELEMETRY: {
        "name": "Stale / Clock-Drifted Telemetry Injection",
        "target": FailureTarget.EDGE_INGESTION,
        "expected": "Edge validator identifies expired timestamp; reading flagged as STALE without crashing ingestion.",
    },
    FailureScenarioType.ML_MODEL_LOAD_FAILURE: {
        "name": "ML Model Bundle Load Failure (Missing / Corrupt Artifact)",
        "target": FailureTarget.ML_INFERENCE,
        "expected": "ML service degrades gracefully to ERROR/DEGRADED; rule-based alerts and storage continue running at full speed without ML blocking.",
    },
    FailureScenarioType.ML_INFERENCE_FAILURE: {
        "name": "ML Inference Runtime Exception / Corrupted Feature Vector",
        "target": FailureTarget.ML_INFERENCE,
        "expected": "Prediction exception isolated; ML result record saved with status=ERROR; telemetry ingestion and persistence proceed uninterrupted.",
    },
    FailureScenarioType.ALERT_PERSISTENCE_FAILURE: {
        "name": "Alert Database Persistence Failure",
        "target": FailureTarget.ALERT_ENGINE,
        "expected": "Rule-based evaluation continues in memory; in-memory alert state and cooldowns remain active; error logged without crashing telemetry loop.",
    },
    FailureScenarioType.API_DEPENDENCY_FAILURE: {
        "name": "FastAPI Downstream Dependency Outage",
        "target": FailureTarget.REST_API,
        "expected": "API returns 503/500 with sanitized error message; no internal database passwords or stack traces exposed to client.",
    },
    FailureScenarioType.DEVICE_JOB_FAILURE: {
        "name": "Device Management Job Failure & Retry Exhaustion",
        "target": FailureTarget.DEVICE_JOB_ENGINE,
        "expected": "Job transitions PENDING -> IN_PROGRESS -> FAILED -> RETRY -> FAILED; max attempts enforced; complete attempt audit history logged.",
    },
    FailureScenarioType.NETWORK_INTERRUPTION: {
        "name": "Transient Network Flap / Packet Loss Simulation",
        "target": FailureTarget.PROTOCOL_ADAPTER,
        "expected": "Adapters auto-reconnect on network recovery; temporary disconnect marked in health registry; zero permanent stall.",
    },
    FailureScenarioType.SERVICE_RESTART_RECOVERY: {
        "name": "Service Restart During Active Buffer Accumulation",
        "target": FailureTarget.STORE_AND_FORWARD_BUFFER,
        "expected": "Uncommitted events in local buffer survive process termination; restart worker reads persisted buffer and replays completely.",
    },
}


def get_scenario_config(scenario_type: FailureScenarioType) -> FailureInjectionConfig:
    """Get default injection config for a scenario."""
    defn = SCENARIO_DEFINITIONS[scenario_type]
    return FailureInjectionConfig(
        scenario_type=scenario_type,
        target_component=defn["target"],
    )
