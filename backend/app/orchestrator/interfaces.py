"""Abstract interfaces for safe emulation execution runners."""

from abc import ABC, abstractmethod
from typing import Any

from backend.app.orchestrator.models import ExecutionMode
from backend.app.planner.models import CampaignStage
from backend.app.techniques.models import SimulationEvent


class BaseRunner(ABC):
    """Abstract base class for emulation runners (FR-3.1, FR-3.2, FR-3.3)."""

    @property
    @abstractmethod
    def runner_name(self) -> str:
        """Unique identifier for this execution runner."""
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """Return whether the underlying execution environment is currently accessible."""
        pass

    @abstractmethod
    def execute_stage(
        self,
        stage: CampaignStage,
        run_id: str,
        mode: ExecutionMode,
        context: dict[str, Any] | None = None,
    ) -> SimulationEvent:
        """Execute or emulate an approved campaign stage safely.

        Args:
            stage: The validated campaign stage to execute.
            run_id: Correlation ID for the campaign execution.
            mode: DRY_RUN or LIVE_SIMULATION.
            context: Additional operational parameters or fixtures.

        Returns:
            SimulationEvent recording emitted telemetry, IOCs, and execution status.
        """
        pass

