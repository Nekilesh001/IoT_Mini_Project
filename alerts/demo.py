"""
Phase 6 Systematic Fault-Injection & Rule-Based Alerting Demonstration.
"""

from datetime import datetime, timezone
import time
from pathlib import Path

from simulator.runtime.factory_runtime import FactorySimulator
from scenarios.manager import FaultScenarioManager
from protocols.manager import FactoryProtocolManager
from edge.service import EdgeIngestionService
from edge.models import IngestionStatus
from storage.database import get_engine, get_session_factory, init_db
from storage.repository import TelemetryRepository
from alerts.models import AlertRecord
from alerts.repository import AlertRepository
from alerts.engine import AlertEngine
from alerts.rules import AlertSeverity, AlertStatus


def run_alerts_demo():
    print("=" * 80)
    print(" SMART FACTORY MACHINE MONITORING & PREDICTIVE MAINTENANCE SYSTEM")
    print(" PHASE 6 — SYSTEMATIC FAULT INJECTION & RULE-BASED ALERTS DEMO")
    print("=" * 80)

    demo_db_path = "demo_phase6_alerts.db"
    db_url = f"sqlite:///{demo_db_path}"

    # 1. Initialize Simulator, Protocol Layer, Edge Ingestion, and Alert Infrastructure
    print("\n[1] Initializing 12-Machine Simulator, Protocols, Edge Ingestion, and Alert Engine...")
    engine = get_engine(db_url)
    init_db(engine)
    session_factory = get_session_factory(engine)

    telemetry_repo = TelemetryRepository(session_factory)
    alert_repo = AlertRepository(session_factory)
    alert_engine = AlertEngine(repository=alert_repo)

    factory = FactorySimulator(seed=42)
    scenario_mgr = FaultScenarioManager(factory=factory)
    profiles = {m.machine_id: m.profile for m in factory.get_all_machines()}

    protocol_mgr = FactoryProtocolManager()
    protocol_mgr.register_simulator(factory)
    edge_service = EdgeIngestionService(profiles=profiles)

    protocol_mgr.start_all()
    factory.start()

    try:
        # 2. Baseline Normal Operation (Ticks 1-3)
        print("\n[2] Executing Baseline Healthy Telemetry Generation (3 Ticks)...")
        for tick in range(1, 4):
            factory.step()
            snapshots = factory.collect_telemetry()
            protocol_mgr.update_from_simulator(snapshots)
            time.sleep(0.05)

            readings = protocol_mgr.read_all_adapters()
            for r in readings:
                res = edge_service.ingest_reading(r)
                if res.status == IngestionStatus.ACCEPTED and res.canonical_telemetry:
                    telemetry_repo.insert(res.canonical_telemetry)
                    alert_engine.process_telemetry(res.canonical_telemetry)

        active_alerts = alert_repo.list_active_alerts()
        print(f" -> Baseline complete. Active alerts count: {len(active_alerts)} (Expected: 0)")
        assert len(active_alerts) == 0

        # 3. Sudden Fault Scenario: CONVEYOR_BELT_JAM on CON-001
        print("\n[3] Ingesting Sudden Fault Scenario: CONVEYOR_BELT_JAM (CON-001)...")
        scenario_mgr.start_scenario("CONVEYOR_BELT_JAM")
        print(" -> Injected belt jam condition into CON-001. Stepping simulator...")

        for tick in range(4, 6):
            factory.step()
            scenario_mgr.step()
            snapshots = factory.collect_telemetry()
            protocol_mgr.update_from_simulator(snapshots)
            time.sleep(0.05)

            readings = protocol_mgr.read_all_adapters()
            for r in readings:
                res = edge_service.ingest_reading(r)
                if res.status == IngestionStatus.ACCEPTED and res.canonical_telemetry:
                    telemetry_repo.insert(res.canonical_telemetry)
                    alert_engine.process_telemetry(res.canonical_telemetry)

        con_alerts = alert_repo.list_machine_alerts("CON-001")
        print(f" -> Generated {len(con_alerts)} alerts for CON-001:")
        for a in con_alerts:
            print(f"    - [{a.severity}] Code: {a.alert_code} | {a.title} | Triggering: {a.triggering_measurements}")
        assert len(con_alerts) > 0, "Expected at least one alert for CON-001"

        # 4. Acknowledge the Conveyor Alert
        con_alert = con_alerts[0]
        print(f"\n[4] Acknowledging Alert '{con_alert.alert_id}' by operator...")
        acked = alert_repo.acknowledge_alert(con_alert.alert_id, acknowledged_by="lead_operator")
        print(f" -> Alert Status: {acked.status} | Acknowledged by: {acked.acknowledged_by}")
        assert acked.status == AlertStatus.ACKNOWLEDGED.value

        # 5. Progressive Degradation Scenario: PUMP_BEARING_WEAR on PMP-001
        print("\n[5] Ingesting Progressive Degradation Scenario: PUMP_BEARING_WEAR (PMP-001)...")
        scenario_mgr.start_scenario("PUMP_BEARING_WEAR")
        print(" -> Injected progressive bearing wear into PMP-001. Stepping simulator over 6 degradation ticks...")

        for tick in range(6, 12):
            factory.step()
            scenario_mgr.step()
            snapshots = factory.collect_telemetry()
            protocol_mgr.update_from_simulator(snapshots)
            time.sleep(0.05)

            readings = protocol_mgr.read_all_adapters()
            for r in readings:
                res = edge_service.ingest_reading(r)
                if res.status == IngestionStatus.ACCEPTED and res.canonical_telemetry:
                    telemetry_repo.insert(res.canonical_telemetry)
                    alert_engine.process_telemetry(res.canonical_telemetry)

        pmp_alerts = alert_repo.list_machine_alerts("PMP-001")
        print(f" -> Generated {len(pmp_alerts)} alerts for PMP-001:")
        for a in pmp_alerts:
            print(f"    - [{a.severity}] Code: {a.alert_code} | {a.title} | Occurrences: {a.occurrence_count} | Triggering: {a.triggering_measurements}")
        assert len(pmp_alerts) > 0, "Expected bearing wear alert for PMP-001"

        # 6. Fault Resolution & Recovery (Hysteresis & Auto-Clear)
        print("\n[6] Clearing Fault Scenarios (Maintenance Recovery)...")
        scenario_mgr.stop_scenario("CONVEYOR_BELT_JAM")
        scenario_mgr.stop_scenario("PUMP_BEARING_WEAR")

        print(" -> Advancing simulation under restored healthy operation...")
        for tick in range(12, 16):
            factory.step()
            snapshots = factory.collect_telemetry()
            protocol_mgr.update_from_simulator(snapshots)
            time.sleep(0.05)

            readings = protocol_mgr.read_all_adapters()
            for r in readings:
                res = edge_service.ingest_reading(r)
                if res.status == IngestionStatus.ACCEPTED and res.canonical_telemetry:
                    telemetry_repo.insert(res.canonical_telemetry)
                    alert_engine.process_telemetry(res.canonical_telemetry)

        # 7. Operational Summary & History Verification
        print("\n[7] Verifying Factory-Wide Alert Summary and Audit History:")
        summary = alert_repo.get_summary()
        for k, v in summary.items():
            print(f"    - {k}: {v}")

        history = alert_repo.list_alerts(limit=10)
        print(f"\n -> Total Recorded Audit History: {len(history)} alert records")
        for h in history:
            print(f"    - [{h.status}] [{h.severity}] Machine: {h.machine_id} | Rule: {h.rule_id} | Resolved: {h.resolved_at is not None}")

    finally:
        print("\n[8] Cleaning up demonstration resources...")
        protocol_mgr.stop_all()
        engine.dispose()
        p = Path(demo_db_path)
        if p.exists():
            p.unlink(missing_ok=True)
        print(" -> All services stopped cleanly.")

    print("\n" + "=" * 80)
    print(" PHASE 6 FAULT INJECTION & ALERTING DEMONSTRATION SUCCESSFUL")
    print("=" * 80)


if __name__ == "__main__":
    run_alerts_demo()
