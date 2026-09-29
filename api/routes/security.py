"""
FastAPI Routes for Authentication, User Profile, Security Status, and Security Audit Logs.
"""

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel

from security.auth import AuthenticationService
from security.audit import SecurityAuditLogger, get_security_audit_logger
from security.authorization import get_auth_service, get_current_user, require_permission
from security.config import SecurityConfig
from security.models import Permission, Role, SecurityAuditAction, SecurityAuditRecord, TokenResponse, User

router = APIRouter(tags=["Security & Authentication"])


class LoginRequest(BaseModel):
    username: str
    password: str


class SecurityStatusResponse(BaseModel):
    tls_enabled: bool
    mtls_enabled: bool
    auth_enabled: bool
    allow_anonymous_viewer: bool
    jwt_algorithm: str
    jwt_expiration_minutes: int
    active_users_count: int


@router.post("/api/auth/token", response_model=TokenResponse)
@router.post("/api/auth/login", response_model=TokenResponse)
def login_for_access_token(
    req: LoginRequest,
    auth_service: AuthenticationService = Depends(get_auth_service),
    audit_logger: SecurityAuditLogger = Depends(get_security_audit_logger),
):
    """Authenticate with username and password to obtain a signed JWT bearer token."""
    user = auth_service.authenticate_user(req.username, req.password)
    if not user:
        audit_logger.log_event(
            action=SecurityAuditAction.AUTH_LOGIN_FAILED,
            actor=req.username,
            status="FAILURE",
            error_message="Invalid username or password",
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token_response = auth_service.create_access_token(user)
    audit_logger.log_event(
        action=SecurityAuditAction.AUTH_LOGIN_SUCCESS,
        actor=user.username,
        role=user.role.value,
        status="SUCCESS",
    )
    return token_response


@router.get("/api/auth/me", response_model=Dict[str, Any])
def get_authenticated_user_profile(
    current_user: User = Depends(get_current_user),
):
    """Retrieve identity and authorized permissions for the current caller."""
    from security.models import ROLE_PERMISSIONS
    perms = [p.value for p in ROLE_PERMISSIONS.get(current_user.role, set())]
    return {
        "username": current_user.username,
        "role": current_user.role.value,
        "full_name": current_user.full_name,
        "email": current_user.email,
        "permissions": perms,
    }


@router.get("/api/security/status", response_model=SecurityStatusResponse)
def get_security_status(
    auth_service: AuthenticationService = Depends(get_auth_service),
):
    """Query current security configuration and transport encryption status."""
    cfg = auth_service.config
    return SecurityStatusResponse(
        tls_enabled=cfg.tls_enabled,
        mtls_enabled=cfg.mtls_enabled,
        auth_enabled=cfg.auth_enabled,
        allow_anonymous_viewer=cfg.allow_anonymous_viewer,
        jwt_algorithm=cfg.jwt_algorithm,
        jwt_expiration_minutes=cfg.jwt_expiration_minutes,
        active_users_count=len(auth_service._user_store),
    )


@router.get("/api/security/audit", response_model=List[SecurityAuditRecord])
def list_security_audit_logs(
    action: Optional[SecurityAuditAction] = Query(None, description="Filter by security action"),
    actor: Optional[str] = Query(None, description="Filter by actor username"),
    limit: int = Query(100, ge=1, le=500),
    current_user: User = Depends(require_permission(Permission.READ_SECURITY_AUDIT)),
    audit_logger: SecurityAuditLogger = Depends(get_security_audit_logger),
):
    """Retrieve recent security audit logs (requires MAINTAINER or ADMIN role)."""
    return audit_logger.list_events(action=action, actor=actor, limit=limit)
