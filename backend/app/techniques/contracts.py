"""Contract verification and validation engine for ATT&CK techniques."""

from backend.app.core.exceptions import SafetyPolicyViolationError
from backend.app.techniques.models import TechniqueContract


class TechniqueContractValidator:
    """Verifies that technique contracts satisfy mandatory safety and schema standards."""

    @staticmethod
    def validate_contract(contract: TechniqueContract) -> None:
        """Validate that a technique contract includes all required fields and invariants."""
        if not contract.technique_id:
            raise SafetyPolicyViolationError("Technique contract missing 'technique_id'.")
        if not contract.name:
            raise SafetyPolicyViolationError(f"Technique {contract.technique_id} missing 'name'.")
        if not contract.description:
            raise SafetyPolicyViolationError(
                f"Technique {contract.technique_id} missing 'description'."
            )
        if not contract.safety_constraints:
            raise SafetyPolicyViolationError(
                f"Technique {contract.technique_id} must declare explicit safety constraints."
            )
        if not contract.expected_telemetry:
            raise SafetyPolicyViolationError(
                f"Technique {contract.technique_id} must declare expected telemetry."
            )
        if not contract.expected_iocs:
            raise SafetyPolicyViolationError(
                f"Technique {contract.technique_id} must declare expected benign IOCs."
            )
        if contract.teardown_required and not contract.teardown_instructions:
            raise SafetyPolicyViolationError(
                f"Technique {contract.technique_id} requires teardown but provides no instructions."
            )
