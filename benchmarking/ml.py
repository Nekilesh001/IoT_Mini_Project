"""
Machine Learning Benchmarks.
Measures real-time feature extraction, Isolation Forest anomaly inference, HistGradientBoosting RUL estimation, and ONNX Runtime performance.
"""

import time
import statistics
from typing import Dict, Any, List
from datetime import datetime, timezone
import uuid

from edge.models import CanonicalTelemetry, CanonicalSource, CanonicalState, QualityCode, EventType
from protocols.models import ProtocolType
from ml.inference.config import InferenceConfig
from ml.inference.service import MLInferenceService


def benchmark_ml_pipeline(iterations: int = 200) -> Dict[str, Any]:
    """Benchmark temporal feature generation and ML model inference."""
    config = InferenceConfig(enabled=True)
    service = MLInferenceService(config=config)

    total_latencies_us: List[float] = []

    # Warm-up buffer
    for i in range(30):
        t = CanonicalTelemetry(
            schema_version="1.0.0",
            event_id=f"bench-warm-{i}",
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
            sequence=i + 1,
            state=CanonicalState(
                operating="RUNNING",
                health="HEALTHY",
            ),
            quality=QualityCode.GOOD,
            measurements={
                "spindle_speed_rpm": 1200.0 + (i % 10),
                "spindle_temperature_c": 45.0 + (i * 0.1),
                "vibration_rms_mm_s": 1.2 + (i * 0.02),
                "coolant_pressure_bar": 4.5,
            },
        )
        service.infer(t)

    for i in range(iterations):
        t = CanonicalTelemetry(
            schema_version="1.0.0",
            event_id=f"bench-inf-{i}",
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
            sequence=100 + i,
            state=CanonicalState(
                operating="RUNNING",
                health="HEALTHY",
            ),
            quality=QualityCode.GOOD,
            measurements={
                "spindle_speed_rpm": 1200.0 + (i % 5),
                "spindle_temperature_c": 46.2,
                "vibration_rms_mm_s": 1.45,
                "coolant_pressure_bar": 4.4,
            },
        )

        t0 = time.perf_counter()
        result = service.infer(t)
        total_latencies_us.append((time.perf_counter() - t0) * 1_000_000)

    return {
        "iterations": iterations,
        "total_pipeline_mean_us": round(statistics.mean(total_latencies_us), 2),
        "total_pipeline_median_us": round(statistics.median(total_latencies_us), 2),
        "total_pipeline_p95_us": round(statistics.quantiles(total_latencies_us, n=20)[18], 2) if len(total_latencies_us) >= 20 else round(max(total_latencies_us), 2),
        "total_pipeline_max_us": round(max(total_latencies_us), 2),
        "inferences_per_sec": round(1_000_000 / statistics.mean(total_latencies_us), 2),
    }
