"""
Cloud Jobs Interface.
Abstract contract for synchronizing job execution, rollout targets, and execution status with cloud IoT Job brokers.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from device_management.models import (
    JobStatus,
    ManagementJobRecord,
    JobAttemptRecord,
)


class CloudJobsInterface(ABC):
    """
    Interface for dispatching and tracking cloud IoT Jobs (e.g., AWS IoT Jobs).
    """

    @abstractmethod
    def create_cloud_job(
        self,
        job_id: str,
        targets: List[str],
        document: Dict[str, Any],
        description: Optional[str] = None,
    ) -> ManagementJobRecord:
        """Create an AWS IoT Job resource for fleet execution."""
        pass

    @abstractmethod
    def get_cloud_job_status(self, job_id: str) -> Optional[ManagementJobRecord]:
        """Query cloud job rollout progress across fleet targets."""
        pass

    @abstractmethod
    def update_job_execution(
        self,
        job_id: str,
        thing_name: str,
        status: JobStatus,
        status_details: Optional[Dict[str, str]] = None,
        expected_version: Optional[int] = None,
    ) -> bool:
        """Report execution outcome from an edge device to the cloud IoT Jobs service."""
        pass

    @abstractmethod
    def cancel_cloud_job(self, job_id: str, reason: Optional[str] = None) -> bool:
        """Cancel a pending cloud job."""
        pass
