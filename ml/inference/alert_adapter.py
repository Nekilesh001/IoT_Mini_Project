"""
ML-to-Alert Engine Adapter integrating ML Predictions into the Operational Alert Lifecycle.
"""

from datetime import datetime, timezone
import logging
from typing import List, Optional

from alerts.models import AlertRecord
from alerts.repository import AlertRepository
from alerts.rules import AlertSeverity, AlertStatus
from ml.inference.config import InferenceConfig
from ml.inference.models import AnomalyLabel, InferenceStatus
from ml.inference.result import MLInferenceResult

logger = logging.getLogger(__name__)


class MLAlertAdapter:
    """
    Evaluates ML inference outputs against predictive maintenance thresholds
    and manages operational alerts through the existing AlertRepository.
    """

    def __init__(
        self,
        alert_repository: AlertRepository,
        config: Optional[InferenceConfig] = None,
    ):
        self.alert_repo = alert_repository
        self.config = config or InferenceConfig()

    def process_inference_result(self, result: MLInferenceResult) -> List[AlertRecord]:
        """
        Processes an ML inference result and triggers or clears operational alerts.
        Returns any newly created or updated AlertRecords.
        """
        if result.status != InferenceStatus.READY:
            return []

        triggered_alerts: List[AlertRecord] = []
        m_id = result.machine_id
        m_type = result.machine_type
        if isinstance(result.event_time, str):
            try:
                now = datetime.fromisoformat(result.event_time.replace("Z", "+00:00"))
            except Exception:
                now = datetime.now(timezone.utc)
        elif isinstance(result.event_time, datetime):
            now = result.event_time
        else:
            now = datetime.now(timezone.utc)

        # 1. Anomaly Alert Evaluation
        rule_id_anom = "ML_ANOMALY_DETECTION"
        if result.anomaly_label == AnomalyLabel.ANOMALOUS or (
            result.anomaly_score is not None and result.anomaly_score >= self.config.anomaly_alert_threshold
        ):
            active = self.alert_repo.get_active_alert_by_key(m_id, rule_id_anom)
            if not active:
                alert = AlertRecord(
                    rule_id=rule_id_anom,
                    machine_id=m_id,
                    machine_type=m_type,
                    alert_code="ML-ANOM-01",
                    severity=AlertSeverity.WARNING.value,
                    title=f"ML Anomaly Detected: {m_id}",
                    description=(
                        f"Unsupervised Isolation Forest flagged anomalous operating condition "
                        f"(Anomaly Score: {result.anomaly_score:.3f}, Raw: {result.raw_anomaly_score:.3f})."
                    ),
                    status=AlertStatus.OPEN.value,
                    triggered_at=now,
                    triggering_measurements={
                        "source": "ML",
                        "anomaly_score": result.anomaly_score,
                        "raw_anomaly_score": result.raw_anomaly_score,
                        "model_version": result.anomaly_model_version,
                    },
                    current_measurements={
                        "anomaly_score": result.anomaly_score,
                        "predicted_rul_seconds": result.predicted_rul_seconds,
                    },
                )
                saved = self.alert_repo.save_alert(alert)
                triggered_alerts.append(saved)
                logger.info(f"Triggered ML Anomaly alert for {m_id}")
        else:
            # Auto-clear anomaly alert if condition returned to normal
            active = self.alert_repo.get_active_alert_by_key(m_id, rule_id_anom)
            if active and result.anomaly_score is not None and result.anomaly_score < (self.config.anomaly_alert_threshold - 0.1):
                self.alert_repo.resolve_alert(
                    active.alert_id,
                    resolution_notes="ML anomaly score returned to nominal baseline.",
                )

        # 2. Remaining Useful Life (RUL) Alert Evaluation
        rule_id_rul = "ML_PREDICTIVE_RUL_CRITICAL"
        if result.predicted_rul_seconds is not None:
            if result.predicted_rul_seconds <= self.config.rul_critical_threshold_seconds:
                active = self.alert_repo.get_active_alert_by_key(m_id, rule_id_rul)
                if not active:
                    alert = AlertRecord(
                        rule_id=rule_id_rul,
                        machine_id=m_id,
                        machine_type=m_type,
                        alert_code="ML-RUL-01",
                        severity=AlertSeverity.CRITICAL.value,
                        title=f"Critical RUL Horizon: {m_id}",
                        description=(
                            f"Predictive Maintenance Regressor estimated Remaining Useful Life below critical threshold "
                            f"({result.predicted_rul_seconds:.1f}s / {result.predicted_rul_minutes:.1f}m)."
                        ),
                        status=AlertStatus.OPEN.value,
                        triggered_at=now,
                        triggering_measurements={
                            "source": "ML",
                            "predicted_rul_seconds": result.predicted_rul_seconds,
                            "predicted_rul_minutes": result.predicted_rul_minutes,
                            "model_version": result.rul_model_version,
                        },
                        current_measurements={
                            "predicted_rul_seconds": result.predicted_rul_seconds,
                            "anomaly_score": result.anomaly_score,
                        },
                    )
                    saved = self.alert_repo.save_alert(alert)
                    triggered_alerts.append(saved)
                    logger.warning(f"Triggered Critical ML RUL alert for {m_id}")
            elif result.predicted_rul_seconds > (self.config.rul_critical_threshold_seconds + 300.0):
                # Auto-clear RUL critical alert if reset/recovered
                active = self.alert_repo.get_active_alert_by_key(m_id, rule_id_rul)
                if active:
                    self.alert_repo.resolve_alert(
                        active.alert_id,
                        resolution_notes="Predicted RUL recovered above critical threshold.",
                    )

        return triggered_alerts
