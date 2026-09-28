"""
Unit tests for UnitNormalizer.
"""

from simulator.core.domain import SignalDefinition, SignalType
from edge.normalization import UnitNormalizer


def test_unit_conversion_fahrenheit_to_celsius():
    sig = SignalDefinition(name="temp", unit="°C", signal_type=SignalType.FLOAT)
    # 212°F should convert to 100.0°C
    c = UnitNormalizer.normalize_value(212.0, sig, source_unit="°F")
    assert c == 100.0


def test_unit_conversion_psi_to_bar():
    sig = SignalDefinition(name="pressure", unit="BAR", signal_type=SignalType.FLOAT)
    # 100 PSI should convert to ~6.8948 BAR
    bar = UnitNormalizer.normalize_value(100.0, sig, source_unit="PSI")
    assert abs(bar - 6.8948) < 0.001


def test_is_conversion_supported():
    assert UnitNormalizer.is_conversion_supported("°F", "°C")
    assert UnitNormalizer.is_conversion_supported("PSI", "BAR")
    assert not UnitNormalizer.is_conversion_supported("GALLONS", "LITERS")
