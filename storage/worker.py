"""
Continuous Background Ingestion Worker.

Runs the continuous loop:
Factory Simulator -> Protocol Adapters -> Edge Ingestion -> Database (PostgreSQL / SQLite)
"""

import logging
import os
import signal
import sys
import time

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from edge.models import IngestionStatus
from edge.service import EdgeIngestionService
from protocols.manager import FactoryProtocolManager
from simulator.runtime.factory_runtime import FactorySimulator
from storage.config import StorageConfig
from storage.database import get_engine, get_session_factory, init_db
from storage.repository import TelemetryRepository, MLInferenceRepository
from alerts.models import AlertRecord
from alerts.repository import AlertRepository
from alerts.engine import AlertEngine
from alerts.rules import create_default_rules
from scenarios.fault_scenarios import FaultLifecycleState
from scenarios.manager import FaultScenarioManager
from scenarios.repository import ScenarioStateRepository
from ml.inference.service import MLInferenceService
from ml.inference.alert_adapter import MLAlertAdapter
from ml.inference.models import InferenceStatus, AnomalyLabel
from ml.inference.window_aggregator import WindowedAnomalyAggregator
from protocols.wokwi.config import WokwiConfig
from protocols.wokwi.bridge import WokwiMQTTBridge
from protocols.wokwi.registry import get_external_device_registry

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("storage.worker")


