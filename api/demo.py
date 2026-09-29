"""
Phase 5 Complete Demonstration: FastAPI Backend, Realtime SSE Streaming, and Operations Dashboard Integration.
"""

import time
import asyncio
from datetime import datetime, timezone
from fastapi.testclient import TestClient

from simulator.runtime.factory_runtime import FactorySimulator
from protocols.manager import FactoryProtocolManager
from edge.service import EdgeIngestionService
from edge.models import IngestionStatus
from storage.coordinator import Phase4ServiceCoordinator
from api.main import app
from api.dependencies import get_db_engine, get_telemetry_repository, get_factory_profiles


def run_phase5_demo():
    print("=" * 80)
    print(" SMART FACTORY MACHINE MONITORING & PREDICTIVE MAINTENANCE SYSTEM")
    print(" PHASE 5 — FASTAPI BACKEND & OPERATIONS DASHBOARD DEMO")
    print("=" * 80)

    # 1. Initialize Simulator, Protocol Layer, Edge Ingestion, and Phase 4 Storage Coordinator
    print("\n[1] Initializing 12-Machine Factory Simulator, Protocols, Edge Ingestion, and Phase 4 Storage...")
    factory = FactorySimulator(seed=42)
    profiles = {m.machine_id: m.profile for m in factory.get_all_machines()}

    protocol_mgr = FactoryProtocolManager()
    protocol_mgr.register_simulator(factory)
    edge_service = EdgeIngestionService(profiles=profiles)

    db_url = os.getenv("DATABASE_URL", "sqlite:///demo_api.db")
    coordinator = Phase4ServiceCoordinator(db_url=db_url)
    coordinator.start()
    protocol_mgr.start_all()

    # Configure FastAPI dependencies to use active coordinator repository
    app.dependency_overrides[get_db_engine] = lambda: coordinator._engine
    app.dependency_overrides[get_telemetry_repository] = lambda: coordinator.repository

    client = TestClient(app)

    try:
        # 2. Advance simulation and ingest real machine telemetry
        print("\n[2] Advancing simulation and ingesting multi-protocol machine telemetry...")
        factory.start()
        factory.step()

        snapshots = factory.collect_telemetry()
        protocol_mgr.update_from_simulator(snapshots)
        time.sleep(0.3)

        readings = protocol_mgr.read_all_adapters()
        print(f" -> Collected {len(readings)} readings across Modbus TCP, OPC UA, and MQTT.")

        for r in readings:
            res = edge_service.ingest_reading(r)
            if res.status == IngestionStatus.ACCEPTED and res.canonical_telemetry:
                coordinator.process_canonical_telemetry(res.canonical_telemetry)

        time.sleep(0.5)

        # 3. Test GET /api/health
        print("\n[3] Testing GET /api/health...")
        resp_health = client.get("/api/health")
        assert resp_health.status_code == 200
        health_data = resp_health.json()
        print(f" -> Status: {health_data['status']} | DB Connected: {health_data['database_connected']} | Version: {health_data['version']}")

        # 4. Test GET /api/factory/summary
        print("\n[4] Testing GET /api/factory/summary...")
        resp_summary = client.get("/api/factory/summary")
        assert resp_summary.status_code == 200
        sum_data = resp_summary.json()
        print(f" -> Total Machines: {sum_data['total_machines']}")
        print(f" -> Operational States: Running={sum_data['states']['running']}, Idle={sum_data['states']['idle']}, Maintenance={sum_data['states']['maintenance']}, Off={sum_data['states']['off']}")
        print(f" -> Health States: Healthy={sum_data['health']['healthy']}, Warning={sum_data['health']['warning']}, Critical={sum_data['health']['critical']}")
        print(f" -> Total Stored Telemetry Records: {sum_data['total_telemetry_records']}")

        # 5. Test GET /api/machines
        print("\n[5] Testing GET /api/machines (Machine Fleet Overview)...")
        resp_machines = client.get("/api/machines")
        assert resp_machines.status_code == 200
        machines_data = resp_machines.json()
        print(f" -> Retrieved {len(machines_data)} machines.")
        for m in machines_data[:4]:
            print(f"    - [{m['machine_id']}] Type: {m['machine_type']} | Proto: {m['protocol']} | State: {m['operating_state']} | Seq: #{m['sequence']} | Key Signals: {list(m['key_measurements'].keys())[:2]}")

        # 6. Test GET /api/machines/{machine_id}
        print("\n[6] Testing GET /api/machines/CNC-001 (Machine Detail & Provenance)...")
        resp_cnc = client.get("/api/machines/CNC-001")
        assert resp_cnc.status_code == 200
        cnc_data = resp_cnc.json()
        print(f" -> Machine ID: {cnc_data['machine_id']} | Type: {cnc_data['machine_type']}")
        print(f" -> Signal Catalog: {len(cnc_data['signals'])} defined signals ({', '.join([s['name'] for s in cnc_data['signals'][:3]])}...)")
        print(f" -> Live Measurements: {cnc_data['current_measurements']}")

        # 7. Test GET /api/machines/{machine_id}/history
        print("\n[7] Testing GET /api/machines/CNC-001/history (Time-Series Trends)...")
        resp_hist = client.get("/api/machines/CNC-001/history?limit=50")
        assert resp_hist.status_code == 200
        hist_data = resp_hist.json()
        print(f" -> Historical Points: {hist_data['total_records']} | Available Signals: {len(hist_data['available_signals'])}")

        # 8. Test GET /api/protocols/health
        print("\n[8] Testing GET /api/protocols/health (Gateway Status)...")
        resp_proto = client.get("/api/protocols/health")
        assert resp_proto.status_code == 200
        proto_data = resp_proto.json()
        for p in proto_data["protocols"]:
            print(f" -> [{p['protocol']}] Status: {p['status']} | Endpoint: {p['endpoint']} | Assigned: {p['assigned_machines']}")

        # 9. Verify Realtime SSE Stream Generator
        print("\n[9] Verifying Realtime SSE Generator...")
        from api.services.realtime_service import RealtimeService
        rt_service = RealtimeService(repository=coordinator.repository, profiles=profiles, interval_seconds=0.1)

        async def test_sse_sample():
            gen = rt_service.event_generator()
            event_chunk = await anext(gen)
            print(f" -> Received Live SSE Chunk: {event_chunk.strip()[:100]}...")

        asyncio.run(test_sse_sample())

        print("\n" + "=" * 80)
        print(" PHASE 5 COMPLETE — FASTAPI & OPERATIONS DASHBOARD VERIFIED")
        print("=" * 80)

    finally:
        print("\n[10] Stopping Phase 5 Demo Services...")
        coordinator.stop()
        protocol_mgr.stop_all()
        app.dependency_overrides.clear()
        print(" -> All services cleanly stopped.")


if __name__ == "__main__":
    run_phase5_demo()
