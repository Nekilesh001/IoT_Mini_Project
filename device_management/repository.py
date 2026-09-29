"""
SQLAlchemy ORM models and repository for Device Management persistence.
Supports both SQLite and PostgreSQL with JSON/JSONB fields and atomic operations.
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
import uuid

from sqlalchemy import (
    Column,
    String,
    BigInteger,
    Integer,
    DateTime,
    JSON,
    Index,
    Enum as SQLEnum,
    desc,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Session, sessionmaker

from storage.database import Base
from device_management.models import (
    ConnectivityState,
    ManagementState,
    JobType,
    JobStatus,
    AuditAction,
    AuditSource,
    DeviceShadowRecord,
    FleetDeviceRecord,
    ManagementJobRecord,
    JobAttemptRecord,
    ManagementAuditRecord,
    FleetSummary,
)


class DeviceShadowModel(Base):
    """ORM table storing device twin desired, reported, and version state."""
    __tablename__ = "device_shadow"

    device_id = Column(String(64), primary_key=True, index=True)
    desired_state = Column(JSON().with_variant(JSONB, "postgresql"), nullable=False, default=dict)
    reported_state = Column(JSON().with_variant(JSONB, "postgresql"), nullable=False, default=dict)
    version = Column(BigInteger, nullable=False, default=1)
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        index=True,
    )

    def to_record(self) -> DeviceShadowRecord:
        desired = self.desired_state or {}
        reported = self.reported_state or {}
        delta = {k: v for k, v in desired.items() if reported.get(k) != v}
        return DeviceShadowRecord(
            device_id=self.device_id,
            desired_state=desired,
            reported_state=reported,
            delta=delta,
            version=self.version,
            is_sync_pending=len(delta) > 0,
            updated_at=self.updated_at,
        )


class FleetDeviceModel(Base):
    """ORM table storing fleet device metadata, connectivity, and management status."""
    __tablename__ = "fleet_devices"

    machine_id = Column(String(64), primary_key=True, index=True)
    machine_type = Column(String(64), nullable=False, index=True)
    protocol = Column(String(32), nullable=False, index=True)
    connectivity = Column(String(32), nullable=False, default=ConnectivityState.UNKNOWN.value, index=True)
    management_state = Column(String(32), nullable=False, default=ManagementState.ACTIVE.value, index=True)
    software_version = Column(String(32), nullable=False, default="1.0.0")
    firmware_version = Column(String(32), nullable=False, default="v1.0.0")
    config_version = Column(String(32), nullable=False, default="1.0.0")
    metadata_json = Column(JSON().with_variant(JSONB, "postgresql"), nullable=False, default=dict)
    last_seen = Column(DateTime(timezone=True), nullable=True, index=True)
    registered_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    def to_record(self) -> FleetDeviceRecord:
        return FleetDeviceRecord(
            machine_id=self.machine_id,
            machine_type=self.machine_type,
            protocol=self.protocol,
            connectivity=ConnectivityState(self.connectivity),
            management_state=ManagementState(self.management_state),
            software_version=self.software_version,
            firmware_version=self.firmware_version,
            config_version=self.config_version,
            metadata=self.metadata_json or {},
            last_seen=self.last_seen,
            registered_at=self.registered_at,
            updated_at=self.updated_at,
        )


class ManagementJobModel(Base):
    """ORM table storing administrative and configuration jobs."""
    __tablename__ = "management_jobs"

    job_id = Column(String(64), primary_key=True, index=True)
    machine_id = Column(String(64), nullable=False, index=True)
    job_type = Column(String(32), nullable=False, index=True)
    payload = Column(JSON().with_variant(JSONB, "postgresql"), nullable=False, default=dict)
    status = Column(String(32), nullable=False, default=JobStatus.PENDING.value, index=True)
    attempt = Column(Integer, nullable=False, default=0)
    max_attempts = Column(Integer, nullable=False, default=3)
    error = Column(String(512), nullable=True)
    result = Column(JSON().with_variant(JSONB, "postgresql"), nullable=True)
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        index=True,
    )
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        Index("ix_mgmt_jobs_machine_status", "machine_id", "status"),
        Index("ix_mgmt_jobs_created_desc", created_at.desc()),
    )

    def to_record(self) -> ManagementJobRecord:
        return ManagementJobRecord(
            job_id=self.job_id,
            machine_id=self.machine_id,
            job_type=JobType(self.job_type),
            payload=self.payload or {},
            status=JobStatus(self.status),
            attempt=self.attempt,
            max_attempts=self.max_attempts,
            error=self.error,
            result=self.result,
            created_at=self.created_at,
            started_at=self.started_at,
            completed_at=self.completed_at,
        )


class JobAttemptModel(Base):
    """ORM table storing individual retry and execution attempts."""
    __tablename__ = "job_attempts"

    attempt_id = Column(String(64), primary_key=True, index=True)
    job_id = Column(String(64), nullable=False, index=True)
    attempt_number = Column(Integer, nullable=False)
    status = Column(String(32), nullable=False, index=True)
    error = Column(String(512), nullable=True)
    result = Column(JSON().with_variant(JSONB, "postgresql"), nullable=True)
    started_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    completed_at = Column(DateTime(timezone=True), nullable=True)

    def to_record(self) -> JobAttemptRecord:
        return JobAttemptRecord(
            attempt_id=self.attempt_id,
            job_id=self.job_id,
            attempt_number=self.attempt_number,
            status=JobStatus(self.status),
            error=self.error,
            result=self.result,
            started_at=self.started_at,
            completed_at=self.completed_at,
        )


class ManagementAuditModel(Base):
    """ORM table storing complete audit trail of management activities."""
    __tablename__ = "management_audit"

    event_id = Column(String(64), primary_key=True, index=True)
    machine_id = Column(String(64), nullable=False, index=True)
    action = Column(String(64), nullable=False, index=True)
    actor = Column(String(32), nullable=False, default=AuditSource.LOCAL_SERVICE.value)
    timestamp = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        index=True,
    )
    before_state = Column(JSON().with_variant(JSONB, "postgresql"), nullable=True)
    after_state = Column(JSON().with_variant(JSONB, "postgresql"), nullable=True)
    result = Column(JSON().with_variant(JSONB, "postgresql"), nullable=True)
    error = Column(String(512), nullable=True)

    __table_args__ = (
        Index("ix_audit_machine_time", "machine_id", "timestamp"),
        Index("ix_audit_time_desc", timestamp.desc()),
    )

    def to_record(self) -> ManagementAuditRecord:
        return ManagementAuditRecord(
            event_id=self.event_id,
            machine_id=self.machine_id,
            action=AuditAction(self.action),
            actor=AuditSource(self.actor),
            timestamp=self.timestamp,
            before_state=self.before_state,
            after_state=self.after_state,
            result=self.result,
            error=self.error,
        )


class DeviceManagementRepository:
    """
    Data Access Object providing CRUD operations for device management domain tables.
    """

    def __init__(self, session_factory: sessionmaker):
        self._session_factory = session_factory

    # -------------------------------------------------------------------------
    # Shadow Repository Methods
    # -------------------------------------------------------------------------
    def get_shadow(self, device_id: str) -> Optional[DeviceShadowRecord]:
        with self._session_factory() as session:
            model = session.query(DeviceShadowModel).filter(DeviceShadowModel.device_id == device_id).first()
            return model.to_record() if model else None

    def upsert_shadow(
        self,
        device_id: str,
        desired_state: Optional[Dict[str, Any]] = None,
        reported_state: Optional[Dict[str, Any]] = None,
        version: Optional[int] = None,
    ) -> DeviceShadowRecord:
        with self._session_factory() as session:
            model = session.query(DeviceShadowModel).filter(DeviceShadowModel.device_id == device_id).first()
            now = datetime.now(timezone.utc)
            if not model:
                model = DeviceShadowModel(
                    device_id=device_id,
                    desired_state=desired_state or {},
                    reported_state=reported_state or {},
                    version=version if version is not None else 1,
                    updated_at=now,
                )
                session.add(model)
            else:
                if desired_state is not None:
                    model.desired_state = desired_state
                if reported_state is not None:
                    model.reported_state = reported_state
                if version is not None:
                    model.version = version
                model.updated_at = now
            session.commit()
            session.refresh(model)
            return model.to_record()

    def list_all_shadows(self) -> List[DeviceShadowRecord]:
        with self._session_factory() as session:
            models = session.query(DeviceShadowModel).all()
            return [m.to_record() for m in models]

    # -------------------------------------------------------------------------
    # Fleet Repository Methods
    # -------------------------------------------------------------------------
    def register_or_update_device(self, record: FleetDeviceRecord) -> FleetDeviceRecord:
        with self._session_factory() as session:
            model = session.query(FleetDeviceModel).filter(FleetDeviceModel.machine_id == record.machine_id).first()
            now = datetime.now(timezone.utc)
            if not model:
                model = FleetDeviceModel(
                    machine_id=record.machine_id,
                    machine_type=record.machine_type,
                    protocol=record.protocol,
                    connectivity=record.connectivity.value,
                    management_state=record.management_state.value,
                    software_version=record.software_version,
                    firmware_version=record.firmware_version,
                    config_version=record.config_version,
                    metadata_json=record.metadata,
                    last_seen=record.last_seen,
                    registered_at=record.registered_at,
                    updated_at=now,
                )
                session.add(model)
            else:
                model.machine_type = record.machine_type
                model.protocol = record.protocol
                model.connectivity = record.connectivity.value
                model.management_state = record.management_state.value
                model.software_version = record.software_version
                model.firmware_version = record.firmware_version
                model.config_version = record.config_version
                model.metadata_json = record.metadata
                if record.last_seen:
                    model.last_seen = record.last_seen
                model.updated_at = now
            session.commit()
            session.refresh(model)
            return model.to_record()

    def get_device(self, machine_id: str) -> Optional[FleetDeviceRecord]:
        with self._session_factory() as session:
            model = session.query(FleetDeviceModel).filter(FleetDeviceModel.machine_id == machine_id).first()
            return model.to_record() if model else None

    def list_devices(
        self,
        connectivity: Optional[ConnectivityState] = None,
        management_state: Optional[ManagementState] = None,
    ) -> List[FleetDeviceRecord]:
        with self._session_factory() as session:
            query = session.query(FleetDeviceModel)
            if connectivity:
                query = query.filter(FleetDeviceModel.connectivity == connectivity.value)
            if management_state:
                query = query.filter(FleetDeviceModel.management_state == management_state.value)
            models = query.order_by(FleetDeviceModel.machine_id).all()
            return [m.to_record() for m in models]

    def update_connectivity(
        self,
        machine_id: str,
        connectivity: ConnectivityState,
        last_seen: Optional[datetime] = None,
    ) -> Optional[FleetDeviceRecord]:
        with self._session_factory() as session:
            model = session.query(FleetDeviceModel).filter(FleetDeviceModel.machine_id == machine_id).first()
            if not model:
                return None
            model.connectivity = connectivity.value
            model.last_seen = last_seen or datetime.now(timezone.utc)
            model.updated_at = datetime.now(timezone.utc)
            session.commit()
            session.refresh(model)
            return model.to_record()

    def get_fleet_summary(self) -> FleetSummary:
        with self._session_factory() as session:
            devices = session.query(FleetDeviceModel).all()
            total = len(devices)
            online = sum(1 for d in devices if d.connectivity == ConnectivityState.ONLINE.value)
            offline = sum(1 for d in devices if d.connectivity == ConnectivityState.OFFLINE.value)
            degraded = sum(1 for d in devices if d.connectivity == ConnectivityState.DEGRADED.value)

            by_type: Dict[str, int] = {}
            by_proto: Dict[str, int] = {}
            for d in devices:
                by_type[d.machine_type] = by_type.get(d.machine_type, 0) + 1
                by_proto[d.protocol] = by_proto.get(d.protocol, 0) + 1

            active_jobs = session.query(ManagementJobModel).filter(
                ManagementJobModel.status.in_([JobStatus.PENDING.value, JobStatus.IN_PROGRESS.value])
            ).count()

            shadows = session.query(DeviceShadowModel).all()
            pending_sync = 0
            for s in shadows:
                des = s.desired_state or {}
                rep = s.reported_state or {}
                if any(k not in rep or rep[k] != v for k, v in des.items()):
                    pending_sync += 1

            return FleetSummary(
                total_machines=total,
                online_count=online,
                offline_count=offline,
                degraded_count=degraded,
                active_jobs_count=active_jobs,
                pending_sync_count=pending_sync,
                machines_by_type=by_type,
                machines_by_protocol=by_proto,
            )

    # -------------------------------------------------------------------------
    # Job Repository Methods
    # -------------------------------------------------------------------------
    def create_job(self, job: ManagementJobRecord) -> ManagementJobRecord:
        with self._session_factory() as session:
            model = ManagementJobModel(
                job_id=job.job_id,
                machine_id=job.machine_id,
                job_type=job.job_type.value,
                payload=job.payload,
                status=job.status.value,
                attempt=job.attempt,
                max_attempts=job.max_attempts,
                error=job.error,
                result=job.result,
                created_at=job.created_at,
                started_at=job.started_at,
                completed_at=job.completed_at,
            )
            session.add(model)
            session.commit()
            session.refresh(model)
            return model.to_record()

    def get_job(self, job_id: str) -> Optional[ManagementJobRecord]:
        with self._session_factory() as session:
            model = session.query(ManagementJobModel).filter(ManagementJobModel.job_id == job_id).first()
            return model.to_record() if model else None

    def update_job(self, job: ManagementJobRecord) -> ManagementJobRecord:
        with self._session_factory() as session:
            model = session.query(ManagementJobModel).filter(ManagementJobModel.job_id == job.job_id).first()
            if not model:
                raise ValueError(f"Job not found: {job.job_id}")
            model.status = job.status.value
            model.attempt = job.attempt
            model.max_attempts = job.max_attempts
            model.error = job.error
            model.result = job.result
            model.started_at = job.started_at
            model.completed_at = job.completed_at
            session.commit()
            session.refresh(model)
            return model.to_record()

    def list_jobs(
        self,
        machine_id: Optional[str] = None,
        status: Optional[JobStatus] = None,
        limit: int = 100,
    ) -> List[ManagementJobRecord]:
        with self._session_factory() as session:
            query = session.query(ManagementJobModel)
            if machine_id:
                query = query.filter(ManagementJobModel.machine_id == machine_id)
            if status:
                query = query.filter(ManagementJobModel.status == status.value)
            models = query.order_by(desc(ManagementJobModel.created_at)).limit(limit).all()
            return [m.to_record() for m in models]

    def record_attempt(self, attempt: JobAttemptRecord) -> JobAttemptRecord:
        with self._session_factory() as session:
            model = JobAttemptModel(
                attempt_id=attempt.attempt_id,
                job_id=attempt.job_id,
                attempt_number=attempt.attempt_number,
                status=attempt.status.value,
                error=attempt.error,
                result=attempt.result,
                started_at=attempt.started_at,
                completed_at=attempt.completed_at,
            )
            session.add(model)
            session.commit()
            session.refresh(model)
            return model.to_record()

    def get_job_attempts(self, job_id: str) -> List[JobAttemptRecord]:
        with self._session_factory() as session:
            models = (
                session.query(JobAttemptModel)
                .filter(JobAttemptModel.job_id == job_id)
                .order_by(JobAttemptModel.attempt_number)
                .all()
            )
            return [m.to_record() for m in models]

    # -------------------------------------------------------------------------
    # Audit Repository Methods
    # -------------------------------------------------------------------------
    def record_audit(self, audit: ManagementAuditRecord) -> ManagementAuditRecord:
        with self._session_factory() as session:
            model = ManagementAuditModel(
                event_id=audit.event_id,
                machine_id=audit.machine_id,
                action=audit.action.value,
                actor=audit.actor.value,
                timestamp=audit.timestamp,
                before_state=audit.before_state,
                after_state=audit.after_state,
                result=audit.result,
                error=audit.error,
            )
            session.add(model)
            session.commit()
            session.refresh(model)
            return model.to_record()

    def list_audit_events(
        self,
        machine_id: Optional[str] = None,
        action: Optional[AuditAction] = None,
        limit: int = 100,
    ) -> List[ManagementAuditRecord]:
        with self._session_factory() as session:
            query = session.query(ManagementAuditModel)
            if machine_id:
                query = query.filter(ManagementAuditModel.machine_id == machine_id)
            if action:
                query = query.filter(ManagementAuditModel.action == action.value)
            models = query.order_by(desc(ManagementAuditModel.timestamp)).limit(limit).all()
            return [m.to_record() for m in models]
