"""
AWS IoT Jobs Adapter Scaffolding.
Placeholder implementation of CloudJobsInterface for future AWS IoT Jobs rollout and status tracking.
Currently disabled (local-first mode).
"""

import logging
from typing import Any, Dict, List, Optional
from cloud.interfaces.jobs import CloudJobsInterface
from cloud.aws.config import AWSConfig
from device_management.models import (
    JobType,
    JobStatus,
    ManagementJobRecord,
)

logger = logging.getLogger("cloud.aws.jobs")


class AWSIoTJobsAdapter(CloudJobsInterface):
    """
    Scaffold adapter for future AWS IoT Jobs integration.
    Planned Responsibility:
      - Coordinate OTA simulation / firmware distribution documents via AWS IoT Jobs API.
      - Track job rollout across dynamic target groups (e.g. CNCs, Pumps, Robots).
      - Relay execution outcome (IN_PROGRESS, SUCCEEDED, FAILED) back to AWS.
    """

    def __init__(self, config: Optional[AWSConfig] = None):
        self.config = config or AWSConfig()

    @property
    def is_enabled(self) -> bool:
        return self.config.enabled

    def create_cloud_job(
        self,
        job_id: str,
        targets: List[str],
        document: Dict[str, Any],
        description: Optional[str] = None,
    ) -> ManagementJobRecord:
        if not self.config.enabled:
            logger.debug(f"[Scaffold] create_cloud_job '{job_id}' returning local stub (AWS disabled).")
            return ManagementJobRecord(
                job_id=job_id,
                machine_id=targets[0] if targets else "unknown",
                job_type=JobType.CONFIG_UPDATE,
                payload=document,
                status=JobStatus.PENDING,
            )
        raise NotImplementedError("AWS IoT Jobs API call is not active in local-first mode.")

    def get_cloud_job_status(self, job_id: str) -> Optional[ManagementJobRecord]:
        if not self.config.enabled:
            return None
        raise NotImplementedError("AWS IoT Jobs API call is not active in local-first mode.")

    def update_job_execution(
        self,
        job_id: str,
        thing_name: str,
        status: JobStatus,
        status_details: Optional[Dict[str, str]] = None,
        expected_version: Optional[int] = None,
    ) -> bool:
        if not self.config.enabled:
            logger.debug(f"[Scaffold] update_job_execution '{job_id}' for '{thing_name}' ignored (AWS disabled).")
            return True
        raise NotImplementedError("AWS IoT Jobs API call is not active in local-first mode.")

    def cancel_cloud_job(self, job_id: str, reason: Optional[str] = None) -> bool:
        if not self.config.enabled:
            return True
        raise NotImplementedError("AWS IoT Jobs API call is not active in local-first mode.")
