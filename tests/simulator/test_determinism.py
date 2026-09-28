"""
Unit tests for deterministic simulation reproducibility.
"""

from simulator.runtime.factory_runtime import FactorySimulator
from simulator.scenarios.scenarios import NormalOperationScenario, BearingDegradationScenario


def test_simulation_reproducibility():
    # Run 1 with seed=42
    fac1 = FactorySimulator(seed=42)
    scen1 = NormalOperationScenario(fac1, seed=42)
    hist1 = scen1.execute(ticks=5)

    # Run 2 with seed=42
    fac2 = FactorySimulator(seed=42)
    scen2 = NormalOperationScenario(fac2, seed=42)
    hist2 = scen2.execute(ticks=5)

    assert len(hist1) == len(hist2)
    for tick_idx in range(len(hist1)):
        snaps1 = hist1[tick_idx]
        snaps2 = hist2[tick_idx]
        for m_idx in range(len(snaps1)):
            d1 = snaps1[m_idx].to_dict(include_ground_truth=True)
            d2 = snaps2[m_idx].to_dict(include_ground_truth=True)
            # Timestamps may differ slightly if wall-clock based, so exclude timestamp for strict numerical equality check
            d1.pop("timestamp", None)
            d2.pop("timestamp", None)
            assert d1 == d2, f"Determinism failure at tick {tick_idx} for machine {snaps1[m_idx].machine_id}."
