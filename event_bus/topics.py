"""
Deterministic canonical MQTT topic definitions.
"""

import re
from typing import Dict, Optional


class CanonicalTopicMapper:
    """
    Constructs and parses canonical telemetry MQTT topics:
    factory/{plant}/{line}/{machine_id}/telemetry/canonical
    """

    TOPIC_PATTERN = re.compile(r"^factory/([^/]+)/([^/]+)/([^/]+)/telemetry/canonical$")

    @classmethod
    def get_canonical_topic(cls, plant_id: str, line_id: str, machine_id: str) -> str:
        return f"factory/{plant_id}/{line_id}/{machine_id}/telemetry/canonical"

    @classmethod
    def get_wildcard_subscription(cls, plant_id: str = "+", line_id: str = "+") -> str:
        return f"factory/{plant_id}/{line_id}/+/telemetry/canonical"

    @classmethod
    def parse_topic(cls, topic: str) -> Optional[Dict[str, str]]:
        match = cls.TOPIC_PATTERN.match(topic)
        if match:
            return {
                "plant_id": match.group(1),
                "line_id": match.group(2),
                "machine_id": match.group(3),
            }
        return None
