"""State capture helper for environment and runtime auditing (FR-3.5)."""


from backend.app.collectors.models import NormalizedEnvironmentData
from backend.app.orchestrator.baseline import BaselineRecorder
from backend.app.orchestrator.models import BaselineSnapshot


class StateCaptureManager:
    """Manages pre-execution and post-execution state snapshots for campaign runs."""

    def __init__(self) -> None:
        self._snapshots: dict[str, dict[str, BaselineSnapshot]] = {}

    def capture_pre_run(
        self,
        run_id: str,
        environment_data: NormalizedEnvironmentData | None,
        account_id: str = "000000000000",
    ) -> BaselineSnapshot:
        """Capture and cache pre-run baseline snapshot."""
        snapshot = BaselineRecorder.capture(
            run_id=run_id, environment_data=environment_data, account_id=account_id
        )
        if run_id not in self._snapshots:
            self._snapshots[run_id] = {}
        self._snapshots[run_id]["pre_run"] = snapshot
        return snapshot

    def capture_post_run(
        self,
        run_id: str,
        environment_data: NormalizedEnvironmentData | None,
        account_id: str = "000000000000",
    ) -> BaselineSnapshot:
        """Capture and cache post-run state snapshot."""
        snapshot = BaselineRecorder.capture(
            run_id=run_id, environment_data=environment_data, account_id=account_id
        )
        if run_id not in self._snapshots:
            self._snapshots[run_id] = {}
        self._snapshots[run_id]["post_run"] = snapshot
        return snapshot

    def get_pre_run_snapshot(self, run_id: str) -> BaselineSnapshot | None:
        """Retrieve cached pre-run snapshot."""
        return self._snapshots.get(run_id, {}).get("pre_run")

    def get_post_run_snapshot(self, run_id: str) -> BaselineSnapshot | None:
        """Retrieve cached post-run snapshot."""
        return self._snapshots.get(run_id, {}).get("post_run")
