"""Abstract base class for all curated ATT&CK emulation techniques."""

from abc import ABC, abstractmethod
from typing import Any

from backend.app.techniques.models import SimulationEvent, TechniqueContract


class BaseTechnique(ABC):
    """Abstract base class for a self-contained, contract-bound ATT&CK technique module."""

    def __init__(self, contract: TechniqueContract) -> None:
        self.contract = contract

    @property
    def id(self) -> str:
        return self.contract.technique_id

    @property
    def name(self) -> str:
        return self.contract.name

    @abstractmethod
    def validate_preconditions(self, target_resource: dict[str, Any]) -> tuple[bool, str]:
        """Verify whether target resource satisfies technique preconditions.

        Returns:
            tuple: (is_valid, reason)
        """
        pass

    @abstractmethod
    def simulate(
        self, target_resource_id: str, parameters: dict[str, Any] | None = None
    ) -> SimulationEvent:
        """Execute safe, inert, observable behavioral simulation.

        Returns:
            SimulationEvent: Structured observation record with benign IOCs and telemetry.
        """
        pass

