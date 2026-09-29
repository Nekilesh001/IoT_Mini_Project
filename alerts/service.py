"""
Alert Service for API query orchestration and lifecycle modifications.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from alerts.models import AlertRecord
from alerts.repository import AlertRepository


class AlertService:
    """
    Business logic layer for alert queries, acknowledgments, resolutions, and operational metrics.
    """

    def __init__(self, repository: AlertRepository):
        self._repository = repository

    def list_alerts(
        self,
        machine_id: Optional[str] = None,
        severity: Optional[str] = None,
        status: Optional[str] = None,
        start: Optional[datetime] = None,
        end: Optional[datetime] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        records = self._repository.list_alerts(
            machine_id=machine_id,
            severity=severity,
            status=status,
            start=start,
            end=end,
            limit=limit,
        )
        return [r.to_dict() for r in records]

    def list_active_alerts(self, limit: int = 200) -> List[Dict[str, Any]]:
        records = self._repository.list_active_alerts(limit=limit)
        return [r.to_dict() for r in records]

    def get_alert_by_id(self, alert_id: str) -> Optional[Dict[str, Any]]:
        record = self._repository.get_by_id(alert_id)
        return record.to_dict() if record else None

    def list_machine_alerts(self, machine_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        records = self._repository.list_machine_alerts(machine_id, limit=limit)
        return [r.to_dict() for r in records]

    def acknowledge_alert(self, alert_id: str, acknowledged_by: str = "operator") -> Optional[Dict[str, Any]]:
        record = self._repository.acknowledge_alert(alert_id, acknowledged_by=acknowledged_by)
        return record.to_dict() if record else None

    def resolve_alert(self, alert_id: str, resolution_notes: str = "Resolved by operator") -> Optional[Dict[str, Any]]:
        record = self._repository.resolve_alert(alert_id, resolution_notes=resolution_notes)
        return record.to_dict() if record else None

    def get_alert_summary(self) -> Dict[str, Any]:
        return self._repository.get_summary()
