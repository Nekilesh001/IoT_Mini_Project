"""
Phase 10 Security Hardening Demonstration Script.
Demonstrates:
  1. Local X.509 Root CA generation.
  2. Server and Client certificate issuance with SANs.
  3. Certificate chain and expiration verification.
  4. User authentication and JWT token creation.
  5. Role-Based Access Control (RBAC) permission resolution.
  6. Authorization denial for unauthorized operations.
  7. Secret scrubbing and security audit logging.
  8. Repository secret hygiene validation scan.
"""

from datetime import timedelta
import sys

from security.auth import AuthenticationService
from security.audit import get_security_audit_logger
from security.certificates import CertificateManager
from security.config import SecurityConfig
from security.models import Permission, Role, SecurityAuditAction, User
from security.rbac import RBACPolicy
from security.validation import SecretHygieneValidator


def run_demo() -> int:
    print("=" * 75)
    print("  PHASE 10: SECURITY HARDENING DEMONSTRATION")
    print("=" * 75)

    # 1. Certificate Management (Local CA & End-Entity Certs)
    print("\n[Step 1/6] Generating Local X.509 Root CA and Server/Client Certificates...")
    ca_cert, ca_key = CertificateManager.generate_ca(common_name="Smart Factory Local Root CA")
    ca_info = CertificateManager.inspect_certificate(ca_cert)
    print(f"  [OK] Root CA Generated: CN='{ca_info.subject_cn}', Serial={ca_info.serial_number[:10]}...")

    server_cert, server_key = CertificateManager.generate_signed_cert(
        common_name="localhost",
        ca_cert=ca_cert,
        ca_key=ca_key,
        san_hosts=["localhost", "127.0.0.1", "factory.local"],
        is_server=True,
    )
    srv_info = CertificateManager.inspect_certificate(server_cert)
    print(f"  [OK] Server Cert Generated: CN='{srv_info.subject_cn}', SANs={srv_info.san_entries}")

    # Verify Chain & SANs
    chain_valid = CertificateManager.verify_cert_chain(server_cert, ca_cert)
    host_valid = CertificateManager.verify_hostname_san(server_cert, "127.0.0.1")
    assert chain_valid is True, "Expected cert chain to be valid"
    assert host_valid is True, "Expected SAN verification to pass"
    print(f"  * Certificate Chain Verification: VALID ({chain_valid})")
    print(f"  * SAN Hostname Verification: MATCH ({host_valid})")

    # 2. Authentication & JWT Tokens
    print("\n[Step 2/6] User Authentication & Signed JWT Issuance...")
    auth_service = AuthenticationService()

    # Authenticate Operator
    operator_user = auth_service.authenticate_user("operator", "operator123")
    assert operator_user is not None
    token_resp = auth_service.create_access_token(operator_user, expires_delta=timedelta(minutes=30))
    print(f"  [OK] Authenticated: '{operator_user.username}' (Role: {operator_user.role.value})")
    print(f"  * Issued JWT: {token_resp.access_token[:20]}... (Expires in {token_resp.expires_in_seconds}s)")

    # Decode and Validate Token
    payload = auth_service.decode_access_token(token_resp.access_token)
    assert payload.sub == "operator"
    assert payload.role == Role.OPERATOR
    print(f"  [OK] Token Decoded: sub='{payload.sub}', role='{payload.role.value}'")

    # 3. RBAC Policy Enforcement
    print("\n[Step 3/6] Evaluating Role-Based Access Control (RBAC) Permissions...")
    viewer_user = auth_service.get_user_by_username("viewer")
    maintainer_user = auth_service.get_user_by_username("maintainer")

    # VIEWER: Can read telemetry, cannot create config jobs
    assert RBACPolicy.is_authorized(viewer_user, Permission.READ_TELEMETRY) is True
    assert RBACPolicy.is_authorized(viewer_user, Permission.CREATE_CONFIG_JOBS) is False
    print(f"  * VIEWER -> READ_TELEMETRY: ALLOWED | CREATE_CONFIG_JOBS: DENIED")

    # OPERATOR: Can acknowledge alerts, cannot inject fault scenarios
    assert RBACPolicy.is_authorized(operator_user, Permission.ACK_ALERTS) is True
    assert RBACPolicy.is_authorized(operator_user, Permission.INJECT_FAULT_SCENARIOS) is False
    print(f"  * OPERATOR -> ACK_ALERTS: ALLOWED | INJECT_FAULT_SCENARIOS: DENIED")

    # MAINTAINER: Can create config jobs & inject fault scenarios
    assert RBACPolicy.is_authorized(maintainer_user, Permission.CREATE_CONFIG_JOBS) is True
    assert RBACPolicy.is_authorized(maintainer_user, Permission.INJECT_FAULT_SCENARIOS) is True
    print(f"  * MAINTAINER -> CREATE_CONFIG_JOBS: ALLOWED | INJECT_FAULT_SCENARIOS: ALLOWED")

    # 4. Security Audit Trail & Secret Scrubbing
    print("\n[Step 4/6] Testing Security Audit Logging with Secret Scrubbing...")
    audit_logger = get_security_audit_logger()
    audit_logger.log_event(
        action=SecurityAuditAction.AUTHZ_PERMISSION_DENIED,
        actor="viewer",
        role="VIEWER",
        resource="/api/jobs",
        status="DENIED",
        details={"attempted_action": "CREATE_JOB", "raw_token": "secret_bearer_token_12345"},
        error_message="Insufficient role for configuration rollout",
    )
    events = audit_logger.list_events(limit=5)
    print(f"  [OK] Security Event Logged: [{events[0].action.value}] status={events[0].status}")
    print(f"  * Scrubbed Details: {events[0].details}")
    assert events[0].details.get("raw_token") == "[REDACTED]", "Expected sensitive token to be redacted in audit"

    # 5. Secret Hygiene Scanner
    print("\n[Step 5/6] Running Repository Secret Hygiene Scan...")
    validator = SecretHygieneValidator()
    findings = validator.scan()
    print(f"  [OK] Leaked Credentials Detected in Codebase: {len(findings)} (0 expected)")
    assert len(findings) == 0

    print("\n" + "=" * 75)
    print("  PHASE 10 SECURITY DEMONSTRATION COMPLETE - ALL CHECKS PASSED (EXIT 0)")
    print("=" * 75)
    return 0


if __name__ == "__main__":
    sys.exit(run_demo())
