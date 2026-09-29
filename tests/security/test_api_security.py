"""
Integration tests for FastAPI security headers, JWT authentication endpoints, and RBAC authorization guards.
"""

import pytest
from fastapi.testclient import TestClient
from api.main import create_app


@pytest.fixture
def client():
    app = create_app()
    return TestClient(app)


def test_security_hardening_headers(client):
    response = client.get("/api/health")
    assert response.status_code == 200

    # Verify security headers injected by middleware
    assert response.headers.get("X-Content-Type-Options") == "nosniff"
    assert response.headers.get("X-Frame-Options") == "DENY"
    assert response.headers.get("Referrer-Policy") == "strict-origin-when-cross-origin"
    assert "X-Correlation-ID" in response.headers


def test_auth_login_flow(client):
    # 1. Invalid login
    bad_res = client.post("/api/auth/login", json={"username": "operator", "password": "wrong_password"})
    assert bad_res.status_code == 401

    # 2. Valid login
    login_res = client.post("/api/auth/login", json={"username": "operator", "password": "operator123"})
    assert login_res.status_code == 200
    token = login_res.json()["access_token"]
    assert token is not None

    # 3. Access /api/auth/me with token
    me_res = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me_res.status_code == 200
    user_data = me_res.json()
    assert user_data["username"] == "operator"
    assert user_data["role"] == "OPERATOR"
    assert "telemetry:read" in user_data["permissions"]


def test_rbac_security_audit_access(client):
    # 1. Anonymous access rejected
    anon_res = client.get("/api/security/audit")
    assert anon_res.status_code == 403

    # 2. Operator token (insufficient permissions) rejected
    op_login = client.post("/api/auth/login", json={"username": "operator", "password": "operator123"})
    op_token = op_login.json()["access_token"]
    op_res = client.get("/api/security/audit", headers={"Authorization": f"Bearer {op_token}"})
    assert op_res.status_code == 403

    # 3. Admin token allowed
    admin_login = client.post("/api/auth/login", json={"username": "admin", "password": "admin123"})
    admin_token = admin_login.json()["access_token"]
    admin_res = client.get("/api/security/audit", headers={"Authorization": f"Bearer {admin_token}"})
    assert admin_res.status_code == 200
    assert isinstance(admin_res.json(), list)
