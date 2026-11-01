"""Unit tests for Agentic Campaign Planner (Phase 7)."""

import pytest

from backend.app.collectors.synthetic import SyntheticEnvironmentProvider
from backend.app.core.exceptions import BlastRadiusExceededError, SafetyPolicyViolationError
from backend.app.graph.enrichment import MisconfigurationAnalyzer
from backend.app.graph.ingestion import GraphIngestor
from backend.app.graph.path_finder import AttackPathFinder
from backend.app.graph.store import InMemoryGraphStore
from backend.app.planner.adaptive import AdaptivePlanningEngine
from backend.app.planner.models import CampaignPlan, CampaignStage
from backend.app.planner.planner import CampaignPlanner
from backend.app.planner.providers import GeminiPlannerProvider
from backend.app.planner.validation import CampaignPlanValidator
from backend.app.techniques.models import AttackTactic, SimulationEvent


@pytest.fixture
def sample_attack_path():
    """Build graph from synthetic flawed environment and return top attack path."""
    env_data = SyntheticEnvironmentProvider.generate_flawed_environment("000000000000")
    store = InMemoryGraphStore()
    ingestor = GraphIngestor(store)
    ingestor.ingest(env_data)
    analyzer = MisconfigurationAnalyzer(store)
    findings = analyzer.analyze(env_data)
    finder = AttackPathFinder(store)
    paths = finder.discover_paths(findings=findings)
    assert len(paths) > 0
    return paths[0], findings


def test_deterministic_campaign_planning(sample_attack_path) -> None:
    """Verify deterministic planner generates valid campaign without API keys (FR-2.1)."""
    path, findings = sample_attack_path
    planner = CampaignPlanner(provider_name="deterministic")
    plan = planner.plan_campaign(path=path, findings=findings, run_id="test-run-123")

    assert plan.run_id == "test-run-123"
    assert plan.source_attack_path_id == path.path_id
    assert len(plan.stages) >= 3
    assert plan.planner_provider == "deterministic"
    assert plan.approved_by_policy is False

    # Check stage techniques are allowlisted
    for stage in plan.stages:
        assert stage.technique_id in plan.selected_techniques
        assert stage.tactic in [
            AttackTactic.INITIAL_ACCESS,
            AttackTactic.DISCOVERY,
            AttackTactic.PRIVILEGE_ESCALATION,
            AttackTactic.CREDENTIAL_ACCESS,
            AttackTactic.COMMAND_AND_CONTROL,
        ]

    # Verify expected telemetry and IOCs populated
    assert len(plan.expected_iocs) > 0
    assert len(plan.expected_telemetry) > 0


def test_gemini_fallback_when_no_credentials(sample_attack_path) -> None:
    """Verify Gemini provider cleanly falls back to deterministic planner when unauthenticated."""
    path, findings = sample_attack_path
    provider = GeminiPlannerProvider()
    plan = provider.plan(path=path, findings=findings, run_id="gemini-run-01")

    assert plan is not None
    assert "deterministic" in plan.planner_provider
    assert len(plan.stages) >= 3


def test_plan_validator_rejects_empty_stages() -> None:
    """Verify validator rejects campaign with empty stages."""
    empty_plan = CampaignPlan(
        run_id="run-0",
        source_attack_path_id="path-0",
        objective="test",
        stages=[],
        risk_summary="none",
        planning_rationale="test",
    )
    with pytest.raises(SafetyPolicyViolationError) as exc_info:
        CampaignPlanValidator.validate_plan(empty_plan)
    assert "zero stages" in str(exc_info.value)


def test_plan_validator_rejects_unapproved_technique() -> None:
    """Verify validator rejects unknown technique IDs (FR-2.2)."""
    bad_plan = CampaignPlan(
        run_id="run-1",
        source_attack_path_id="path-1",
        objective="test",
        stages=[
            CampaignStage(
                stage_name="Exploit Arbitrary",
                tactic=AttackTactic.INITIAL_ACCESS,
                technique_id="T9999",  # Unapproved!
                technique_name="Unknown Attack",
                target_resource_id="res-1",
                expected_observation="none",
            )
        ],
        risk_summary="none",
        planning_rationale="test",
    )
    with pytest.raises(SafetyPolicyViolationError) as exc_info:
        CampaignPlanValidator.validate_plan(bad_plan)
    assert "not an approved technique" in str(exc_info.value).lower()


