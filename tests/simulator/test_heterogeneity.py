"""
Unit tests for machine heterogeneity and machine-specific signal catalog verification.
"""

from simulator.runtime.factory_runtime import FactorySimulator


def test_machine_signal_heterogeneity():
    factory = FactorySimulator(seed=42)
    factory.start()
    factory.step(1.0)
    snapshots = factory.collect_telemetry()

    signal_sets = {}
    for snap in snapshots:
        signal_sets[snap.machine_id] = set(snap.public_measurements.keys())

    # Verify that different machine classes do NOT produce identical signal catalogs
    cnc_signals = signal_sets["CNC-001"]
    rob_signals = signal_sets["ROB-001"]
    con_signals = signal_sets["CON-001"]
    agv_signals = signal_sets["AGV-001"]

    assert cnc_signals != rob_signals, "CNC and Robot must have distinct signal catalogs."
    assert rob_signals != con_signals, "Robot and Conveyor must have distinct signal catalogs."
    assert con_signals != agv_signals, "Conveyor and AGV must have distinct signal catalogs."

    # Verify machine-specific signature signals
    assert "spindle_speed_rpm" in cnc_signals
    assert "joint_1_torque_nm" in rob_signals
    assert "belt_speed_m_s" in con_signals
    assert "battery_soc_pct" in agv_signals
    assert "refrigerant_high_pressure_bar" not in agv_signals
