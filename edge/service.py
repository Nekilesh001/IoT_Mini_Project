"""
Central Edge Ingestion Service orchestrating protocol reading canonicalization.
"""

from datetime import datetime, timezone
import logging
from typing import Any, Dict, List, Optional
import uuid

from simulator.core.domain import MachineProfile
from protocols.models import ProtocolReading
from edge.models import (
    CanonicalSource,
    CanonicalState,
    CanonicalTelemetry,
    EventType,
    IngestionResult,
    IngestionStatus,
    QualityCode,
)
from edge.validation import TelemetryValidator
from edge.normalization import UnitNormalizer
from edge.quality import QualityEvaluator
from edge.sequence import SequenceTracker
from edge.derived import DerivedMetricsCalculator

logger = logging.getLogger(__name__)


class EdgeIngestionService:
    """
    Protocol-agnostic edge ingestion pipeline for validating, normalizing,
    quality-tagging, deduplicating, and building canonical telemetry envelopes.
    """

    def __init__(self, profiles: Optional[Dict[str, MachineProfile]] = None, max_staleness_seconds: float = 60.0):
        self._profiles: Dict[str, MachineProfile] = profiles or {}
        self._sequence_tracker: SequenceTracker = SequenceTracker()
        self._max_staleness_seconds: float = max_staleness_seconds
        self._ingested_count: int = 0
        self._duplicate_count: int = 0
        self._out_of_order_count: int = 0
        self._rejected_count: int = 0

    def register_profile(self, profile: MachineProfile) -> None:
        self._profiles[profile.machine_id] = profile

    def register_profiles(self, profiles: Dict[str, MachineProfile]) -> None:
        self._profiles.update(profiles)

    def ingest_reading(self, reading: ProtocolReading) -> IngestionResult:
        """
        Execute full edge ingestion pipeline on an incoming ProtocolReading.
        """
        # 1. Identity & Profile Resolution
        profile = self._profiles.get(reading.machine_id)
        if not profile:
            self._rejected_count += 1
            return IngestionResult(
                status=IngestionStatus.REJECTED,
                errors=[f"Unknown machine_id '{reading.machine_id}'. Machine is not registered."]
            )

        # 2. Schema and Range Validation
        val_res = TelemetryValidator.validate_reading(reading, profile)
        if not val_res.is_valid:
            self._rejected_count += 1
            return IngestionResult(
                status=IngestionStatus.INVALID,
                errors=val_res.errors,
                warnings=val_res.warnings
            )

        # 3. Stable Event ID & Ingestion Timestamp
        event_id = reading.metadata.get("event_id") if isinstance(reading.metadata, dict) else None
        if not event_id:
            event_id = f"evt_{uuid.uuid4()}"

        ingestion_time = datetime.now(timezone.utc).isoformat()

        # 4. Sequence & Duplicate Processing
        seq_status, seq_metrics = self._sequence_tracker.process_sequence(
            machine_id=reading.machine_id,
            sequence=reading.sequence,
            event_id=event_id
        )

        if seq_status == IngestionStatus.DUPLICATE:
            self._duplicate_count += 1
            return IngestionResult(
                status=IngestionStatus.DUPLICATE,
                errors=[f"Duplicate event detected for machine '{reading.machine_id}' (sequence: {reading.sequence}, event_id: {event_id})."],
                metrics=seq_metrics,
                warnings=val_res.warnings
            )
        elif seq_status == IngestionStatus.OUT_OF_ORDER:
            self._out_of_order_count += 1
            return IngestionResult(
                status=IngestionStatus.OUT_OF_ORDER,
                errors=[f"Out-of-order sequence received for machine '{reading.machine_id}' (received: {reading.sequence}, last: {seq_metrics['previous_sequence']})."],
                metrics=seq_metrics,
                warnings=val_res.warnings
            )

        # 5. Extract state and filter from raw measurements
        raw_measurements = dict(reading.measurements)
        op_state = str(raw_measurements.pop("operating_state", "RUNNING"))
        health_state = str(raw_measurements.pop("health_state", "HEALTHY"))

        # 6. Unit Normalization
        normalized_measurements = UnitNormalizer.normalize_measurements(raw_measurements, profile)

        # 7. Quality Evaluation
        quality = QualityEvaluator.evaluate_quality(
            event_time_str=reading.timestamp,
            is_valid=val_res.is_valid,
            signal_qualities=val_res.signal_qualities,
            max_staleness_seconds=self._max_staleness_seconds
        )

        # 8. Derived Metrics
        derived_metrics = DerivedMetricsCalculator.calculate_derived_metrics(normalized_measurements, profile)

        # 9. Build Canonical Telemetry Envelope
        endpoint = str(reading.metadata.get("endpoint", "")) if isinstance(reading.metadata, dict) else ""
        canonical = CanonicalTelemetry(
            schema_version="1.0.0",
            event_id=event_id,
            event_type=EventType.TELEMETRY,
            plant_id=profile.plant_id,
            line_id=profile.line_id,
            machine_id=profile.machine_id,
            machine_type=profile.machine_type.value if hasattr(profile.machine_type, "value") else str(profile.machine_type),
            source=CanonicalSource(
                protocol=reading.protocol.value,
                endpoint=endpoint,
                source_address=reading.source_address
            ),
            event_time=reading.timestamp,
            ingestion_time=ingestion_time,
            sequence=reading.sequence,
            state=CanonicalState(
                operating=op_state,
                health=health_state
            ),
            quality=quality,
            measurements=normalized_measurements,
            derived=derived_metrics,
            ml={},
            measurement_quality=val_res.signal_qualities
        )

        self._ingested_count += 1

        return IngestionResult(
            status=IngestionStatus.ACCEPTED,
            canonical_telemetry=canonical,
            warnings=val_res.warnings,
            metrics=seq_metrics
        )

    def get_metrics(self) -> Dict[str, Any]:
        return {
            "ingested_count": self._ingested_count,
            "duplicate_count": self._duplicate_count,
            "out_of_order_count": self._out_of_order_count,
            "rejected_count": self._rejected_count,
        }

    def reset(self) -> None:
        self._sequence_tracker.reset()
        self._ingested_count = 0
        self._duplicate_count = 0
        self._out_of_order_count = 0
        self._rejected_count = 0
