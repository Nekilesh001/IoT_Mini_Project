"""
Device Shadow State logic, versioning, optimistic concurrency, and delta computation.
"""

from copy import deepcopy
from datetime import datetime, timezone
from typing import Any, Dict, Optional, Tuple
from device_management.models import DeviceShadowRecord


class VersionConflictError(Exception):
    """Raised when an update specifies an expected version that does not match the current state."""
    pass


class DeviceShadowState:
    """
    Manages the desired, reported, and delta state of an individual device twin.
    Provides optimistic version validation and automatic delta recalculation.
    """

    def __init__(
        self,
        device_id: str,
        desired_state: Optional[Dict[str, Any]] = None,
        reported_state: Optional[Dict[str, Any]] = None,
        version: int = 1,
        updated_at: Optional[datetime] = None,
    ):
        self.device_id = device_id
        self.desired_state: Dict[str, Any] = deepcopy(desired_state or {})
        self.reported_state: Dict[str, Any] = deepcopy(reported_state or {})
        self.version = version
        self.updated_at = updated_at or datetime.now(timezone.utc)
        self.delta: Dict[str, Any] = {}
        self._recompute_delta()

    def _recompute_delta(self) -> None:
        """
        Compute delta = keys in desired that either don't exist in reported or have different values.
        """
        delta = {}
        for k, v in self.desired_state.items():
            if k not in self.reported_state or self.reported_state[k] != v:
                delta[k] = v
        self.delta = delta

    @property
    def is_sync_pending(self) -> bool:
        return len(self.delta) > 0

    def update_desired(
        self,
        new_desired: Dict[str, Any],
        expected_version: Optional[int] = None,
        merge: bool = True,
    ) -> "DeviceShadowState":
        """
        Update desired state and increment version.
        Optionally validates optimistic version concurrency.
        """
        if expected_version is not None and expected_version != self.version:
            raise VersionConflictError(
                f"Version conflict for device '{self.device_id}': expected version {expected_version}, but current version is {self.version}"
            )

        if merge:
            self.desired_state.update(deepcopy(new_desired))
        else:
            self.desired_state = deepcopy(new_desired)

        self.version += 1
        self.updated_at = datetime.now(timezone.utc)
        self._recompute_delta()
        return self

    def update_reported(
        self,
        new_reported: Dict[str, Any],
        merge: bool = True,
        increment_version: bool = False,
    ) -> "DeviceShadowState":
        """
        Update reported state received from the device telemetry or state sync.
        """
        if merge:
            self.reported_state.update(deepcopy(new_reported))
        else:
            self.reported_state = deepcopy(new_reported)

        if increment_version:
            self.version += 1

        self.updated_at = datetime.now(timezone.utc)
        self._recompute_delta()
        return self

    def sync_reported_from_desired(self) -> "DeviceShadowState":
        """
        Simulate successful application of desired state into reported state.
        Clears the delta.
        """
        self.reported_state.update(deepcopy(self.desired_state))
        self.updated_at = datetime.now(timezone.utc)
        self._recompute_delta()
        return self

    def to_record(self) -> DeviceShadowRecord:
        return DeviceShadowRecord(
            device_id=self.device_id,
            desired_state=self.desired_state,
            reported_state=self.reported_state,
            delta=self.delta,
            version=self.version,
            is_sync_pending=self.is_sync_pending,
            updated_at=self.updated_at,
        )

    def to_dict(self) -> Dict[str, Any]:
        return self.to_record().model_dump(mode="json")

    @classmethod
    def from_record(cls, record: DeviceShadowRecord) -> "DeviceShadowState":
        instance = cls(
            device_id=record.device_id,
            desired_state=record.desired_state,
            reported_state=record.reported_state,
            version=record.version,
            updated_at=record.updated_at,
        )
        return instance
