"""Pydantic schemas and models for campaign plans and stages."""

from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field

from backend.app.techniques.models import AttackTactic, TechniqueRiskLevel


class CampaignStage(BaseModel):
    """An individual actionable stage within a multi-stage emulation campaign (FR-2.1)."""

    stage_id: str = Field(default_factory=lambda: f"STAGE-{uuid4().hex[:6].upper()}")
    stage_name: str = Field(description="Descriptive name of the stage")
    tactic: AttackTactic = Field(description="Primary MITRE ATT&CK tactic")
    technique_id: str = Field(description="Approved MITRE ATT&CK technique ID (e.g., T1078)")
    technique_name: str = Field(description="Approved MITRE ATT&CK technique name")
    target_resource_id: str = Field(description="Target resource ARN or node ID")
    action_parameters: dict[str, Any] = Field(
        default_factory=dict, description="Safe, inert parameters passed to emulation module"
    )
    expected_observation: str = Field(
        description="Expected security log or telemetry observable upon execution"
    )
    estimated_risk: TechniqueRiskLevel = Field(default=TechniqueRiskLevel.LOW)
    dependencies: list[str] = Field(
        default_factory=list,
        description="List of prerequisite stage_ids that must precede this stage",
    )


class CampaignPlan(BaseModel):
    """A complete, structured, multi-stage adversary emulation campaign (FR-2.1, FR-2.3)."""

    campaign_id: str = Field(default_factory=lambda: f"CAMP-{uuid4().hex[:8].upper()}")
    schema_version: str = Field(default="1.0.0")
    run_id: str = Field(description="Campaign correlation / run ID threading audit logs (NFR-A3)")
    created_at: str = Field(default_factory=lambda: datetime.now(UTC).isoformat())
    source_attack_path_id: str = Field(
        description="ID of the ranked attack path this campaign is grounded on"
    )
    objective: str = Field(
        description="High-level operational objective (e.g. validate detection of privilege escalation to cloud admin)"
    )
    target_resources: list[str] = Field(
        default_factory=list, description="List of target resource IDs involved in this campaign"
    )
    stages: list[CampaignStage] = Field(
        default_factory=list, description="Ordered stages composing the campaign"
    )
    selected_techniques: list[str] = Field(
        default_factory=list, description="All technique IDs utilized in this campaign"
    )
    expected_iocs: list[str] = Field(
        default_factory=list, description="Summary of expected benign IOC signatures"
    )
    expected_telemetry: list[str] = Field(
        default_factory=list, description="Summary of expected CloudTrail / VPC flow events"
    )
    risk_summary: str = Field(
        description="Summary of overall campaign risk and blast radius containment guarantees"
    )
    planner_provider: str = Field(
        default="deterministic", description="Provider used: deterministic, gemini, openai"
    )
    planning_rationale: str = Field(
        description="Detailed justification of technique sequencing and targeting"
    )
    approved_by_policy: bool = Field(
        default=False, description="Whether this plan has passed the Safety Policy Gate"
    )


class CampaignGenerationRequest(BaseModel):
    """API request payload for generating a campaign from an attack path."""

    attack_path_id: str | None = Field(
        default=None,
        description="Optional ID of attack path to target (defaults to top-ranked path)",
    )
    provider: str = Field(
        default="deterministic", description="Planner provider: deterministic, gemini, or openai"
    )
    run_id: str | None = Field(
        default=None, description="Optional custom campaign run_id (UUID generated if omitted)"
    )
