"""Abstract interfaces for SIEM and EDR detection sources (FR-5.1)."""

from abc import ABC, abstractmethod

from backend.app.detection.models import DetectionSourceType, SecurityDetectionEvent


class BaseSIEMAdapter(ABC):
    """Abstract base class for security alert and detection ingestion adapters."""

    @property
    @abstractmethod
    def adapter_name(self) -> str:
        """Name of the SIEM/EDR platform (e.g. crowdstrike_falcon, splunk, sentinel)."""
        pass

    @property
    @abstractmethod
    def source_type(self) -> DetectionSourceType:
        """Provenance classification of alerts returned by this adapter."""
        pass

    @abstractmethod
    def is_connected(self) -> bool:
        """Return True only if valid credentials and verified live API connectivity exist."""
        pass

    @abstractmethod
    def query_detections(
        self,
        run_id: str,
        start_time: str,
        end_time: str | None = None,
    ) -> list[SecurityDetectionEvent]:
        """Query detection events matching a campaign run timeframe.

        Args:
            run_id: Campaign execution run identifier.
            start_time: ISO timestamp marking the beginning of the emulation window.
            end_time: ISO timestamp marking the end of the emulation window.

        Returns:
            list[SecurityDetectionEvent] containing alerts matching criteria.
        """
        pass

