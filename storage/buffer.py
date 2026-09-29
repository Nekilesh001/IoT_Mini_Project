"""
Durable SQLite-backed store-and-forward buffer surviving process restarts and network outages.
"""

from dataclasses import dataclass
from enum import Enum
import json
import logging
from pathlib import Path
import sqlite3
import time
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class BufferStatus(str, Enum):
    PENDING = "PENDING"
    IN_FLIGHT = "IN_FLIGHT"
    DELIVERED = "DELIVERED"
    FAILED = "FAILED"


@dataclass
class BufferedEvent:
    event_id: str
    machine_id: str
    sequence: int
    topic: str
    payload: str
    created_at: float
    retry_count: int
    next_retry_at: float
    status: str  # PENDING, IN_FLIGHT, DELIVERED, FAILED
    last_error: Optional[str] = None

    def get_payload_dict(self) -> Dict[str, Any]:
        return json.loads(self.payload)


from contextlib import contextmanager


class PersistentBuffer:
    """
    SQLite-backed store-and-forward persistent buffer.
    """

    def __init__(self, db_path: str = "local_buffer.db"):
        self._db_path = Path(db_path)
        self._init_db()

    @contextmanager
    def _get_connection(self):
        conn = sqlite3.connect(str(self._db_path), timeout=10.0)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()

    def _init_db(self) -> None:
        """Create buffer table and indexes if not exists."""
        with self._get_connection() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS buffer_events (
                    event_id TEXT PRIMARY KEY,
                    machine_id TEXT NOT NULL,
                    sequence INTEGER NOT NULL,
                    topic TEXT NOT NULL,
                    payload TEXT NOT NULL,
                    created_at REAL NOT NULL,
                    retry_count INTEGER NOT NULL DEFAULT 0,
                    next_retry_at REAL NOT NULL,
                    status TEXT NOT NULL DEFAULT 'PENDING',
                    last_error TEXT
                )
            """)
            conn.execute("CREATE INDEX IF NOT EXISTS ix_buffer_status_retry ON buffer_events(status, next_retry_at)")
            conn.execute("CREATE INDEX IF NOT EXISTS ix_buffer_machine_seq ON buffer_events(machine_id, sequence)")
            conn.commit()

    def add_event(self, event_id: str, machine_id: str, sequence: int, topic: str, payload_json: str) -> bool:
        """Add an event to the persistent buffer."""
        now = time.time()
        try:
            with self._get_connection() as conn:
                conn.execute("""
                    INSERT OR IGNORE INTO buffer_events (
                        event_id, machine_id, sequence, topic, payload, created_at, retry_count, next_retry_at, status
                    ) VALUES (?, ?, ?, ?, ?, ?, 0, ?, 'PENDING')
                """, (event_id, machine_id, sequence, topic, payload_json, now, now))
                conn.commit()
            return True
        except Exception as e:
            logger.error(f"Failed to buffer event {event_id}: {e}")
            return False

    def get_pending_events(self, batch_size: int = 50) -> List[BufferedEvent]:
        """Fetch pending events whose next_retry_at <= current time, ordered deterministically."""
        now = time.time()
        events = []
        with self._get_connection() as conn:
            cursor = conn.execute("""
                SELECT event_id, machine_id, sequence, topic, payload, created_at, retry_count, next_retry_at, status, last_error
                FROM buffer_events
                WHERE (status = 'PENDING' OR status = 'IN_FLIGHT') AND next_retry_at <= ?
                ORDER BY created_at ASC, machine_id ASC, sequence ASC
                LIMIT ?
            """, (now, batch_size))

            for row in cursor.fetchall():
                events.append(BufferedEvent(
                    event_id=row["event_id"],
                    machine_id=row["machine_id"],
                    sequence=row["sequence"],
                    topic=row["topic"],
                    payload=row["payload"],
                    created_at=row["created_at"],
                    retry_count=row["retry_count"],
                    next_retry_at=row["next_retry_at"],
                    status=row["status"],
                    last_error=row["last_error"]
                ))
        return events

    def mark_in_flight(self, event_ids: List[str]) -> None:
        if not event_ids:
            return
        with self._get_connection() as conn:
            placeholders = ",".join("?" * len(event_ids))
            conn.execute(f"UPDATE buffer_events SET status = 'IN_FLIGHT' WHERE event_id IN ({placeholders})", event_ids)
            conn.commit()

    def mark_delivered(self, event_ids: List[str], delete_on_success: bool = True) -> None:
        if not event_ids:
            return
        with self._get_connection() as conn:
            placeholders = ",".join("?" * len(event_ids))
            if delete_on_success:
                conn.execute(f"DELETE FROM buffer_events WHERE event_id IN ({placeholders})", event_ids)
            else:
                conn.execute(f"UPDATE buffer_events SET status = 'DELIVERED' WHERE event_id IN ({placeholders})", event_ids)
            conn.commit()

    def mark_retry_failed(self, event_id: str, error: str, retry_delay_sec: float, max_retries: int = 10) -> None:
        now = time.time()
        with self._get_connection() as conn:
            row = conn.execute("SELECT retry_count FROM buffer_events WHERE event_id = ?", (event_id,)).fetchone()
            if row:
                count = row["retry_count"] + 1
                status = "FAILED" if count >= max_retries else "PENDING"
                next_retry = now + retry_delay_sec
                conn.execute("""
                    UPDATE buffer_events
                    SET retry_count = ?, next_retry_at = ?, status = ?, last_error = ?
                    WHERE event_id = ?
                """, (count, next_retry, status, error, event_id))
                conn.commit()

    def count_by_status(self, status: Optional[str] = None) -> int:
        with self._get_connection() as conn:
            if status:
                cursor = conn.execute("SELECT COUNT(*) FROM buffer_events WHERE status = ?", (status,))
            else:
                cursor = conn.execute("SELECT COUNT(*) FROM buffer_events")
            return cursor.fetchone()[0]

    def clear(self) -> None:
        with self._get_connection() as conn:
            conn.execute("DELETE FROM buffer_events")
            conn.commit()
