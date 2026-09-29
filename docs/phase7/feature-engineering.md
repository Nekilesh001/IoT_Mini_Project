# Phase 7: Feature Engineering & Signal Whitelisting

## 1. Feature Extraction Principles

Feature engineering transforms raw temporal physical measurements into structured numerical vectors while enforcing three fundamental physical constraints:

1. **Strict Signal Whitelisting**: Only physical measurements defined in the machine's specification are extracted. Non-existent signals are never synthesized or zero-padded.
2. **Backward-Looking Only**: Rolling statistics and differences are computed using strictly past and current observations ($t \le T$). No forward-looking windows ($t > T$).
3. **Machine Heterogeneity**: Common operational variables (state, load, quality) are standardized across all machines, while machine-specific signals are appropriately prefixed and aggregated.

---

## 2. Observable Signal Whitelist by Machine Type

| Machine Type | Primary Observable Physical Signals |
| :--- | :--- |
| **CNC Machine** | `spindle_speed_rpm`, `spindle_temperature_c`, `vibration_x_g`, `vibration_y_g`, `vibration_z_g`, `feed_rate_mmpm`, `coolant_flow_lpm`, `coolant_temp_c`, `coolant_level_pct`, `motor_current_a`, `axis_load_pct` |
| **Robotic Arm** | `joint_1_position_deg` .. `joint_6_position_deg`, `joint_1_torque_nm` .. `joint_6_torque_nm`, `tcp_speed_mms`, `motor_temp_c`, `payload_weight_kg`, `vibration_rms_g`, `controller_temp_c` |
| **Hydraulic Press** | `hydraulic_pressure_bar`, `ram_position_mm`, `ram_speed_mms`, `oil_temperature_c`, `oil_level_pct`, `cycle_count`, `motor_current_a`, `pressing_force_kn` |
| **Industrial Kiln** | `zone_1_temp_c`, `zone_2_temp_c`, `zone_3_temp_c`, `internal_pressure_mbar`, `gas_flow_rate_m3h`, `exhaust_temp_c`, `oxygen_pct`, `fan_speed_rpm` |
| **AGV** | `battery_soc_pct`, `battery_temp_c`, `battery_voltage_v`, `battery_current_a`, `wheel_speed_rpm`, `payload_weight_kg`, `motor_temp_c`, `vibration_rms_g` |
| **Packager** | `belt_speed_mpm`, `seal_bar_temp_c`, `cutting_blade_cycles`, `film_tension_n`, `motor_current_a`, `vibration_rms_g` |
| **Pump** | `discharge_pressure_bar`, `suction_pressure_bar`, `flow_rate_m3h`, `motor_current_a`, `motor_temp_c`, `vibration_overall_mms`, `bearing_temp_c` |
| **Compressor** | `discharge_pressure_bar`, `interstage_pressure_bar`, `discharge_temp_c`, `motor_current_a`, `motor_temp_c`, `vibration_overall_mms`, `oil_pressure_bar`, `ambient_temp_c` |

---

## 3. Temporal Transformations & Windows

For each observable signal $S$, the following temporal features are extracted across configurable rolling windows $W \in \{5, 15, 30\}$ (representing 5, 15, and 30 measurement periods):

1. **Raw Observable Value**: $S_t$
2. **Rolling Mean**: $\bar{S}_{W, t} = \frac{1}{|W|} \sum_{i \in W} S_{t-i}$
3. **Rolling Standard Deviation**: $\sigma_{W, t} = \sqrt{\frac{1}{|W|} \sum_{i \in W} (S_{t-i} - \bar{S}_{W, t})^2}$
4. **Rolling Minimum**: $\min_{i \in W} S_{t-i}$
5. **Rolling Maximum**: $\max_{i \in W} S_{t-i}$
6. **Rate of Change (First Difference)**: $\Delta S_t = S_t - S_{t-1}$
7. **Baseline Deviation**: $D_{W, t} = S_t - \bar{S}_{W, t}$
8. **Categorical Operational State**: Encoded numerically (IDLE=0, RUNNING=1, DEGRADED=2, FAULT=3, MAINTENANCE=4).
9. **Signal Quality Indicator**: Encoded numerically (GOOD=1.0, DEGRADED=0.5, UNRELIABLE=0.0).

---

## 4. Feature Manifest

The extraction pipeline automatically compiles a detailed `FeatureManifest` recording every column name, source signal, machine type applicability, unit, transformation type, window size, and leakage status verification.
