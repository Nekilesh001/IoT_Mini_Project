"""
Security Audit Logging Module.
Provides structured, non-repudiable audit logging for authentication, authorization, certificate lifecycle, and management actions.
"""

from collections import deque
from datetime import datetime, timezone
import logging
from threading import Lock
from typing import Any, Dict, List, Optional
import uuid

from security.models import SecurityAuditAction, SecurityAuditRecord

logger = logging.getLogger("security.audit")


class SecurityAuditLogger:
    """
    Thread-safe security audit trail logger with automatic secret scrubbing.
    """

    SENSITIVE_KEYWORDS = {
        "password",
        "secret",
        "token",
        "access_token",
        "private_key",
        "jwt",
        "auth_header",
    }

    def __init__(self, max_records: int = 1000):
        self._records: deque = deque(maxlen=max_records)
        self._lock = Lock()

    @staticmethod
    def _sanitize_details(details: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Scrub any sensitive fields from details before logging."""
        if not details:
            return {}
        clean = {}
        for k, v in details.items():
            if any(sens in k.lower() for sens in SecurityAuditLogger.SENSITIVE_KEYWORDS):
                clean[k] = "[REDACTED]"
            elif isinstance(v, dict):
                clean[k] = SecurityAuditLogger._sanitize_details(v)
            else:
                clean[k] = v
        return clean

    def log_event(
        self,
        action: SecurityAuditAction,
        actor: str,
        role: Optional[str] = None,
        resource: Optional[str] = None,
        status: str = "SUCCESS",
        client_ip: Optional[str] = None,
        correlation_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        error_message: Optional[str] = None,
    ) -> SecurityAuditRecord:
        """Record an auditable security event."""
        record = SecurityAuditRecord(
            event_id=f"sec_audit_{uuid.uuid4().hex[:12]}",
            timestamp=datetime.now(timezone.utc),
            actor=actor,
            role=role,
            action=action,
            resource=resource,
            status=status,
            client_ip=client_ip,
            correlation_id=correlation_id,
            details=self._sanitize_details(details),
            error_message=error_message,
        )

        with self._lock:
            self._records.appendleft(record)

        log_msg = f"[{record.action.value}] actor='{record.actor}' status='{record.status}' resource='{record.resource or ''}'"
        if error_message:
            log_msg += f" error='{error_message}'"
        logger.info(log_msg)

        return record

    def list_events(
        self,
        action: Optional[SecurityAuditAction] = None,
        actor: Optional[str] = None,
        limit: int = 100,
    ) -> List[SecurityAuditRecord]:
        """Retrieve recent security audit events with optional filtering."""
        with self._lock:
            results = []
            for r in self._records:
                if action and r.action != action:
                    continue
                if actor and r.actor != actor:
                    continue
                results.append(r)
                if len(results) >= limit:
                    break
            return results

    def clear(self) -> None:
        """Clear audit history (used in tests)."""
        with self._lock:
            self._records.clear()


_global_audit_logger: Optional[SecurityAuditLogger] = None


def get_security_audit_logger() -> SecurityAuditLogger:
    global _global_audit_logger
    if _global_audit_logger is None:
        _global_audit_logger = SecurityAuditLogger()
    return _global_audit_logger
