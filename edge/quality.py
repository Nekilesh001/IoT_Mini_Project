"""
Quality Assessment Engine for edge telemetry events.
"""

from datetime import datetime, timezone
from typing import Any, Dict, Optional
from edge.models import QualityCode


class QualityEvaluator:
    """
    Evaluates telemetry event quality based on timestamp freshness, validation status, and signal ranges.
    """

    # Default freshness threshold in seconds
    DEFAULT_MAX_STALENESS_SECONDS: float = 60.0

    @classmethod
    def evaluate_quality(
        cls,
        event_time_str: str,
        is_valid: bool,
        signal_qualities: Dict[str, QualityCode],
        max_staleness_seconds: float = DEFAULT_MAX_STALENESS_SECONDS,
        is_estimated: bool = False,
    ) -> QualityCode:
        """
        Derives top-level event QualityCode according to precedence rules:
        BAD > OUT_OF_RANGE > MISSING > STALE > ESTIMATED > GOOD
        """
        if not is_valid:
            return QualityCode.BAD

        # Check timestamp staleness
        try:
            event_dt = datetime.fromisoformat(event_time_str)
            if event_dt.tzinfo is None:
                event_dt = event_dt.replace(tzinfo=timezone.utc)
            now_dt = datetime.now(timezone.utc)
            age_seconds = (now_dt - event_dt).total_seconds()
            if age_seconds > max_staleness_seconds:
                return QualityCode.STALE
        except Exception:
            return QualityCode.BAD

        # Check individual signal qualities
        qualities_set = set(signal_qualities.values())

        if QualityCode.BAD in qualities_set:
            return QualityCode.BAD
        if QualityCode.OUT_OF_RANGE in qualities_set:
            return QualityCode.OUT_OF_RANGE
        if QualityCode.MISSING in qualities_set:
            return QualityCode.MISSING
        if is_estimated or QualityCode.ESTIMATED in qualities_set:
            return QualityCode.ESTIMATED

        return QualityCode.GOOD
