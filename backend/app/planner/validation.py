"""Strict schema and safety validation for generated campaign plans (FR-2.2, FR-2.3)."""

from backend.app.core.exceptions import BlastRadiusExceededError, SafetyPolicyViolationError
from backend.app.planner.models import CampaignPlan
from backend.app.planner.schemas import (
    MAX_CAMPAIGN_STAGES,
    MAX_TARGET_RESOURCES,
)
from backend.app.techniques.registry import technique_registry


class CampaignPlanValidator:
    """Enforces technique allowlists, blast-radius caps, and schema consistency on plans."""

    @staticmethod
    def validate_plan(plan: CampaignPlan, valid_resource_ids: set[str] | None = None) -> None:
        """Validate a campaign plan strictly. Fails closed on any violation."""
        if not plan.stages:
            raise SafetyPolicyViolationError(
                "Campaign plan contains zero stages. Non-empty plan required."
            )

        # 1. Enforce Blast-Radius Stage Limits
        if len(plan.stages) > MAX_CAMPAIGN_STAGES:
            raise BlastRadiusExceededError(
                f"Campaign exceeds maximum permitted stages ({len(plan.stages)} > {MAX_CAMPAIGN_STAGES}).",
                details={"stage_count": len(plan.stages), "max_allowed": MAX_CAMPAIGN_STAGES},
            )

        # 2. Enforce Target Resource Limits
        unique_targets = {s.target_resource_id for s in plan.stages}
        if len(unique_targets) > MAX_TARGET_RESOURCES:
            raise BlastRadiusExceededError(
                f"Campaign touches {len(unique_targets)} distinct target resources, exceeding cap of {MAX_TARGET_RESOURCES}.",
                details={"target_count": len(unique_targets), "max_allowed": MAX_TARGET_RESOURCES},
            )

        # 3. Enforce Technique Allowlist & Duplicate Detection
        seen_actions: set[tuple[str, str]] = set()

        for stage in plan.stages:
            # Must exist in approved registry (FR-2.2)
            if not technique_registry.is_approved(stage.technique_id):
                raise SafetyPolicyViolationError(
                    f"Technique ID '{stage.technique_id}' in stage '{stage.stage_id}' is NOT an approved technique.",
                    details={"technique_id": stage.technique_id, "stage_id": stage.stage_id},
                )

            # Contract verification
            contract = technique_registry.get(stage.technique_id)
            if contract and contract.name != stage.technique_name:
                stage.technique_name = contract.name

            # Detect duplicate identical actions
            action_signature = (stage.technique_id, stage.target_resource_id)
            if action_signature in seen_actions:
                raise SafetyPolicyViolationError(
                    f"Duplicate stage action detected: technique '{stage.technique_id}' on resource '{stage.target_resource_id}'.",
                    details={"action": action_signature},
                )
            seen_actions.add(action_signature)

            # Optional resource validation against graph
            if (
                valid_resource_ids is not None
                and stage.target_resource_id not in valid_resource_ids
            ):
                raise SafetyPolicyViolationError(
                    f"Stage '{stage.stage_id}' targets unknown resource '{stage.target_resource_id}' "
                    "not present in the active environment graph.",
                    details={"target": stage.target_resource_id},
                )
