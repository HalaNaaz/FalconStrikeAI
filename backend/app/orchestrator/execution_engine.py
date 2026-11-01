"""Core orchestration execution engine for safe adversary emulation (FR-3.1, FR-3.2, FR-3.3, FR-3.5)."""

import time
from datetime import UTC, datetime
from typing import Any

from backend.app.collectors.models import NormalizedEnvironmentData
from backend.app.core.exceptions import FalconSecurityException
from backend.app.core.logging import logger
from backend.app.orchestrator.baseline import BaselineRecorder
from backend.app.orchestrator.docker_runner import DockerRunner
from backend.app.orchestrator.in_memory_runner import InMemorySimulatorRunner
from backend.app.orchestrator.interfaces import BaseRunner
from backend.app.orchestrator.kill_switch import EmergencyKillSwitch, kill_switch
from backend.app.orchestrator.lifecycle import StageLifecycleManager
from backend.app.orchestrator.models import (
    CampaignExecutionRecord,
    ExecutionMode,
    ExecutionStatus,
    StageExecutionRecord,
)
from backend.app.orchestrator.teardown import TeardownEngine
from backend.app.planner.models import CampaignPlan
from backend.app.techniques.models import AttackTactic
from backend.app.techniques.registry import TechniqueRegistry, technique_registry
from backend.app.telemetry.collector import TelemetryCollector, telemetry_collector
from backend.app.telemetry.ioc_generator import SyntheticIOCGenerator