def test_plan_validator_rejects_duplicate_stage_actions() -> None:
    """Verify validator detects duplicate actions on the same resource."""
    dup_plan = CampaignPlan(
        run_id="run-dup",
        source_attack_path_id="path-dup",
        objective="test",
        stages=[
            CampaignStage(
                stage_name="Stage 1",
                tactic=AttackTactic.DISCOVERY,
                technique_id="T1526",
                technique_name="Cloud Service Discovery",
                target_resource_id="res-1",
                expected_observation="test",
            ),
            CampaignStage(
                stage_name="Stage 2",
                tactic=AttackTactic.DISCOVERY,
                technique_id="T1526",
                technique_name="Cloud Service Discovery",
                target_resource_id="res-1",  # Duplicate!
                expected_observation="test",
            ),
        ],
        risk_summary="none",
        planning_rationale="test",
    )
    with pytest.raises(SafetyPolicyViolationError) as exc_info:
        CampaignPlanValidator.validate_plan(dup_plan)
    assert "duplicate stage action detected" in str(exc_info.value).lower()


def test_plan_validator_enforces_blast_radius_stage_caps() -> None:
    """Verify campaign exceeding 10 stages raises BlastRadiusExceededError (NFR-S5)."""
    stages = [
        CampaignStage(
            stage_name=f"Stage {i}",
            tactic=AttackTactic.DISCOVERY,
            technique_id="T1580" if i % 2 == 0 else "T1526",
            technique_name="Discovery",
            target_resource_id=f"res-{i}",
            expected_observation="test",
        )
        for i in range(12)  # 12 > MAX_CAMPAIGN_STAGES (10)
    ]
    huge_plan = CampaignPlan(
        run_id="run-huge",
        source_attack_path_id="path-huge",
        objective="test",
        stages=stages,
        risk_summary="none",
        planning_rationale="test",
    )
    with pytest.raises(BlastRadiusExceededError) as exc_info:
        CampaignPlanValidator.validate_plan(huge_plan)
    assert "exceeds maximum permitted stages" in str(exc_info.value)


def test_adaptive_planning_engine() -> None:
    """Verify adaptive engine prunes failed stages and appends exfiltration on successful privesc (FR-2.4)."""
    plan = CampaignPlan(
        run_id="run-adapt",
        source_attack_path_id="path-adapt",
        objective="test",
        target_resources=["res-1", "res-2"],
        stages=[
            CampaignStage(
                stage_id="s1",
                stage_name="Initial Recon",
                tactic=AttackTactic.DISCOVERY,
                technique_id="T1526",
                technique_name="Cloud Service Discovery",
                target_resource_id="res-1",
                expected_observation="test",
            ),
            CampaignStage(
                stage_id="s2",
                stage_name="Role Chaining",
                tactic=AttackTactic.PRIVILEGE_ESCALATION,
                technique_id="T1098",
                technique_name="Account Manipulation",
                target_resource_id="res-2",
                expected_observation="test",
            ),
        ],
        selected_techniques=["T1526", "T1098"],
        risk_summary="test",
        planning_rationale="test",
    )

    completed_events = [
        SimulationEvent(
            technique_id="T1526",
            tactic=AttackTactic.DISCOVERY,
            target_resource_id="res-1",
            status="EMULATED_BENIGN",
        ),
        SimulationEvent(
            technique_id="T1098",
            tactic=AttackTactic.PRIVILEGE_ESCALATION,
            target_resource_id="res-2",
            status="SUCCESS",
        ),
    ]

    adapted = AdaptivePlanningEngine.adapt_plan(plan, completed_events)
    # S2 succeeded in privesc -> should add T1537 (Transfer Data)
    assert "T1537" in adapted.selected_techniques
    assert any(s.technique_id == "T1537" for s in adapted.stages)
