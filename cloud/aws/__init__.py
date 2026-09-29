"""
AWS Scaffolding Adapters and Configurations.
Disabled by default (AWS_ENABLED=false).
"""

from cloud.aws.config import AWSConfig
from cloud.aws.iot_core import AWSIoTCoreAdapter
from cloud.aws.device_shadow import AWSIoTDeviceShadowAdapter
from cloud.aws.jobs import AWSIoTJobsAdapter
from cloud.aws.fleet_indexing import AWSIoTFleetIndexingAdapter

__all__ = [
    "AWSConfig",
    "AWSIoTCoreAdapter",
    "AWSIoTDeviceShadowAdapter",
    "AWSIoTJobsAdapter",
    "AWSIoTFleetIndexingAdapter",
]
