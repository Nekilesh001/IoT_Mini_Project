"""
Unit tests for SequenceTracker.
"""

from edge.sequence import SequenceTracker
from edge.models import IngestionStatus


def test_sequence_tracking_monotonic_and_gap():
    tracker = SequenceTracker()

    # 1. First event
    st1, m1 = tracker.process_sequence("CNC-001", sequence=1, event_id="evt_1")
    assert st1 == IngestionStatus.ACCEPTED
    assert not m1["gap_detected"]

    # 2. Next event
    st2, m2 = tracker.process_sequence("CNC-001", sequence=2, event_id="evt_2")
    assert st2 == IngestionStatus.ACCEPTED
    assert not m2["gap_detected"]

    # 3. Sequence jump (gap)
    st3, m3 = tracker.process_sequence("CNC-001", sequence=5, event_id="evt_5")
    assert st3 == IngestionStatus.ACCEPTED
    assert m3["gap_detected"]
    assert m3["gap_size"] == 2  # 3 and 4 missing


def test_sequence_tracking_independent_per_machine():
    tracker = SequenceTracker()

    st1, _ = tracker.process_sequence("CNC-001", sequence=10)
    assert st1 == IngestionStatus.ACCEPTED

    st2, _ = tracker.process_sequence("ROB-001", sequence=1)
    assert st2 == IngestionStatus.ACCEPTED

    assert tracker.get_last_sequence("CNC-001") == 10
    assert tracker.get_last_sequence("ROB-001") == 1
