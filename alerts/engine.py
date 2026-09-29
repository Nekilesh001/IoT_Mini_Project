"""
Alert Engine coordinating rule evaluation, alert deduplication, cooldown, hysteresis, and lifecycle persistence.
"""

from datetime import datetime, timezone
import logging
from typing import Any, Callable, Dict, List, Optional

from edge.models import CanonicalTelemetry
from alerts.models import AlertRecord
from alerts.repository import AlertRepository
from alerts.rules import AlertRule, AlertSeverity, AlertStatus, RuleEvaluator, get_default_rules

logger = logging.getLogger(__name__)


class AlertEngine:
    """
    Evaluates streaming CanonicalTelemetry packets against alert rules.
    Manages active alert deduplication, cooldown timers, hysteresis resolution, and persistence.
    """

    def __init__(
        self,
        repository: AlertRepository,
        rules: Optional[List[AlertRule]] = None,
    ):
        self._repository = repository
        self._rules = rules if rules is not None else get_default_rules()
        self._evaluator = RuleEvaluator(self._rules)
        # Track last trigger timestamp for cooldown: (machine_id, rule_id) -> float timestamp
        self._last_trigger_times: Dict[str, float] = {}
        # Callback listeners for real-time alert event delivery
        self._listeners: List[Callable[[Dict[str, Any]], None]] = []
        # Restore cooldown state from currently active alerts to prevent
        # duplicate alert creation after a worker restart.
        self._restore_cooldowns_from_db()

    @property
    def repository(self) -> AlertRepository:
        return self._repository

    @property
    def rules(self) -> List[AlertRule]:
        return self._rules

    def add_listener(self, listener: Callable[[Dict[str, Any]], None]) -> None:
        self._listeners.append(listener)

    def remove_listener(self, listener: Callable[[Dict[str, Any]], None]) -> None:
        if listener in self._listeners:
            self._listeners.remove(listener)

    def _restore_cooldowns_from_db(self) -> None:
        """
        Repopulate in-memory cooldown timestamps from currently OPEN alerts in the DB.
        Called once at startup to prevent duplicate alerts after a worker restart.
        """
        try:
            active_alerts = self._repository.get_all_active_alerts()
            restored = 0
            for alert in active_alerts:
                alert_key = f"{alert.machine_id}:{alert.rule_id}"
                if alert.triggered_at:
                    try:
                        if isinstance(alert.triggered_at, datetime):
                            ref_ts = alert.triggered_at.timestamp()
                        else:
                            ref_ts = datetime.fromisoformat(
                                str(alert.triggered_at).replace("Z", "+00:00")
                            ).timestamp()
                    except Exception:
                        ref_ts = datetime.now(timezone.utc).timestamp()
                else:
                    ref_ts = datetime.now(timezone.utc).timestamp()
                self._last_trigger_times[alert_key] = ref_ts
                restored += 1
            if restored:
                logger.info(
                    f"[AlertEngine] Restored cooldown state for {restored} active alert(s) from DB."
                )
        except Exception as ex:
            logger.warning(f"[AlertEngine] Could not restore cooldowns from DB: {ex}")

    def _notify_listeners(self, event_type: str, alert: AlertRecord) -> None:
        payload = {
            "event_type": event_type,  # 'ALERT_CREATED', 'ALERT_UPDATED', 'ALERT_RESOLVED'
            "alert": alert.to_dict(),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        for listener in list(self._listeners):
            try:
                listener(payload)
            except Exception as e:
                logger.error(f"Error in alert listener: {e}")

    def process_telemetry(self, telemetry: CanonicalTelemetry) -> List[AlertRecord]:
        """
        Evaluates canonical telemetry against all rules.
        Creates new alerts or updates/resolves existing active alerts.
        """
        eval_results = self._evaluator.evaluate_telemetry(telemetry)
        affected_alerts: List[AlertRecord] = []
        try:
            event_dt = datetime.fromisoformat(telemetry.event_time.replace("Z", "+00:00"))
            now_ts = event_dt.timestamp()
        except Exception:
            event_dt = datetime.now(timezone.utc)
            now_ts = event_dt.timestamp()

        machine_type = str(telemetry.machine_type)

        for rule, is_triggered, is_cleared, measurements in eval_results:
            alert_key = f"{telemetry.machine_id}:{rule.rule_id}"
            active_alert = self._repository.get_active_alert_by_key(telemetry.machine_id, rule.rule_id)

            if is_triggered:
                if active_alert:
                    # Condition continues: update current measurements and occurrence count
                    updated = self._repository.update_active_alert_occurrence(
                        active_alert.alert_id,
                        current_measurements=measurements,
                        timestamp=event_dt,
                    )
                    if updated:
                        affected_alerts.append(updated)
                        # Rate-limit listener notifications by cooldown
                        last_trig = self._last_trigger_times.get(alert_key, 0.0)
                        if (now_ts - last_trig) >= rule.cooldown_seconds:
                            self._last_trigger_times[alert_key] = now_ts
                            self._notify_listeners("ALERT_UPDATED", updated)
                else:
                    # New alert violation: create OPEN alert
                    self._last_trigger_times[alert_key] = now_ts
                    new_alert = self._repository.create_alert(
                        rule_id=rule.rule_id,
                        machine_id=telemetry.machine_id,
                        machine_type=machine_type,
                        alert_code=rule.alert_code,
                        severity=rule.severity,
                        title=rule.title,
                        description=rule.description,
                        triggering_measurements=measurements,
                        triggered_at=event_dt,
                    )
                    affected_alerts.append(new_alert)
                    self._notify_listeners("ALERT_CREATED", new_alert)
                    logger.info(
                        f"🚨 [{rule.severity.value}] Alert '{rule.rule_id}' created for {telemetry.machine_id}: {measurements}"
                    )


            elif is_cleared and active_alert:
                # Condition returned within normal bounds (hysteresis clear)
                resolved = self._repository.resolve_alert(
                    active_alert.alert_id,
                    resolution_notes=f"Telemetry normalized ({measurements}) below clear threshold.",
                )
                if resolved:
                    affected_alerts.append(resolved)
                    self._notify_listeners("ALERT_RESOLVED", resolved)
                    logger.info(
                        f"✅ Alert '{rule.rule_id}' auto-resolved for {telemetry.machine_id} (recovered)."
                    )

        return affected_alerts
