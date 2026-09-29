"""
Telemetry & Edge Pipeline Benchmarks.
Measures ingestion throughput, normalization latency, and rule alert evaluation latency.
"""

import time
import statistics
from typing import Dict, Any, List
from datetime import datetime, timezone
import uuid

from edge.service import EdgeIngestionService
from edge.models import CanonicalTelemetry, CanonicalState, CanonicalSource, EventType, QualityCode
from protocols.models import ProtocolReading, ProtocolType
from simulator.runtime.factory_runtime import FactorySimulator
from alerts.rules import RuleEvaluator, get_default_rules


def benchmark_edge_normalization(iterations: int = 1000) -> Dict[str, Any]:
    """Benchmark raw protocol reading ingestion, validation, and canonicalization."""
    factory = FactorySimulator(seed=42)
    profiles = {m.machine_id: m.profile for m in factory.get_all_machines()}
    edge_service = EdgeIngestionService(profiles=profiles)

    latencies_us: List[float] = []

    # Warm-up
    for i in range(20):
        reading = ProtocolReading(
            machine_id="PMP-001",
            machine_type="PUMP",
            protocol=ProtocolType.MQTT,
            sequence=i + 1,
            timestamp=datetime.now(timezone.utc).isoformat(),
            measurements={
                "vibration_rms": 2.45,
                "flow_rate": 85.2,
                "inlet_pressure": 3.2,
                "outlet_pressure": 6.8,
                "motor_temperature": 52.3,
                "ambient_temp": 24.5,
            },
            source_address="mqtt://localhost:1883/telemetry/pmp001",
            metadata={"event_id": f"warm-{i}"},
        )
        edge_service.ingest_reading(reading)

    for i in range(iterations):
        reading = ProtocolReading(
            machine_id="PMP-001",
            machine_type="PUMP",
            protocol=ProtocolType.MQTT,
            sequence=100 + i,
            timestamp=datetime.now(timezone.utc).isoformat(),
            measurements={
                "vibration_rms": 2.45,
                "flow_rate": 85.2,
                "inlet_pressure": 3.2,
                "outlet_pressure": 6.8,
                "motor_temperature": 52.3,
                "ambient_temp": 24.5,
            },
            source_address="mqtt://localhost:1883/telemetry/pmp001",
            metadata={"event_id": f"bench-norm-{i}"},
        )
        t0 = time.perf_counter()
        res = edge_service.ingest_reading(reading)
        latencies_us.append((time.perf_counter() - t0) * 1_000_000)

    return {
        "iterations": iterations,
        "mean_us": round(statistics.mean(latencies_us), 2),
        "median_us": round(statistics.median(latencies_us), 2),
        "p95_us": round(statistics.quantiles(latencies_us, n=20)[18], 2) if len(latencies_us) >= 20 else round(max(latencies_us), 2),
        "p99_us": round(statistics.quantiles(latencies_us, n=100)[98], 2) if len(latencies_us) >= 100 else round(max(latencies_us), 2),
        "max_us": round(max(latencies_us), 2),
        "throughput_events_per_sec": round(1_000_000 / statistics.mean(latencies_us), 2),
    }


def benchmark_rule_alert_evaluation(iterations: int = 1000) -> Dict[str, Any]:
    """Benchmark rule evaluator across machine telemetry."""
    rules = get_default_rules()
    evaluator = RuleEvaluator(rules)

    canonical = CanonicalTelemetry(
        schema_version="1.0.0",
        event_id=str(uuid.uuid4()),
        event_type=EventType.TELEMETRY,
        plant_id="PLANT_01",
        line_id="LINE_A",
        machine_id="CNC-001",
        machine_type="CNC_MILLING",
        source=CanonicalSource(
            protocol="OPC_UA",
            endpoint="opc.tcp://localhost:4840",
            source_address="ns=2;s=CNC-001",
        ),
        event_time=datetime.now(timezone.utc).isoformat(),
        ingestion_time=datetime.now(timezone.utc).isoformat(),
        sequence=100,
        state=CanonicalState(
            operating="RUNNING",
            health="HEALTHY",
        ),
        quality=QualityCode.GOOD,
        measurements={
            "spindle_speed": 4500.0,
            "vibration_x": 3.8,
            "spindle_temp": 62.5,
            "feed_rate": 800.0,
            "tool_wear": 0.45,
        },
    )

    latencies_us: List[float] = []

    # Warm-up
    for _ in range(50):
        evaluator.evaluate(canonical)

    for _ in range(iterations):
        t0 = time.perf_counter()
        evaluator.evaluate(canonical)
        latencies_us.append((time.perf_counter() - t0) * 1_000_000)

    return {
        "iterations": iterations,
        "mean_us": round(statistics.mean(latencies_us), 2),
        "median_us": round(statistics.median(latencies_us), 2),
        "p95_us": round(statistics.quantiles(latencies_us, n=20)[18], 2) if len(latencies_us) >= 20 else round(max(latencies_us), 2),
        "p99_us": round(statistics.quantiles(latencies_us, n=100)[98], 2) if len(latencies_us) >= 100 else round(max(latencies_us), 2),
        "max_us": round(max(latencies_us), 2),
        "throughput_evals_per_sec": round(1_000_000 / statistics.mean(latencies_us), 2),
    }
