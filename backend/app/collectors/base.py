"""Base collector interface and common collector primitives."""

import time
from abc import ABC, abstractmethod
from typing import Any

from backend.app.collectors.models import CollectionError, CollectionSourceType
from backend.app.core.logging import logger


class BaseCollector(ABC):
    """Abstract base class for service-specific read-only collectors."""

    def __init__(self, source_type: CollectionSourceType = CollectionSourceType.SYNTHETIC) -> None:
        self.source_type = source_type

    @property
    @abstractmethod
    def service_name(self) -> str:
        """Name of the AWS service being collected (e.g., iam, ec2, s3)."""
        pass

    def validate_scope(self, account_id: str) -> None:
        """Enforce account allowlist prior to any SDK or fixture calls (NFR-S1)."""
        from backend.app.core.config import settings

        settings.assert_account_allowlisted(account_id)

    @abstractmethod
    def collect(self, account_id: str) -> tuple[list[Any], list[CollectionError]]:
        """Collect read-only resource metadata.

        Returns:
            tuple: (collected_resources_list, errors_list)
        """
        pass

    def timed_collect(self, account_id: str) -> tuple[list[Any], list[CollectionError], float]:
        """Execute collection and measure duration in milliseconds."""
        start = time.perf_counter()
        logger.debug(
            f"Starting {self.service_name} collection",
            extra={"details": {"account_id": account_id, "source": self.source_type.value}},
        )
        try:
            resources, errors = self.collect(account_id)
        except Exception as exc:
            duration_ms = (time.perf_counter() - start) * 1000.0
            error = CollectionError(
                service=self.service_name,
                operation="collect_unhandled",
                error_type=type(exc).__name__,
                message=str(exc),
            )
            logger.error(
                f"Unhandled error in {self.service_name} collector: {exc}",
                extra={"details": {"error": str(exc)}},
            )
            return [], [error], duration_ms

        duration_ms = (time.perf_counter() - start) * 1000.0
        logger.debug(
            f"Completed {self.service_name} collection in {duration_ms:.2f}ms",
            extra={"details": {"count": len(resources), "errors": len(errors)}},
        )
        return resources, errors, duration_ms
