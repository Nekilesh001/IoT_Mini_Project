"""
Configuration settings for local storage, event bus, and store-and-forward buffer.
"""

import os
from dataclasses import dataclass


@dataclass
class StorageConfig:
    database_url: str = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@127.0.0.1:5432/smart_factory")
    echo_sql: bool = os.getenv("ECHO_SQL", "False").lower() in ("true", "1")


@dataclass
class MQTTConfig:
    broker_host: str = os.getenv("MQTT_BROKER_HOST", "127.0.0.1")
    broker_port: int = int(os.getenv("MQTT_BROKER_PORT", "1883"))
    qos: int = int(os.getenv("MQTT_QOS", "1"))
    topic_prefix: str = os.getenv("MQTT_TOPIC_PREFIX", "factory")
    client_id_prefix: str = os.getenv("MQTT_CLIENT_ID_PREFIX", "edge_service")


@dataclass
class BufferConfig:
    db_path: str = os.getenv("BUFFER_DB_PATH", "local_buffer.db")
    max_retries: int = int(os.getenv("BUFFER_MAX_RETRIES", "10"))
    initial_retry_delay_sec: float = float(os.getenv("BUFFER_INITIAL_RETRY_DELAY_SEC", "1.0"))
    max_retry_delay_sec: float = float(os.getenv("BUFFER_MAX_RETRY_DELAY_SEC", "30.0"))
    batch_size: int = int(os.getenv("BUFFER_BATCH_SIZE", "50"))
