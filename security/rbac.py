"""
Role-Based Access Control (RBAC) Module.
Evaluates permissions, hierarchical role inheritance, and role-based policies.
"""

from typing import Optional, Set
from security.models import Role, Permission, User, ROLE_PERMISSIONS


class RBACPolicy:
    """
    Evaluates role permissions and checks whether an action is permitted.
    """

    @staticmethod
    def get_permissions_for_role(role: Role) -> Set[Permission]:
        """Return the complete set of permissions associated with a role."""
        return ROLE_PERMISSIONS.get(role, set())

    @staticmethod
    def has_permission(role: Role, permission: Permission) -> bool:
        """Check if a specific role possesses a permission."""
        return permission in ROLE_PERMISSIONS.get(role, set())

    @staticmethod
    def is_authorized(user: Optional[User], required_permission: Permission) -> bool:
        """
        Check if user holds required permission.
        If user is None (unauthenticated), returns False.
        """
        if not user or not user.is_active:
            return False
        return user.has_permission(required_permission)

    @staticmethod
    def is_role_at_least(user_role: Role, required_role: Role) -> bool:
        """
        Check if user_role meets or exceeds required_role in the hierarchy:
        VIEWER (1) < OPERATOR (2) < MAINTAINER (3) < ADMIN (4)
        """
        hierarchy = {
            Role.VIEWER: 1,
            Role.OPERATOR: 2,
            Role.MAINTAINER: 3,
            Role.ADMIN: 4,
        }
        return hierarchy.get(user_role, 0) >= hierarchy.get(required_role, 0)
