"""
Unit tests for SecretsManager and repository SecretHygieneValidator.
"""

import os
import tempfile
from pathlib import Path
import pytest
from security.secrets import SecretsManager
from security.validation import SecretHygieneValidator


def test_secrets_manager_masking():
    sm = SecretsManager()

    masked = sm.mask_secret("very_secret_database_password_123")
    assert masked.startswith("very")
    assert "*" in masked
    assert sm.mask_secret("short", visible_chars=2).startswith("sh***")
    assert sm.mask_secret("") == "<EMPTY>"


def test_secrets_manager_environment_lookup(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgresql://user:pass@localhost:5432/factory")
    monkeypatch.setenv("JWT_SECRET", "super_secret_signing_key_32_characters_long")

    sm = SecretsManager()
    assert sm.get_secret("DATABASE_URL") == "postgresql://user:pass@localhost:5432/factory"
    assert sm.get_secret("JWT_SECRET") == "super_secret_signing_key_32_characters_long"
    assert sm.get_secret("NONEXISTENT_KEY", default="default_val") == "default_val"


def test_secret_hygiene_scanner_clean_repo():
    validator = SecretHygieneValidator(root_dir=Path(__file__).parent.parent.parent)
    findings = validator.scan()

    # The codebase must have 0 committed credential leaks
    assert len(findings) == 0
