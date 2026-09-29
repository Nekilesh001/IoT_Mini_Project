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
from storage.repository import TelemetryRepository
from alerts.models import AlertRecord
from alerts.repository import AlertRepository
from alerts.engine import AlertEngine
from alerts.rules import create_default_rules
from scenarios.fault_scenarios import FaultLifecycleState
from scenarios.manager import FaultScenarioManager
from scenarios.repository import ScenarioStateRepository

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("storage.worker")


def run_worker():
    db_url = os.getenv("DATABASE_URL", StorageConfig().database_url)
    poll_interval = float(os.getenv("WORKER_POLL_INTERVAL", "1.0"))

    print("=" * 80)
    print(" SMART FACTORY — CONTINUOUS SIMULATION & INGESTION WORKER")
    print(f" Database URL: {db_url}")
    print(f" Loop Interval: {poll_interval}s")
    print("=" * 80)

    # 1. Initialize Database & Repositories
    engine = get_engine(db_url)
    init_db(engine)
    session_factory = get_session_factory(engine)
    repository = TelemetryRepository(session_factory)
    alert_repository = AlertRepository(session_factory)
    alert_engine = AlertEngine(rules=create_default_rules(), repository=alert_repository)
    scenario_repository = ScenarioStateRepository(session_factory)

    # 2. Initialize Simulator, Scenarios & Protocols
    factory = FactorySimulator(seed=42)
    scenario_mgr = FaultScenarioManager(factory=factory)
    profiles = {m.machine_id: m.profile for m in factory.get_all_machines()}

    protocol_mgr = FactoryProtocolManager()
    protocol_mgr.register_simulator(factory)
    edge_service = EdgeIngestionService(profiles=profiles)

    # 3. Start services
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
    print("[StorageWorker] Running continuous ingestion & alerting loop. Press Ctrl+C to stop.")

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
            persisted = 0
            new_alerts = 0
            for r in readings:
                res = edge_service.ingest_reading(r)
                if res.status == IngestionStatus.ACCEPTED and res.canonical_telemetry:
                    if repository.insert(res.canonical_telemetry):
                        persisted += 1
                    # Evaluate operational alert rules
                    triggered = alert_engine.process_telemetry(res.canonical_telemetry)
                    if triggered:
                        new_alerts += len(triggered)

            active_scenarios_str = f" | Active Scenarios: {', '.join(active_scenarios_in_db)}" if active_scenarios_in_db else ""
            alert_info = f" | Alerts: {new_alerts}" if new_alerts > 0 else ""
            print(
                f"[{time.strftime('%H:%M:%S')}] Step {step_count:04d} | "
                f"Readings: {len(readings)} | Persisted: {persisted} records to database{alert_info}{active_scenarios_str}",
                flush=True
            )
            time.sleep(poll_interval)
    except KeyboardInterrupt:
        pass
    finally:
        print("[StorageWorker] Cleaning up services...")
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