def run_worker():
    db_url = os.getenv("DATABASE_URL", StorageConfig().database_url)
    poll_interval = float(os.getenv("WORKER_POLL_INTERVAL", "1.0"))
    ml_enabled = os.getenv("ML_INFERENCE_ENABLED", "true").lower() in ("true", "1", "yes")

    wokwi_config = WokwiConfig.from_env()

    print("=" * 80)
    print(" SMART FACTORY — CONTINUOUS SIMULATION & INGESTION WORKER")
    print(f" Database URL: {db_url}")
    print(f" Loop Interval: {poll_interval}s")
    print(f" ML Inference: {'ENABLED' if ml_enabled else 'DISABLED'}")
    print(f" Wokwi Bridge: {'ENABLED (' + wokwi_config.broker + ':' + str(wokwi_config.port) + ')' if wokwi_config.enabled else 'DISABLED'}")
    print("=" * 80)

    # 1. Initialize Database & Repositories
    engine = get_engine(db_url)
    init_db(engine)
    session_factory = get_session_factory(engine)
    repository = TelemetryRepository(session_factory)
    ml_repository = MLInferenceRepository(session_factory)
    alert_repository = AlertRepository(session_factory)
    alert_engine = AlertEngine(rules=create_default_rules(), repository=alert_repository)
    ml_alert_adapter = MLAlertAdapter(alert_repository)
    scenario_repository = ScenarioStateRepository(session_factory)

    # 2a. Initialize Windowed Anomaly Aggregator
    # Requires 10+ readings, and 40%+ must be anomalous before any ML alert fires.
    # This prevents single-reading false positives from transient sensor spikes.
    ml_window_size = int(os.getenv("ML_WINDOW_SIZE", "30"))
    ml_min_readings = int(os.getenv("ML_MIN_READINGS_BEFORE_ALERT", "10"))
    ml_alert_ratio = float(os.getenv("ML_ALERT_RATIO_THRESHOLD", "0.40"))
    anomaly_aggregator = WindowedAnomalyAggregator(
        window_size=ml_window_size,
        min_readings_before_alert=ml_min_readings,
        alert_ratio_threshold=ml_alert_ratio,
    )
    logger.info(
        f"[StorageWorker] Windowed anomaly aggregator: window={ml_window_size}, "
        f"min_readings={ml_min_readings}, ratio_threshold={ml_alert_ratio}"
    )

    # 2b. Initialize ML Inference Service
    ml_service = MLInferenceService() if ml_enabled else None

    # 3. Initialize Simulator, Scenarios & Protocols
    factory = FactorySimulator(seed=42)
    scenario_mgr = FaultScenarioManager(factory=factory)
    profiles = {m.machine_id: m.profile for m in factory.get_all_machines()}

    # Register external IoT profiles (e.g. Wokwi IOT-SENSOR-001) alongside factory machines
    external_registry = get_external_device_registry()
    external_profiles = external_registry.get_all_machine_profiles()
    all_profiles = dict(profiles)
    all_profiles.update(external_profiles)

    # Synchronize starting sequence counters from database
    max_seqs = repository.get_max_sequences()
    for m in factory.get_all_machines():
        if m.machine_id in max_seqs:
            m.set_sequence_counter(max_seqs[m.machine_id])

    protocol_mgr = FactoryProtocolManager()
    protocol_mgr.register_simulator(factory)
    edge_service = EdgeIngestionService(profiles=all_profiles)

    # 3b. Initialize Wokwi MQTT Bridge
    wokwi_bridge = None
    if wokwi_config.enabled:
        try:
            wokwi_bridge = WokwiMQTTBridge(wokwi_config)
            wokwi_bridge.start()
            logger.info("[StorageWorker] Wokwi MQTT Bridge service started.")
        except Exception as e:
            logger.warning(f"[StorageWorker] Could not start Wokwi MQTT Bridge: {e}")

    # 4. Start services
    protocol_mgr.start_all()
    factory.start()

    running = True

    def signal_handler(signum, frame):
        nonlocal running
        print("\nStopping background ingestion worker...")
        running = False

    signal.signal(signal.SIGINT, signal_handler)
    try:
        signal.signal(signal.SIGTERM, signal_handler)
    except AttributeError:
        pass

    step_count = 0
    print("[StorageWorker] Running continuous ingestion, alerting & ML inference loop. Press Ctrl+C to stop.")

    try:
        while running:
            step_count += 1

            # Synchronize active fault scenarios from database
            active_scenarios_in_db = set(scenario_repository.get_active_scenarios())
            for scen_id in active_scenarios_in_db:
                scen = scenario_mgr.get_scenario(scen_id)
                if scen and scen.state != FaultLifecycleState.ACTIVE:
                    try:
                        scenario_mgr.start_scenario(scen_id)
                        print(f" -> [Scenario] Started fault injection: {scen_id} on {scen.machine_id}")
                    except Exception as ex:
                        logger.warning(f"Error starting scenario {scen_id}: {ex}")

            for scen_id, scen in list(scenario_mgr.get_active_scenarios().items()):
                if scen_id not in active_scenarios_in_db:
                    try:
                        scenario_mgr.stop_scenario(scen_id)
                        print(f" -> [Scenario] Stopped fault injection: {scen_id}")
                    except Exception as ex:
                        logger.warning(f"Error stopping scenario {scen_id}: {ex}")

            # Advance degradation physics
            scenario_mgr.step(dt_seconds=poll_interval)
            factory.step()

            snapshots = factory.collect_telemetry()
            protocol_mgr.update_from_simulator(snapshots)
            time.sleep(0.05)

            readings = protocol_mgr.read_all_adapters()
            if wokwi_bridge is not None:
                wokwi_readings = wokwi_bridge.pop_all_readings()
                if wokwi_readings:
                    readings.extend(wokwi_readings)

            persisted = 0
            new_alerts = 0
            ml_inferences_count = 0
            for r in readings:
                res = edge_service.ingest_reading(r)
                if res.status == IngestionStatus.ACCEPTED and res.canonical_telemetry:
                    if repository.insert(res.canonical_telemetry):
                        persisted += 1

                    # Evaluate rule-based operational alert rules
                    triggered = alert_engine.process_telemetry(res.canonical_telemetry)
                    if triggered:
                        new_alerts += len(triggered)

                    # Execute Edge ML Inference pipeline (only for industrial machines)
                    if ml_service is not None and res.canonical_telemetry.machine_type != "ENVIRONMENT_SENSOR" and not res.canonical_telemetry.machine_id.startswith("IOT-"):
                        ml_res = ml_service.infer(res.canonical_telemetry)
                        if ml_res.status == InferenceStatus.READY:
                            ml_inferences_count += 1
                            m_id = res.canonical_telemetry.machine_id

                            # Step 1: Record raw result into the sliding window aggregator FIRST.
                            # The window tracks the trend: EMA score and anomaly ratio across
                            # the last N readings. A single-reading spike does NOT qualify as
                            # an anomaly — only a sustained trend does.
                            anomaly_aggregator.record(ml_res)

                            # Step 2: Overwrite the anomaly label and score with the
                            # trend-based windowed determination before writing to DB.
                            # This means the dashboard chart and the persisted record both
                            # reflect the actual sustained trend, not per-second jitter.
                            ml_res.anomaly_score = anomaly_aggregator.get_ema_score(m_id)
                            sustained = anomaly_aggregator.should_alert(m_id)
                            ml_res.anomaly_label = (
                                AnomalyLabel.ANOMALOUS if sustained else AnomalyLabel.NORMAL
                            )

                            # Step 3: Persist the trend-enriched result to the database.
                            ml_repository.insert(ml_res)

                            # Step 4: Only fire an ML alert when the sustained anomaly is confirmed.
                            if sustained:
                                ml_alerts = ml_alert_adapter.process_inference_result(ml_res)
                                if ml_alerts:
                                    new_alerts += len(ml_alerts)
                                    summary = anomaly_aggregator.get_window_summary(m_id)
                                    logger.info(
                                        f"[ML-Window] Sustained anomaly confirmed for {m_id}: "
                                        f"ratio={summary['anomaly_ratio']:.2f}, "
                                        f"ema={summary['ema_score']:.3f}"
                                    )

            active_scenarios_str = f" | Active Scenarios: {', '.join(active_scenarios_in_db)}" if active_scenarios_in_db else ""
            alert_info = f" | Alerts: {new_alerts}" if new_alerts > 0 else ""
            ml_info = f" | ML Predictions: {ml_inferences_count}" if ml_inferences_count > 0 else ""
            print(
                f"[{time.strftime('%H:%M:%S')}] Step {step_count:04d} | "
                f"Readings: {len(readings)} | Persisted: {persisted} records{ml_info}{alert_info}{active_scenarios_str}",
                flush=True
            )
            time.sleep(poll_interval)
    except KeyboardInterrupt:
        pass
    finally:
        print("[StorageWorker] Cleaning up services...")
        if wokwi_bridge is not None:
            try:
                wokwi_bridge.stop()
            except Exception:
                pass
        try:
            protocol_mgr.stop_all()
        except Exception:
            pass
        try:
            engine.dispose()
        except Exception:
            pass
        print("[StorageWorker] Stopped cleanly.")


if __name__ == "__main__":
    run_worker()

