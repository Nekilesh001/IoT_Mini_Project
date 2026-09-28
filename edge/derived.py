"""
Edge-side simple deterministic derived metrics calculation.
"""

from typing import Any, Dict
from simulator.core.domain import MachineProfile, MachineType


class DerivedMetricsCalculator:
    """
    Computes simple, deterministic derived edge metrics from normalized measurements.
    """

    @classmethod
    def calculate_derived_metrics(cls, measurements: Dict[str, Any], profile: MachineProfile) -> Dict[str, Any]:
        derived: Dict[str, Any] = {}
        m_type = profile.machine_type

        # 1. Industrial Chiller: Thermal temperature differential
        if m_type == MachineType.INDUSTRIAL_CHILLER:
            ret_t = measurements.get("return_fluid_temp_c")
            sup_t = measurements.get("supply_fluid_temp_c")
            if isinstance(ret_t, (int, float)) and isinstance(sup_t, (int, float)):
                derived["delta_t_c"] = round(float(ret_t) - float(sup_t), 2)

        # 2. Industrial Pump: Pressure differential across pump head
        elif m_type == MachineType.INDUSTRIAL_PUMP:
            dis_p = measurements.get("discharge_pressure_bar")
            suc_p = measurements.get("suction_pressure_bar")
            if isinstance(dis_p, (int, float)) and isinstance(suc_p, (int, float)):
                derived["pressure_delta_bar"] = round(float(dis_p) - float(suc_p), 2)

        # 3. CNC Machines: Estimated active cutting power (assuming 15kW base spindle motor)
        elif m_type in (MachineType.CNC_MACHINING_CENTER, MachineType.CNC_LATHE):
            load_pct = measurements.get("spindle_load_pct")
            if isinstance(load_pct, (int, float)):
                derived["estimated_spindle_power_kw"] = round((float(load_pct) / 100.0) * 15.0, 2)

        # 4. Air Compressor: Compression pressure ratio against 1.0 bar atmospheric baseline
        elif m_type == MachineType.AIR_COMPRESSOR:
            dis_p = measurements.get("discharge_pressure_bar")
            if isinstance(dis_p, (int, float)):
                derived["compression_ratio"] = round(float(dis_p) / 1.0, 2)

        return derived
