"""
Repository abstraction for PostgreSQL / SQLite Alert persistence and lifecycle queries.
"""

from datetime import datetime, timezone
import logging
from typing import Any, Dict, List, Optional
from sqlalchemy import desc, func, and_, or_
from sqlalchemy.orm import Session, sessionmaker

from alerts.models import AlertRecord
from alerts.rules import AlertSeverity, AlertStatus

logger = logging.getLogger(__name__)


class AlertRepository:
    """
    Data access layer for operational alerts.
    """

    def __init__(self, session_factory: sessionmaker):
        self._session_factory = session_factory

    def create_alert(
        self,
        rule_id: str,
        machine_id: str,
        machine_type: str,
        alert_code: str,
        severity: AlertSeverity,
        title: str,
        description: str,
        triggering_measurements: Dict[str, Any],
        triggered_at: Optional[datetime] = None,
    ) -> AlertRecord:
        """Creates a new OPEN alert record."""
        now = triggered_at or datetime.now(timezone.utc)
        record = AlertRecord(
            rule_id=rule_id,
            machine_id=machine_id,
            machine_type=machine_type,
            alert_code=alert_code,
            severity=severity.value if hasattr(severity, 'value') else str(severity),
            title=title,
            description=description,
            status=AlertStatus.OPEN.value,
            triggered_at=now,
            triggering_measurements=triggering_measurements,
            current_measurements=triggering_measurements,
            occurrence_count=1,
            last_occurrence_at=now,
        )

        session: Session = self._session_factory()
        try:
            session.add(record)
            session.commit()
            session.refresh(record)
            return record
        except Exception as e:
            session.rollback()
            logger.error(f"Failed to create alert for {machine_id} ({rule_id}): {e}")
            raise
        finally:
            session.close()

    def save_alert(self, record: AlertRecord) -> AlertRecord:
        """Persists an instantiated AlertRecord."""
        session: Session = self._session_factory()
        try:
            session.merge(record)
            session.commit()
            return record
        except Exception as e:
            session.rollback()
            logger.error(f"Failed to save alert {record.alert_id}: {e}")
            raise
        finally:
            session.close()

    def get_by_id(self, alert_id: str) -> Optional[AlertRecord]:
        session: Session = self._session_factory()
        try:
            return session.query(AlertRecord).filter(AlertRecord.alert_id == alert_id).first()
        finally:
            session.close()

    def get_alert_by_id(self, alert_id: str) -> Optional[AlertRecord]:
        return self.get_by_id(alert_id)

    def get_active_alert_by_key(self, machine_id: str, rule_id: str) -> Optional[AlertRecord]:
        """Finds active (OPEN or ACKNOWLEDGED) alert for a machine and rule."""
        session: Session = self._session_factory()
        try:
            return session.query(AlertRecord).filter(
                AlertRecord.machine_id == machine_id,
                AlertRecord.rule_id == rule_id,
                AlertRecord.status.in_([AlertStatus.OPEN.value, AlertStatus.ACKNOWLEDGED.value])
            ).order_by(desc(AlertRecord.triggered_at)).first()
        finally:
            session.close()

    def update_active_alert_occurrence(
        self,
        alert_id: str,
        current_measurements: Dict[str, Any],
        timestamp: Optional[datetime] = None,
    ) -> Optional[AlertRecord]:
        """Increments occurrence count and updates current measurements for an active alert."""
        session: Session = self._session_factory()
        try:
            record = session.query(AlertRecord).filter(AlertRecord.alert_id == alert_id).first()
            if record:
                record.occurrence_count += 1
                record.current_measurements = current_measurements
                record.last_occurrence_at = timestamp or datetime.now(timezone.utc)
                session.commit()
                session.refresh(record)
            return record
        except Exception as e:
            session.rollback()
            logger.error(f"Failed to update alert {alert_id}: {e}")
            return None
        finally:
            session.close()

    def acknowledge_alert(
        self,
        alert_id: str,
        acknowledged_by: Optional[str] = "operator",
    ) -> Optional[AlertRecord]:
        """Transitions an alert from OPEN -> ACKNOWLEDGED."""
        session: Session = self._session_factory()
        try:
            record = session.query(AlertRecord).filter(AlertRecord.alert_id == alert_id).first()
            if not record:
                return None
            if record.status == AlertStatus.RESOLVED.value:
                raise ValueError(f"Cannot acknowledge a resolved alert '{alert_id}'.")
            if record.status == AlertStatus.ACKNOWLEDGED.value:
                return record

            record.status = AlertStatus.ACKNOWLEDGED.value
            record.acknowledged_at = datetime.now(timezone.utc)
            record.acknowledged_by = acknowledged_by
            session.commit()
            session.refresh(record)
            return record
        except Exception as e:
            session.rollback()
            if isinstance(e, ValueError):
                raise
            logger.error(f"Failed to acknowledge alert {alert_id}: {e}")
            raise
        finally:
            session.close()

    def resolve_alert(
        self,
        alert_id: str,
        resolution_notes: Optional[str] = "Condition cleared automatically or by operator.",
        raise_if_already_resolved: bool = True,
    ) -> Optional[AlertRecord]:
        """Transitions an alert to RESOLVED."""
        session: Session = self._session_factory()
        try:
            record = session.query(AlertRecord).filter(AlertRecord.alert_id == alert_id).first()
            if not record:
                return None
            if record.status == AlertStatus.RESOLVED.value:
                if raise_if_already_resolved:
                    raise ValueError(f"Alert is already resolved: '{alert_id}'.")
                return record

            record.status = AlertStatus.RESOLVED.value
            record.resolved_at = datetime.now(timezone.utc)
            record.resolution_notes = resolution_notes
            session.commit()
            session.refresh(record)
            return record
        except Exception as e:
            session.rollback()
            if isinstance(e, ValueError):
                raise
            logger.error(f"Failed to resolve alert {alert_id}: {e}")
            raise
        finally:
            session.close()

    def list_alerts(
        self,
        machine_id: Optional[str] = None,
        severity: Optional[str] = None,
        status: Optional[str] = None,
        start: Optional[datetime] = None,
        end: Optional[datetime] = None,
        limit: int = 100,
    ) -> List[AlertRecord]:
        """Queries historical and active alerts with bounded filtering."""
        session: Session = self._session_factory()
        try:
            query = session.query(AlertRecord)
            if machine_id:
                query = query.filter(AlertRecord.machine_id == machine_id)
            if severity:
                query = query.filter(AlertRecord.severity == severity.upper())
            if status:
                query = query.filter(AlertRecord.status == status.upper())
            if start:
                query = query.filter(AlertRecord.triggered_at >= start)
            if end:
                query = query.filter(AlertRecord.triggered_at <= end)

            query = query.order_by(desc(AlertRecord.triggered_at)).limit(min(limit, 1000))
            return query.all()
        finally:
            session.close()

    def list_active_alerts(self, limit: int = 200) -> List[AlertRecord]:
        """Lists all un-resolved (OPEN or ACKNOWLEDGED) alerts."""
        session: Session = self._session_factory()
        try:
            return session.query(AlertRecord).filter(
                AlertRecord.status.in_([AlertStatus.OPEN.value, AlertStatus.ACKNOWLEDGED.value])
            ).order_by(desc(AlertRecord.triggered_at)).limit(limit).all()
        finally:
            session.close()

    def list_machine_alerts(self, machine_id: str, limit: int = 50) -> List[AlertRecord]:
        """Lists active and historical alerts for a specific machine."""
        return self.list_alerts(machine_id=machine_id, limit=limit)

    def get_all_active_alerts(self) -> List[AlertRecord]:
        """Returns all currently OPEN or ACKNOWLEDGED alerts (unbounded for cooldown restore)."""
        return self.list_active_alerts(limit=10000)

    def get_summary(self) -> Dict[str, Any]:
        """Calculates aggregated factory alert KPIs."""
        session: Session = self._session_factory()
        try:
            active_alerts = session.query(AlertRecord).filter(
                AlertRecord.status.in_([AlertStatus.OPEN.value, AlertStatus.ACKNOWLEDGED.value])
            ).all()

            total_active = len(active_alerts)
            open_count = sum(1 for a in active_alerts if a.status == AlertStatus.OPEN.value)
            ack_count = sum(1 for a in active_alerts if a.status == AlertStatus.ACKNOWLEDGED.value)
            crit_count = sum(1 for a in active_alerts if a.severity == AlertSeverity.CRITICAL.value)
            warn_count = sum(1 for a in active_alerts if a.severity == AlertSeverity.WARNING.value)
            info_count = sum(1 for a in active_alerts if a.severity == AlertSeverity.INFO.value)

            active_machine_ids = list(set(a.machine_id for a in active_alerts))

            # Total historical alerts count
            total_history = session.query(func.count(AlertRecord.alert_id)).scalar() or 0

            return {
                "active_total": total_active,
                "open_total": open_count,
                "acknowledged_total": ack_count,
                "critical_count": crit_count,
                "warning_count": warn_count,
                "info_count": info_count,
                "active_machines_count": len(active_machine_ids),
                "machines_with_active_alerts": len(active_machine_ids),
                "active_machines": active_machine_ids,
                "total_historical_alerts": total_history,
                "recent_alert_count": total_history,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        finally:
            session.close()
