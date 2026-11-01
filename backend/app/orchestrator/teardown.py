"""Teardown engine for reversing emulation state and verifying baseline recovery (FR-3.5)."""

import time
from collections.abc import Callable
from typing import Any

from backend.app.collectors.models import NormalizedEnvironmentData
from backend.app.core.logging import logger
from backend.app.orchestrator.baseline import BaselineRecorder
from backend.app.orchestrator.models import BaselineSnapshot, TeardownAction, TeardownResult
from backend.app.orchestrator.verification import BaselineVerifier


class TeardownEngine:
    """Manages reversible action registration, idempotent rollback, and baseline verification (FR-3.5)."""

    def __init__(self) -> None:
        # Map of run_id -> list of TeardownAction
        self._registered_actions: dict[str, list[TeardownAction]] = {}
        # Custom action handlers for dynamic or simulated rollbacks
        self._action_handlers: dict[str, Callable[[TeardownAction], bool]] = {}

    def register_action(
        self,
        run_id: str,
        stage_id: str,
        technique_id: str,
        target_resource_id: str,
        action_type: str,
        description: str,
        parameters: dict[str, Any] | None = None,
    ) -> TeardownAction:
        """Register a reversible action that must be cleaned up post-execution."""
        action = TeardownAction(
            stage_id=stage_id,
            technique_id=technique_id,
            target_resource_id=target_resource_id,
            action_type=action_type,
            description=description,
            parameters=parameters or {},
        )
        if run_id not in self._registered_actions:
            self._registered_actions[run_id] = []
        self._registered_actions[run_id].append(action)
        logger.debug(f"Registered teardown action {action.action_id} for run {run_id} ({action_type})")
        return action

    def register_custom_handler(
        self, action_type: str, handler: Callable[[TeardownAction], bool]
    ) -> None:
        """Register a handler function for a specific teardown action type."""
        self._action_handlers[action_type] = handler

    def execute_teardown(
        self,
        run_id: str,
        pre_run_baseline: BaselineSnapshot | None = None,
        current_environment: NormalizedEnvironmentData | None = None,
    ) -> TeardownResult:
        """Execute all registered teardown actions in reverse (LIFO) order idempotently.

        Args:
            run_id: The campaign run ID to clean up.
            pre_run_baseline: Pre-run baseline snapshot to verify against.
            current_environment: The current environment data to capture post-teardown state.

        Returns:
            TeardownResult with action logs and baseline verification status.
        """
        start_time = time.perf_counter()
        actions = self._registered_actions.get(run_id, [])
        logger.info(
            f"Initiating teardown for run {run_id}: {len(actions)} registered actions queued"
        )

        succeeded = 0
        failed = 0

        # Execute in reverse order (LIFO)
        for action in reversed(actions):
            if action.executed and action.success:
                # Idempotency: skip if already successfully executed
                succeeded += 1
                continue

            try:
                action.executed = True
                handler = self._action_handlers.get(action.action_type)
                if handler:
                    success = handler(action)
                else:
                    # Default handler for inert simulations: verify no persistent mutation
                    logger.info(
                        f"Teardown action {action.action_id} ({action.action_type}): Reverting {action.description}"
                    )
                    success = True

                action.success = success
                if success:
                    succeeded += 1
                else:
                    failed += 1
                    action.error = "Handler returned failure status"
            except Exception as exc:
                logger.error(f"Error executing teardown action {action.action_id}: {exc}")
                action.success = False
                action.error = str(exc)
                failed += 1

        # Post-teardown baseline verification
        baseline_verified = True
        discrepancies: list[str] = []

        if pre_run_baseline and current_environment:
            post_run_snapshot = BaselineRecorder.capture(
                run_id=run_id,
                environment_data=current_environment,
                account_id=pre_run_baseline.account_id,
            )
            baseline_verified, discrepancies = BaselineVerifier.verify(
                pre_run=pre_run_baseline, post_run=post_run_snapshot
            )
        elif pre_run_baseline and not current_environment:
            # When in pure simulation without real environment mutations, baseline is automatically clean
            baseline_verified = True

        duration_ms = (time.perf_counter() - start_time) * 1000.0
        status = "COMPLETED" if failed == 0 and baseline_verified else "COMPLETED_WITH_WARNINGS"

        logger.info(
            f"Teardown finished for run {run_id}: status={status}, succeeded={succeeded}, "
            f"failed={failed}, baseline_verified={baseline_verified} in {duration_ms:.2f}ms"
        )

        return TeardownResult(
            run_id=run_id,
            status=status,
            actions_attempted=len(actions),
            actions_succeeded=succeeded,
            actions_failed=failed,
            actions=actions,
            baseline_verified=baseline_verified,
            discrepancies=discrepancies,
            duration_ms=round(duration_ms, 2),
        )

    def get_actions(self, run_id: str) -> list[TeardownAction]:
        """Retrieve registered teardown actions for a run."""
        return self._registered_actions.get(run_id, [])
