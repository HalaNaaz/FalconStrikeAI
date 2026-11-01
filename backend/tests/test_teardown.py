"""Unit tests for baseline capture, verification, and teardown engine (FR-3.5)."""


from backend.app.collectors.synthetic import SyntheticEnvironmentProvider
from backend.app.orchestrator.baseline import BaselineRecorder
from backend.app.orchestrator.models import BaselineSnapshot, TeardownAction
from backend.app.orchestrator.teardown import TeardownEngine
from backend.app.orchestrator.verification import BaselineVerifier


class TestBaselineRecorderAndVerifier:
    """Test suite for BaselineRecorder and BaselineVerifier."""

    def test_baseline_capture_fingerprint_deterministic(self) -> None:
        """Verify baseline capture creates reproducible SHA-256 fingerprint."""
        env = SyntheticEnvironmentProvider.generate_flawed_environment("000000000000")
        snap1 = BaselineRecorder.capture("RUN-1", env, "000000000000")
        snap2 = BaselineRecorder.capture("RUN-2", env, "000000000000")

        assert snap1.state_fingerprint == snap2.state_fingerprint
        assert snap1.resource_counts["iam_roles"] > 0
        assert len(snap1.resource_ids) > 0

    def test_baseline_capture_empty_environment(self) -> None:
        """Verify handling when environment is None."""
        snap = BaselineRecorder.capture("RUN-EMPTY", None, "000000000000")
        assert snap.resource_counts["iam_roles"] == 0
        assert len(snap.resource_ids) == 0
        assert snap.state_fingerprint is not None

    def test_baseline_verifier_exact_match(self) -> None:
        """Verify verification passes when fingerprints match."""
        snap1 = BaselineSnapshot(
            run_id="RUN-1",
            account_id="000000000000",
            resource_counts={"iam_roles": 2},
            resource_ids=["role1", "role2"],
            state_fingerprint="abc123hash",
        )
        snap2 = snap1.model_copy()

        verified, discrepancies = BaselineVerifier.verify(snap1, snap2)
        assert verified is True
        assert len(discrepancies) == 0

    def test_baseline_verifier_detects_residual_and_missing_resources(self) -> None:
        """Verify verifier flags uncleaned resources and accidental deletions."""
        pre_run = BaselineSnapshot(
            run_id="RUN-1",
            account_id="000000000000",
            resource_counts={"iam_roles": 2, "s3_buckets": 1},
            resource_ids=["role1", "role2", "bucket1"],
            state_fingerprint="hash_pre",
        )
        post_run = BaselineSnapshot(
            run_id="RUN-1",
            account_id="000000000000",
            resource_counts={"iam_roles": 3, "s3_buckets": 0},
            resource_ids=["role1", "role2", "role_malicious_backdoor"],
            state_fingerprint="hash_post",
        )

        verified, discrepancies = BaselineVerifier.verify(pre_run, post_run)
        assert verified is False
        assert any("Residual resource detected" in d for d in discrepancies)
        assert any("Missing resource detected" in d for d in discrepancies)
        assert any("Count mismatch" in d for d in discrepancies)


class TestTeardownEngine:
    """Test suite for TeardownEngine."""

    def test_teardown_executes_actions_in_lifo_order(self) -> None:
        """Verify teardown actions execute in reverse (LIFO) order."""
        engine = TeardownEngine()
        run_id = "RUN-TEARDOWN-01"

        execution_order: list[str] = []

        def handler1(action: TeardownAction) -> bool:
            execution_order.append(action.action_type)
            return True

        def handler2(action: TeardownAction) -> bool:
            execution_order.append(action.action_type)
            return True

        engine.register_custom_handler("ACTION_FIRST", handler1)
        engine.register_custom_handler("ACTION_SECOND", handler2)

        engine.register_action(
            run_id=run_id,
            stage_id="STAGE-1",
            technique_id="T1526",
            target_resource_id="res1",
            action_type="ACTION_FIRST",
            description="First action",
        )
        engine.register_action(
            run_id=run_id,
            stage_id="STAGE-2",
            technique_id="T1078",
            target_resource_id="res2",
            action_type="ACTION_SECOND",
            description="Second action",
        )

        result = engine.execute_teardown(run_id)
        assert result.status == "COMPLETED"
        assert result.actions_attempted == 2
        assert result.actions_succeeded == 2
        assert execution_order == ["ACTION_SECOND", "ACTION_FIRST"]

    def test_teardown_idempotency(self) -> None:
        """Verify executing teardown multiple times is safe and idempotent."""
        engine = TeardownEngine()
        run_id = "RUN-IDEMPOTENT"

        engine.register_action(
            run_id=run_id,
            stage_id="STAGE-1",
            technique_id="T1526",
            target_resource_id="res1",
            action_type="GENERIC_REVERT",
            description="Generic revert",
        )

        res1 = engine.execute_teardown(run_id)
        assert res1.status == "COMPLETED"
        assert res1.actions_succeeded == 1

        # Second run should skip already executed actions safely
        res2 = engine.execute_teardown(run_id)
        assert res2.status == "COMPLETED"
        assert res2.actions_succeeded == 1


class TestStateCaptureManager:
    """Test suite for StateCaptureManager."""

    def test_capture_pre_and_post_run(self) -> None:
        """Verify StateCaptureManager records and caches pre and post snapshots."""
        from backend.app.orchestrator.state_capture import StateCaptureManager

        mgr = StateCaptureManager()
        env = SyntheticEnvironmentProvider.generate_flawed_environment("000000000000")
        run_id = "RUN-STATE-CAP-01"

        pre = mgr.capture_pre_run(run_id, env, "000000000000")
        assert pre.state_fingerprint is not None
        assert mgr.get_pre_run_snapshot(run_id) == pre

        post = mgr.capture_post_run(run_id, env, "000000000000")
        assert post.state_fingerprint is not None
        assert mgr.get_post_run_snapshot(run_id) == post
        assert mgr.get_pre_run_snapshot("NONEXISTENT") is None
