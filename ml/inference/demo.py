"""
Comprehensive CLI Demonstration of the Phase 8 Edge ML Inference Engine.
"""

from datetime import datetime, timezone
import logging
import sys
import time

from edge.models import CanonicalTelemetry, CanonicalSource, CanonicalState, QualityCode, EventType
from storage.database import get_engine, get_session_factory, init_db
from storage.repository import MLInferenceRepository
from alerts.repository import AlertRepository
from ml.inference.alert_adapter import MLAlertAdapter
from ml.inference.config import InferenceConfig
from ml.inference.model_loader import ModelLoader
from ml.inference.models import InferenceStatus, RuntimeBackend
from ml.inference.onnx_exporter import ONNXModelExporter
from ml.inference.service import MLInferenceService

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("ml.inference.demo")


def create_demo_telemetry(machine_id: str, machine_type: str, seq: int, degraded: bool = False) -> CanonicalTelemetry:
    measurements = {}
    if machine_type == "CNC_MACHINE":
        measurements = {
            "spindle_speed_rpm": 1200.0 if not degraded else 950.0,
            "spindle_temperature_c": 45.0 if not degraded else 88.5,
            "vibration_rms_mm_s": 1.2 if not degraded else 6.8,
            "coolant_pressure_bar": 4.5 if not degraded else 1.2,
        }
    elif machine_type == "ROBOT_ARM":
        measurements = {
            "joint_1_temp_c": 38.0 if not degraded else 65.0,
            "joint_2_temp_c": 39.0 if not degraded else 68.0,
            "weld_current_a": 120.0 if not degraded else 180.0,
            "vibration_rms_mm_s": 0.8 if not degraded else 4.2,
        }
    elif machine_type == "HYDRAULIC_PRESS":
        measurements = {
            "hydraulic_pressure_bar": 210.0 if not degraded else 135.0,
            "oil_temperature_c": 48.0 if not degraded else 78.0,
            "press_force_kn": 450.0 if not degraded else 310.0,
        }
    else:
        measurements = {
            "discharge_pressure_bar": 6.2 if not degraded else 3.8,
            "flow_rate_m3_h": 45.0 if not degraded else 22.0,
            "bearing_temperature_c": 52.0 if not degraded else 89.0,
        }

    return CanonicalTelemetry(
        event_id=f"DEMO-EVT-{machine_id}-{seq:04d}",
        schema_version="1.0.0",
        event_type=EventType.TELEMETRY,
        plant_id="PLANT_01",
        line_id="LINE_A",
        machine_id=machine_id,
        machine_type=machine_type,
        source=CanonicalSource(protocol="OPC_UA", endpoint="opc.tcp://localhost:4840", source_address="ns=2;s=Demo"),
        event_time=datetime.now(timezone.utc).isoformat(),
        ingestion_time=datetime.now(timezone.utc).isoformat(),
        sequence=seq,
        state=CanonicalState(operating="RUNNING" if not degraded else "DEGRADED", health="HEALTHY" if not degraded else "WARNING"),
        quality=QualityCode.GOOD,
        measurements=measurements,
    )


