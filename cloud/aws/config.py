"""
AWS IoT Configuration Scaffolding.
Default is AWS_ENABLED=false. No credentials or live connections are initiated.
"""

import os
from typing import Optional
from pydantic import BaseModel, Field


class AWSConfig(BaseModel):
    """
    Configuration settings for future AWS IoT Core and hybrid cloud connectivity.
    Default: enabled = False (strictly local-first operation).
    """
    enabled: bool = Field(
        default_factory=lambda: os.getenv("AWS_ENABLED", "false").lower() in ("true", "1", "yes")
    )
    endpoint: Optional[str] = Field(
        default_factory=lambda: os.getenv("AWS_IOT_ENDPOINT", "")
    )
    region: Optional[str] = Field(
        default_factory=lambda: os.getenv("AWS_REGION", "us-east-1")
    )
    thing_prefix: str = Field(
        default_factory=lambda: os.getenv("AWS_IOT_THING_PREFIX", "factory_machine_")
    )
    root_ca_path: Optional[str] = Field(
        default_factory=lambda: os.getenv("AWS_IOT_ROOT_CA_PATH", None)
    )
    certificate_path: Optional[str] = Field(
        default_factory=lambda: os.getenv("AWS_IOT_CERTIFICATE_PATH", None)
    )
    private_key_path: Optional[str] = Field(
        default_factory=lambda: os.getenv("AWS_IOT_PRIVATE_KEY_PATH", None)
    )
