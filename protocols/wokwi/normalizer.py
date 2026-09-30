"""
Payload Normalizer converting Wokwi MicroPython JSON messages into ProtocolReading objects.
"""

from datetime import datetime, timezone
import json
import logging
from typing import Any, Dict, Optional, Tuple

from protocols.models import ProtocolReading, ProtocolType
from protocols.wokwi.models import ExternalDeviceProfile
from protocols.wokwi.registry import get_external_device_registry

logger = logging.getLogger(__name__)


class WokwiPayloadNormalizer:
    """
    Decoupled normalizer parsing external Wokwi MicroPython MQTT payloads
    into standard ProtocolReading domain objects.
    """

    def __init__(self):
        self._registry = get_external_device_registry()
        self._device_sequences: Dict[str, int] = {}

    def normalize(
        self,
        raw_payload: Any,
        topic: str = "",
        ingress_broker: str = "broker.hivemq.com"
    ) -> Tuple[Optional[ProtocolReading], Optional[str]]:
        """
        Parse and validate a raw Wokwi JSON payload string or bytes.
        Returns (ProtocolReading, None) on success or (None, error_message) on failure.
        """
        # 1. Decode bytes if needed and parse JSON
        if isinstance(raw_payload, (bytes, bytearray)):
            try:
                raw_payload = raw_payload.decode("utf-8")
            except Exception as e:
                return None, f"Payload UTF-8 decoding error: {e}"

        if isinstance(raw_payload, str):
            try:
                data = json.loads(raw_payload)
            except json.JSONDecodeError as e:
                return None, f"Malformed JSON: {e}"
        elif isinstance(raw_payload, dict):
            data = raw_payload
        else:
            return None, f"Unsupported payload type: {type(raw_payload)}"

        if not isinstance(data, dict):
            return None, "Payload must be a JSON object"

        # 2. Extract and validate Device Identity
        device_id = data.get("deviceId") or data.get("device_id") or data.get("machineId")
        if not device_id:
            return None, "Missing required field 'deviceId'"

        device_profile = self._registry.get_device(device_id)
        if not device_profile:
            return None, f"Unregistered external deviceId: '{device_id}'"

        # 3. Extract and normalize Timestamp
        raw_ts = data.get("timestamp")
        event_time_str = self._normalize_timestamp(raw_ts)

        # 4. Extract and normalize Sequence counter
        raw_seq = data.get("sequence")
        if raw_seq is not None:
            try:
                sequence = int(raw_seq)
                self._device_sequences[device_id] = sequence
            except (ValueError, TypeError):
                sequence = self._next_sequence(device_id)
        else:
            # Generate local sequence if device firmware did not send one
            sequence = self._next_sequence(device_id)

        # 5. Extract and normalize Physical Measurements (temperature_c, humidity_pct)
        readings = data.get("readings", {})
        if not isinstance(readings, dict):
            readings = {}

        # Look for temperature in readings or root level
        temp_val = (
            readings.get("temperatureC")
            if "temperatureC" in readings
            else readings.get("temperature_c", readings.get("temperature", data.get("temperatureC", data.get("temperature_c"))))
        )

        # Look for humidity in readings or root level
        hum_val = (
            readings.get("humidityPct")
            if "humidityPct" in readings
            else readings.get("humidity_pct", readings.get("humidity", data.get("humidityPct", data.get("humidity_pct"))))
        )

        if temp_val is None:
            return None, f"Missing required temperature measurement in payload for {device_id}"
        if hum_val is None:
            return None, f"Missing required humidity measurement in payload for {device_id}"

        try:
            temp_float = float(temp_val)
            hum_float = float(hum_val)
        except (ValueError, TypeError) as e:
            return None, f"Non-numeric measurement values: {e}"

        measurements: Dict[str, Any] = {
            "temperature_c": round(temp_float, 2),
            "humidity_pct": round(hum_float, 2),
        }

        # 6. Extract external IoT metadata (actuator, control, firmwareVersion)
        metadata: Dict[str, Any] = {
            "ingress_broker": ingress_broker,
            "topic": topic,
            "device_class": "EXTERNAL_IOT",
            "firmwareVersion": data.get("firmwareVersion", device_profile.firmware_version),
        }

        if "actuator" in data and isinstance(data["actuator"], dict):
            metadata["actuator"] = data["actuator"]
        if "control" in data and isinstance(data["control"], dict):
            metadata["control"] = data["control"]
        if "plantId" in data:
            metadata["plantId"] = data["plantId"]
        if "lineId" in data:
            metadata["lineId"] = data["lineId"]

        device_type = data.get("deviceType", device_profile.device_type)

        reading = ProtocolReading(
            machine_id=device_id,
            machine_type=device_type,
            protocol=ProtocolType.MQTT,
            timestamp=event_time_str,
            sequence=sequence,
            measurements=measurements,
            source_address=topic or device_profile.telemetry_topic,
            raw_payload=data,
            metadata=metadata,
        )

        return reading, None

    def _next_sequence(self, device_id: str) -> int:
        cur = self._device_sequences.get(device_id, 0) + 1
        self._device_sequences[device_id] = cur
        return cur

    def reset_sequence(self, device_id: str, seq: int = 0) -> None:
        self._device_sequences[device_id] = seq

    @staticmethod
    def _normalize_timestamp(raw_ts: Any) -> str:
        if isinstance(raw_ts, str) and raw_ts.strip():
            try:
                # Validate ISO format
                parsed = datetime.fromisoformat(raw_ts.replace("Z", "+00:00"))
                if parsed.tzinfo is None:
                    parsed = parsed.replace(tzinfo=timezone.utc)
                return parsed.isoformat()
            except Exception:
                pass
        return datetime.now(timezone.utc).isoformat()
