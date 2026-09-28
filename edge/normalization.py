"""
Unit Normalization Engine for canonical telemetry values.
"""

from typing import Any, Dict, Optional
from simulator.core.domain import MachineProfile, SignalDefinition


class UnitNormalizer:
    """
    Handles deterministic engineering unit conversions into canonical target units.
    """

    # Supported conversion registry: (source_unit, target_unit) -> conversion function
    _CONVERSIONS = {
        ("°F", "°C"): lambda v: (v - 32.0) * (5.0 / 9.0),
        ("FAHRENHEIT", "CELSIUS"): lambda v: (v - 32.0) * (5.0 / 9.0),
        ("K", "°C"): lambda v: v - 273.15,
        ("KELVIN", "CELSIUS"): lambda v: v - 273.15,
        ("PSI", "BAR"): lambda v: v * 0.0689476,
        ("KPA", "BAR"): lambda v: v * 0.01,
        ("MPA", "BAR"): lambda v: v * 10.0,
        ("MM/S", "M/S"): lambda v: v / 1000.0,
        ("L/MIN", "M3/H"): lambda v: v * 0.06,
        ("W", "KW"): lambda v: v / 1000.0,
    }

    @classmethod
    def normalize_measurements(cls, measurements: Dict[str, Any], profile: MachineProfile) -> Dict[str, Any]:
        """
        Normalize measurements dictionary using machine profile signal definitions.
        """
        normalized = {}
        signals_by_name = {s.name: s for s in profile.signals}

        for k, v in measurements.items():
            if k in signals_by_name:
                sig_def = signals_by_name[k]
                normalized[k] = cls.normalize_value(v, sig_def)
            else:
                normalized[k] = v

        return normalized

    @classmethod
    def normalize_value(cls, value: Any, sig_def: SignalDefinition, source_unit: Optional[str] = None) -> Any:
        """
        Convert a single signal value into its standard unit if a source unit is specified.
        If value is numeric, standardizes rounding to 4 decimal places.
        """
        if not isinstance(value, (int, float)) or isinstance(value, bool):
            return value

        target_unit = (sig_def.unit or "").strip().upper()
        if source_unit:
            src = source_unit.strip().upper()
            if src != target_unit and (src, target_unit) in cls._CONVERSIONS:
                conv_fn = cls._CONVERSIONS[(src, target_unit)]
                converted = conv_fn(float(value))
                return round(converted, 4)

        if isinstance(value, float):
            return round(value, 4)
        return value

    @classmethod
    def is_conversion_supported(cls, source_unit: str, target_unit: str) -> bool:
        src = source_unit.strip().upper()
        tgt = target_unit.strip().upper()
        return src == tgt or (src, tgt) in cls._CONVERSIONS
