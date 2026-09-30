"""
Alert rule domain models, evaluation logic, and configuration catalog.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

from edge.models import CanonicalTelemetry, QualityCode



class RuleType(str, Enum):
    THRESHOLD = "THRESHOLD"
    RATE_OF_CHANGE = "RATE_OF_CHANGE"
    MISSING_SIGNAL = "MISSING_SIGNAL"
    STALE_SIGNAL = "STALE_SIGNAL"
    STATE = "STATE"
    COMPOSITE = "COMPOSITE"


class AlertSeverity(str, Enum):
    INFO = "INFO"
    WARNING = "WARNING"
    CRITICAL = "CRITICAL"


class AlertStatus(str, Enum):
    OPEN = "OPEN"
    ACKNOWLEDGED = "ACKNOWLEDGED"
    RESOLVED = "RESOLVED"


@dataclass
class AlertRule:
    """
    Explicit, configurable alert rule definition.
    Evaluated against validated CanonicalTelemetry.
    """
    rule_id: str
    machine_type: Optional[str] = None  # None matches any machine
    machine_id: Optional[str] = None    # None matches any machine of machine_type
    rule_type: RuleType = RuleType.THRESHOLD
    signal_name: Optional[str] = None
    signal: Optional[str] = None        # Alias for signal_name
    operator: str = ">"                 # '>', '<', '>=', '<=', '==', '!=', 'BETWEEN'
    threshold: Optional[float] = None
    clear_threshold: Optional[float] = None  # Hysteresis recovery threshold
    rate_threshold: Optional[float] = None    # Change rate per second
    state_condition: Optional[str] = None     # For STATE rules
    composite_conditions: Optional[List[Dict[str, Any]]] = None # For COMPOSITE rules
    conditions: Optional[List[Dict[str, Any]]] = None           # Alias for composite_conditions
    severity: AlertSeverity = AlertSeverity.WARNING
    alert_code: str = "ALT-001"
    title: str = "Alert Triggered"
    description: str = "An operational threshold was violated."
    cooldown_seconds: float = 30.0
    enabled: bool = True

    def __post_init__(self):
        if self.signal and not self.signal_name:
            self.signal_name = self.signal
        elif self.signal_name and not self.signal:
            self.signal = self.signal_name

        if self.conditions and not self.composite_conditions:
            self.composite_conditions = self.conditions
        elif self.composite_conditions and not self.conditions:
            self.conditions = self.composite_conditions

        if self.rule_type == RuleType.RATE_OF_CHANGE and self.threshold is not None and self.rate_threshold is None:
            self.rate_threshold = self.threshold

    def matches_machine(self, machine_id: str, machine_type: str) -> bool:
        if self.machine_id and self.machine_id != machine_id:
            return False
        if self.machine_type and self.machine_type != machine_type:
            return False
        return True



def get_default_rules() -> List[AlertRule]:
    """Default representative rules catalog for the 12 factory machines."""
    return [
        # --- PUMP RULES (PMP-001) ---
        AlertRule(
            rule_id="PUMP_VIBRATION_CRITICAL",
            machine_type="INDUSTRIAL_PUMP",
            machine_id="PMP-001",
            rule_type=RuleType.THRESHOLD,
            signal_name="vibration_x_mm_s",
            operator=">",
            threshold=4.5,
            clear_threshold=3.0,  # Hysteresis
            severity=AlertSeverity.CRITICAL,
            alert_code="ALT-PMP-01",
            title="Pump Critical Vibration Exceeded",
            description="Bearing vibration exceeded safety limits (4.5 mm/s), indicating mechanical degradation.",
            cooldown_seconds=10.0,
        ),
        AlertRule(
            rule_id="PUMP_BEARING_TEMP_HIGH",
            machine_type="INDUSTRIAL_PUMP",
            machine_id="PMP-001",
            rule_type=RuleType.THRESHOLD,
            signal_name="bearing_temperature_c",
            operator=">",
            threshold=80.0,
            clear_threshold=70.0,
            severity=AlertSeverity.WARNING,
            alert_code="ALT-PMP-02",
            title="Pump Bearing Temperature High",
            description="Bearing temperature elevated above 80.0 °C.",
            cooldown_seconds=15.0,
        ),
        # --- CONVEYOR RULES (CON-001) ---
        AlertRule(
            rule_id="CONVEYOR_BELT_JAM_CRITICAL",
            machine_type="INDUSTRIAL_CONVEYOR",
            machine_id="CON-001",
            rule_type=RuleType.THRESHOLD,
            signal_name="drive_motor_current_a",
            operator=">",
            threshold=24.0,
            clear_threshold=16.0,
            severity=AlertSeverity.CRITICAL,
            alert_code="ALT-CON-01",
            title="Conveyor Motor Overcurrent / Jam",
            description="Drive motor current surged above 24.0 A, indicating belt obstruction or motor stall.",
            cooldown_seconds=10.0,
        ),

        # --- CNC RULES (CNC-001) ---
        AlertRule(
            rule_id="CNC_SPINDLE_TEMP_WARNING",
            machine_type="CNC_MACHINING_CENTER",
            machine_id="CNC-001",
            rule_type=RuleType.THRESHOLD,
            signal_name="spindle_temperature_c",
            operator=">",
            threshold=65.0,
            clear_threshold=55.0,
            severity=AlertSeverity.WARNING,
            alert_code="ALT-CNC-01",
            title="CNC Spindle Overtemperature Warning",
            description="Spindle bearing temperature exceeded 65.0 °C.",
            cooldown_seconds=20.0,
        ),
        AlertRule(
            rule_id="CNC_SPINDLE_TEMP_CRITICAL",
            machine_type="CNC_MACHINING_CENTER",
            machine_id="CNC-001",
            rule_type=RuleType.THRESHOLD,
            signal_name="spindle_temperature_c",
            operator=">",
            threshold=80.0,
            clear_threshold=70.0,
            severity=AlertSeverity.CRITICAL,
            alert_code="ALT-CNC-02",
            title="CNC Spindle Thermal Overload",
            description="Spindle bearing temperature reached critical threshold (80.0 °C).",
            cooldown_seconds=15.0,
        ),
        # --- CHILLER RULES (CHL-001) ---
        AlertRule(
            rule_id="CHILLER_FLOW_LOW",
            machine_type="INDUSTRIAL_CHILLER",
            machine_id="CHL-001",
            rule_type=RuleType.THRESHOLD,
            signal_name="coolant_flow_rate_l_min",
            operator="<",
            threshold=60.0,
            clear_threshold=75.0,
            severity=AlertSeverity.WARNING,
            alert_code="ALT-CHL-01",
            title="Chiller Flow Restriction",
            description="Coolant flow dropped below 60.0 L/min.",
            cooldown_seconds=20.0,
        ),
        AlertRule(
            rule_id="CHILLER_SUPPLY_TEMP_HIGH",
            machine_type="INDUSTRIAL_CHILLER",
            machine_id="CHL-001",
            rule_type=RuleType.THRESHOLD,
            signal_name="supply_temperature_c",
            operator=">",
            threshold=18.0,
            clear_threshold=12.0,
            severity=AlertSeverity.WARNING,
            alert_code="ALT-CHL-02",
            title="Chiller Supply Temperature High",
            description="Supply coolant temperature elevated above 18.0 °C.",
            cooldown_seconds=20.0,
        ),
        # --- AGV RULES (AGV-001) ---
        AlertRule(
            rule_id="AGV_BATTERY_LOW",
            machine_type="AUTONOMOUS_MOBILE_ROBOT",
            machine_id="AGV-001",
            rule_type=RuleType.THRESHOLD,
            signal_name="battery_soc_pct",
            operator="<",
            threshold=20.0,
            clear_threshold=30.0,
            severity=AlertSeverity.WARNING,
            alert_code="ALT-AGV-01",
            title="AGV Battery Depleted",
            description="Battery state-of-charge dropped below 20.0%. Navigation to charging station required.",
            cooldown_seconds=30.0,
        ),
        # --- COMPRESSOR RULES (CMP-001) ---
        AlertRule(
            rule_id="COMPRESSOR_TEMP_HIGH",
            machine_type="AIR_COMPRESSOR",
            machine_id="CMP-001",
            rule_type=RuleType.THRESHOLD,
            signal_name="element_temperature_c",
            operator=">",
            threshold=110.0,
            clear_threshold=100.0,
            severity=AlertSeverity.CRITICAL,
            alert_code="ALT-CMP-01",
            title="Air Compressor Element Overheat",
            description="Discharge element temperature exceeded 110.0 °C.",
            cooldown_seconds=20.0,
        ),
        # --- ROBOT RULES (ROB-001) ---
        AlertRule(
            rule_id="ROBOT_JOINT_OVERLOAD",
            machine_type="INDUSTRIAL_ROBOT_6AXIS",
            machine_id="ROB-001",
            rule_type=RuleType.THRESHOLD,
            signal_name="joint_1_torque_nm",
            operator=">",
            threshold=180.0,
            clear_threshold=150.0,
            severity=AlertSeverity.WARNING,
            alert_code="ALT-ROB-01",
            title="Robot Joint 1 Over-Torque",
            description="Joint torque exceeded 180.0 Nm.",
            cooldown_seconds=15.0,
        ),
        # --- RATE OF CHANGE RULE ---
        AlertRule(
            rule_id="CNC_TEMP_RAPID_RISE",
            machine_type="CNC_MACHINING_CENTER",
            machine_id="CNC-001",
            rule_type=RuleType.RATE_OF_CHANGE,
            signal_name="spindle_temperature_c",
            rate_threshold=15.0,  # > 15.0 deg/sec
            severity=AlertSeverity.WARNING,
            alert_code="ALT-CNC-ROC",
            title="Rapid Thermal Escalation",
            description="Spindle temperature rising faster than 15.0 °C/sec.",
            cooldown_seconds=30.0,
        ),
        # --- STALE / SENSOR QUALITY RULE ---
        AlertRule(
            rule_id="SENSOR_QUALITY_STALE",
            rule_type=RuleType.STALE_SIGNAL,
            severity=AlertSeverity.WARNING,
            alert_code="ALT-Q-STALE",
            title="Stale Sensor Telemetry Detected",
            description="Telemetry quality flagged as STALE or BAD.",
            cooldown_seconds=30.0,
            enabled=False,  # Disabled by default so normal transient ticks do not spuriously trigger
        ),
        # --- MACHINE STATE RULE ---
        AlertRule(
            rule_id="MACHINE_FAULT_STATE",
            rule_type=RuleType.STATE,
            state_condition="FAULT",
            severity=AlertSeverity.CRITICAL,
            alert_code="ALT-SYS-FAULT",
            title="Machine Transitioned to FAULT State",
            description="Equipment entered an emergency or unrecoverable FAULT operating state.",
            cooldown_seconds=15.0,
        ),
        # --- COMPOSITE RULE ---
        AlertRule(
            rule_id="CHILLER_THERMAL_OVERLOAD_COMPOSITE",
            machine_type="INDUSTRIAL_CHILLER",
            machine_id="CHL-001",
            rule_type=RuleType.COMPOSITE,
            composite_conditions=[
                {"signal": "supply_temperature_c", "op": ">", "val": 18.0},
                {"signal": "coolant_flow_rate_l_min", "op": "<", "val": 60.0},
            ],
            severity=AlertSeverity.CRITICAL,
            alert_code="ALT-CHL-COMP",
            title="Chiller Dual Thermal & Flow Degradation",
            description="Combined high supply temperature (>18°C) and low coolant flow (<60 L/min).",
            cooldown_seconds=20.0,
        ),
        # --- EXTERNAL IOT ENVIRONMENTAL SENSOR RULES (IOT-SENSOR-001) ---
        AlertRule(
            rule_id="ENV_TEMP_HIGH_WARNING",
            machine_type="ENVIRONMENT_SENSOR",
            machine_id="IOT-SENSOR-001",
            rule_type=RuleType.THRESHOLD,
            signal_name="temperature_c",
            operator=">=",
            threshold=30.0,
            clear_threshold=28.0,  # Hysteresis
            severity=AlertSeverity.WARNING,
            alert_code="ALT-ENV-01",
            title="Environmental High Temperature Warning",
            description="Ambient temperature reached or exceeded warning threshold (>= 30.0 °C).",
            cooldown_seconds=15.0,
        ),
        AlertRule(
            rule_id="ENV_TEMP_HIGH_CRITICAL",
            machine_type="ENVIRONMENT_SENSOR",
            machine_id="IOT-SENSOR-001",
            rule_type=RuleType.THRESHOLD,
            signal_name="temperature_c",
            operator=">=",
            threshold=35.0,
            clear_threshold=33.0,
            severity=AlertSeverity.CRITICAL,
            alert_code="ALT-ENV-02",
            title="Environmental Critical Temperature Exceeded",
            description="Ambient temperature exceeded critical threshold (>= 35.0 °C).",
            cooldown_seconds=15.0,
        ),
        AlertRule(
            rule_id="ENV_HUMIDITY_HIGH_WARNING",
            machine_type="ENVIRONMENT_SENSOR",
            machine_id="IOT-SENSOR-001",
            rule_type=RuleType.THRESHOLD,
            signal_name="humidity_pct",
            operator=">=",
            threshold=85.0,
            clear_threshold=80.0,
            severity=AlertSeverity.WARNING,
            alert_code="ALT-ENV-03",
            title="Environmental High Humidity Warning",
            description="Relative humidity exceeded high warning threshold (>= 85.0 %).",
            cooldown_seconds=15.0,
        ),

    ]


@dataclass
class RuleEvaluationResult:
    rule: AlertRule
    triggered: bool
    observed_value: Any
    is_cleared: bool = False


class RuleEvaluator:
    """
    Evaluates CanonicalTelemetry against a rule set.
    Supports THRESHOLD, RATE_OF_CHANGE, MISSING_SIGNAL, STALE_SIGNAL, STATE, and COMPOSITE rules.
    """

    def __init__(self, rules: Optional[List[AlertRule]] = None):
        self._rules = rules if rules is not None else get_default_rules()
        # Track previous readings per machine for rate-of-change: (timestamp_float, value)
        self._history: Dict[str, Dict[str, Tuple[float, float]]] = {}

    def evaluate(self, telemetry: CanonicalTelemetry) -> List[RuleEvaluationResult]:
        """Convenience method returning list of RuleEvaluationResult for triggered rules."""
        results = []
        for rule in self._rules:
            is_trig, is_clr, meas = self.evaluate_rule(rule, telemetry)
            if is_trig:
                if "rate_per_sec" in meas:
                    val = meas.get("rate_per_sec")
                elif rule.signal_name and rule.signal_name in meas:
                    val = meas.get(rule.signal_name)
                else:
                    val = meas
                results.append(RuleEvaluationResult(rule=rule, triggered=True, observed_value=val, is_cleared=is_clr))
        return results

    def evaluate_rule(
        self, rule: AlertRule, telemetry: CanonicalTelemetry
    ) -> Tuple[bool, bool, Dict[str, Any]]:
        """
        Evaluates a single rule.
        Returns: (is_triggered, is_cleared, triggering_measurements)
        """
        if not rule.enabled:
            return False, False, {}

        # 1. Check machine compatibility
        machine_type = str(telemetry.machine_type)
        if not rule.matches_machine(telemetry.machine_id, machine_type):
            return False, False, {}

        # 2. STATE rule
        if rule.rule_type == RuleType.STATE:
            curr_state = telemetry.state.operating if hasattr(telemetry.state, 'operating') else str(telemetry.state)
            is_trig = curr_state == rule.state_condition
            is_clr = not is_trig
            return is_trig, is_clr, {"state": curr_state}

        # 3. STALE / MISSING rule
        if rule.rule_type in (RuleType.STALE_SIGNAL, RuleType.MISSING_SIGNAL):
            qual = telemetry.quality.value if hasattr(telemetry.quality, 'value') else str(telemetry.quality)
            if rule.rule_type == RuleType.MISSING_SIGNAL:
                val = telemetry.measurements.get(rule.signal_name) if rule.signal_name else None
                is_trig = val is None or qual in ("MISSING", "BAD")
                is_clr = not is_trig
                return is_trig, is_clr, {"quality": qual, "signal": rule.signal_name}
            else:
                is_trig = qual in ("STALE", "MISSING", "BAD", "OUT_OF_RANGE")
                is_clr = qual == "GOOD"
                return is_trig, is_clr, {"quality": qual}

        # 4. COMPOSITE rule
        if rule.rule_type == RuleType.COMPOSITE and rule.composite_conditions:
            all_met = True
            meas_dict = {}
            for cond in rule.composite_conditions:
                sig = cond["signal"]
                op = cond.get("op", cond.get("operator", ">"))
                val = cond.get("val", cond.get("threshold", 0.0))
                actual = telemetry.measurements.get(sig)
                if actual is None:
                    all_met = False
                    break
                meas_dict[sig] = actual
                if op == ">" and not (actual > val):
                    all_met = False
                elif op == "<" and not (actual < val):
                    all_met = False
                elif op == ">=" and not (actual >= val):
                    all_met = False
                elif op == "<=" and not (actual <= val):
                    all_met = False
                elif op == "==" and not (actual == val):
                    all_met = False
            return all_met, not all_met, meas_dict

        # 5. RATE_OF_CHANGE rule
        if rule.rule_type == RuleType.RATE_OF_CHANGE and rule.signal_name and rule.rate_threshold:
            val = telemetry.measurements.get(rule.signal_name)
            if val is None:
                return False, False, {}

            try:
                if hasattr(telemetry, 'timestamp') and isinstance(telemetry.timestamp, datetime):
                    now_ts = telemetry.timestamp.timestamp()
                elif hasattr(telemetry, 'event_time') and telemetry.event_time:
                    now_ts = datetime.fromisoformat(str(telemetry.event_time).replace("Z", "+00:00")).timestamp()
                else:
                    now_ts = datetime.now(timezone.utc).timestamp()
            except Exception:
                now_ts = datetime.now(timezone.utc).timestamp()

            machine_hist = self._history.setdefault(telemetry.machine_id, {})
            prev = machine_hist.get(rule.signal_name)
            machine_hist[rule.signal_name] = (now_ts, float(val))

            if prev:
                prev_ts, prev_val = prev
                dt = now_ts - prev_ts
                if dt > 0.001:
                    rate = abs(float(val) - prev_val) / dt
                    is_trig = rate >= rule.rate_threshold
                    return is_trig, not is_trig, {rule.signal_name: val, "rate_per_sec": round(rate, 2)}
            return False, False, {}

        # 6. THRESHOLD rule
        if rule.rule_type == RuleType.THRESHOLD and rule.signal_name:
            val = telemetry.measurements.get(rule.signal_name)
            if val is None:
                return False, False, {}

            num_val = float(val)
            thresh = rule.threshold
            clear_thresh = rule.clear_threshold if rule.clear_threshold is not None else thresh

            is_trig = False
            is_clr = False

            if rule.operator == ">":
                is_trig = num_val > thresh
                is_clr = num_val < clear_thresh
            elif rule.operator == ">=":
                is_trig = num_val >= thresh
                is_clr = num_val < clear_thresh
            elif rule.operator == "<":
                is_trig = num_val < thresh
                is_clr = num_val > clear_thresh
            elif rule.operator == "<=":
                is_trig = num_val <= thresh
                is_clr = num_val > clear_thresh
            elif rule.operator == "==":
                is_trig = num_val == thresh
                is_clr = num_val != thresh
            elif rule.operator == "!=":
                is_trig = num_val != thresh
                is_clr = num_val == thresh

            return is_trig, is_clr, {rule.signal_name: val}

        return False, False, {}

    def evaluate_telemetry(self, telemetry: CanonicalTelemetry) -> List[Tuple[AlertRule, bool, bool, Dict[str, Any]]]:
        """Evaluates all rules against the incoming telemetry packet."""
        results = []
        for rule in self._rules:
            is_trig, is_clr, meas = self.evaluate_rule(rule, telemetry)
            if is_trig or is_clr:
                results.append((rule, is_trig, is_clr, meas))
        return results


create_default_rules = get_default_rules

