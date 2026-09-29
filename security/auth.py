"""
Authentication & JWT Token Management.
Provides password verification, JWT creation, token signature decoding, and identity retrieval.
"""

from datetime import datetime, timedelta, timezone
import hashlib
import hmac
import os
from typing import Dict, Optional
import uuid

import jwt
from pydantic import ValidationError

from security.config import SecurityConfig
from security.models import Role, User, TokenPayload, TokenResponse


class AuthenticationService:
    """
    Handles local authentication, user bootstrap verification, and JWT lifecycle.
    """

    def __init__(self, config: Optional[SecurityConfig] = None):
        self.config = config or SecurityConfig()
        self._user_store: Dict[str, User] = {}
        self._password_store: Dict[str, str] = {}
        self._init_bootstrap_users()

    def _init_bootstrap_users(self) -> None:
        """Initialize local development accounts from environment config."""
        users_config = [
            (self.config.admin_username, self.config.admin_password, Role.ADMIN, "System Administrator"),
            (self.config.operator_username, self.config.operator_password, Role.OPERATOR, "Factory Operator"),
            (self.config.maintainer_username, self.config.maintainer_password, Role.MAINTAINER, "Plant Maintainer"),
            (self.config.viewer_username, self.config.viewer_password, Role.VIEWER, "Dashboard Viewer"),
        ]

        for uname, pwd, role, fname in users_config:
            if uname and pwd:
                user = User(
                    username=uname,
                    role=role,
                    full_name=fname,
                    email=f"{uname}@smartfactory.local",
                )
                self._user_store[uname] = user
                self._password_store[uname] = self.hash_password(pwd)

    @staticmethod
    def hash_password(password: str, salt: Optional[str] = None) -> str:
        """Hash password using PBKDF2-HMAC-SHA256."""
        s = salt or "smart_factory_static_local_salt"
        dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), s.encode("utf-8"), 100000)
        return f"{s}${dk.hex()}"

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """Verify plain password against hashed format."""
        try:
            salt, hash_val = hashed_password.split("$", 1)
            re_hashed = AuthenticationService.hash_password(plain_password, salt=salt)
            return hmac.compare_digest(re_hashed, hashed_password)
        except Exception:
            return False

    def authenticate_user(self, username: str, password: str) -> Optional[User]:
        """Authenticate user against credential store."""
        user = self._user_store.get(username)
        if not user or not user.is_active:
            return None

        stored_hash = self._password_store.get(username)
        if not stored_hash or not self.verify_password(password, stored_hash):
            return None

        return user

    def get_user_by_username(self, username: str) -> Optional[User]:
        return self._user_store.get(username)

    def create_access_token(
        self,
        user: User,
        expires_delta: Optional[timedelta] = None,
    ) -> TokenResponse:
        """Generate signed JWT token for authenticated user."""
        now = datetime.now(timezone.utc)
        exp_delta = expires_delta or timedelta(minutes=self.config.jwt_expiration_minutes)
        exp = now + exp_delta
        jti = str(uuid.uuid4())

        payload = {
            "sub": user.username,
            "role": user.role.value,
            "exp": int(exp.timestamp()),
            "iat": int(now.timestamp()),
            "jti": jti,
        }

        token = jwt.encode(
            payload,
            self.config.jwt_secret_key,
            algorithm=self.config.jwt_algorithm,
        )

        return TokenResponse(
            access_token=token,
            token_type="bearer",
            expires_in_seconds=int(exp_delta.total_seconds()),
            role=user.role,
            username=user.username,
        )

    def decode_access_token(self, token: str) -> TokenPayload:
        """
        Validate and decode JWT token.
        Raises jwt.ExpiredSignatureError, jwt.InvalidTokenError, or ValueError on failure.
        """
        decoded = jwt.decode(
            token,
            self.config.jwt_secret_key,
            algorithms=[self.config.jwt_algorithm],
        )
        return TokenPayload(
            sub=decoded["sub"],
            role=Role(decoded["role"]),
            exp=decoded["exp"],
            iat=decoded["iat"],
            jti=decoded.get("jti"),
        )
