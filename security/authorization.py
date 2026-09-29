"""
FastAPI Authorization & Permission Guard Dependencies.
Enforces role-based access control and records security audit events on authorization decisions.
"""

from typing import Callable, Optional
from fastapi import Depends, Header, HTTPException, Request, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt

from security.auth import AuthenticationService
from security.audit import get_security_audit_logger
from security.config import SecurityConfig
from security.models import Permission, Role, SecurityAuditAction, User
from security.rbac import RBACPolicy

security_bearer = HTTPBearer(auto_error=False)
_auth_service = AuthenticationService()


def get_auth_service() -> AuthenticationService:
    return _auth_service


def get_current_user(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_bearer),
    auth_service: AuthenticationService = Depends(get_auth_service),
) -> User:
    """
    Extract and validate authenticated user from Bearer token.
    Falls back to anonymous VIEWER if ALLOW_ANONYMOUS_VIEWER=true and no token is present.
    """
    audit_logger = get_security_audit_logger()
    client_ip = request.client.host if request.client else "unknown"
    correlation_id = getattr(request.state, "correlation_id", None)
    path = request.url.path

    if not credentials:
        if auth_service.config.allow_anonymous_viewer:
            return User(
                username="anonymous_viewer",
                role=Role.VIEWER,
                full_name="Anonymous Guest",
            )
        audit_logger.log_event(
            action=SecurityAuditAction.AUTH_LOGIN_FAILED,
            actor="anonymous",
            resource=path,
            status="DENIED",
            client_ip=client_ip,
            correlation_id=correlation_id,
            error_message="Missing Authorization Header",
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication credentials were not provided.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = credentials.credentials
    try:
        payload = auth_service.decode_access_token(token)
        user = auth_service.get_user_by_username(payload.sub)
        if not user:
            # Token valid but user removed
            user = User(username=payload.sub, role=payload.role)
        return user
    except jwt.ExpiredSignatureError:
        audit_logger.log_event(
            action=SecurityAuditAction.AUTH_TOKEN_EXPIRED,
            actor="token_holder",
            resource=path,
            status="DENIED",
            client_ip=client_ip,
            correlation_id=correlation_id,
            error_message="JWT Token Expired",
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token signature has expired. Please log in again.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except Exception as e:
        audit_logger.log_event(
            action=SecurityAuditAction.AUTH_TOKEN_INVALID,
            actor="token_holder",
            resource=path,
            status="DENIED",
            client_ip=client_ip,
            correlation_id=correlation_id,
            error_message=f"Invalid Token: {str(e)}",
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token.",
            headers={"WWW-Authenticate": "Bearer"},
        )


def require_permission(required_permission: Permission) -> Callable:
    """
    FastAPI dependency factory enforcing that the authenticated user possesses the given Permission.
    """
    def _permission_guard(
        request: Request,
        user: User = Depends(get_current_user),
    ) -> User:
        audit_logger = get_security_audit_logger()
        client_ip = request.client.host if request.client else "unknown"
        correlation_id = getattr(request.state, "correlation_id", None)
        path = request.url.path

        if not user.has_permission(required_permission):
            audit_logger.log_event(
                action=SecurityAuditAction.AUTHZ_PERMISSION_DENIED,
                actor=user.username,
                role=user.role.value,
                resource=path,
                status="DENIED",
                client_ip=client_ip,
                correlation_id=correlation_id,
                details={"required_permission": required_permission.value},
                error_message=f"Role '{user.role.value}' lacks required permission '{required_permission.value}'",
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied: permission '{required_permission.value}' is required for this operation.",
            )

        audit_logger.log_event(
            action=SecurityAuditAction.AUTHZ_PERMISSION_GRANTED,
            actor=user.username,
            role=user.role.value,
            resource=path,
            status="SUCCESS",
            client_ip=client_ip,
            correlation_id=correlation_id,
            details={"granted_permission": required_permission.value},
        )
        return user

    return _permission_guard


def require_role(min_role: Role) -> Callable:
    """
    FastAPI dependency factory enforcing that user has at least the specified Role in hierarchy.
    """
    def _role_guard(
        request: Request,
        user: User = Depends(get_current_user),
    ) -> User:
        if not RBACPolicy.is_role_at_least(user.role, min_role):
            audit_logger = get_security_audit_logger()
            audit_logger.log_event(
                action=SecurityAuditAction.AUTHZ_PERMISSION_DENIED,
                actor=user.username,
                role=user.role.value,
                resource=request.url.path,
                status="DENIED",
                client_ip=request.client.host if request.client else "unknown",
                correlation_id=getattr(request.state, "correlation_id", None),
                details={"required_min_role": min_role.value},
                error_message=f"Role '{user.role.value}' does not meet minimum role '{min_role.value}'",
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied: minimum role '{min_role.value}' is required for this operation.",
            )
        return user

    return _role_guard
