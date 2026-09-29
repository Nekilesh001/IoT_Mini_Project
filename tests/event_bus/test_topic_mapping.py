import pytest
from event_bus.topics import CanonicalTopicMapper

def test_canonical_topic_generation():
    topic = CanonicalTopicMapper.get_canonical_topic("PLANT_01", "LINE_A", "CNC-001")
    assert topic == "factory/PLANT_01/LINE_A/CNC-001/telemetry/canonical"

def test_wildcard_subscription():
    sub = CanonicalTopicMapper.get_wildcard_subscription()
    assert sub == "factory/+/+/+/telemetry/canonical"
    
    line_sub = CanonicalTopicMapper.get_wildcard_subscription("PLANT_01", "LINE_A")
    assert line_sub == "factory/PLANT_01/LINE_A/+/telemetry/canonical"

def test_topic_parsing():
    topic = "factory/PLANT_01/LINE_A/CNC-001/telemetry/canonical"
    parsed = CanonicalTopicMapper.parse_topic(topic)
    assert parsed is not None
    assert parsed["plant_id"] == "PLANT_01"
    assert parsed["line_id"] == "LINE_A"
    assert parsed["machine_id"] == "CNC-001"

def test_invalid_topic_parsing():
    invalid = "factory/PLANT_01/telemetry/raw"
    assert CanonicalTopicMapper.parse_topic(invalid) is None
