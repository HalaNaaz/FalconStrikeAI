"""High-level Campaign Planner service orchestrating providers, validation, and audit."""

from uuid import uuid4

from backend.app.core.logging import current_run_id, logger
from backend.app.graph.attack_path_models import AttackPath
from backend.app.graph.models import MisconfigurationFinding
from backend.app.planner.models import CampaignPlan
from backend.app.planner.providers import get_planner_provider
from backend.app.planner.validation import CampaignPlanValidator


class CampaignPlanner:
    """Orchestrates campaign generation from attack paths with strict safety validation."""

    def __init__(self, provider_name: str = "deterministic") -> None:
        self.provider_name = provider_name
        self.provider = get_planner_provider(provider_name)
        self.cached_campaigns: dict[str, CampaignPlan] = {}

    def plan_campaign(
        self,
        path: AttackPath,
        findings: list[MisconfigurationFinding],
        run_id: str | None = None,
    ) -> CampaignPlan:
        """Formulate, validate, and register a multi-stage adversary emulation campaign."""
        active_run_id = run_id or str(uuid4())
        token = current_run_id.set(active_run_id)

        try:
            logger.info(
                f"Planning campaign for path {path.path_id} using provider '{self.provider_name}'",
                extra={
                    "technique_id": "PLANNER",
                    "actor": "CampaignPlanner",
                    "details": {"path_id": path.path_id, "run_id": active_run_id},
                },
            )

            # Generate raw plan via provider
            plan = self.provider.plan(path=path, findings=findings, run_id=active_run_id)

            # Strict Safety & Schema Validation
            valid_resource_ids = {n.id for n in path.ordered_nodes}
            CampaignPlanValidator.validate_plan(plan, valid_resource_ids=valid_resource_ids)

            # Cache campaign
            self.cached_campaigns[plan.campaign_id] = plan

            logger.info(
                f"Campaign plan {plan.campaign_id} created with {len(plan.stages)} stages",
                extra={
                    "details": {
                        "campaign_id": plan.campaign_id,
                        "stages": len(plan.stages),
                        "techniques": plan.selected_techniques,
                    }
                },
            )

            return plan
        finally:
            current_run_id.reset(token)

    def get_campaign(self, campaign_id: str) -> CampaignPlan | None:
        """Retrieve a cached campaign plan by ID."""
        return self.cached_campaigns.get(campaign_id)

    def list_campaigns(self) -> list[CampaignPlan]:
        """List all cached campaign plans."""
        return list(self.cached_campaigns.values())

