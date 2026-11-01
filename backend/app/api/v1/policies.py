"""API endpoints for safety policy gate evaluation and status (FR-2.5, NFR-S1, NFR-S2)."""

from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel

from backend.app.core.config import settings
from backend.app.core.state import app_state
from backend.app.policies.models import PolicyDecision, PolicyEvaluationRequest
from backend.app.policies.rules import is_global_kill_switch_active

router = APIRouter(prefix="/policies", tags=["Safety Policy Gate"])


class PolicyStatusResponse(BaseModel):
    """Current configuration of safety policy gate."""

    policy_version: str = "1.0.0"
    active_rules: list[str]
    allowlisted_accounts: list[str]
    dry_run_default: bool
    kill_switch_active: bool
    blast_radius_limits: dict[str, Any]


@router.get("/status", response_model=PolicyStatusResponse)
async def get_policy_status() -> dict[str, Any]:
    """Retrieve policy gate configuration, active rules, and guardrail boundaries."""
    return {
        "policy_version": "1.0.0",
        "active_rules": [r.rule_name for r in app_state.policy_engine.rules],
        "allowlisted_accounts": settings.allowlisted_accounts,
        "dry_run_default": settings.dry_run,
        "kill_switch_active": is_global_kill_switch_active(),
        "blast_radius_limits": {
            "max_resources_touched": settings.max_resources_touched,
            "max_duration_seconds": settings.max_run_duration_seconds,
            "max_campaign_stages": 10,
        },
    }


@router.post("/evaluate", response_model=PolicyDecision)
async def evaluate_campaign_policy(request: PolicyEvaluationRequest) -> PolicyDecision:
    """Evaluate a campaign plan against safety policies and guardrails."""
    decision = app_state.policy_engine.evaluate(request)
    app_state.cached_policy_decisions[decision.decision_id] = decision
    return decision
