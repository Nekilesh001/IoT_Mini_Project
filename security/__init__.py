"""
Security Package for Smart Factory.
Provides authentication, RBAC authorization, secret validation, TLS/mTLS certificate management, and security audit logs.
"""

from security.models import (
    Role,
    Permission,
    ROLE_PERMISSIONS,
    User,
    TokenPayload,
    TokenResponse,
    SecurityAuditAction,
    SecurityAuditRecord,
    CertificateInfo,
)
from security.config import SecurityConfig
from security.secrets import SecretsManager, MissingSecretError
from security.validation import SecretHygieneValidator, SecretFinding
from security.certificates import CertificateManager
from security.mtls import MTLSContextBuilder
from security.rbac import RBACPolicy
from security.auth import AuthenticationService
from security.authorization import (
    get_auth_service,
    get_current_user,
    require_permission,
    require_role,
)
from security.audit import SecurityAuditLogger, get_security_audit_logger
from security.middleware import SecurityHeadersMiddleware

__all__ = [
    "Role",
    "Permission",
    "ROLE_PERMISSIONS",
    "User",
    "TokenPayload",
    "TokenResponse",
    "SecurityAuditAction",
    "SecurityAuditRecord",
    "CertificateInfo",
    "SecurityConfig",
    "SecretsManager",
    "MissingSecretError",
    "SecretHygieneValidator",
    "SecretFinding",
    "CertificateManager",
    "MTLSContextBuilder",
    "RBACPolicy",
    "AuthenticationService",
    "get_auth_service",
    "get_current_user",
    "require_permission",
    "require_role",
    "SecurityAuditLogger",
    "get_security_audit_logger",
    "SecurityHeadersMiddleware",
]
