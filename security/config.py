"""
Security Configuration.
Loads environment configuration for JWT signing, token TTL, RBAC bootstrap users, TLS, and mTLS.
"""

import os
from pathlib import Path
from typing import Optional
from pydantic import BaseModel, Field


class SecurityConfig(BaseModel):
    """
    Centralized security settings for local authentication, authorization, and transport security.
    """
    # JWT authentication
    jwt_secret_key: str = Field(
        default_factory=lambda: os.getenv("JWT_SECRET_KEY", "dev_insecure_jwt_secret_change_in_prod_key_32chars")
    )
    jwt_algorithm: str = Field(
        default_factory=lambda: os.getenv("JWT_ALGORITHM", "HS256")
    )
    jwt_expiration_minutes: int = Field(
        default_factory=lambda: int(os.getenv("JWT_EXPIRATION_MINUTES", "60"))
    )

    # Local development bootstrap users (username -> password_hash / raw for dev)
    admin_username: str = Field(
        default_factory=lambda: os.getenv("ADMIN_USERNAME", "admin")
    )
    admin_password: str = Field(
        default_factory=lambda: os.getenv("ADMIN_PASSWORD", "admin123")
    )
    operator_username: str = Field(
        default_factory=lambda: os.getenv("OPERATOR_USERNAME", "operator")
    )
    operator_password: str = Field(
        default_factory=lambda: os.getenv("OPERATOR_PASSWORD", "operator123")
    )
    maintainer_username: str = Field(
        default_factory=lambda: os.getenv("MAINTAINER_USERNAME", "maintainer")
    )
    maintainer_password: str = Field(
        default_factory=lambda: os.getenv("MAINTAINER_PASSWORD", "maintainer123")
    )
    viewer_username: str = Field(
        default_factory=lambda: os.getenv("VIEWER_USERNAME", "viewer")
    )
    viewer_password: str = Field(
        default_factory=lambda: os.getenv("VIEWER_PASSWORD", "viewer123")
    )

    # TLS / mTLS configuration
    tls_enabled: bool = Field(
        default_factory=lambda: os.getenv("TLS_ENABLED", "false").lower() in ("true", "1", "yes")
    )
    mtls_enabled: bool = Field(
        default_factory=lambda: os.getenv("MTLS_ENABLED", "false").lower() in ("true", "1", "yes")
    )

    # Certificate paths
    certs_dir: Path = Field(
        default_factory=lambda: Path(os.getenv("CERTS_DIR", "certs"))
    )
    ca_cert_path: Optional[Path] = Field(
        default_factory=lambda: Path(os.getenv("CA_CERT_PATH", "certs/ca/ca.crt"))
    )
    ca_key_path: Optional[Path] = Field(
        default_factory=lambda: Path(os.getenv("CA_KEY_PATH", "certs/ca/ca.key"))
    )
    server_cert_path: Optional[Path] = Field(
        default_factory=lambda: Path(os.getenv("SERVER_CERT_PATH", "certs/server/server.crt"))
    )
    server_key_path: Optional[Path] = Field(
        default_factory=lambda: Path(os.getenv("SERVER_KEY_PATH", "certs/server/server.key"))
    )
    client_cert_path: Optional[Path] = Field(
        default_factory=lambda: Path(os.getenv("CLIENT_CERT_PATH", "certs/clients/client.crt"))
    )
    client_key_path: Optional[Path] = Field(
        default_factory=lambda: Path(os.getenv("CLIENT_KEY_PATH", "certs/clients/client.key"))
    )

    # Enforcement flags
    auth_enabled: bool = Field(
        default_factory=lambda: os.getenv("AUTH_ENABLED", "true").lower() in ("true", "1", "yes")
    )
    allow_anonymous_viewer: bool = Field(
        default_factory=lambda: os.getenv("ALLOW_ANONYMOUS_VIEWER", "true").lower() in ("true", "1", "yes")
    )
