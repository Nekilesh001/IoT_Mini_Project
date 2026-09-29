"""
Secrets Management & Validation Module.
Provides secure retrieval, validation, and masking of environmental secrets and credentials.
"""

import os
import re
from typing import Dict, List, Optional, Set, Tuple


class MissingSecretError(Exception):
    """Raised when a mandatory environment secret is missing or empty in production mode."""
    pass


class SecretsManager:
    """
    Validates and retrieves application secrets safely without logging raw secret values.
    """

    MANDATORY_KEYS = {
        "JWT_SECRET_KEY",
        "DATABASE_URL",
    }

    @staticmethod
    def mask_secret(value: Optional[str], visible_chars: int = 4) -> str:
        """Mask a sensitive string, exposing only the first few characters."""
        if not value:
            return "<EMPTY>"
        if len(value) <= visible_chars:
            return "*" * len(value)
        return f"{value[:visible_chars]}{'*' * (len(value) - visible_chars)}"

    @staticmethod
    def get_secret(key: str, default: Optional[str] = None, required: bool = False) -> str:
        """
        Fetch a secret from environment variables.
        If required is True and the key is missing/empty, raises MissingSecretError.
        """
        val = os.getenv(key, default)
        if required and (val is None or val.strip() == ""):
            raise MissingSecretError(f"Mandatory environment secret '{key}' is missing or empty.")
        return val or ""

    @staticmethod
    def validate_environment(
        required_keys: Optional[Set[str]] = None,
        is_production: bool = False,
    ) -> Tuple[bool, List[str]]:
        """
        Check that all required secret keys exist in the environment.
        Returns (is_valid, list_of_missing_keys).
        """
        keys_to_check = required_keys or (SecretsManager.MANDATORY_KEYS if is_production else set())
        missing = []
        for key in keys_to_check:
            val = os.getenv(key)
            if not val or val.strip() == "":
                missing.append(key)

        return (len(missing) == 0, missing)
