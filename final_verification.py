"""
Phase 13: Final System Health & Verification Verifier.
Checks package imports, directories, model artifacts, API app, dashboard build, AWS disabled status, secret hygiene, and documentation completeness.
Usage: python -m final_verification
"""

import importlib
import os
import sys

from security.validation import SecretHygieneValidator
from cloud.aws.config import AWSConfig
from security.config import SecurityConfig


def verify_system() -> int:
    print("=" * 75)
    print("  SMART FACTORY SYSTEM: FINAL HEALTH & INTEGRITY CHECK")
    print("=" * 75)

    checks_passed = 0
    total_checks = 8

    # 1. Package Imports
    print("\n[Check 1/8] Verifying Subsystem Python Imports...")
    required_packages = [
        "simulator",
        "protocols",
        "edge",
        "event_bus",
        "storage",
        "alerts",
        "ml",
        "device_management",
        "security",
        "failure_testing",
        "benchmarking",
        "final_demo",
        "api",
        "cloud",
    ]
    for pkg in required_packages:
        importlib.import_module(pkg)
    print(f"  [OK] All {len(required_packages)} core subsystems imported successfully.")
    checks_passed += 1

    # 2. Critical Directories
    print("\n[Check 2/8] Verifying Workspace Directory Structure...")
    required_dirs = [
        "simulator", "protocols", "edge", "event_bus", "storage",
        "alerts", "ml", "device_management", "security", "failure_testing",
        "benchmarking", "final_demo", "api", "dashboard", "cloud", "docs", "tests",
    ]
    for d in required_dirs:
        assert os.path.isdir(d), f"Missing required directory: {d}"
    print(f"  [OK] All {len(required_dirs)} required workspace directories exist.")
    checks_passed += 1

    # 3. Model Artifacts
    print("\n[Check 3/8] Verifying Machine Learning Model Artifacts...")
    model_paths = [
        "data/models/anomaly_isolation_forest_v1.0.0.joblib",
        "data/models/anomaly_isolation_forest_v1.0.0.onnx",
        "data/models/rul_gradient_boosting_v1.0.0.joblib",
        "data/models/rul_gradient_boosting_v1.0.0.onnx",
    ]
    for p in model_paths:
        assert os.path.exists(p), f"Missing required model artifact: {p}"
    print("  [OK] Anomaly and RUL trained joblib and ONNX model binaries present.")
    checks_passed += 1

    # 4. FastAPI Application Import
    print("\n[Check 4/8] Verifying FastAPI Application...")
    from api.main import create_app
    app = create_app()
    assert app is not None
    print("  [OK] FastAPI app and all sub-routers instantiated successfully.")
    checks_passed += 1

    # 5. Dashboard Build Artifacts
    print("\n[Check 5/8] Verifying React Operations Dashboard Build...")
    dist_index = "dashboard/react-app/dist/index.html"
    assert os.path.exists(dist_index), f"Dashboard build artifact missing at {dist_index}"
    print("  [OK] Production React bundle verified in dashboard/react-app/dist.")
    checks_passed += 1

    # 6. AWS Disabled & Cloud-Optional Boundary
    print("\n[Check 6/8] Verifying AWS Boundary (PLANNED / NOT CONNECTED)...")
    aws_cfg = AWSConfig()
    assert aws_cfg.enabled is False, "AWS_ENABLED must default to False"
    print("  [OK] AWS Cloud integration is strictly disabled (AWS_ENABLED=false).")
    checks_passed += 1

    # 7. Secret Hygiene Scan
    print("\n[Check 7/8] Running Automated Secret Hygiene Scanner...")
    validator = SecretHygieneValidator()
    leaks = validator.scan()
    assert len(leaks) == 0, f"Found {len(leaks)} leaked secrets in codebase!"
    print("  [OK] Secret hygiene scan passed with 0 detected leaks.")
    checks_passed += 1

    # 8. Documentation Files
    print("\n[Check 8/8] Verifying Final Documentation Complete Suite...")
    doc_paths = [
        "docs/final/architecture.md",
        "docs/final/project-overview.md",
        "docs/final/component-inventory.md",
        "docs/final/requirements-traceability.md",
        "docs/final/phase-summary.md",
        "docs/final/machine-fleet.md",
        "docs/final/protocol-matrix.md",
        "docs/final/ml-results.md",
        "docs/final/security-summary.md",
        "docs/final/resilience-summary.md",
        "docs/final/aws-status.md",
        "docs/final/setup.md",
        "docs/final/runbook.md",
        "docs/final/troubleshooting.md",
        "docs/final/limitations.md",
        "docs/final/test-matrix.md",
        "docs/final/benchmark-results.md",
        "docs/final/final-verification.md",
    ]
    for p in doc_paths:
        assert os.path.exists(p), f"Missing required documentation: {p}"
    print(f"  [OK] All {len(doc_paths)} final documentation files present and verified.")
    checks_passed += 1

    print("\n" + "=" * 75)
    print(f"  FINAL HEALTH CHECK SUMMARY: {checks_passed}/{total_checks} CHECKS PASSED")
    print("  [OK] SYSTEM INTEGRITY & ARCHITECTURE VERIFIED (EXIT 0)")
    print("=" * 75)
    return 0


if __name__ == "__main__":
    sys.exit(verify_system())
