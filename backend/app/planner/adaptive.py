"""Adaptive planning engine for dynamic campaign adjustment based on stage outcomes (FR-2.4)."""

from backend.app.core.logging import logger
from backend.app.planner.models import CampaignPlan, CampaignStage
from backend.app.techniques.models import AttackTactic, SimulationEvent, TechniqueRiskLevel


class AdaptivePlanningEngine:
    """Dynamically adapts remaining campaign stages based on prior emulation outcomes."""

    @staticmethod
    def adapt_plan(
        plan: CampaignPlan,
        completed_events: list[SimulationEvent],
    ) -> CampaignPlan:
        """Inspect completed stage outcomes and prune or adapt future stages."""
        logger.info(
            f"Evaluating adaptive plan adjustments for campaign {plan.campaign_id} based on {len(completed_events)} completed events"
        )

        failed_technique_ids = {
            e.technique_id
            for e in completed_events
            if e.status not in ("EMULATED_BENIGN", "SUCCESS")
        }

        # If a stage failed, prune any downstream stages depending on it
        adapted_stages: list[CampaignStage] = []
        for stage in plan.stages:
            if stage.technique_id in failed_technique_ids:
                logger.warning(
                    f"Stage {stage.stage_id} ({stage.technique_id}) failed; pruning from execution queue."
                )
                continue
            adapted_stages.append(stage)

        # If privilege escalation succeeded, add an optional exfiltration check if not already present
        has_privesc_success = any(
            e.technique_id == "T1098" and e.status in ("EMULATED_BENIGN", "SUCCESS")
            for e in completed_events
        )
        if has_privesc_success and "T1537" not in plan.selected_techniques:
            logger.info(
                "Privilege escalation succeeded; adding benign data transfer validation stage."
            )
            new_stage = CampaignStage(
                stage_name="Benign Marker Exfiltration Validation",
                tactic=AttackTactic.EXFILTRATION,
                technique_id="T1537",
                technique_name="Transfer Data to Cloud Account",
                target_resource_id=plan.target_resources[-1],
                action_parameters={"marker_id": "FALCON_BENIGN_TRANSFER_01"},
                expected_observation="CloudTrail s3:CopyObject copying benign marker string.",
                estimated_risk=TechniqueRiskLevel.LOW,
            )
            adapted_stages.append(new_stage)
            plan.selected_techniques.append("T1537")

        plan.stages = adapted_stages
        return plan
