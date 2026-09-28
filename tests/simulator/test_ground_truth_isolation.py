"""
Unit tests asserting ground-truth data isolation from public telemetry envelopes.
"""

from simulator.runtime.factory_runtime import FactorySimulator


def test_ground_truth_isolation_from_public_telemetry():
    factory = FactorySimulator(seed=42)
    factory.start()

    pump = factory.get_machine("PMP-001")
    pump.set_degradation(85.0)
    pump.apply_condition("bearing_wear", severity=85.0)

    snapshot = pump.generate_snapshot()
    public_dict = snapshot.to_dict(include_ground_truth=False)

    # 1. Ground truth envelope must not exist in public dict
    assert "_simulationGroundTruth" not in public_dict

    # 2. Simulator internal variables MUST NOT leak into measurements payload
    forbidden_keys = [
        "degradation_level",
        "scenario_id",
        "fault_label",
        "active_conditions",
        "hidden_wear_counter",
        "bearing_wear"
    ]

    for key in forbidden_keys:
        assert key not in public_dict["measurements"], (
            f"Target leakage detected! Ground-truth variable '{key}' "
            f"was found inside public telemetry measurements payload."
        )
