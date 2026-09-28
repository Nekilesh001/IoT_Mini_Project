"""
End-to-end integration test connecting Phase 1 simulator -> Phase 2 protocols -> Phase 3 Edge Ingestion.
"""

import time
from simulator.runtime.factory_runtime import FactorySimulator
from protocols.manager import FactoryProtocolManager
from edge.service import EdgeIngestionService
from edge.models import IngestionStatus


def test_end_to_end_multiprotocol_edge_ingestion():
    factory = FactorySimulator(seed=42)
    profiles = {m.machine_id: m.profile for m in factory.get_all_machines()}

    protocol_mgr = FactoryProtocolManager()
    protocol_mgr.register_simulator(factory)
    edge_service = EdgeIngestionService(profiles=profiles)

    try:
        protocol_mgr.start_all()
        time.sleep(0.3)

        factory.start()
        factory.step()

        snapshots = factory.collect_telemetry()
        protocol_mgr.update_from_simulator(snapshots)
        time.sleep(0.2)

        readings = protocol_mgr.read_all_adapters()
        assert len(readings) == 12

        canonical_list = []
        for r in readings:
            res = edge_service.ingest_reading(r)
            assert res.status == IngestionStatus.ACCEPTED
            assert res.canonical_telemetry is not None
            canonical_list.append(res.canonical_telemetry)

        assert len(canonical_list) == 12

        # Verify representation across all 3 protocols
        protocols_seen = {c.source.protocol for c in canonical_list}
        assert "MODBUS_TCP" in protocols_seen
        assert "OPC_UA" in protocols_seen
        assert "MQTT" in protocols_seen

    finally:
        protocol_mgr.stop_all()
