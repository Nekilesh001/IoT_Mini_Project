"""
Machine-specific observable measurement catalogs and signal mappings.
"""

from typing import Dict, List, Set

# Explicit whitelist of physically observable measurements per machine type
OBSERVABLE_SIGNALS_BY_MACHINE_TYPE: Dict[str, List[str]] = {
    "CNC_MACHINING_CENTER": [
        "spindle_speed_rpm",
        "spindle_load_pct",
        "spindle_temperature_c",
        "vibration_rms_mm_s",
        "feed_rate_mm_min",
        "coolant_pressure_bar",
        "tool_wear_pct",
        "axis_x_position_mm",
        "axis_y_position_mm",
        "axis_z_position_mm",
    ],
    "CNC_LATHE": [
        "spindle_speed_rpm",
        "spindle_load_pct",
        "spindle_temperature_c",
        "vibration_rms_mm_s",
        "feed_rate_mm_min",
        "chuck_pressure_bar",
        "cutting_temperature_c",
        "tool_wear_pct",
    ],
    "INDUSTRIAL_ROBOT_6AXIS": [
        "joint_1_temp_c",
        "joint_2_temp_c",
        "joint_3_temp_c",
        "joint_4_temp_c",
        "joint_5_temp_c",
        "joint_6_temp_c",
        "motor_current_a",
        "cycle_time_s",
    ],
    "WELDING_ROBOT": [
        "joint_1_temp_c",
        "joint_2_temp_c",
        "joint_3_temp_c",
        "weld_current_a",
        "weld_voltage_v",
        "wire_feed_speed_m_min",
        "gas_flow_rate_l_min",
    ],
    "INDUSTRIAL_CONVEYOR": [
        "belt_speed_m_s",
        "drive_motor_current_a",
        "drive_motor_temp_c",
        "vibration_amplitude_mm",
        "belt_tension_n",
        "load_kg",
    ],
    "INDUSTRIAL_PRESS": [
        "hydraulic_pressure_bar",
        "press_force_kn",
        "ram_position_mm",
        "ram_speed_mm_s",
        "oil_temperature_c",
        "motor_load_pct",
    ],
    "INJECTION_MOLDING_MACHINE": [
        "barrel_temp_zone_1_c",
        "barrel_temp_zone_2_c",
        "barrel_temp_zone_3_c",
        "barrel_temp_zone_4_c",
        "mold_temperature_c",
        "injection_pressure_bar",
        "holding_pressure_bar",
        "screw_position_mm",
        "screw_speed_rpm",
    ],
    "AIR_COMPRESSOR": [
        "discharge_pressure_bar",
        "regulating_pressure_bar",
        "element_temperature_c",
        "ambient_temperature_c",
        "motor_current_a",
        "motor_load_pct",
    ],
    "INDUSTRIAL_PUMP": [
        "suction_pressure_bar",
        "discharge_pressure_bar",
        "flow_rate_m3_h",
        "speed_rpm",
        "motor_current_a",
        "power_kw",
        "bearing_temperature_c",
        "vibration_x_mm_s",
        "vibration_y_mm_s",
    ],
    "INDUSTRIAL_CHILLER": [
        "evaporator_temp_in_c",
        "evaporator_temp_out_c",
        "condenser_temp_c",
        "flow_rate_l_min",
        "cop",
        "compressor_power_kw",
    ],
    "AUTONOMOUS_MOBILE_ROBOT": [
        "pos_x_m",
        "pos_y_m",
        "speed_m_s",
        "heading_deg",
        "battery_soc_pct",
        "battery_voltage_v",
        "battery_temperature_c",
        "motor_current_a",
        "motor_speed_rpm",
        "total_distance_m",
    ],
    "VISION_INSPECTION_STATION": [
        "exposure_time_ms",
        "defect_rate_pct",
        "good_parts_count",
        "rejected_parts_count",
        "camera_temperature_c",
    ],
}

# Categorical encodings
OPERATING_STATE_ENCODING: Dict[str, float] = {
    "OFF": 0.0,
    "IDLE": 1.0,
    "STARTING": 2.0,
    "RUNNING": 3.0,
    "WARNING": 4.0,
    "MAINTENANCE": 5.0,
    "RECOVERY": 6.0,
    "EMERGENCY_STOP": 7.0,
}

QUALITY_ENCODING: Dict[str, float] = {
    "GOOD": 1.0,
    "SUSPECT": 0.5,
    "OUT_OF_RANGE": 0.0,
    "MISSING": -1.0,
}
