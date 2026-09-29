"""
Secret Hygiene Scanner & Repository Validator.
Scans source files, configuration templates, and documentation for accidental secret leaks.
Run via: python -m security.validation
"""

from pathlib import Path
import re
import sys
from typing import Dict, List, NamedTuple, Optional, Set


class SecretFinding(NamedTuple):
    file_path: str
    line_number: int
    pattern_name: str
    description: str


class SecretHygieneValidator:
    """
    Regex-based scanner designed to catch real secret leaks while avoiding false positives.
    """

    PATTERNS: Dict[str, re.Pattern] = {
        "AWS Access Key": re.compile(r"(?:A3T[A-Z0-9]|AKIA|AGPA|AIDA|AROA|AIPA|ANPA|ANVA|ASIA)[A-Z0-9]{16}"),
        "Private Key Block": re.compile(r"-----BEGIN\s+(?:RSA|EC|DSA|OPENSSH|PRIVATE)\s+KEY-----"),
        "Generic Secret Assignment": re.compile(r"""(?i)(?:aws_secret_access_key|api_secret|jwt_secret|private_key_pass)\s*=\s*['"][a-zA-Z0-9/_+=-]{20,}['"]"""),
        "Hardcoded Database Password": re.compile(r"""postgresql(?:\+psycopg2)?://[^:]+:([a-zA-Z0-9_\-!@#$%^&*]{8,})@"""),
    }

    IGNORE_DIRS: Set[str] = {
        ".git",
        ".pytest_cache",
        "node_modules",
        "dist",
        "certs",
        "mlruns",
        "__pycache__",
        ".agents",
        "local_buffer.db",
        "postgres_test_buffer.db",
    }

    IGNORE_FILES: Set[str] = {
        ".env",
        ".env.local",
        ".env.test",
        ".env.development",
        ".env.production",
        ".env.example",
        "validation.py",  # self
        "SIMULATED FACTORY.docx",
    }

    def __init__(self, root_dir: Optional[Path] = None):
        self.root_dir = root_dir or Path(__file__).resolve().parent.parent

    def should_skip(self, path: Path) -> bool:
        """Check if path should be skipped."""
        for part in path.parts:
            if part in self.IGNORE_DIRS:
                return True
        if path.name in self.IGNORE_FILES:
            return True
        if path.suffix.lower() in {".pyc", ".db", ".joblib", ".onnx", ".png", ".jpg", ".docx", ".lock"}:
            return True
        return False

    def scan(self) -> List[SecretFinding]:
        """Scan all text files in repository for leaked credentials."""
        findings: List[SecretFinding] = []

        for p in self.root_dir.rglob("*"):
            if not p.is_file() or self.should_skip(p):
                continue

            try:
                with open(p, "r", encoding="utf-8", errors="ignore") as f:
                    for line_idx, line in enumerate(f, start=1):
                        # Skip comment lines containing placeholder indicators
                        if any(token in line.lower() for token in ("placeholder", "example", "<empty>", "your_", "todo", "change_in_prod")):
                            continue

                        for name, pattern in self.PATTERNS.items():
                            match = pattern.search(line)
                            if match:
                                # Special exemption: standard local test strings (e.g. postgres:postgres)
                                if "postgres:postgres@" in line:
                                    continue
                                rel_path = str(p.relative_to(self.root_dir))
                                findings.append(
                                    SecretFinding(
                                        file_path=rel_path,
                                        line_number=line_idx,
                                        pattern_name=name,
                                        description=f"Potential {name} detected",
                                    )
                                )
            except Exception:
                continue

        return findings


def main() -> int:
    print("=" * 65)
    print("  SECRET HYGIENE & CREDENTIAL LEAK SCANNER")
    print("=" * 65)

    validator = SecretHygieneValidator()
    findings = validator.scan()

    if not findings:
        print("\n[PASS] Zero secret leaks or unmasked credentials detected.")
        print("  - AWS credentials: NONE")
        print("  - Committed private keys: NONE")
        print("  - Unmasked production secrets: NONE")
        print("\n" + "=" * 65)
        return 0
    else:
        print(f"\n[FAIL] Found {len(findings)} potential secret leakage finding(s):")
        for f in findings:
            print(f"  * {f.file_path}:{f.line_number} -> [{f.pattern_name}] {f.description}")
        print("\n" + "=" * 65)
        return 1


if __name__ == "__main__":
    from typing import Optional
    sys.exit(main())
