"""Unit tests for MITRE ATT&CK Technique Registry, contracts, and simulation (Phase 8)."""

import pytest

from backend.app.core.exceptions import SafetyPolicyViolationError
from backend.app.techniques.catalog import CURATED_TECHNIQUE_CONTRACTS
from backend.app.techniques.contracts import TechniqueContractValidator
from backend.app.techniques.models import AttackTactic, TechniqueContract
from backend.app.techniques.registry import TechniqueRegistry, technique_registry
from backend.app.techniques.simulator import TechniqueSimulator


def test_all_curated_techniques_registered() -> None:
    """Verify all 15 PRD Appendix A techniques are present in the registry."""
    expected_tids = [
        "T1078",
        "T1526",
        "T1087",
        "T1580",
        "T1098",
        "T1136",
        "T1053",
        "T1552",
        "T1555",
        "T1550",
        "T1071",
        "T1071.004",
        "T1572",
        "T1568",
        "T1090.004",
        "T1537",
    ]
    for tid in expected_tids:
        assert technique_registry.is_approved(tid), (
            f"Technique {tid} must be in the approved registry"
        )
        contract = technique_registry.get(tid)
        assert contract is not None
        assert contract.technique_id == tid
        assert contract.name is not None
        assert len(contract.safety_constraints) > 0
        assert len(contract.expected_iocs) > 0
        assert len(contract.expected_telemetry) > 0


def test_technique_registry_rejects_unknown_id() -> None:
    """Verify querying an unregistered technique ID raises SafetyPolicyViolationError."""
    assert technique_registry.is_approved("T9999") is False
    with pytest.raises(SafetyPolicyViolationError) as exc_info:
        technique_registry.get_or_raise("T9999")
    assert "not present in the approved technique registry" in str(exc_info.value).lower()


def test_duplicate_registration_rejected() -> None:
    """Verify attempting to register a duplicate technique ID raises error."""
    custom_reg = TechniqueRegistry()
    existing_contract = CURATED_TECHNIQUE_CONTRACTS["T1078"]
    with pytest.raises(SafetyPolicyViolationError) as exc_info:
        custom_reg.register(existing_contract)
    assert "already registered" in str(exc_info.value)


def test_technique_contract_validation() -> None:
    """Verify TechniqueContractValidator catches incomplete contracts."""
    incomplete = TechniqueContract(
        technique_id="T0000",
        name="Test",
        tactic=AttackTactic.DISCOVERY,
        description="test",
        safety_constraints=[],  # Missing!
        expected_telemetry=["test"],
        expected_iocs=["test"],
    )
    with pytest.raises(SafetyPolicyViolationError) as exc_info:
        TechniqueContractValidator.validate_contract(incomplete)
    assert "must declare explicit safety constraints" in str(exc_info.value)


def test_technique_simulation_is_inert_and_deterministic() -> None:
    """Verify simulator generates structured observation events with benign markers."""
    contract = technique_registry.get_or_raise("T1071")
    event = TechniqueSimulator.simulate(
        contract=contract,
        target_resource_id="endpoint:public-internet",
        parameters={"interval_sec": 5},
    )

    assert event.status == "EMULATED_BENIGN"
    assert event.technique_id == "T1071"
    assert event.tactic == AttackTactic.COMMAND_AND_CONTROL
    assert len(event.emitted_iocs) > 0
    assert len(event.emitted_telemetry) > 0
    assert event.output_marker is not None
    assert "FALCON_BENIGN_MARKER_T1071" in event.output_marker
    assert event.duration_ms >= 0.0


def test_list_techniques_by_tactic() -> None:
    """Verify listing techniques filtered by specific ATT&CK tactic."""
    c2_techs = technique_registry.list_by_tactic(AttackTactic.COMMAND_AND_CONTROL)
    assert len(c2_techs) >= 4
    assert any(t.technique_id == "T1071" for t in c2_techs)
    assert any(t.technique_id == "T1071.004" for t in c2_techs)
