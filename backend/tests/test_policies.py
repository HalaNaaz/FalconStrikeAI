"""Unit tests for Safety Policy Gate Engine and Two-Key Authorization (Phase 9)."""

import pytest

from backend.app.core.config import settings
from backend.app.core.security import create_authorization_token
from backend.app.planner.models import CampaignPlan, CampaignStage
from backend.app.policies.engine import PolicyGateEngine
from backend.app.policies.models import PolicyDecisionType, PolicyEvaluationRequest
from backend.app.policies.rules import set_global_kill_switch
from backend.app.techniques.models import AttackTactic


@pytest.fixture(autouse=True)
def reset_kill_switch():
    """Ensure kill switch is reset to False before each test."""
    set_global_kill_switch(False)
    yield
    set_global_kill_switch(False)


@pytest.fixture
def valid_campaign_plan() -> CampaignPlan:
    """Create a standard valid campaign plan conforming to all safety rules."""
    return CampaignPlan(
        run_id="run-policy-test-01",
        source_attack_path_id="path-01",
        objective="Validate detection on test attack path",
        target_resources=["000000000000", "res-ec2-01"],
        stages=[
            CampaignStage(
                stage_name="Initial Access Recon",
                tactic=AttackTactic.INITIAL_ACCESS,
                technique_id="T1078",
                technique_name="Valid Accounts",
                target_resource_id="res-ec2-01",
                expected_observation="AssumeRole event logged",
            ),
            CampaignStage(
                stage_name="Service Discovery",
                tactic=AttackTactic.DISCOVERY,
                technique_id="T1526",
                technique_name="Cloud Service Discovery",
                target_resource_id="res-ec2-01",
                expected_observation="DescribeInstances logged",
            ),
        ],
        selected_techniques=["T1078", "T1526"],
        risk_summary="Safe test plan",
        planning_rationale="Testing policy gate",
    )


def test_policy_gate_approves_valid_dry_run(valid_campaign_plan: CampaignPlan) -> None:
    """Verify conforming campaign is APPROVED_FOR_DRY_RUN in dry-run mode (NFR-S4)."""
    engine = PolicyGateEngine()
    req = PolicyEvaluationRequest(
        campaign_plan=valid_campaign_plan,
        target_account_id="000000000000",
        request_live_execution=False,
    )
    decision = engine.evaluate(req)

    assert decision.approved is True
    assert decision.decision == PolicyDecisionType.APPROVED_FOR_DRY_RUN
    assert len(decision.rejected_rules) == 0
    assert "APPROVED FOR DRY-RUN" in decision.evaluation_summary


def test_policy_gate_rejects_unallowlisted_account(valid_campaign_plan: CampaignPlan) -> None:
    """Verify targeting an unapproved account is REJECTED by policy gate (NFR-S1)."""
    engine = PolicyGateEngine()
    req = PolicyEvaluationRequest(
        campaign_plan=valid_campaign_plan,
        target_account_id="999888777666",  # Out-of-scope account!
        request_live_execution=False,
    )
    decision = engine.evaluate(req)

    assert decision.approved is False
    assert decision.decision == PolicyDecisionType.REJECTED
    assert any("ACCOUNT_ALLOWLIST_CHECK" in r for r in decision.rejected_rules)


def test_policy_gate_rejects_unapproved_technique() -> None:
    """Verify campaign with an unapproved technique ID is REJECTED (FR-2.2)."""
    bad_plan = CampaignPlan(
        run_id="run-bad-tech",
        source_attack_path_id="path-bad",
        objective="test",
        stages=[
            CampaignStage(
                stage_name="Unknown Action",
                tactic=AttackTactic.INITIAL_ACCESS,
                technique_id="T9999",  # Unapproved technique
                technique_name="Unknown Attack",
                target_resource_id="res-1",
                expected_observation="none",
            )
        ],
        risk_summary="test",
        planning_rationale="test",
    )
    engine = PolicyGateEngine()
    req = PolicyEvaluationRequest(
        campaign_plan=bad_plan,
        target_account_id="000000000000",
    )
    decision = engine.evaluate(req)

    assert decision.approved is False
    assert decision.decision == PolicyDecisionType.REJECTED
    assert any("TECHNIQUE_ALLOWLIST_CHECK" in r for r in decision.rejected_rules)