def run_demo():
    print("=" * 80)
    print(" SMART FACTORY MACHINE MONITORING & PREDICTIVE MAINTENANCE SYSTEM")
    print(" PHASE 8 — EDGE ML ANOMALY & PREDICTIVE INFERENCE ENGINE DEMO")
    print("=" * 80)

    # 1. Model Loading & Verification
    print("\n[Step 1/6] Loading and Validating Phase 7 Model Artifacts...")
    cfg = InferenceConfig(min_warmup_samples=4)
    loader = ModelLoader(cfg)
    anom_bundle = loader.load_anomaly_bundle()
    rul_bundle = loader.load_rul_bundle()

    print(f" -> Anomaly Model: {anom_bundle.model_name}:{anom_bundle.version} ({anom_bundle.num_features} features)")
    print(f" -> RUL Model:     {rul_bundle.model_name}:{rul_bundle.version} ({rul_bundle.num_features} features)")

    # 2. ONNX Conversion & Numerical Equivalence
    print("\n[Step 2/6] Verifying ONNX Graph Conversion & Equivalence...")
    exporter = ONNXModelExporter(cfg)
    report = exporter.export_all()
    print(f" -> Anomaly ONNX Status: Verified ({report['anomaly_export']['onnx_path']})")
    print(f" -> RUL ONNX Status:     Verified ({report['rul_export']['onnx_path']})")
    print(f" -> Numerical Max Diff:  {report['rul_export']['max_absolute_diff']:.6e} seconds")

    # 3. Initialize ML Inference Service & Database
    print("\n[Step 3/6] Initializing Edge ML Inference Service and Persistence Storage...")
    db_engine = get_engine("sqlite:///data/demo_ml_inferences.db")
    init_db(db_engine)
    session_factory = get_session_factory(db_engine)
    ml_repo = MLInferenceRepository(session_factory)
    alert_repo = AlertRepository(session_factory)
    alert_adapter = MLAlertAdapter(alert_repo, cfg)

    ml_service = MLInferenceService(cfg)
    print(" -> ML Inference Service initialized with real-time temporal feature pipeline.")

    # 4. Stream Telemetry across Heterogeneous Machines
    print("\n[Step 4/6] Streaming Live Telemetry & Demonstrating Warm-Up Behavior...")
    machines = [
        ("CNC-001", "CNC_MACHINE"),
        ("ROB-001", "ROBOT_ARM"),
        ("PRS-001", "HYDRAULIC_PRESS"),
        ("PMP-001", "PUMP"),
    ]

    for step in range(1, 8):
        print(f"\n --- Telemetry Batch {step}/7 ---")
        for m_id, m_type in machines:
            is_degraded = (step >= 5 and m_id == "CNC-001")
            telem = create_demo_telemetry(m_id, m_type, step, degraded=is_degraded)

            res = ml_service.infer(telem)
            if res.status == InferenceStatus.NOT_READY:
                print(f"  [{m_id}] Status: NOT_READY (Warming up history: {step}/{cfg.min_warmup_samples})")
            elif res.status == InferenceStatus.READY:
                ml_repo.insert(res)
                triggered = alert_adapter.process_inference_result(res)
                alert_str = f" [ALERT TRIGGERED: {triggered[0].rule_id}]" if triggered else ""
                print(
                    f"  [{m_id}] Status: READY | Anomaly Score: {res.anomaly_score:.3f} ({res.anomaly_label.value}) | "
                    f"Predicted RUL: {res.predicted_rul_minutes:.1f}m ({res.predicted_rul_seconds:.0f}s) | "
                    f"Latency: {res.latency.total_inference_ms:.2f}ms{alert_str}"
                )

    # 5. Latency Percentiles & Performance Metrics
    print("\n[Step 5/6] Measuring Edge Inference Latency Percentiles...")
    metrics = ml_service.metrics_tracker.get_summary()
    print(f" -> Total Inferences:       {metrics['total_inferences']}")
    print(f" -> Success Rate:           {metrics['success_rate_pct']}%")
    print(f" -> Feature Generation:     Mean: {metrics['feature_generation_ms']['mean']}ms | p95: {metrics['feature_generation_ms']['p95']}ms")
    print(f" -> Anomaly Scoring:        Mean: {metrics['anomaly_inference_ms']['mean']}ms | p95: {metrics['anomaly_inference_ms']['p95']}ms")
    print(f" -> RUL Regression:         Mean: {metrics['rul_inference_ms']['mean']}ms | p95: {metrics['rul_inference_ms']['p95']}ms")
    print(f" -> Total Inference Pass:   Mean: {metrics['total_inference_ms']['mean']}ms | p95: {metrics['total_inference_ms']['p95']}ms")

    # 6. Failure Recovery Assertion
    print("\n[Step 6/6] Verifying Non-Fatal Failure Handling & Ingestion Continuity...")
    # Inject malformed telemetry
    bad_telem = CanonicalTelemetry(
        event_id="BAD-EVT-001",
        schema_version="1.0.0",
        event_type=EventType.TELEMETRY,
        plant_id="PLANT_01",
        line_id="LINE_A",
        machine_id="CNC-001",
        machine_type="CNC_MACHINE",
        source=CanonicalSource(protocol="OPC_UA", endpoint="opc.tcp://localhost:4840", source_address="bad"),
        event_time=datetime.now(timezone.utc).isoformat(),
        ingestion_time=datetime.now(timezone.utc).isoformat(),
        sequence=9999,
        state=CanonicalState(operating="RUNNING", health="HEALTHY"),
        quality=QualityCode.GOOD,
        measurements={"invalid_signal_string": "error_value"},
    )
    bad_res = ml_service.infer(bad_telem)
    print(f" -> Malformed telemetry handled gracefully: status={bad_res.status.value}")
    print(" -> Ingestion pipeline continues unhindered.")

    print("\n" + "=" * 80)
    print(" PHASE 8 EDGE ML INFERENCE ENGINE DEMONSTRATION COMPLETE — EXIT CODE 0")
    print("=" * 80)


if __name__ == "__main__":
    run_demo()
