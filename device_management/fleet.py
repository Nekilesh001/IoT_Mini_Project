"""
Fleet Manager.
Provides device registration, inventory querying, connectivity tracking, and fleet summary aggregations.
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
import uuid

from simulator.core.domain import MachineProfile
from device_management.backends.base import FleetBackend, AuditBackend
from device_management.models import (
    ConnectivityState,
    ManagementState,
    FleetDeviceRecord,
    FleetSummary,
    AuditAction,
    AuditSource,
    ManagementAuditRecord,
)


class FleetManager:
    """
    Business logic layer for fleet registry and lifecycle management.
    """

    def __init__(
        self,
        fleet_backend: FleetBackend,
        audit_backend: Optional[AuditBackend] = None,
    ):
        self._fleet_backend = fleet_backend
        self._audit_backend = audit_backend

    def register_machine_from_profile(
        self,
        profile: MachineProfile,
        connectivity: ConnectivityState = ConnectivityState.ONLINE,
        software_version: str = "1.0.0",
        firmware_version: str = "v1.0.0",
        config_version: str = "1.0.0",
        actor: AuditSource = AuditSource.SYSTEM,
    ) -> FleetDeviceRecord:
        """
        Register or update a factory machine using its existing MachineProfile.
        """
        protocol_val = profile.protocol_metadata.value if hasattr(profile, "protocol_metadata") else getattr(profile, "protocol", "MQTT")
        if hasattr(protocol_val, "value"):
            protocol_val = protocol_val.value

        m_type = profile.machine_type.value if hasattr(profile.machine_type, "value") else str(profile.machine_type)

        record = FleetDeviceRecord(
            machine_id=profile.machine_id,
            machine_type=m_type,
            protocol=protocol_val,
            connectivity=connectivity,
            management_state=ManagementState.ACTIVE,
            software_version=software_version,
            firmware_version=firmware_version,
            config_version=config_version,
            metadata={
                "plant_id": getattr(profile, "plant_id", "PLANT_01"),
                "line_id": getattr(profile, "line_id", "LINE_A"),
                "description": getattr(profile, "description", ""),
                "nominal_load": getattr(profile, "nominal_load", 70.0),
                "signals_count": len(getattr(profile, "signals", [])),
            },
            last_seen=datetime.now(timezone.utc),
            registered_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )

        saved = self._fleet_backend.register_device(record)

        if self._audit_backend:
            self._audit_backend.record_event(
                ManagementAuditRecord(
                    event_id=f"audit_{uuid.uuid4()}",
                    machine_id=profile.machine_id,
                    action=AuditAction.DEVICE_REGISTERED,
                    actor=actor,
                    timestamp=datetime.now(timezone.utc),
                    after_state=saved.model_dump(mode="json"),
                    result={"status": "REGISTERED", "machine_id": profile.machine_id},
                )
            )

        return saved

    def register_all_from_profiles(
        self,
        profiles: Dict[str, MachineProfile],
        actor: AuditSource = AuditSource.SYSTEM,
    ) -> List[FleetDeviceRecord]:
        """
        Bootstrap the entire 12-machine factory fleet from the simulator profiles.
        """
        records = []
        for profile in profiles.values():
            records.append(self.register_machine_from_profile(profile, actor=actor))
        return records

    def get_machine(self, machine_id: str) -> Optional[FleetDeviceRecord]:
        return self._fleet_backend.get_device(machine_id)

    def list_machines(
        self,
        connectivity: Optional[ConnectivityState] = None,
        management_state: Optional[ManagementState] = None,
    ) -> List[FleetDeviceRecord]:
        return self._fleet_backend.list_devices(
            connectivity=connectivity,
            management_state=management_state,
        )

    def update_connectivity(
        self,
        machine_id: str,
        connectivity: ConnectivityState,
        actor: AuditSource = AuditSource.SYSTEM,
    ) -> Optional[FleetDeviceRecord]:
        """
        Update connectivity state (e.g. ONLINE, OFFLINE, DEGRADED) and emit audit event.
        """
        saved = self._fleet_backend.update_connectivity(machine_id, connectivity)
        if saved and self._audit_backend:
            self._audit_backend.record_event(
                ManagementAuditRecord(
                    event_id=f"audit_{uuid.uuid4()}",
                    machine_id=machine_id,
                    action=AuditAction.CONNECTIVITY_CHANGED,
                    actor=actor,
                    timestamp=datetime.now(timezone.utc),
                    after_state={"connectivity": connectivity.value},
                    result={"status": "CONNECTIVITY_UPDATED", "machine_id": machine_id},
                )
            )
        return saved

    def update_device_metadata(
        self,
        machine_id: str,
        software_version: Optional[str] = None,
        firmware_version: Optional[str] = None,
        config_version: Optional[str] = None,
        management_state: Optional[ManagementState] = None,
        metadata_patch: Optional[Dict[str, Any]] = None,
        actor: AuditSource = AuditSource.LOCAL_UI,
    ) -> Optional[FleetDeviceRecord]:
        """
        Update machine versions, management lifecycle state, or custom metadata.
        """
        record = self._fleet_backend.get_device(machine_id)
        if not record:
            return None

        before_state = record.model_dump(mode="json")

        if software_version is not None:
            record.software_version = software_version
        if firmware_version is not None:
            record.firmware_version = firmware_version
        if config_version is not None:
            record.config_version = config_version
        if management_state is not None:
            record.management_state = management_state
        if metadata_patch:
            record.metadata.update(metadata_patch)

        record.updated_at = datetime.now(timezone.utc)
        saved = self._fleet_backend.register_device(record)

        if self._audit_backend:
            self._audit_backend.record_event(
                ManagementAuditRecord(
                    event_id=f"audit_{uuid.uuid4()}",
                    machine_id=machine_id,
                    action=AuditAction.DEVICE_UPDATED,
                    actor=actor,
                    timestamp=datetime.now(timezone.utc),
                    before_state=before_state,
                    after_state=saved.model_dump(mode="json"),
                    result={"status": "UPDATED"},
                )
            )

        return saved

    def get_fleet_summary(self) -> FleetSummary:
        return self._fleet_backend.get_summary()