def test_policy_gate_rejects_when_kill_switch_active(valid_campaign_plan: CampaignPlan) -> None:
    """Verify active kill switch immediately REJECTS campaign approval (NFR-S3)."""
    set_global_kill_switch(True)  # Engage emergency kill switch

    engine = PolicyGateEngine()
    req = PolicyEvaluationRequest(
        campaign_plan=valid_campaign_plan,
        target_account_id="000000000000",
    )
    decision = engine.evaluate(req)

    assert decision.approved is False
    assert decision.decision == PolicyDecisionType.REJECTED
    assert any("KILL_SWITCH_STATUS_CHECK" in r for r in decision.rejected_rules)
    assert "Emergency Kill Switch is ACTIVE" in str(decision.rejected_rules)


def test_two_key_approval_success_for_live_execution(valid_campaign_plan: CampaignPlan) -> None:
    """Verify two distinct signed authorization tokens satisfy live execution gate (NFR-S2)."""
    secret = settings.auth_secret_key
    target_account = "000000000000"

    # Token 1: Red Team Engineer
    op_token = create_authorization_token(
        operator_id="Engineer-Alice",
        target_account_id=target_account,
        secret_key=secret,
        role="RedTeamEngineer",
    )
    # Token 2: Mentor / Security Lead
    sec_token = create_authorization_token(
        operator_id="Mentor-Bob",
        target_account_id=target_account,
        secret_key=secret,
        role="LeadSecurityMentor",
    )

    engine = PolicyGateEngine()
    req = PolicyEvaluationRequest(
        campaign_plan=valid_campaign_plan,
        target_account_id=target_account,
        operator_token=op_token,
        secondary_approver_token=sec_token,
        request_live_execution=True,
    )
    decision = engine.evaluate(req)

    assert decision.approved is True
    assert decision.decision == PolicyDecisionType.APPROVED_FOR_REVIEW
    assert "Two-key authorization confirmed" in decision.evaluation_summary


def test_two_key_approval_rejects_identical_identity(valid_campaign_plan: CampaignPlan) -> None:
    """Verify the same person cannot satisfy both keys (approver separation enforcement)."""
    secret = settings.auth_secret_key
    target_account = "000000000000"

    # Both tokens generated with identical subject 'Engineer-Alice'
    token1 = create_authorization_token(
        operator_id="Engineer-Alice",
        target_account_id=target_account,
        secret_key=secret,
    )
    token2 = create_authorization_token(
        operator_id="Engineer-Alice",
        target_account_id=target_account,
        secret_key=secret,
    )

    engine = PolicyGateEngine()
    req = PolicyEvaluationRequest(
        campaign_plan=valid_campaign_plan,
        target_account_id=target_account,
        operator_token=token1,
        secondary_approver_token=token2,
        request_live_execution=True,
    )
    decision = engine.evaluate(req)

    assert decision.approved is False
    assert decision.decision == PolicyDecisionType.REJECTED
    assert any("Two-key separation violation" in r for r in decision.rejected_rules)


def test_two_key_approval_rejects_missing_second_token(valid_campaign_plan: CampaignPlan) -> None:
    """Verify live execution request with only 1 token is rejected."""
    secret = settings.auth_secret_key
    target_account = "000000000000"
    op_token = create_authorization_token(
        operator_id="Engineer-Alice",
        target_account_id=target_account,
        secret_key=secret,
    )

    engine = PolicyGateEngine()
    req = PolicyEvaluationRequest(
        campaign_plan=valid_campaign_plan,
        target_account_id=target_account,
        operator_token=op_token,
        secondary_approver_token=None,  # Missing!
        request_live_execution=True,
    )
    decision = engine.evaluate(req)

    assert decision.approved is False
    assert decision.decision == PolicyDecisionType.REJECTED
    assert any("Missing secondary approver" in r for r in decision.rejected_rules)
