"""
Machine-aware telemetry schema and signal validation engine.
"""

from typing import Any, Dict, List, Optional, Tuple
from simulator.core.domain import MachineProfile, SignalDefinition, SignalType
from protocols.models import ProtocolReading
from edge.models import QualityCode


class ValidationResult:
    def __init__(self, is_valid: bool, errors: Optional[List[str]] = None, warnings: Optional[List[str]] = None, signal_qualities: Optional[Dict[str, QualityCode]] = None):
        self.is_valid = is_valid
        self.errors = errors or []
        self.warnings = warnings or []
        self.signal_qualities = signal_qualities or {}


class TelemetryValidator:
    """
    Validates ProtocolReading instances against configured MachineProfile signal catalogs.
    """

    @classmethod
    def validate_reading(cls, reading: ProtocolReading, profile: Optional[MachineProfile]) -> ValidationResult:
        errors: List[str] = []
        warnings: List[str] = []
        signal_qualities: Dict[str, QualityCode] = {}

        # 1. Verify profile existence
        if not profile:
            errors.append(f"Unknown machine_id '{reading.machine_id}'. No registered machine profile found.")
            return ValidationResult(is_valid=False, errors=errors)

        # 2. Verify machine_type match
        if reading.machine_type != profile.machine_type.value:
            errors.append(f"Machine type mismatch for '{reading.machine_id}': expected '{profile.machine_type.value}', got '{reading.machine_type}'.")

        # 3. Verify protocol consistency
        if reading.protocol.value != profile.protocol_metadata.value:
            errors.append(f"Protocol mismatch for '{reading.machine_id}': expected '{profile.protocol_metadata.value}', got '{reading.protocol.value}'.")

        # 4. Validate measurements against signal catalog
        signals_by_name = {s.name: s for s in profile.signals}

        # Check for missing required signals
        for sig_name, sig_def in signals_by_name.items():
            if sig_name not in reading.measurements:
                warnings.append(f"Signal '{sig_name}' missing from measurements for machine '{reading.machine_id}'.")
                signal_qualities[sig_name] = QualityCode.MISSING

        # Validate provided measurements
        for key, val in reading.measurements.items():
            if key in ("operating_state", "health_state"):
                continue  # State metadata handled separately

            if key not in signals_by_name:
                warnings.append(f"Uncatalogued signal '{key}' present in measurements for machine '{reading.machine_id}'.")
                continue

            sig_def = signals_by_name[key]
            val_valid, val_quality, err_msg = cls._validate_signal_value(val, sig_def)
            signal_qualities[key] = val_quality
            if not val_valid:
                errors.append(f"Signal '{key}' validation failure: {err_msg}")

        is_valid = len(errors) == 0
        return ValidationResult(is_valid=is_valid, errors=errors, warnings=warnings, signal_qualities=signal_qualities)

    @classmethod
    def _validate_signal_value(cls, val: Any, sig_def: SignalDefinition) -> Tuple[bool, QualityCode, str]:
        """Validate value datatype and physical engineering bounds."""
        if val is None:
            return False, QualityCode.MISSING, "Value is None"

        expected_type = sig_def.signal_type

        # Type validation
        if expected_type in (SignalType.FLOAT, SignalType.INT):
            if not isinstance(val, (int, float)) or isinstance(val, bool):
                return False, QualityCode.BAD, f"Expected numeric type for {sig_def.name}, got {type(val).__name__}"

            # Range validation
            num_val = float(val)
            if sig_def.min_value is not None and num_val < sig_def.min_value:
                return True, QualityCode.OUT_OF_RANGE, f"Value {num_val} below minimum bound {sig_def.min_value}"
            if sig_def.max_value is not None and num_val > sig_def.max_value:
                return True, QualityCode.OUT_OF_RANGE, f"Value {num_val} exceeds maximum bound {sig_def.max_value}"

            return True, QualityCode.GOOD, ""

        elif expected_type == SignalType.BOOL:
            if not isinstance(val, bool):
                return False, QualityCode.BAD, f"Expected bool for {sig_def.name}, got {type(val).__name__}"
            return True, QualityCode.GOOD, ""

        elif expected_type in (SignalType.STRING, SignalType.ENUM):
            if not isinstance(val, str):
                return False, QualityCode.BAD, f"Expected str for {sig_def.name}, got {type(val).__name__}"
            return True, QualityCode.GOOD, ""

        return True, QualityCode.GOOD, ""
