"""
Unit tests for QualityEvaluator.
"""

from datetime import datetime, timezone, timedelta
from edge.models import QualityCode
from edge.quality import QualityEvaluator


def test_quality_good_reading():
    now_str = datetime.now(timezone.utc).isoformat()
    q = QualityEvaluator.evaluate_quality(
        event_time_str=now_str,
        is_valid=True,
        signal_qualities={"temp": QualityCode.GOOD, "speed": QualityCode.GOOD}
    )
    assert q == QualityCode.GOOD


def test_quality_stale_reading():
    old_time = (datetime.now(timezone.utc) - timedelta(seconds=120)).isoformat()
    q = QualityEvaluator.evaluate_quality(
        event_time_str=old_time,
        is_valid=True,
        signal_qualities={"temp": QualityCode.GOOD},
        max_staleness_seconds=60.0
    )
    assert q == QualityCode.STALE


def test_quality_out_of_range_precedence():
    now_str = datetime.now(timezone.utc).isoformat()
    q = QualityEvaluator.evaluate_quality(
        event_time_str=now_str,
        is_valid=True,
        signal_qualities={"temp": QualityCode.OUT_OF_RANGE, "speed": QualityCode.GOOD}
    )
    assert q == QualityCode.OUT_OF_RANGE


def test_quality_bad_validation():
    now_str = datetime.now(timezone.utc).isoformat()
    q = QualityEvaluator.evaluate_quality(
        event_time_str=now_str,
        is_valid=False,
        signal_qualities={"temp": QualityCode.BAD}
    )
    assert q == QualityCode.BAD
