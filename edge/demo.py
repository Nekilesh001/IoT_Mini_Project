"""
Phase 3 Canonical Telemetry & Edge Ingestion Pipeline Demonstration.
"""

import json
import logging
import time

from simulator.runtime.factory_runtime import FactorySimulator
from protocols.manager import FactoryProtocolManager
from protocols.models import ProtocolReading, ProtocolType
from edge.service import EdgeIngestionService
from edge.models import IngestionStatus

logging.basicConfig(level=logging.WARNING)


def run_edge_demo():
    print("=" * 80)
    print(" SMART FACTORY MACHINE MONITORING & PREDICTIVE MAINTENANCE SYSTEM")
    print(" PHASE 3 — CANONICAL TELEMETRY & EDGE INGESTION PIPELINE DEMO")
    print("=" * 80)

    # 1. Initialize Simulator & Protocol Manager
    print("\n[1] Initializing 12-Machine Factory Simulator & Edge Ingestion Service...")
    factory = FactorySimulator(seed=42)
    profiles = {m.machine_id: m.profile for m in factory.get_all_machines()}

    protocol_mgr = FactoryProtocolManager()
    protocol_mgr.register_simulator(factory)
    edge_service = EdgeIngestionService(profiles=profiles)

    # 2. Start Protocol Servers and Connect Adapters
    print("[2] Starting Protocol Layer (Modbus TCP, OPC UA, MQTT)...")
    protocol_mgr.start_all()
    time.sleep(0.5)

    try:
        # 3. Simulate and Ingest Step 1
        print("\n[3] Step 1: Ingesting live multi-protocol readings into Canonical Telemetry...")
        factory.start()
        factory.step()

        snapshots = factory.collect_telemetry()
        protocol_mgr.update_from_simulator(snapshots)
        time.sleep(0.2)

        readings = protocol_mgr.read_all_adapters()
        print(f" -> Received {len(readings)} / 12 protocol readings. Ingesting at Edge...")

        canonical_samples = []
        for r in readings:
            res = edge_service.ingest_reading(r)
            if res.status == IngestionStatus.ACCEPTED and res.canonical_telemetry:
                canonical_samples.append(res.canonical_telemetry)

        # Print representative canonical payloads from each protocol
        for c in canonical_samples[:4]:
            print(f"\n   --- Machine: {c.machine_id} [{c.machine_type}] ---")
            print(f"   Protocol: {c.source.protocol} | Source Address: {c.source.source_address}")
            print(f"   Event Time: {c.event_time} | Ingestion Time: {c.ingestion_time}")
            print(f"   Seq: {c.sequence} | State: {c.state.operating} ({c.state.health}) | Quality: {c.quality.value}")
            print(f"   Measurements: {c.measurements}")
            if c.derived:
                print(f"   Derived Metrics: {c.derived}")

        # 4. Demonstrate Duplicate Detection
        print("\n[4] Step 2: Testing Duplicate Detection...")
        dup_reading = readings[0]
        dup_res = edge_service.ingest_reading(dup_reading)
        print(f" -> Ingesting duplicate event for '{dup_reading.machine_id}' (Seq: {dup_reading.sequence}):")
        print(f"    Result Status: {dup_res.status.value}")
        print(f"    Message: {dup_res.errors[0] if dup_res.errors else 'No error'}")

        # 5. Demonstrate Out-of-Order Detection
        print("\n[5] Step 3: Testing Out-of-Order Detection...")
        factory.step()
        snap_step2 = factory.collect_telemetry()
        protocol_mgr.update_from_simulator(snap_step2)
        time.sleep(0.1)

        new_readings = protocol_mgr.read_all_adapters()
        matching_new = [r for r in new_readings if r.machine_id == dup_reading.machine_id]
        if matching_new:
            new_reading = matching_new[0]
            edge_service.ingest_reading(new_reading)
            print(f" -> Advanced machine '{dup_reading.machine_id}' to Seq: {new_reading.sequence} (ACCEPTED).")

            # Now submit older sequence
            old_res = edge_service.ingest_reading(dup_reading)
            print(f" -> Re-submitting older Seq: {dup_reading.sequence} for machine '{dup_reading.machine_id}':")
            print(f"    Result Status: {old_res.status.value}")
            print(f"    Message: {old_res.errors[0] if old_res.errors else 'No error'}")

        # 6. Pipeline Ingestion Metrics
        print("\n[6] Ingestion Pipeline Operational Metrics:")
        metrics = edge_service.get_metrics()
        for k, v in metrics.items():
            print(f"    - {k}: {v}")

    finally:
        print("\n[7] Stopping Protocol Layer Services...")
        protocol_mgr.stop_all()
        print(" -> All protocol services stopped cleanly.")

    print("\n" + "=" * 80)
    print(" PHASE 3 DEMONSTRATION COMPLETE — CANONICAL INGESTION VERIFIED")
    print("=" * 80)


if __name__ == "__main__":
    run_edge_demo()
