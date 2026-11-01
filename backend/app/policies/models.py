"""Data models for policy evaluation requests, rule results, and decisions."""

from datetime import UTC, datetime
from enum import StrEnum
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field

from backend.app.planner.models import CampaignPlan


class PolicyDecisionType(StrEnum):
    """Categorical outcomes of safety policy evaluation."""

    APPROVED_FOR_DRY_RUN = "APPROVED_FOR_DRY_RUN"
    APPROVED_FOR_REVIEW = "APPROVED_FOR_REVIEW"
    REJECTED = "REJECTED"


class PolicyRuleResult(BaseModel):
    """Result of an individual policy rule evaluation."""

    rule_name: str
    passed: bool
    reason: str
    details: dict[str, Any] = Field(default_factory=dict)


class PolicyDecision(BaseModel):
    """Comprehensive policy gate verdict on a campaign plan (FR-2.5)."""

    decision_id: str = Field(default_factory=lambda: f"DEC-{uuid4().hex[:8].upper()}")
    campaign_id: str
    run_id: str
    decision: PolicyDecisionType
    approved: bool
    rejected_rules: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    evaluated_at: str = Field(default_factory=lambda: datetime.now(UTC).isoformat())
    policy_version: str = Field(default="1.0.0")
    evaluation_summary: str = Field(description="Human-readable explanation of policy decision")
    rule_results: list[PolicyRuleResult] = Field(default_factory=list)


class PolicyEvaluationRequest(BaseModel):
    """Request payload for evaluating a campaign against the policy gate."""

    campaign_plan: CampaignPlan
    target_account_id: str = Field(default="000000000000")
    operator_token: str | None = Field(
        default=None, description="Primary authorization token signed by operator"
    )
    secondary_approver_token: str | None = Field(
        default=None, description="Secondary authorization token signed by security lead/mentor"
    )
    request_live_execution: bool = Field(
        default=False, description="Whether live execution is requested (requires two-key approval)"
    )

