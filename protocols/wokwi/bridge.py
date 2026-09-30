"""
Production-ready lightweight Wokwi MQTT Bridge connecting HiveMQ to the Smart Factory edge.
"""

from datetime import datetime, timezone
import json
import logging
import queue
import threading
import time
from typing import Any, Callable, Dict, List, Optional

try:
    import paho.mqtt.client as mqtt
    PAHO_AVAILABLE = True
except ImportError:
    mqtt = None  # type: ignore
    PAHO_AVAILABLE = False

from protocols.models import ProtocolHealth, ProtocolReading, ProtocolType
from protocols.wokwi.config import WokwiConfig
from protocols.wokwi.normalizer import WokwiPayloadNormalizer

logger = logging.getLogger(__name__)


class WokwiMQTTBridge:
    """
    Local MQTT Bridge subscribing to external HiveMQ broker for Wokwi Raspberry Pi Pico W telemetry.
    Normalizes incoming messages into the project's canonical ingestion path.
    """

    def __init__(self, config: Optional[WokwiConfig] = None):
        self.config = config or WokwiConfig.from_env()
        self.normalizer = WokwiPayloadNormalizer()
        self._health: ProtocolHealth = ProtocolHealth.DISCONNECTED
        self._client: Optional[Any] = None
        self._is_running: bool = False
        self._lock = threading.Lock()
        
        # Ingestion message queue and latest readings store
        self._reading_queue: queue.Queue = queue.Queue(maxsize=1000)
        self._latest_readings: Dict[str, ProtocolReading] = {}
        
        # Telemetry / Health metrics
        self._received_count: int = 0
        self._rejected_count: int = 0
        self._reconnect_count: int = 0
        self._last_message_time: Optional[str] = None
        self._last_error: Optional[str] = None
        self._connect_thread: Optional[threading.Thread] = None

    @property
    def is_running(self) -> bool:
        return self._is_running

    @property
    def is_connected(self) -> bool:
        return self._health == ProtocolHealth.CONNECTED

    def start(self) -> bool:
        """Start the background bridge connection to the external HiveMQ broker."""
        if not self.config.enabled:
            logger.info("Wokwi MQTT Bridge is disabled via configuration.")
            return False

        if self._is_running:
            return True

        self._is_running = True
        logger.info(
            f"Starting Wokwi MQTT Bridge: connecting to {self.config.broker}:{self.config.port} "
            f"subscribing to '{self.config.telemetry_topic}'..."
        )

        self._init_client()
        return True

    def _init_client(self) -> None:
        """Initialize Paho MQTT client and start background network loop."""
        if not PAHO_AVAILABLE:
            self._health = ProtocolHealth.ERROR
            self._last_error = "paho-mqtt package is not installed"
            logger.error("paho-mqtt is required for Wokwi MQTT Bridge.")
            return

        try:
            # Handle Paho MQTT 2.x vs 1.x constructor API
            client_id = f"{self.config.client_id}-{int(time.time())}"
            try:
                self._client = mqtt.Client(
                    mqtt.CallbackAPIVersion.VERSION2,
                    client_id=client_id,
                    clean_session=True,
                )
            except AttributeError:
                self._client = mqtt.Client(
                    client_id=client_id,
                    clean_session=True,
                )

            if self.config.username:
                self._client.username_pw_set(self.config.username, self.config.password)

            self._client.on_connect = self._on_connect
            self._client.on_disconnect = self._on_disconnect
            self._client.on_message = self._on_message

            # Connect asynchronously to avoid blocking the caller if network is down
            def _connect_worker():
                try:
                    self._client.connect(
                        self.config.broker,
                        self.config.port,
                        keepalive=self.config.keepalive,
                    )
                    self._client.loop_start()
                except Exception as e:
                    with self._lock:
                        self._health = ProtocolHealth.DEGRADED
                        self._last_error = str(e)
                    logger.warning(
                        f"Wokwi MQTT Bridge initial connection failed to {self.config.broker}:{self.config.port}: {e}. "
                        "Will retry in background."
                    )
                    if self._is_running:
                        try:
                            self._client.loop_start()
                        except Exception:
                            pass

            self._connect_thread = threading.Thread(target=_connect_worker, daemon=True, name="WokwiBridgeConnect")
            self._connect_thread.start()

        except Exception as ex:
            self._health = ProtocolHealth.ERROR
            self._last_error = str(ex)
            logger.error(f"Failed to initialize Wokwi MQTT Bridge client: {ex}")

    def stop(self) -> None:
        """Disconnect and stop background bridge network loop."""
        self._is_running = False
        if self._client:
            try:
                self._client.loop_stop()
                self._client.disconnect()
            except Exception as e:
                logger.debug(f"Error disconnecting Wokwi MQTT client: {e}")
            self._client = None

        self._health = ProtocolHealth.DISCONNECTED
        logger.info("Wokwi MQTT Bridge stopped.")

    def _on_connect(self, client, userdata, flags, rc, properties=None) -> None:
        """Callback when connected to HiveMQ broker."""
        # In Paho 2.x, rc is a ReasonCode object whose value is 0 on success
        rc_code = getattr(rc, "value", rc)
        if rc_code == 0:
            with self._lock:
                self._health = ProtocolHealth.CONNECTED
                self._last_error = None
            logger.info(
                f"Wokwi MQTT Bridge connected successfully to {self.config.broker}:{self.config.port}. "
                f"Subscribing to '{self.config.telemetry_topic}'."
            )
            try:
                client.subscribe(self.config.telemetry_topic, qos=1)
            except Exception as sub_err:
                logger.error(f"Error subscribing to topic: {sub_err}")
        else:
            with self._lock:
                self._health = ProtocolHealth.DEGRADED
                self._last_error = f"Connection failed with return code {rc}"
            logger.warning(f"Wokwi MQTT Bridge connection rejected with code: {rc}")

    def _on_disconnect(self, client, userdata, rc, properties=None) -> None:
        """Callback when disconnected from HiveMQ broker."""
        with self._lock:
            self._health = ProtocolHealth.DISCONNECTED
            self._reconnect_count += 1
        rc_code = getattr(rc, "value", rc)
        if rc_code != 0:
            logger.warning(f"Wokwi MQTT Bridge unexpectedly disconnected (rc={rc}). Auto-reconnect active.")

    def _on_message(self, client, userdata, message) -> None:
        """Callback when telemetry message is received from HiveMQ."""
        topic = message.topic
        payload_bytes = message.payload

        reading, err = self.normalizer.normalize(
            raw_payload=payload_bytes,
            topic=topic,
            ingress_broker=self.config.broker,
        )

        with self._lock:
            if reading is not None:
                self._received_count += 1
                self._last_message_time = datetime.now(timezone.utc).isoformat()
                self._latest_readings[reading.machine_id] = reading
                try:
                    self._reading_queue.put_nowait(reading)
                except queue.Full:
                    # Drop oldest if queue full
                    try:
                        self._reading_queue.get_nowait()
                        self._reading_queue.put_nowait(reading)
                    except Exception:
                        pass
            else:
                self._rejected_count += 1
                self._last_error = err
                logger.warning(f"Wokwi MQTT Bridge rejected message on topic '{topic}': {err}")

    def pop_all_readings(self) -> List[ProtocolReading]:
        """Drain all received ProtocolReading objects currently in queue."""
        readings = []
        while not self._reading_queue.empty():
            try:
                readings.append(self._reading_queue.get_nowait())
            except queue.Empty:
                break
        return readings

    def get_latest_reading(self, device_id: str = "IOT-SENSOR-001") -> Optional[ProtocolReading]:
        """Return the most recently normalized ProtocolReading for device_id."""
        with self._lock:
            return self._latest_readings.get(device_id)

    def publish_command(self, payload: Dict[str, Any]) -> bool:
        """Send command JSON to external Wokwi device via MQTT command topic."""
        if not self._client or self._health != ProtocolHealth.CONNECTED:
            logger.warning("Cannot send command: Wokwi MQTT Bridge is not connected.")
            return False

        try:
            payload_str = json.dumps(payload)
            info = self._client.publish(self.config.command_topic, payload_str, qos=1)
            return info.rc == mqtt.MQTT_ERR_SUCCESS
        except Exception as e:
            logger.error(f"Failed to publish command to Wokwi: {e}")
            return False

    def get_health(self) -> ProtocolHealth:
        return self._health

    def get_status(self) -> Dict[str, Any]:
        """Return comprehensive observability metrics for the bridge."""
        with self._lock:
            return {
                "enabled": self.config.enabled,
                "connected": self._health == ProtocolHealth.CONNECTED,
                "health": self._health.value,
                "broker": self.config.broker,
                "port": self.config.port,
                "telemetry_topic": self.config.telemetry_topic,
                "command_topic": self.config.command_topic,
                "received_count": self._received_count,
                "rejected_count": self._rejected_count,
                "reconnect_count": self._reconnect_count,
                "last_message_time": self._last_message_time,
                "last_error": self._last_error,
                "queue_size": self._reading_queue.qsize(),
            }
