"""
Unit tests for AuthenticationService: token creation, expiration, invalid token, password verification.
"""

from datetime import timedelta
import time
import pytest
from security.auth import AuthenticationService
from security.config import SecurityConfig
from security.models import Role, User


def test_authenticate_valid_and_invalid_user():
    cfg = SecurityConfig(jwt_secret_key="test_secret_key_12345678901234567890")
    service = AuthenticationService(cfg)

    # Valid user
    user = service.authenticate_user("operator", "operator123")
    assert user is not None
    assert user.username == "operator"
    assert user.role == Role.OPERATOR

    # Wrong password
    wrong = service.authenticate_user("operator", "wrong_password")
    assert wrong is None

    # Nonexistent user
    none_user = service.authenticate_user("nonexistent", "some_password")
    assert none_user is None


def test_token_creation_and_decoding():
    cfg = SecurityConfig(jwt_secret_key="test_secret_key_12345678901234567890", jwt_expiration_minutes=15)
    service = AuthenticationService(cfg)

    user = User(username="admin_user", role=Role.ADMIN)
    token_resp = service.create_access_token(user)

    assert token_resp.access_token is not None
    assert token_resp.token_type == "bearer"
    assert token_resp.expires_in_seconds == 900

    # Decode token
    payload = service.decode_access_token(token_resp.access_token)
    assert payload is not None
    assert payload.sub == "admin_user"
    assert payload.role == Role.ADMIN


def test_token_expiration():
    import jwt
    cfg = SecurityConfig(jwt_secret_key="test_secret_key_12345678901234567890", jwt_expiration_minutes=1)
    service = AuthenticationService(cfg)

    user = User(username="temp_user", role=Role.VIEWER)
    # Issue token with negative expiry
    expired_token = service.create_access_token(user, expires_delta=timedelta(seconds=-5))

    with pytest.raises(jwt.ExpiredSignatureError):
        service.decode_access_token(expired_token.access_token)


def test_tampered_token_rejection():
    import jwt
    cfg = SecurityConfig(jwt_secret_key="test_secret_key_12345678901234567890")
    service = AuthenticationService(cfg)

    user = User(username="operator", role=Role.OPERATOR)
    token = service.create_access_token(user).access_token

    # Tamper token
    tampered = token[:-5] + "XXXXX"
    with pytest.raises(jwt.InvalidTokenError):
        service.decode_access_token(tampered)
