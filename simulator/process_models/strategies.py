"""
Machine-specific telemetry behavior strategies for all 12 heterogeneous factory machines.
"""

import math
import random
from typing import Any, Dict
from simulator.core.domain import MachineProfile, OperatingState
from simulator.degradation.degradation_model import DegradationModel
from simulator.process_models.base import MachineBehaviorStrategy


class CNCMachiningCenterBehavior(MachineBehaviorStrategy):
    def calculate_telemetry(
        self, profile: MachineProfile, operating_state: OperatingState, load_pct: float,
        degradation: DegradationModel, time_elapsed_seconds: float, rng: random.Random
    ) -> Dict[str, Any]:
        deg_lvl = degradation.degradation_level
        is_running = operating_state in (OperatingState.RUNNING, OperatingState.WARNING)

        base_speed = 12000.0 * (load_pct / 100.0) if is_running else 0.0
        spindle_speed = max(0.0, base_speed + rng.uniform(-50.0, 50.0)) if is_running else 0.0

        spindle_load = max(0.0, load_pct + (deg_lvl * 0.2) + rng.uniform(-1.5, 1.5)) if is_running else 0.0

        ambient = 25.0
        heat_rise = (spindle_load * 0.3) + (deg_lvl * 0.4)
        if degradation.get_condition_severity("overheating") > 0:
            heat_rise += degradation.get_condition_severity("overheating") * 0.5
        spindle_temp = ambient + heat_rise + rng.uniform(-0.5, 0.5) if is_running else ambient

        vib_base = 1.0 + (deg_lvl * 0.15)
        if degradation.get_condition_severity("bearing_wear") > 0:
            vib_base += (degradation.get_condition_severity("bearing_wear") * 0.1)
        vibration = max(0.1, vib_base + rng.uniform(-0.1, 0.1)) if is_running else 0.05

        feed_rate = 1500.0 * (load_pct / 100.0) if is_running else 0.0
        coolant_p = 20.0 - (deg_lvl * 0.05) + rng.uniform(-0.3, 0.3) if is_running else 0.0
        tool_wear = min(100.0, 10.0 + (time_elapsed_seconds * 0.01) + (deg_lvl * 0.5))

        x_pos = math.sin(time_elapsed_seconds * 0.1) * 200.0 if is_running else 0.0
        y_pos = math.cos(time_elapsed_seconds * 0.1) * 150.0 if is_running else 0.0
        z_pos = -25.0 if is_running else 0.0

        cycle_st = "CUTTING" if is_running else ("OFF" if operating_state == OperatingState.OFF else "IDLE")
        parts = int(time_elapsed_seconds // 30.0)

        return {
            "spindle_speed_rpm": round(spindle_speed, 2),
            "spindle_load_pct": round(spindle_load, 2),
            "spindle_temperature_c": round(spindle_temp, 2),
            "vibration_rms_mm_s": round(vibration, 3),
            "feed_rate_mm_min": round(feed_rate, 2),
            "coolant_pressure_bar": round(coolant_p, 2),
            "tool_wear_pct": round(tool_wear, 2),
            "axis_x_position_mm": round(x_pos, 2),
            "axis_y_position_mm": round(y_pos, 2),
            "axis_z_position_mm": round(z_pos, 2),
            "cycle_state": cycle_st,
            "parts_produced_count": parts
        }


class CNCLatheBehavior(MachineBehaviorStrategy):
    def calculate_telemetry(
        self, profile: MachineProfile, operating_state: OperatingState, load_pct: float,
        degradation: DegradationModel, time_elapsed_seconds: float, rng: random.Random
    ) -> Dict[str, Any]:
        deg_lvl = degradation.degradation_level
        is_running = operating_state in (OperatingState.RUNNING, OperatingState.WARNING)

        speed = 3500.0 * (load_pct / 100.0) + rng.uniform(-20.0, 20.0) if is_running else 0.0
        load = max(0.0, load_pct + (deg_lvl * 0.15) + rng.uniform(-1.0, 1.0)) if is_running else 0.0
        spindle_temp = 22.0 + (load * 0.25) + (deg_lvl * 0.3) + rng.uniform(-0.4, 0.4) if is_running else 22.0
        vibration = 0.8 + (deg_lvl * 0.12) + rng.uniform(-0.08, 0.08) if is_running else 0.04
        feed_rate = 500.0 * (load_pct / 100.0) if is_running else 0.0
        chuck_p = 35.0 + rng.uniform(-0.5, 0.5) if operating_state != OperatingState.OFF else 0.0
        cutting_temp = 180.0 + (load * 2.0) + (deg_lvl * 1.5) if is_running else 22.0
        tool_wear = min(100.0, 15.0 + (time_elapsed_seconds * 0.015))
        cycle_t = 45.0
        parts = int(time_elapsed_seconds // 45.0)

        return {
            "spindle_speed_rpm": round(speed, 2),
            "spindle_load_pct": round(load, 2),
            "spindle_temperature_c": round(spindle_temp, 2),
            "vibration_rms_mm_s": round(vibration, 3),
            "feed_rate_mm_min": round(feed_rate, 2),
            "chuck_pressure_bar": round(chuck_p, 2),
            "cutting_temperature_c": round(cutting_temp, 2),
            "tool_wear_pct": round(tool_wear, 2),
            "cycle_time_s": round(cycle_t, 2),
            "parts_produced_count": parts
        }


class Robot6AxisBehavior(MachineBehaviorStrategy):
    def calculate_telemetry(
        self, profile: MachineProfile, operating_state: OperatingState, load_pct: float,
        degradation: DegradationModel, time_elapsed_seconds: float, rng: random.Random
    ) -> Dict[str, Any]:
        deg_lvl = degradation.degradation_level
        is_running = operating_state in (OperatingState.RUNNING, OperatingState.WARNING)

        j_temps = []
        j_torques = []
        base_torques = [120.0, 200.0, 90.0, 45.0, 30.0, 15.0]
        base_temps = [38.0, 40.0, 37.0, 35.0, 34.0, 32.0]

        for i in range(6):
            t_rise = (load_pct * 0.15) + (deg_lvl * 0.25)
            j_temps.append(round((base_temps[i] + t_rise + rng.uniform(-0.5, 0.5)) if is_running else 25.0, 2))
            trq = (base_torques[i] * (load_pct / 100.0) * (1.0 + deg_lvl * 0.005)) + rng.uniform(-2.0, 2.0)
            j_torques.append(round(trq if is_running else 0.0, 2))

        pos_err = 0.05 + (deg_lvl * 0.02) + rng.uniform(-0.01, 0.01) if is_running else 0.005
        ctrl_temp = 35.0 + (load_pct * 0.1) + rng.uniform(-0.3, 0.3) if operating_state != OperatingState.OFF else 22.0
        cycle_st = "MOVING" if is_running else ("OFF" if operating_state == OperatingState.OFF else "IDLE")
        op_hours = 1200.0 + (time_elapsed_seconds / 3600.0)
        alarm = 101 if degradation.get_condition_severity("joint_fault") > 0 else 0

        return {
            "joint_1_temp_c": j_temps[0], "joint_2_temp_c": j_temps[1], "joint_3_temp_c": j_temps[2],
            "joint_4_temp_c": j_temps[3], "joint_5_temp_c": j_temps[4], "joint_6_temp_c": j_temps[6 if False else 5],
            "joint_1_torque_nm": j_torques[0], "joint_2_torque_nm": j_torques[1], "joint_3_torque_nm": j_torques[2],
            "joint_4_torque_nm": j_torques[3], "joint_5_torque_nm": j_torques[4], "joint_6_torque_nm": j_torques[5],
            "position_error_norm_mm": round(pos_err, 4),
            "controller_temperature_c": round(ctrl_temp, 2),
            "cycle_state": cycle_st,
            "operating_hours": round(op_hours, 2),
            "alarm_code": alarm
        }


class WeldingRobotBehavior(MachineBehaviorStrategy):
    def calculate_telemetry(
        self, profile: MachineProfile, operating_state: OperatingState, load_pct: float,
        degradation: DegradationModel, time_elapsed_seconds: float, rng: random.Random
    ) -> Dict[str, Any]:
        deg_lvl = degradation.degradation_level
        is_running = operating_state in (OperatingState.RUNNING, OperatingState.WARNING)

        j1_temp = 39.0 + (load_pct * 0.12) + (deg_lvl * 0.2) if is_running else 22.0
        j2_temp = 41.0 + (load_pct * 0.12) + (deg_lvl * 0.2) if is_running else 22.0
        pos_err = 0.03 + (deg_lvl * 0.015) + rng.uniform(-0.005, 0.005) if is_running else 0.002

        weld_curr = 180.0 + (load_pct * 0.5) + rng.uniform(-3.0, 3.0) if is_running else 0.0
        weld_volt = 24.5 + rng.uniform(-0.4, 0.4) if is_running else 0.0
        weld_dur = 4.2
        gas_flow = 15.0 + rng.uniform(-0.5, 0.5) if is_running else 0.0
        weld_cycles = int(time_elapsed_seconds // 6.0)
        ctrl_temp = 36.0 + (load_pct * 0.08) if operating_state != OperatingState.OFF else 22.0

        return {
            "joint_1_temp_c": round(j1_temp, 2),
            "joint_2_temp_c": round(j2_temp, 2),
            "position_error_norm_mm": round(pos_err, 4),
            "weld_current_a": round(weld_curr, 2),
            "weld_voltage_v": round(weld_volt, 2),
            "weld_duration_s": round(weld_dur, 2),
            "shield_gas_flow_l_min": round(gas_flow, 2),
            "weld_cycles_completed": weld_cycles,
            "controller_temperature_c": round(ctrl_temp, 2)
        }


class ConveyorBehavior(MachineBehaviorStrategy):
    def calculate_telemetry(
        self, profile: MachineProfile, operating_state: OperatingState, load_pct: float,
        degradation: DegradationModel, time_elapsed_seconds: float, rng: random.Random
    ) -> Dict[str, Any]:
        deg_lvl = degradation.degradation_level
        is_jammed = degradation.get_condition_severity("jammed") > 0
        is_running = operating_state in (OperatingState.RUNNING, OperatingState.WARNING) and not is_jammed

        speed = 1.2 * (load_pct / 100.0) if is_running else 0.0
        load_kg = 250.0 * (load_pct / 55.0) if is_running else 0.0
        motor_curr = (14.5 * (load_pct / 55.0) + (deg_lvl * 0.15)) if is_running else (35.0 if is_jammed else 0.0)
        motor_temp = 48.0 + (load_pct * 0.2) + (deg_lvl * 0.3) if operating_state != OperatingState.OFF else 22.0
        vib = 0.4 + (deg_lvl * 0.08) + rng.uniform(-0.04, 0.04) if is_running else 0.02
        tension = 2500.0 + (load_kg * 1.5) + rng.uniform(-20.0, 20.0) if operating_state != OperatingState.OFF else 0.0
        throughput = 30.0 * (speed / 1.2) if is_running else 0.0
        cycles = 120 + int(time_elapsed_seconds // 300.0)

        return {
            "belt_speed_m_s": round(speed, 2),
            "drive_motor_current_a": round(motor_curr, 2),
            "drive_motor_temp_c": round(motor_temp, 2),
            "vibration_amplitude_mm": round(vib, 3),
            "belt_tension_n": round(tension, 2),
            "load_kg": round(load_kg, 2),
            "throughput_units_min": round(throughput, 2),
            "jam_state": is_jammed,
            "start_stop_cycles": cycles
        }


class PressBehavior(MachineBehaviorStrategy):
    def calculate_telemetry(
        self, profile: MachineProfile, operating_state: OperatingState, load_pct: float,
        degradation: DegradationModel, time_elapsed_seconds: float, rng: random.Random
    ) -> Dict[str, Any]:
        deg_lvl = degradation.degradation_level
        is_running = operating_state in (OperatingState.RUNNING, OperatingState.WARNING)

        stroke_phase = (time_elapsed_seconds % 3.0) / 3.0
        ram_pos = math.sin(stroke_phase * math.pi) * 300.0 if is_running else 0.0
        ram_spd = math.cos(stroke_phase * math.pi) * 120.0 if is_running else 0.0

        press_f = (3500.0 * (load_pct / 70.0) if stroke_phase > 0.4 and stroke_phase < 0.6 else 0.0) if is_running else 0.0
        hyd_p = 220.0 + (press_f * 0.02) + rng.uniform(-3.0, 3.0) if is_running else 10.0
        oil_temp = 52.0 + (load_pct * 0.15) + (deg_lvl * 0.25) if operating_state != OperatingState.OFF else 22.0
        motor_l = load_pct + (deg_lvl * 0.1) if is_running else 0.0
        strokes = int(time_elapsed_seconds // 3.0)
        tool_u = min(100.0, 22.0 + (strokes * 0.001))
        alarm = degradation.get_condition_severity("pressure_fault") > 0

        return {
            "ram_position_mm": round(ram_pos, 2),
            "ram_speed_mm_s": round(ram_spd, 2),
            "press_force_kn": round(press_f, 2),
            "hydraulic_pressure_bar": round(hyd_p, 2),
            "oil_temperature_c": round(oil_temp, 2),
            "motor_load_pct": round(motor_l, 2),
            "stroke_count": strokes,
            "tool_usage_pct": round(tool_u, 2),
            "alarm_state": alarm
        }


class InjectionMoldingBehavior(MachineBehaviorStrategy):
    def calculate_telemetry(
        self, profile: MachineProfile, operating_state: OperatingState, load_pct: float,
        degradation: DegradationModel, time_elapsed_seconds: float, rng: random.Random
    ) -> Dict[str, Any]:
        deg_lvl = degradation.degradation_level
        is_running = operating_state in (OperatingState.RUNNING, OperatingState.WARNING)

        b_temps = [210.0, 220.0, 225.0, 230.0]
        actual_b_temps = [
            round((t + rng.uniform(-1.5, 1.5)) if operating_state != OperatingState.OFF else 22.0, 2)
            for t in b_temps
        ]
        mold_t = 60.0 + rng.uniform(-1.0, 1.0) if operating_state != OperatingState.OFF else 22.0
        inj_p = 1200.0 * (load_pct / 80.0) + rng.uniform(-15.0, 15.0) if is_running else 0.0
        hold_p = 700.0 * (load_pct / 80.0) + rng.uniform(-10.0, 10.0) if is_running else 0.0
        screw_pos = 45.0 + rng.uniform(-2.0, 2.0) if is_running else 0.0
        screw_spd = 120.0 if is_running else 0.0
        inj_t = 3.5
        cool_t = 15.0
        cycle_t = 24.0
        shots = int(time_elapsed_seconds // 24.0)
        alarm = degradation.get_condition_severity("heater_fault") > 0

        return {
            "barrel_temp_zone_1_c": actual_b_temps[0],
            "barrel_temp_zone_2_c": actual_b_temps[1],
            "barrel_temp_zone_3_c": actual_b_temps[2],
            "barrel_temp_zone_4_c": actual_b_temps[3],
            "mold_temperature_c": round(mold_t, 2),
            "injection_pressure_bar": round(inj_p, 2),
            "holding_pressure_bar": round(hold_p, 2),
            "screw_position_mm": round(screw_pos, 2),
            "screw_speed_rpm": round(screw_spd, 2),
            "injection_time_s": round(inj_t, 2),
            "cooling_time_s": round(cool_t, 2),
            "cycle_time_s": round(cycle_t, 2),
            "shot_count": shots,
            "alarm_state": alarm
        }


class CompressorBehavior(MachineBehaviorStrategy):
    def calculate_telemetry(
        self, profile: MachineProfile, operating_state: OperatingState, load_pct: float,
        degradation: DegradationModel, time_elapsed_seconds: float, rng: random.Random
    ) -> Dict[str, Any]:
        deg_lvl = degradation.degradation_level
        is_running = operating_state in (OperatingState.RUNNING, OperatingState.WARNING)

        dis_p = 7.5 + rng.uniform(-0.15, 0.15) if is_running else 1.0
        reg_p = 7.2 + rng.uniform(-0.1, 0.1) if is_running else 1.0

        elem_temp = 82.0 + (load_pct * 0.2) + (deg_lvl * 0.35)
        if degradation.get_condition_severity("filter_clog") > 0:
            elem_temp += degradation.get_condition_severity("filter_clog") * 0.4
        elem_temp = round(elem_temp if is_running else 24.0, 2)

        amb_temp = 24.0 + rng.uniform(-0.5, 0.5)
        motor_curr = 115.0 * (load_pct / 75.0) + (deg_lvl * 0.2) if is_running else 0.0
        motor_load = load_pct + (deg_lvl * 0.1) if is_running else 0.0
        run_hrs = 3400.0 + (time_elapsed_seconds / 3600.0)
        starts = 450
        energy = 152000.0 + (motor_curr * 0.4 * (time_elapsed_seconds / 3600.0))
        alarm = elem_temp > 105.0

        return {
            "discharge_pressure_bar": round(dis_p, 2),
            "regulating_pressure_bar": round(reg_p, 2),
            "element_temperature_c": elem_temp,
            "ambient_temperature_c": round(amb_temp, 2),
            "motor_current_a": round(motor_curr, 2),
            "motor_load_pct": round(motor_load, 2),
            "running_hours": round(run_hrs, 2),
            "starts_count": starts,
            "energy_kwh": round(energy, 2),
            "alarm_state": alarm
        }


class PumpBehavior(MachineBehaviorStrategy):
    def calculate_telemetry(
        self, profile: MachineProfile, operating_state: OperatingState, load_pct: float,
        degradation: DegradationModel, time_elapsed_seconds: float, rng: random.Random
    ) -> Dict[str, Any]:
        deg_lvl = degradation.degradation_level
        is_running = operating_state in (OperatingState.RUNNING, OperatingState.WARNING)

        suc_p = 2.1 + rng.uniform(-0.1, 0.1) if operating_state != OperatingState.OFF else 0.0
        dis_p = 8.5 * (load_pct / 65.0) + rng.uniform(-0.2, 0.2) if is_running else suc_p
        flow = 65.0 * (load_pct / 65.0) + rng.uniform(-1.0, 1.0) if is_running else 0.0
        spd = 2900.0 * (load_pct / 65.0) if is_running else 0.0
        curr = 32.0 * (load_pct / 65.0) + (deg_lvl * 0.1) if is_running else 0.0
        pwr = 18.5 * (load_pct / 65.0) if is_running else 0.0

        brg_temp = 55.0 + (load_pct * 0.15) + (deg_lvl * 0.4)
        if degradation.get_condition_severity("bearing_wear") > 0:
            brg_temp += degradation.get_condition_severity("bearing_wear") * 0.3
        brg_temp = round(brg_temp if is_running else 22.0, 2)

        vib_x = 1.1 + (deg_lvl * 0.15) + rng.uniform(-0.05, 0.05) if is_running else 0.02
        vib_y = 0.9 + (deg_lvl * 0.15) + rng.uniform(-0.05, 0.05) if is_running else 0.02
        alarm = brg_temp > 90.0 or vib_x > 8.0

        return {
            "suction_pressure_bar": round(suc_p, 2),
            "discharge_pressure_bar": round(dis_p, 2),
            "flow_rate_m3_h": round(flow, 2),
            "speed_rpm": round(spd, 2),
            "motor_current_a": round(curr, 2),
            "power_kw": round(pwr, 2),
            "bearing_temperature_c": brg_temp,
            "vibration_x_mm_s": round(vib_x, 3),
            "vibration_y_mm_s": round(vib_y, 3),
            "start_stop_count": 310,
            "alarm_state": alarm
        }


class VisionInspectionBehavior(MachineBehaviorStrategy):
    def calculate_telemetry(
        self, profile: MachineProfile, operating_state: OperatingState, load_pct: float,
        degradation: DegradationModel, time_elapsed_seconds: float, rng: random.Random
    ) -> Dict[str, Any]:
        deg_lvl = degradation.degradation_level
        is_running = operating_state in (OperatingState.RUNNING, OperatingState.WARNING)

        st_state = "INSPECTING" if is_running else ("OFF" if operating_state == OperatingState.OFF else "IDLE")
        cam_state = "ONLINE" if operating_state != OperatingState.OFF else "OFFLINE"
        cycle_t = 320.0 + rng.uniform(-15.0, 15.0) if is_running else 0.0

        imgs = int(time_elapsed_seconds * 3.0) if is_running else 0
        defects = int(imgs * (0.012 + deg_lvl * 0.001))
        goods = imgs - defects
        def_rate = (defects / imgs * 100.0) if imgs > 0 else 1.2

        conf = max(50.0, 98.5 - (deg_lvl * 0.2) + rng.uniform(-0.5, 0.5)) if is_running else 100.0
        light = 5000.0 + rng.uniform(-50.0, 50.0) if operating_state != OperatingState.OFF else 0.0
        cam_temp = 38.0 + (load_pct * 0.1) if operating_state != OperatingState.OFF else 22.0
        lat = 45.0 + rng.uniform(-5.0, 5.0) if is_running else 0.0
        alarm = def_rate > 5.0

        return {
            "station_state": st_state,
            "camera_state": cam_state,
            "inspection_cycle_time_ms": round(cycle_t, 2),
            "images_processed_count": imgs,
            "good_parts_count": goods,
            "defect_parts_count": defects,
            "defect_rate_pct": round(def_rate, 2),
            "confidence_score_pct": round(conf, 2),
            "lighting_level_lux": round(light, 2),
            "camera_temperature_c": round(cam_temp, 2),
            "processing_latency_ms": round(lat, 2),
            "alarm_state": alarm
        }


class AGVBehavior(MachineBehaviorStrategy):
    def calculate_telemetry(
        self, profile: MachineProfile, operating_state: OperatingState, load_pct: float,
        degradation: DegradationModel, time_elapsed_seconds: float, rng: random.Random
    ) -> Dict[str, Any]:
        deg_lvl = degradation.degradation_level
        is_running = operating_state in (OperatingState.RUNNING, OperatingState.WARNING)

        spd = 1.5 * (load_pct / 50.0) if is_running else 0.0
        head = (90.0 + time_elapsed_seconds * 2.0) % 360.0 if is_running else 90.0
        px = 12.5 + math.cos(math.radians(head)) * (time_elapsed_seconds * spd)
        py = 45.2 + math.sin(math.radians(head)) * (time_elapsed_seconds * spd)

        soc = max(0.0, 85.0 - (time_elapsed_seconds * 0.01))
        volt = 48.0 * (soc / 100.0) + rng.uniform(-0.2, 0.2)
        batt_temp = 32.0 + (spd * 3.0) + (deg_lvl * 0.1) if is_running else 22.0

        mtr_spd = 1200.0 * (spd / 1.5) if is_running else 0.0
        mtr_curr = 12.0 * (spd / 1.5) + (deg_lvl * 0.05) if is_running else 0.0
        dist = 4500.0 + (time_elapsed_seconds * spd)

        dock = "CHARGING" if soc < 20.0 else "UNDOCKED"
        obs = "CLEAR" if rng.random() > 0.05 else "WARN"
        safety = "NORMAL" if obs == "CLEAR" else "SLOWDOWN"

        return {
            "pos_x_m": round(px, 2),
            "pos_y_m": round(py, 2),
            "heading_deg": round(head, 2),
            "speed_m_s": round(spd, 2),
            "battery_soc_pct": round(soc, 2),
            "battery_voltage_v": round(volt, 2),
            "battery_temperature_c": round(batt_temp, 2),
            "motor_speed_rpm": round(mtr_spd, 2),
            "motor_current_a": round(mtr_curr, 2),
            "active_job_id": "JOB_102",
            "total_distance_m": round(dist, 2),
            "docking_state": dock,
            "obstacle_state": obs,
            "safety_state": safety
        }


class ChillerBehavior(MachineBehaviorStrategy):
    def calculate_telemetry(
        self, profile: MachineProfile, operating_state: OperatingState, load_pct: float,
        degradation: DegradationModel, time_elapsed_seconds: float, rng: random.Random
    ) -> Dict[str, Any]:
        deg_lvl = degradation.degradation_level
        is_running = operating_state in (OperatingState.RUNNING, OperatingState.WARNING)

        sup_t = 7.0 + (deg_lvl * 0.05) + rng.uniform(-0.3, 0.3) if is_running else 25.0
        ret_t = 12.0 + (load_pct * 0.08) + rng.uniform(-0.3, 0.3) if is_running else 25.0
        flow = 250.0 + rng.uniform(-5.0, 5.0) if is_running else 0.0

        comp_st = "RUNNING" if is_running else ("OFF" if operating_state == OperatingState.OFF else "IDLE")
        comp_curr = 85.0 * (load_pct / 75.0) + (deg_lvl * 0.2) if is_running else 0.0
        comp_load = load_pct + (deg_lvl * 0.1) if is_running else 0.0

        high_p = 18.2 + (load_pct * 0.05) + (deg_lvl * 0.08) if is_running else 5.0
        low_p = 4.1 + rng.uniform(-0.2, 0.2) if is_running else 5.0
        amb_t = 25.0 + rng.uniform(-0.5, 0.5)
        energy = 84000.0 + (comp_curr * 0.3 * (time_elapsed_seconds / 3600.0))
        run_hrs = 4800.0 + (time_elapsed_seconds / 3600.0)
        alarm = sup_t > 15.0 or high_p > 25.0

        return {
            "supply_temperature_c": round(sup_t, 2),
            "return_temperature_c": round(ret_t, 2),
            "flow_rate_l_min": round(flow, 2),
            "compressor_state": comp_st,
            "compressor_current_a": round(comp_curr, 2),
            "compressor_load_pct": round(comp_load, 2),
            "high_side_pressure_bar": round(high_p, 2),
            "low_side_pressure_bar": round(low_p, 2),
            "ambient_temperature_c": round(amb_t, 2),
            "energy_kwh": round(energy, 2),
            "running_hours": round(run_hrs, 2),
            "alarm_state": alarm
        }


# Strategy Registry
STRATEGY_REGISTRY = {
    "CNC_MACHINING_CENTER": CNCMachiningCenterBehavior(),
    "CNC_LATHE": CNCLatheBehavior(),
    "INDUSTRIAL_ROBOT_6AXIS": Robot6AxisBehavior(),
    "WELDING_ROBOT": WeldingRobotBehavior(),
    "INDUSTRIAL_CONVEYOR": ConveyorBehavior(),
    "INDUSTRIAL_PRESS": PressBehavior(),
    "INJECTION_MOLDING_MACHINE": InjectionMoldingBehavior(),
    "AIR_COMPRESSOR": CompressorBehavior(),
    "INDUSTRIAL_PUMP": PumpBehavior(),
    "VISION_INSPECTION_STATION": VisionInspectionBehavior(),
    "AUTONOMOUS_MOBILE_ROBOT": AGVBehavior(),
    "INDUSTRIAL_CHILLER": ChillerBehavior(),
}
