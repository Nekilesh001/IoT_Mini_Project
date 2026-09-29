"""
Unit tests for PersistentBuffer durability and status tracking.
"""

from storage.buffer import PersistentBuffer


def test_buffer_durability_and_restart(tmp_path):
    buffer_file = str(tmp_path / "test_buffer.db")

    # Instance 1: Add events
    buffer1 = PersistentBuffer(buffer_file)
    buffer1.add_event("evt_1", "CNC-001", 1, "topic/1", '{"sequence": 1}')
    buffer1.add_event("evt_2", "CNC-001", 2, "topic/2", '{"sequence": 2}')
    assert buffer1.count_by_status("PENDING") == 2

    # Simulate Process Restart: instantiate new buffer on same SQLite file
    buffer2 = PersistentBuffer(buffer_file)
    pending = buffer2.get_pending_events(batch_size=10)
    assert len(pending) == 2
    assert pending[0].event_id == "evt_1"
    assert pending[1].event_id == "evt_2"

    # Mark in flight & delivery
    buffer2.mark_in_flight(["evt_1"])
    buffer2.mark_delivered(["evt_1"], delete_on_success=True)

    assert buffer2.count_by_status("PENDING") == 1
    assert buffer2.get_pending_events()[0].event_id == "evt_2"
