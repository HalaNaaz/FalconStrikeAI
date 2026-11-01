"""Stage lifecycle manager handling pre-execution gates and post-execution hooks (FR-3.1)."""

import time
from datetime import UTC, datetime

from backend.app.core.exceptions import FalconSecurityException
from backend.app.core.logging import logger
from backend.app.orchestrator.kill_switch import EmergencyKillSwitch, kill_switch
from backend.app.orchestrator.models import ExecutionStatus, StageExecutionRecord
from backend.app.orchestrator.teardown import TeardownEngine
from backend.app.planner.models import CampaignStage
from backend.app.techniques.models import SimulationEvent
from backend.app.techniques.registry import TechniqueRegistry, technique_registry


class StageLifecycleManager:
    """Orchestrates stage execution lifecycle, preconditions, teardown registration, and safety gates."""

    def __init__(
        self,
        registry: TechniqueRegistry | None = None,
        teardown_engine: TeardownEngine | None = None,
        ks: EmergencyKillSwitch | None = None,
    ) -> None:
        self.registry = registry or technique_registry
        self.teardown = teardown_engine
        self.kill_switch = ks or kill_switch

    def pre_stage_check(
        self,
        stage: CampaignStage,
        completed_stage_ids: set[str],
        run_id: str,
    ) -> None:
        """Validate safety gates and dependencies prior to stage execution."""
        # 1. Kill-switch check
        if self.kill_switch.is_active():
            raise FalconSecurityException(
                f"Execution halted: Emergency Kill Switch is currently ACTIVE [run_id={run_id}]."
            )

        # 2. Approved technique check
        contract = self.registry.get_contract(stage.technique_id)
        if not contract:
            raise FalconSecurityException(
                f"Execution rejected: Technique '{stage.technique_id}' is not in the approved technique registry."
            )

        # 3. Dependencies check
        missing_deps = [dep for dep in stage.dependencies if dep not in completed_stage_ids]
        if missing_deps:
            raise ValueError(
                f"Stage '{stage.stage_id}' cannot run; missing required prerequisite stages: {missing_deps}"
            )

    def post_stage_hook(
        self,
        stage: CampaignStage,
        event: SimulationEvent,
        run_id: str,
        start_time_iso: str,
        start_perf: float,
        runner_name: str,
    ) -> StageExecutionRecord:
        """Process simulation results, register teardown if needed, and produce execution record."""
        end_time_iso = datetime.now(UTC).isoformat()
        duration_ms = (time.perf_counter() - start_perf) * 1000.0

        contract = self.registry.get_contract(stage.technique_id)
        teardown_required = contract.teardown_required if contract else False
        teardown_status = "NOT_REQUIRED"

        if teardown_required and self.teardown:
            self.teardown.register_action(
                run_id=run_id,
                stage_id=stage.stage_id,
                technique_id=stage.technique_id,
                target_resource_id=stage.target_resource_id,
                action_type=f"REVERT_{stage.technique_id}",
                description=f"Revert simulated changes for technique {stage.technique_id} on {stage.target_resource_id}",
                parameters=stage.action_parameters,
            )
            teardown_status = "REGISTERED"

        logger.info(
            f"Stage {stage.stage_id} ({stage.technique_id}) finished with status {event.status} in {duration_ms:.2f}ms"
        )

        return StageExecutionRecord(
            stage_id=stage.stage_id,
            stage_name=stage.stage_name,
            tactic=stage.tactic,
            technique_id=stage.technique_id,
            technique_name=stage.technique_name,
            target_resource_id=stage.target_resource_id,
            status=ExecutionStatus.COMPLETED,
            start_time=start_time_iso,
            end_time=end_time_iso,
            duration_ms=round(duration_ms, 2),
            simulation_event=event,
            error=None,
            teardown_required=teardown_required,
            teardown_status=teardown_status,
            runner_type=runner_name,
        )
