"""
Phase 4 Operational Storage, MQTT Event Bus, and Store-and-Forward Outage Recovery Demonstration.
"""

from pathlib import Path
import time

from simulator.runtime.factory_runtime import FactorySimulator
from protocols.manager import FactoryProtocolManager
from edge.service import EdgeIngestionService
from storage.coordinator import Phase4ServiceCoordinator
from edge.models import IngestionStatus


def run_storage_demo():
    print("=" * 80)
    print(" SMART FACTORY MACHINE MONITORING & PREDICTIVE MAINTENANCE SYSTEM")
    print(" PHASE 4 — LOCAL STORAGE, MQTT EVENT BUS & BUFFERING DEMO")
    print("=" * 80)

    demo_db_path = "demo_operational_telemetry.db"
    demo_buffer_path = "demo_persistent_buffer.db"
    db_url = f"sqlite:///{demo_db_path}"

    # 1. Initialize Simulator, Protocol Layer & Edge Ingestion
    print("\n[1] Initializing 12-Machine Factory Simulator, Protocols, and Edge Ingestion...")
    factory = FactorySimulator(seed=42)
    profiles = {m.machine_id: m.profile for m in factory.get_all_machines()}

    protocol_mgr = FactoryProtocolManager()
    protocol_mgr.register_simulator(factory)
    edge_service = EdgeIngestionService(profiles=profiles)

    # 2. Initialize Phase 4 Coordinator
    print("[2] Initializing Phase 4 Operational Storage, Event Bus, and Buffer Coordinator...")
    coordinator = Phase4ServiceCoordinator(db_url=db_url, buffer_path=demo_buffer_path)

    protocol_mgr.start_all()
    coordinator.start()
    time.sleep(0.5)

    try:
        # 3. Normal Flow: Simulate -> Protocol -> Edge Ingest -> MQTT Event Bus -> Database
        print("\n[3] Step 1: Normal Ingestion & Persistence Pipeline (Step 1)...")
        factory.start()
        factory.step()

        snapshots = factory.collect_telemetry()
        protocol_mgr.update_from_simulator(snapshots)
        time.sleep(0.2)

        readings = protocol_mgr.read_all_adapters()
        print(f" -> Received {len(readings)} protocol readings. Ingesting at edge and publishing...")

        for r in readings:
            res = edge_service.ingest_reading(r)
            if res.status == IngestionStatus.ACCEPTED and res.canonical_telemetry:
                coordinator.process_canonical_telemetry(res.canonical_telemetry)

        time.sleep(0.5)

        # Verify persisted records in database
        print(" -> Verifying database persistence across heterogeneous machines:")
        for m_id in ["CNC-001", "CNC-002", "ROB-002", "PMP-001"]:
            record = coordinator.repository.get_latest_by_machine(m_id)
            if record:
                print(f"    - [{record.machine_id}] Seq: {record.sequence} | Protocol: {record.protocol} | Quality: {record.quality} | Measurements: {list(record.measurements.keys())[:3]}")

        # 4. Outage Simulation: Simulate broker outage & store-and-forward buffering
        print("\n[4] Step 2: Simulating MQTT Broker Outage (Failure Injection)...")
        coordinator.publisher.simulate_broker_outage()
        print(" -> MQTT Broker marked unavailable. Advancing simulation to Step 2...")

        factory.step()
        snapshots_step2 = factory.collect_telemetry()
        protocol_mgr.update_from_simulator(snapshots_step2)
        time.sleep(0.2)

        readings_step2 = protocol_mgr.read_all_adapters()
        for r in readings_step2:
            res = edge_service.ingest_reading(r)
            if res.status == IngestionStatus.ACCEPTED and res.canonical_telemetry:
                coordinator.process_canonical_telemetry(res.canonical_telemetry)

        pending_count = coordinator.buffer.count_by_status("PENDING")
        print(f" -> Telemetry automatically preserved in SQLite persistent buffer. Pending buffer count: {pending_count}")
        assert pending_count == 12, "Expected all 12 events to be buffered during outage"

        # 5. Recovery & Replay: Restore broker and trigger replay worker
        print("\n[5] Step 3: Restoring Broker Connection & Executing Buffer Replay...")
        coordinator.publisher.restore_broker()
        print(" -> Broker connection restored. Triggering replay worker batch...")

        replayed = coordinator.replay_worker.replay_batch()
        print(f" -> Replay worker successfully delivered {replayed} buffered events to MQTT & Database.")
        time.sleep(0.5)

        remaining_buffer = coordinator.buffer.count_by_status("PENDING")
        print(f" -> Remaining pending buffer count: {remaining_buffer}")
        assert remaining_buffer == 0, "Expected buffer to be fully drained after replay"

        # Verify step 2 records now in database
        cnc_latest = coordinator.repository.get_latest_by_machine("CNC-001")
        print(f" -> Latest CNC-001 record in database: Sequence={cnc_latest.sequence if cnc_latest else 'None'}")
        assert cnc_latest and cnc_latest.sequence == 2

        # 6. Idempotency Test: Re-delivering existing records
        print("\n[6] Step 4: Testing Idempotent Duplicate Rejection...")
        dup_reading = readings[0]
        dup_canonical = edge_service.ingest_reading(dup_reading).canonical_telemetry
        if dup_canonical:
            inserted_again = coordinator.repository.insert(dup_canonical)
            print(f" -> Re-inserting already persisted event {dup_canonical.event_id} (Seq: {dup_canonical.sequence}):")
            print(f"    Inserted flag: {inserted_again} (False confirms duplicate-safe rejection)")
            assert not inserted_again

        # 7. Operational Metrics
        print("\n[7] Phase 4 Operational Metrics:")
        metrics = coordinator.get_metrics()
        for section, data in metrics.items():
            print(f"    - {section}: {data}")

    finally:
        print("\n[8] Stopping Phase 4 Operational Services...")
        coordinator.stop()
        protocol_mgr.stop_all()
        time.sleep(0.5)

        # Clean up demo files
        for p in [demo_db_path, demo_buffer_path]:
            f = Path(p)
            try:
                if f.exists():
                    f.unlink(missing_ok=True)
            except Exception:
                pass
        print(" -> All services stopped and temporary demo artifacts cleaned up.")

    print("\n" + "=" * 80)
    print(" PHASE 4 DEMONSTRATION COMPLETE — STORAGE & BUFFERING VERIFIED")
    print("=" * 80)


if __name__ == "__main__":
    run_storage_demo()
