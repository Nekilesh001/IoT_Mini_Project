"""
Unit tests for Role-Based Access Control (RBAC) hierarchy and permissions.
"""

import pytest
from security.models import Role, Permission
from security.rbac import RBACPolicy


def test_viewer_role_permissions():
    policy = RBACPolicy()

    assert policy.has_permission(Role.VIEWER, Permission.READ_TELEMETRY) is True
    assert policy.has_permission(Role.VIEWER, Permission.READ_ALERTS) is True
    assert policy.has_permission(Role.VIEWER, Permission.READ_ML) is True

    # Denials
    assert policy.has_permission(Role.VIEWER, Permission.ACK_ALERTS) is False
    assert policy.has_permission(Role.VIEWER, Permission.CREATE_CONFIG_JOBS) is False
    assert policy.has_permission(Role.VIEWER, Permission.MANAGE_SECURITY) is False


def test_operator_role_permissions():
    policy = RBACPolicy()

    # Inherits VIEWER permissions
    assert policy.has_permission(Role.OPERATOR, Permission.READ_TELEMETRY) is True
    assert policy.has_permission(Role.OPERATOR, Permission.ACK_ALERTS) is True
    assert policy.has_permission(Role.OPERATOR, Permission.EXECUTE_COMMANDS) is True

    # Denials
    assert policy.has_permission(Role.OPERATOR, Permission.CREATE_CONFIG_JOBS) is False
    assert policy.has_permission(Role.OPERATOR, Permission.INJECT_FAULT_SCENARIOS) is False


def test_maintainer_role_permissions():
    policy = RBACPolicy()

    assert policy.has_permission(Role.MAINTAINER, Permission.ACK_ALERTS) is True
    assert policy.has_permission(Role.MAINTAINER, Permission.CREATE_CONFIG_JOBS) is True
    assert policy.has_permission(Role.MAINTAINER, Permission.INJECT_FAULT_SCENARIOS) is True
    assert policy.has_permission(Role.MAINTAINER, Permission.UPDATE_SHADOW_DESIRED) is True

    # Admin only
    assert policy.has_permission(Role.MAINTAINER, Permission.MANAGE_SECURITY) is False


def test_admin_role_permissions():
    policy = RBACPolicy()

    # All permissions allowed
    for perm in Permission:
        assert policy.has_permission(Role.ADMIN, perm) is True
