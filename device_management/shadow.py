"""
Device Shadow Manager.
Orchestrates desired/reported state queries, updates, delta notifications, and optimistic version checks.
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
import uuid

from device_management.backends.base import DeviceStateBackend, AuditBackend
from device_management.models import (
    DeviceShadowRecord,
    AuditAction,
    AuditSource,
    ManagementAuditRecord,
)
from device_management.state import DeviceShadowState, VersionConflictError


class DeviceShadowManager:
    """
    Business logic layer for digital twins / Device Shadows.
    """

    def __init__(
        self,
        state_backend: DeviceStateBackend,
        audit_backend: Optional[AuditBackend] = None,
    ):
        self._state_backend = state_backend
        self._audit_backend = audit_backend

    def get_shadow(self, device_id: str) -> DeviceShadowRecord:
        """
        Get or initialize the shadow record for a device.
        """
        record = self._state_backend.get_state(device_id)
        if not record:
            record = self._state_backend.update_desired(device_id, desired_state={})
        return record

    def update_desired_state(
        self,
        device_id: str,
        desired_state: Dict[str, Any],
        expected_version: Optional[int] = None,
        actor: AuditSource = AuditSource.LOCAL_UI,
    ) -> DeviceShadowRecord:
        """
        Set or patch desired state configuration.
        Increments shadow version and records an audit trail event.
        """
        before_record = self._state_backend.get_state(device_id)
        before_state = before_record.desired_state if before_record else {}

        record = self._state_backend.update_desired(
            device_id=device_id,
            desired_state=desired_state,
            expected_version=expected_version,
        )

        if self._audit_backend:
            self._audit_backend.record_event(
                ManagementAuditRecord(
                    event_id=f"audit_{uuid.uuid4()}",
                    machine_id=device_id,
                    action=AuditAction.SHADOW_DESIRED_UPDATED,
                    actor=actor,
                    timestamp=datetime.now(timezone.utc),
                    before_state={"desired": before_state},
                    after_state={"desired": record.desired_state, "version": record.version, "delta": record.delta},
                    result={"status": "UPDATED", "version": record.version},
                )
            )

        return record

    def update_reported_state(
        self,
        device_id: str,
        reported_state: Dict[str, Any],
        actor: AuditSource = AuditSource.SYSTEM,
    ) -> DeviceShadowRecord:
        """
        Update reported state received from live device telemetry or state response.
        """
        before_record = self._state_backend.get_state(device_id)
        before_state = before_record.reported_state if before_record else {}

        record = self._state_backend.update_reported(
            device_id=device_id,
            reported_state=reported_state,
        )

        if self._audit_backend:
            self._audit_backend.record_event(
                ManagementAuditRecord(
                    event_id=f"audit_{uuid.uuid4()}",
                    machine_id=device_id,
                    action=AuditAction.SHADOW_REPORTED_UPDATED,
                    actor=actor,
                    timestamp=datetime.now(timezone.utc),
                    before_state={"reported": before_state},
                    after_state={"reported": record.reported_state, "delta": record.delta},
                    result={"status": "REPORTED_UPDATED", "is_sync_pending": record.is_sync_pending},
                )
            )

        return record

    def sync_reported_from_desired(
        self,
        device_id: str,
        actor: AuditSource = AuditSource.LOCAL_SERVICE,
    ) -> DeviceShadowRecord:
        """
        Acknowledge synchronization: sets reported_state to desired_state, clearing the delta.
        """
        shadow = self.get_shadow(device_id)
        record = self._state_backend.update_reported(device_id, shadow.desired_state)

        if self._audit_backend:
            self._audit_backend.record_event(
                ManagementAuditRecord(
                    event_id=f"audit_{uuid.uuid4()}",
                    machine_id=device_id,
                    action=AuditAction.SHADOW_SYNCED,
                    actor=actor,
                    timestamp=datetime.now(timezone.utc),
                    before_state={"delta": shadow.delta},
                    after_state={"reported": record.reported_state, "delta": record.delta},
                    result={"status": "SYNCHRONIZED"},
                )
            )

        return record

    def list_all_shadows(self) -> List[DeviceShadowRecord]:
        return self._state_backend.list_all_states()
