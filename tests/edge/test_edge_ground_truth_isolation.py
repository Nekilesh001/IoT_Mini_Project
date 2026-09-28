"""
Regression tests verifying that simulation ground-truth fields never enter canonical telemetry.
"""

from simulator.runtime.factory_runtime import FactorySimulator
from protocols.models import ProtocolReading, ProtocolType
from edge.service import EdgeIngestionService
from edge.models import IngestionStatus


def test_ground_truth_isolation_in_canonical_payload():
    factory = FactorySimulator(seed=42)
    factory.start()
    factory.step()

    m = factory.get_machine("CNC-001")
    snap = m.generate_snapshot()

    # Verify snap ground truth exists in simulator
    assert snap.ground_truth.degradation_level is not None
    assert snap.ground_truth.hidden_wear_counter is not None

    profiles = {m.machine_id: m.profile for m in factory.get_all_machines()}
    service = EdgeIngestionService(profiles=profiles)

    # Convert public snapshot to protocol reading
    reading = ProtocolReading(
        machine_id=snap.machine_id,
        machine_type=str(snap.machine_type),
        protocol=ProtocolType.OPC_UA,
        timestamp=snap.timestamp,
        sequence=snap.sequence,
        measurements=snap.public_measurements,
        source_address="ns=2;s=CNC-001",
        raw_payload={}
    )

    res = service.ingest_reading(reading)
    assert res.status == IngestionStatus.ACCEPTED
    canonical = res.canonical_telemetry
    canonical_dict = canonical.to_dict()

    # Assert forbidden ground-truth fields are absent anywhere in the canonical dictionary
    forbidden_keys = {
        "_simulationGroundTruth",
        "ground_truth",
        "degradation_level",
        "scenario_id",
        "fault_label",
        "active_conditions",
        "hidden_wear_counter"
    }

    assert not any(k in canonical_dict for k in forbidden_keys)
    assert not any(k in canonical.measurements for k in forbidden_keys)
    assert not any(k in canonical.derived for k in forbidden_keys)
