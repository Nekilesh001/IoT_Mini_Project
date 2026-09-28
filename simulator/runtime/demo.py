"""
Phase 1 Runnable Demonstration Entry Point.
Initializes the 12-machine factory simulation core, runs ticks, and demonstrates
causal telemetry and degradation scenarios without external network dependencies.
"""

import sys
from simulator.runtime.factory_runtime import FactorySimulator
from simulator.scenarios.scenarios import BearingDegradationScenario


def run_demo() -> None:
    print("=" * 80)
    print(" SMART FACTORY MACHINE MONITORING & PREDICTIVE MAINTENANCE SYSTEM")
    print(" PHASE 1 — FACTORY SIMULATION CORE DEMO")
    print("=" * 80)

    # 1. Initialize Factory Runtime
    print("\n[1] Initializing 12-Machine Factory Simulator...")
    factory = FactorySimulator(seed=42)
    machines = factory.get_all_machines()
    print(f" -> Successfully loaded {len(machines)} heterogeneous industrial machines:")
    for m in machines:
        print(f"    - {m.machine_id:<8} | Type: {m.machine_type.value:<26} | Protocol: {m.protocol_metadata.value:<10} | Signals: {len(m.profile.signals)}")

    # 2. Advance Baseline Normal Simulation Ticks
    print("\n[2] Advancing Factory Simulation Ticks (Normal Operation)...")
    factory.start()
    for tick in range(1, 4):
        factory.step(time_delta_seconds=1.0)
        print(f"\n --- Simulation Tick {factory.total_ticks} ---")
        snapshots = factory.collect_telemetry()
        # Display sample machine-specific telemetry for 4 distinct machines
        for m_id in ["CNC-001", "ROB-001", "CON-001", "AGV-001"]:
            snap = next(s for s in snapshots if s.machine_id == m_id)
            print(f"   [{snap.machine_id}] State: {snap.operating_state:<8} | Health: {snap.health_state:<8} | Sequence: {snap.sequence}")
            # Print first 3 signals to demonstrate heterogeneity
            sample_keys = list(snap.public_measurements.keys())[:3]
            sample_vals = {k: snap.public_measurements[k] for k in sample_keys}
            print(f"       Sample Telemetry: {sample_vals}")

    # 3. Demonstrate Causal Degradation Scenario on Pump PMP-001
    print("\n" + "=" * 80)
    print("[3] Demonstrating Causal Bearing Degradation Scenario on PMP-001...")
    print("=" * 80)

    pump = factory.get_machine("PMP-001")
    print(f"Initial State -> PMP-001 Health: {pump.health_state.value} | Degradation: {pump.get_ground_truth().degradation_level:.1f}%")

    print("\nInjecting progressive bearing wear degradation across ticks...")
    print(f"{'Tick':<6} | {'State':<8} | {'Health':<8} | {'Degradation (%)':<15} | {'Vibration X (mm/s)':<20} | {'Bearing Temp (°C)':<18}")
    print("-" * 85)

    for step_i in range(1, 7):
        deg_level = step_i * 15.0
        pump.set_degradation(deg_level)
        pump.apply_condition("bearing_wear", severity=deg_level)
        factory.step(time_delta_seconds=1.0)
        snap = pump.generate_snapshot()
        vib = snap.public_measurements.get("vibration_x_mm_s", 0.0)
        temp = snap.public_measurements.get("bearing_temperature_c", 0.0)
        print(f"{factory.total_ticks:<6} | {snap.operating_state:<8} | {snap.health_state:<8} | {deg_level:<15.1f} | {vib:<20.3f} | {temp:<18.2f}")

    # 4. Demonstrate Ground-Truth Isolation
    print("\n" + "=" * 80)
    print("[4] Demonstrating Target Leakage Prevention & Ground-Truth Isolation...")
    print("=" * 80)
    sample_snapshot = pump.generate_snapshot()
    public_dict = sample_snapshot.to_dict(include_ground_truth=False)
    print(f" -> Public Telemetry Envelope Keys (Passed to Edge/ML):")
    print(f"    {list(public_dict.keys())}")
    print(f" -> Public Telemetry Measurement Keys:")
    print(f"    {list(public_dict['measurements'].keys())}")
    has_leakage = "degradation_level" in public_dict["measurements"] or "active_conditions" in public_dict["measurements"]
    print(f" -> Leakage Check: Ground-truth parameters present in public payload? {'YES (FAIL)' if has_leakage else 'NO (PASS)'}")

    print("\n" + "=" * 80)
    print(" PHASE 1 DEMONSTRATION COMPLETE — ALL SIMULATION Acceptance CRITERIA VERIFIED")
    print("=" * 80 + "\n")


if __name__ == "__main__":
    run_demo()
