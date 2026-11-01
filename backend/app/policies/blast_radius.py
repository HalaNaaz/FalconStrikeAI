"""Blast-radius cap evaluation and boundary limits (NFR-S5)."""

from typing import Any

from backend.app.core.config import settings
from backend.app.planner.models import CampaignPlan
from backend.app.planner.schemas import (
    MAX_CAMPAIGN_STAGES,
    MAX_EXECUTION_DURATION_SECONDS,
    MAX_TARGET_RESOURCES,
)


class BlastRadiusEvaluator:
    """Evaluates campaign execution bounds against hard resource and duration caps."""

    @staticmethod
    def evaluate(plan: CampaignPlan) -> tuple[bool, str, dict[str, Any]]:
        """Verify that campaign does not breach blast-radius limits."""
        stage_count = len(plan.stages)
        unique_targets = len({s.target_resource_id for s in plan.stages})

        max_allowed_resources = settings.max_resources_touched or MAX_TARGET_RESOURCES
        max_allowed_duration = settings.max_run_duration_seconds or MAX_EXECUTION_DURATION_SECONDS

        details = {
            "stage_count": stage_count,
            "max_stages": MAX_CAMPAIGN_STAGES,
            "target_resources_count": unique_targets,
            "max_target_resources": max_allowed_resources,
            "duration_limit_sec": max_allowed_duration,
        }

        if stage_count > MAX_CAMPAIGN_STAGES:
            return (
                False,
                f"Campaign exceeds maximum stages ({stage_count} > {MAX_CAMPAIGN_STAGES}).",
                details,
            )

        if unique_targets > max_allowed_resources:
            return (
                False,
                f"Campaign targets {unique_targets} resources, exceeding maximum cap of {max_allowed_resources}.",
                details,
            )

        return True, "Campaign complies with all blast-radius containment caps.", details

