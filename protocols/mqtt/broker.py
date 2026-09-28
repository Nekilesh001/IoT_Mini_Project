"""
Lightweight embedded in-process MQTT message broker for local zero-dependency testing.
"""

import fnmatch
import logging
import queue
import re
import threading
from typing import Callable, Dict, List, Set, Tuple

logger = logging.getLogger(__name__)


class LocalMQTTBroker:
    """
    Embedded local MQTT broker managing topics, wildcards (+/#), and message dispatching.
    Ensures 100% offline local integration testing without external MQTT services.
    """

    _instance = None
    _lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(LocalMQTTBroker, cls).__new__(cls)
                cls._instance._initialized = False
            return cls._instance

    def __init__(self, host: str = "127.0.0.1", port: int = 1883):
        if getattr(self, "_initialized", False):
            return
        self._host: str = host
        self._port: int = port
        self._is_running: bool = False
        # topic_pattern -> List[Callable[[str, bytes, int], None]]
        self._subscriptions: Dict[str, List[Callable[[str, bytes, int], None]]] = {}
        self._sub_lock = threading.Lock()
        self._initialized = True

    @property
    def is_running(self) -> bool:
        return self._is_running

    def start(self) -> None:
        self._is_running = True

    def stop(self) -> None:
        self._is_running = False
        with self._sub_lock:
            self._subscriptions.clear()

    def subscribe(self, topic_pattern: str, callback: Callable[[str, bytes, int], None]) -> None:
        with self._sub_lock:
            if topic_pattern not in self._subscriptions:
                self._subscriptions[topic_pattern] = []
            if callback not in self._subscriptions[topic_pattern]:
                self._subscriptions[topic_pattern].append(callback)

    def unsubscribe(self, topic_pattern: str, callback: Callable[[str, bytes, int], None]) -> None:
        with self._sub_lock:
            if topic_pattern in self._subscriptions:
                if callback in self._subscriptions[topic_pattern]:
                    self._subscriptions[topic_pattern].remove(callback)

    def publish(self, topic: str, payload: bytes, qos: int = 1) -> None:
        if not self._is_running:
            return

        matched_callbacks = []
        with self._sub_lock:
            for pattern, callbacks in self._subscriptions.items():
                if self._match_topic(pattern, topic):
                    matched_callbacks.extend(callbacks)

        for cb in matched_callbacks:
            try:
                cb(topic, payload, qos)
            except Exception as e:
                logger.error(f"Error in MQTT broker subscriber callback: {e}")

    @staticmethod
    def _match_topic(pattern: str, topic: str) -> bool:
        """Match MQTT topic with wildcards + and #."""
        if pattern == "#" or pattern == topic:
            return True

        regex_pattern = "^" + pattern.replace("+", "[^/]+").replace("#", ".*") + "$"
        return bool(re.match(regex_pattern, topic))
