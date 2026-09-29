"""
Security Models and Enums.
Defines roles, permissions, authenticated user identity, JWT tokens, certificates, and security audit records.
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Set
from pydantic import BaseModel, Field


class Role(str, Enum):
    """Hierarchical user roles for Local-First RBAC."""
    VIEWER = "VIEWER"
    OPERATOR = "OPERATOR"
    MAINTAINER = "MAINTAINER"
    ADMIN = "ADMIN"


class Permission(str, Enum):
    """Granular permissions enforced at the API and service layers."""
    # Read permissions
    READ_TELEMETRY = "telemetry:read"
    READ_MACHINES = "machines:read"
    READ_ALERTS = "alerts:read"
    READ_ML = "ml:read"
    READ_SHADOW = "shadow:read"
    READ_FLEET = "fleet:read"
    READ_JOBS = "jobs:read"
    READ_SECURITY_AUDIT = "security:audit:read"
    READ_RESILIENCE = "resilience:read"

    # Operational permissions
    ACK_ALERTS = "alerts:ack"
    RESOLVE_ALERTS = "alerts:resolve"
    EXECUTE_COMMANDS = "commands:execute"
    UPDATE_SHADOW_DESIRED = "shadow:desired:update"
    SYNC_SHADOW = "shadow:sync"
    CANCEL_JOBS = "jobs:cancel"

    # Maintainer / Engineer permissions
    CREATE_CONFIG_JOBS = "jobs:config:create"
    CREATE_OTA_JOBS = "jobs:ota:create"
    UPDATE_DEVICE_METADATA = "fleet:metadata:update"
    INJECT_FAULT_SCENARIOS = "scenarios:inject"
    RUN_RESILIENCE_TESTS = "resilience:test:run"

    # Administrative permissions
    MANAGE_SECURITY = "security:manage"
    MANAGE_USERS = "users:manage"
    MANAGE_CERTIFICATES = "certificates:manage"


# Role-to-permission mapping
ROLE_PERMISSIONS: Dict[Role, Set[Permission]] = {
    Role.VIEWER: {
        Permission.READ_TELEMETRY,
        Permission.READ_MACHINES,
        Permission.READ_ALERTS,
        Permission.READ_ML,
        Permission.READ_SHADOW,
        Permission.READ_FLEET,
        Permission.READ_JOBS,
        Permission.READ_RESILIENCE,
    },
    Role.OPERATOR: {
        # Inherits VIEWER
        Permission.READ_TELEMETRY,
        Permission.READ_MACHINES,
        Permission.READ_ALERTS,
        Permission.READ_ML,
        Permission.READ_SHADOW,
        Permission.READ_FLEET,
        Permission.READ_JOBS,
        Permission.READ_RESILIENCE,
        # Operator actions
        Permission.ACK_ALERTS,
        Permission.RESOLVE_ALERTS,
        Permission.EXECUTE_COMMANDS,
        Permission.UPDATE_SHADOW_DESIRED,
        Permission.SYNC_SHADOW,
        Permission.CANCEL_JOBS,
    },
    Role.MAINTAINER: {
        # Inherits OPERATOR
        Permission.READ_TELEMETRY,
        Permission.READ_MACHINES,
        Permission.READ_ALERTS,
        Permission.READ_ML,
        Permission.READ_SHADOW,
        Permission.READ_FLEET,
        Permission.READ_JOBS,
        Permission.READ_RESILIENCE,
        Permission.ACK_ALERTS,
        Permission.RESOLVE_ALERTS,
        Permission.EXECUTE_COMMANDS,
        Permission.UPDATE_SHADOW_DESIRED,
        Permission.SYNC_SHADOW,
        Permission.CANCEL_JOBS,
        # Maintainer actions
        Permission.CREATE_CONFIG_JOBS,
        Permission.CREATE_OTA_JOBS,
        Permission.UPDATE_DEVICE_METADATA,
        Permission.INJECT_FAULT_SCENARIOS,
        Permission.RUN_RESILIENCE_TESTS,
        Permission.READ_SECURITY_AUDIT,
    },
    Role.ADMIN: {
        # All permissions
        p for p in Permission
    },
}


class User(BaseModel):
    """Authenticated user profile."""
    username: str
    role: Role = Role.VIEWER
    full_name: Optional[str] = None
    email: Optional[str] = None
    is_active: bool = True
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    def has_permission(self, permission: Permission) -> bool:
        """Check if user role has the required permission."""
        return permission in ROLE_PERMISSIONS.get(self.role, set())


class TokenPayload(BaseModel):
    """Decoded JWT payload."""
    sub: str  # username
    role: Role
    exp: int  # expiration timestamp
    iat: int  # issued at timestamp
    jti: Optional[str] = None  # unique token id


class TokenResponse(BaseModel):
    """JWT response model."""
    access_token: str
    token_type: str = "bearer"
    expires_in_seconds: int
    role: Role
    username: str


class SecurityAuditAction(str, Enum):
    """Types of security-critical actions recorded in security audit logs."""
    AUTH_LOGIN_SUCCESS = "AUTH_LOGIN_SUCCESS"
    AUTH_LOGIN_FAILED = "AUTH_LOGIN_FAILED"
    AUTH_TOKEN_EXPIRED = "AUTH_TOKEN_EXPIRED"
    AUTH_TOKEN_INVALID = "AUTH_TOKEN_INVALID"
    AUTHZ_PERMISSION_DENIED = "AUTHZ_PERMISSION_DENIED"
    AUTHZ_PERMISSION_GRANTED = "AUTHZ_PERMISSION_GRANTED"
    CERTIFICATE_GENERATED = "CERTIFICATE_GENERATED"
    CERTIFICATE_VALIDATED = "CERTIFICATE_VALIDATED"
    CERTIFICATE_EXPIRED = "CERTIFICATE_EXPIRED"
    CERTIFICATE_INVALID = "CERTIFICATE_INVALID"
    SECRET_ACCESSED = "SECRET_ACCESSED"
    SECURITY_CONFIG_CHANGED = "SECURITY_CONFIG_CHANGED"
    MANAGEMENT_ACTION = "MANAGEMENT_ACTION"


class SecurityAuditRecord(BaseModel):
    """Immutable audit record for security operations."""
    event_id: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    actor: str
    role: Optional[str] = None
    action: SecurityAuditAction
    resource: Optional[str] = None
    status: str = "SUCCESS"  # SUCCESS / FAILURE / DENIED
    client_ip: Optional[str] = None
    correlation_id: Optional[str] = None
    details: Dict[str, Any] = Field(default_factory=dict)
    error_message: Optional[str] = None


class CertificateInfo(BaseModel):
    """Metadata summary of an X.509 certificate."""
    subject_cn: str
    issuer_cn: str
    serial_number: str
    not_before: datetime
    not_after: datetime
    san_entries: List[str] = Field(default_factory=list)
    is_ca: bool = False
    is_expired: bool = False
    days_until_expiration: int = 0
