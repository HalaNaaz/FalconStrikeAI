"""Central registry and allowlist for approved MITRE ATT&CK techniques (FR-2.2)."""

from backend.app.core.exceptions import SafetyPolicyViolationError
from backend.app.core.logging import logger
from backend.app.techniques.catalog import CURATED_TECHNIQUE_CONTRACTS
from backend.app.techniques.contracts import TechniqueContractValidator
from backend.app.techniques.models import AttackTactic, TechniqueContract


class TechniqueRegistry:
    """Manages the approved, safe technique catalog; rejects unknown or unapproved techniques."""

    def __init__(self) -> None:
        self._techniques: dict[str, TechniqueContract] = {}
        self._load_curated_catalog()

    def _load_curated_catalog(self) -> None:
        """Load and validate all curated PRD Appendix A techniques."""
        for _tid, contract in CURATED_TECHNIQUE_CONTRACTS.items():
            self.register(contract)
        logger.info(
            f"TechniqueRegistry initialized with {len(self._techniques)} approved techniques."
        )

    def register(self, contract: TechniqueContract) -> None:
        """Register an approved technique contract with validation."""
        TechniqueContractValidator.validate_contract(contract)
        if contract.technique_id in self._techniques:
            raise SafetyPolicyViolationError(
                f"Technique ID '{contract.technique_id}' is already registered. Duplicates forbidden."
            )
        self._techniques[contract.technique_id] = contract

    def get(self, technique_id: str) -> TechniqueContract | None:
        """Retrieve technique contract by ID if registered."""
        return self._techniques.get(technique_id)

    def get_or_raise(self, technique_id: str) -> TechniqueContract:
        """Retrieve technique contract or raise SafetyPolicyViolationError if unknown/unapproved."""
        contract = self.get(technique_id)
        if contract is None:
            raise SafetyPolicyViolationError(
                f"Technique ID '{technique_id}' is NOT present in the approved technique registry. "
                "Execution and planning strictly blocked."
            )
        return contract

    def is_approved(self, technique_id: str) -> bool:
        """Check if technique ID is in the approved allowlist."""
        return technique_id in self._techniques

    def is_technique_approved(self, technique_id: str) -> bool:
        """Check if technique ID is in the approved allowlist."""
        return self.is_approved(technique_id)

    def get_contract(self, technique_id: str) -> TechniqueContract | None:
        """Retrieve technique contract by ID if registered."""
        return self.get(technique_id)

    def list_all(self) -> list[TechniqueContract]:
        """Return all registered technique contracts."""
        return list(self._techniques.values())

    def list_by_tactic(self, tactic: AttackTactic) -> list[TechniqueContract]:
        """Return all registered technique contracts for a specific tactic."""
        return [t for t in self._techniques.values() if t.tactic == tactic]


# Global singleton instance
technique_registry = TechniqueRegistry()