class ExecutionEngine:
    """Consumes policy-approved campaign plans and coordinates safe, bounded emulation.

    Guarantees:
    - Default mode is DRY_RUN.
    - Zero execution of arbitrary LLM strings or shell commands.
    - All techniques strictly verified against TechniqueRegistry.
    - Kill switch check before every stage (< 2s emergency stop).
    - Automatic baseline capture and post-execution teardown.
    - One unified run_id correlated throughout the entire execution.
    """

    def __init__(
        self,
        registry: TechniqueRegistry | None = None,
        ks: EmergencyKillSwitch | None = None,
        teardown: TeardownEngine | None = None,
        telemetry: TelemetryCollector | None = None,
    ) -> None:
        self.registry = registry or technique_registry
        self.kill_switch = ks or kill_switch
        self.teardown_engine = teardown or TeardownEngine()
        self.telemetry_collector = telemetry or telemetry_collector
        self.lifecycle_manager = StageLifecycleManager(
            registry=self.registry,
            teardown_engine=self.teardown_engine,
            ks=self.kill_switch,
        )

        # Runners
        self._in_memory_runner = InMemorySimulatorRunner()
        self._docker_runner = DockerRunner()

        # In-memory execution store (run_id -> CampaignExecutionRecord)
        self._execution_history: dict[str, CampaignExecutionRecord] = {}
        # Cancellation request flags (run_id -> True)
        self._cancelled_runs: set[str] = set()

    def get_runner(self, prefer_docker: bool = False) -> BaseRunner:
        """Select runner based on preference and availability."""
        if prefer_docker:
            return self._docker_runner
        return self._in_memory_runner

    def cancel_campaign(self, run_id: str) -> bool:
        """Request immediate cancellation of a running campaign."""
        self._cancelled_runs.add(run_id)
        logger.warning(f"Cancellation requested for campaign run {run_id}")
        return True

    def execute_campaign(
        self,
        plan: CampaignPlan,
        mode: ExecutionMode = ExecutionMode.DRY_RUN,
        environment_data: NormalizedEnvironmentData | None = None,
        prefer_docker: bool = False,
        context: dict[str, Any] | None = None,
    ) -> CampaignExecutionRecord:
        """Execute or dry-run a validated adversary emulation campaign plan.

        Args:
            plan: The CampaignPlan to execute.
            mode: DRY_RUN (default) or LIVE_SIMULATION.
            environment_data: Current environment data for baseline capture and verification.
            prefer_docker: Whether to use containerized DockerRunner if available.
            context: Additional execution parameters.

        Returns:
            CampaignExecutionRecord containing full stage execution records and teardown status.
        """
        run_id = plan.run_id
        start_wall_time = datetime.now(UTC).isoformat()
        start_perf = time.perf_counter()

        logger.info(
            f"Initiating campaign execution: plan_id={plan.campaign_id}, run_id={run_id}, "
            f"mode={mode}, stages={len(plan.stages)}"
        )

        # 1. Safety validation: verify kill switch is not engaged
        if self.kill_switch.is_active():
            raise FalconSecurityException(
                "Execution rejected: Emergency Kill Switch is ACTIVE. Halting all campaign actions."
            )

        # 2. Safety validation: verify plan was approved by policy gate
        if not plan.approved_by_policy and mode == ExecutionMode.LIVE_SIMULATION:
            raise FalconSecurityException(
                f"Execution rejected: Campaign '{plan.campaign_id}' has not been approved by the Safety Policy Gate."
            )

        # 3. Verify all techniques are recognized by the approved registry
        for stage in plan.stages:
            if not self.registry.is_technique_approved(stage.technique_id):
                raise FalconSecurityException(
                    f"Execution rejected: Stage '{stage.stage_id}' specifies unapproved technique '{stage.technique_id}'."
                )

        # 4. Pre-run baseline capture
        account_id = "000000000000"
        if environment_data and environment_data.account_id:
            account_id = environment_data.account_id
        pre_run_baseline = BaselineRecorder.capture(
            run_id=run_id, environment_data=environment_data, account_id=account_id
        )

        # Initialize execution record
        record = CampaignExecutionRecord(
            run_id=run_id,
            campaign_id=plan.campaign_id,
            mode=mode,
            status=ExecutionStatus.RUNNING,
            start_time=start_wall_time,
            total_stages=len(plan.stages),
            metadata={
                "objective": plan.objective,
                "planner_provider": plan.planner_provider,
                "source_attack_path_id": plan.source_attack_path_id,
                "prefer_docker": prefer_docker,
            },
        )
        self._execution_history[run_id] = record

        # Select runner
        runner = self.get_runner(prefer_docker=prefer_docker)

        completed_stage_ids: set[str] = set()
        executed_stages: list[StageExecutionRecord] = []
        overall_status = ExecutionStatus.COMPLETED
        error_message: str | None = None

        # Execute stages sequentially
        for stage in plan.stages:
            # Check kill switch before every stage (< 2 second latency guarantee)
            if self.kill_switch.is_active():
                logger.critical(
                    f"Emergency Kill Switch engaged during run {run_id}. Aborting remaining stages."
                )
                overall_status = ExecutionStatus.ABORTED_BY_KILL_SWITCH
                error_message = "Execution aborted by Emergency Kill Switch."
                break

            # Check manual cancellation
            if run_id in self._cancelled_runs:
                logger.warning(f"Campaign run {run_id} cancelled by operator.")
                overall_status = ExecutionStatus.CANCELLED
                error_message = "Execution cancelled by operator."
                break

            stage_start_wall = datetime.now(UTC).isoformat()
            stage_start_perf = time.perf_counter()

            try:
                # Pre-stage safety gate & dependency check
                self.lifecycle_manager.pre_stage_check(
                    stage=stage,
                    completed_stage_ids=completed_stage_ids,
                    run_id=run_id,
                )

                # Execute stage via designated runner
                sim_event = runner.execute_stage(
                    stage=stage,
                    run_id=run_id,
                    mode=mode,
                    context=context,
                )

                # Generate and record synthetic IOCs and telemetry
                iocs = SyntheticIOCGenerator.generate_iocs_for_stage(
                    run_id=run_id,
                    technique_id=stage.technique_id,
                    target_resource_id=stage.target_resource_id,
                    parameters=stage.action_parameters,
                )
                self.telemetry_collector.record_simulation_event(run_id, sim_event)
                self.telemetry_collector.record_iocs(run_id, iocs)

                # Emit benign C2 or DNS signalling events if applicable (FR-3.4)
                if stage.tactic == AttackTactic.COMMAND_AND_CONTROL or "T1071" in stage.technique_id:
                    self.telemetry_collector.c2_sink.emit_beacon(
                        run_id=run_id, technique_id=stage.technique_id
                    )
                if "T1071.004" in stage.technique_id or "T1572" in stage.technique_id:
                    self.telemetry_collector.dns_sink.record_query(
                        run_id=run_id,
                        technique_id=stage.technique_id,
                        subdomain_token=stage.stage_id.lower().replace("-", ""),
                    )

                # Post-stage lifecycle processing
                stage_record = self.lifecycle_manager.post_stage_hook(
                    stage=stage,
                    event=sim_event,
                    run_id=run_id,
                    start_time_iso=stage_start_wall,
                    start_perf=stage_start_perf,
                    runner_name=runner.runner_name,
                )
                executed_stages.append(stage_record)
                completed_stage_ids.add(stage.stage_id)

            except Exception as exc:
                logger.error(f"Stage '{stage.stage_id}' execution failed: {exc}")
                duration_ms = (time.perf_counter() - stage_start_perf) * 1000.0
                failed_stage_record = StageExecutionRecord(
                    stage_id=stage.stage_id,
                    stage_name=stage.stage_name,
                    tactic=stage.tactic,
                    technique_id=stage.technique_id,
                    technique_name=stage.technique_name,
                    target_resource_id=stage.target_resource_id,
                    status=ExecutionStatus.FAILED,
                    start_time=stage_start_wall,
                    end_time=datetime.now(UTC).isoformat(),
                    duration_ms=round(duration_ms, 2),
                    error=str(exc),
                    runner_type=runner.runner_name,
                )
                executed_stages.append(failed_stage_record)
                overall_status = ExecutionStatus.FAILED
                error_message = f"Stage '{stage.stage_id}' failed: {exc}"
                break

        # Post-execution teardown and baseline recovery (FR-3.5)
        teardown_result = self.teardown_engine.execute_teardown(
            run_id=run_id,
            pre_run_baseline=pre_run_baseline,
            current_environment=environment_data,
        )

        total_duration_ms = (time.perf_counter() - start_perf) * 1000.0
        record.end_time = datetime.now(UTC).isoformat()
        record.duration_ms = round(total_duration_ms, 2)
        record.status = overall_status
        record.stages = executed_stages
        record.completed_stages = len(completed_stage_ids)
        record.failed_stages = len([s for s in executed_stages if s.status == ExecutionStatus.FAILED])
        record.teardown_status = teardown_result.status
        record.error = error_message

        logger.info(
            f"Campaign execution completed: run_id={run_id}, status={overall_status}, "
            f"completed_stages={record.completed_stages}/{record.total_stages}, "
            f"duration={record.duration_ms}ms"
        )

        return record

    def get_execution(self, run_id: str) -> CampaignExecutionRecord | None:
        """Retrieve execution record by run ID."""
        return self._execution_history.get(run_id)

    def list_executions(self) -> list[CampaignExecutionRecord]:
        """List all recorded campaign executions."""
        return list(self._execution_history.values())
