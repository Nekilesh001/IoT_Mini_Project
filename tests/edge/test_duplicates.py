"""
Unit tests for duplicate and out-of-order detection.
"""

from edge.sequence import SequenceTracker
from edge.models import IngestionStatus


def test_duplicate_sequence_and_event_id():
    tracker = SequenceTracker()

    st1, _ = tracker.process_sequence("CNC-001", sequence=1, event_id="evt_1")
    assert st1 == IngestionStatus.ACCEPTED

    # Re-submitting exact same sequence
    st2, _ = tracker.process_sequence("CNC-001", sequence=1, event_id="evt_another")
    assert st2 == IngestionStatus.DUPLICATE

    # Re-submitting seen event_id
    st3, _ = tracker.process_sequence("CNC-001", sequence=2, event_id="evt_1")
    assert st3 == IngestionStatus.DUPLICATE


def test_out_of_order_sequence():
    tracker = SequenceTracker()

    st1, _ = tracker.process_sequence("CNC-001", sequence=5, event_id="evt_5")
    assert st1 == IngestionStatus.ACCEPTED

    # Receiving older sequence
    st2, _ = tracker.process_sequence("CNC-001", sequence=3, event_id="evt_3")
    assert st2 == IngestionStatus.OUT_OF_ORDER
