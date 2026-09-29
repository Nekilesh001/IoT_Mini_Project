"""
Abstract collector and data extraction interfaces for ML datasets.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional
import pandas as pd


class BaseTelemetryCollector(ABC):
    """Abstract interface for collecting factory telemetry datasets."""

    @abstractmethod
    def collect(self, **kwargs) -> pd.DataFrame:
        """
        Collects raw telemetry events into a pandas DataFrame.
        Must return normalized columns: machine_id, machine_type, event_time, sequence,
        operating_state, health_state, quality, plus measurement fields.
        """
        pass
