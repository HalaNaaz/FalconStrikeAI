"""Unit and integration tests for safe execution engine and runners (FR-3.1, FR-3.2, FR-3.3)."""

from unittest.mock import MagicMock, patch

import pytest

from backend.app.collectors.synthetic import SyntheticEnvironmentProvider
from backend.app.core.exceptions import FalconSecurityException
from backend.app.orchestrator.docker_runner import DockerRunner, DockerRuntimeUnavailableError
from backend.app.orchestrator.execution_engine import ExecutionEngine
from backend.app.orchestrator.in_memory_runner import InMemorySimulatorRunner
from backend.app.orchestrator.kill_switch import EmergencyKillSwitch
from backend.app.orchestrator.models import ExecutionMode, ExecutionStatus
from backend.app.planner.models import CampaignPlan, CampaignStage
from backend.app.techniques.models import AttackTactic, TechniqueRiskLevel


@pytest.fixture
def sample_campaign_plan() -> CampaignPlan:
    """Generate a sample valid campaign plan for testing."""
    stage1 = CampaignStage(
        stage_id="STAGE-001",
        stage_name="Initial Discovery",
        tactic=AttackTactic.DISCOVERY,
        technique_id="T1526",
        technique_name="Cloud Service Discovery",
        target_resource_id="arn:aws:iam::000000000000:role/ReadOnlyRole",
        expected_observation="Simulated CloudTrail ListRoles event",
        estimated_risk=TechniqueRiskLevel.LOW,
    )
    stage2 = CampaignStage(
        stage_id="STAGE-002",
        stage_name="Privilege Escalation",
        tactic=AttackTactic.PRIVILEGE_ESCALATION,
        technique_id="T1078",
        technique_name="Valid Accounts",
        target_resource_id="arn:aws:iam::000000000000:role/AdminRole",
        expected_observation="Simulated CloudTrail AssumeRole event",
        estimated_risk=TechniqueRiskLevel.MEDIUM,
        dependencies=["STAGE-001"],
    )
    return CampaignPlan(
        campaign_id="CAMP-TEST-001",
        run_id="RUN-TEST-001",
        source_attack_path_id="PATH-001",
        objective="Test adversary emulation",
        stages=[stage1, stage2],
        selected_techniques=["T1526", "T1078"],
        risk_summary="Low risk containment",
        planning_rationale="Sequential emulation test",
        approved_by_policy=True,
    )


class TestExecutionEngine:
    """Test suite for ExecutionEngine orchestration."""

    def test_dry_run_execution_success(self, sample_campaign_plan: CampaignPlan) -> None:
        """Verify dry-run execution completes safely without modifying environment."""
        ks = EmergencyKillSwitch()
        engine = ExecutionEngine(ks=ks)
        env = SyntheticEnvironmentProvider.generate_flawed_environment("000000000000")

        record = engine.execute_campaign(
            plan=sample_campaign_plan,
            mode=ExecutionMode.DRY_RUN,
            environment_data=env,
        )

        assert record.status == ExecutionStatus.COMPLETED
        assert record.mode == ExecutionMode.DRY_RUN
        assert record.completed_stages == 2
        assert record.failed_stages == 0
        assert len(record.stages) == 2
        assert record.stages[0].technique_id == "T1526"
        assert record.stages[0].status == ExecutionStatus.COMPLETED
        assert record.stages[1].technique_id == "T1078"
        assert record.stages[1].status == ExecutionStatus.COMPLETED
        assert record.teardown_status == "COMPLETED"

    def test_live_simulation_requires_policy_approval(
        self, sample_campaign_plan: CampaignPlan
    ) -> None:
        """Verify live execution is rejected if policy gate approval is missing."""
        sample_campaign_plan.approved_by_policy = False
        ks = EmergencyKillSwitch()
        engine = ExecutionEngine(ks=ks)

        with pytest.raises(FalconSecurityException, match="not been approved by the Safety Policy Gate"):
            engine.execute_campaign(
                plan=sample_campaign_plan,
                mode=ExecutionMode.LIVE_SIMULATION,
            )

    def test_unapproved_technique_rejected(self, sample_campaign_plan: CampaignPlan) -> None:
        """Verify plan containing unapproved technique ID is rejected immediately."""
        unapproved_stage = CampaignStage(
            stage_id="STAGE-BAD",
            stage_name="Unknown Action",
            tactic=AttackTactic.DEFENSE_EVASION,
            technique_id="T9999_MALICIOUS_CUSTOM",
            technique_name="Unapproved",
            target_resource_id="arn:aws:iam::000000000000:role/Test",
            expected_observation="None",
        )
        sample_campaign_plan.stages.append(unapproved_stage)
        sample_campaign_plan.selected_techniques.append("T9999_MALICIOUS_CUSTOM")

        engine = ExecutionEngine()
        with pytest.raises(FalconSecurityException, match="unapproved technique"):
            engine.execute_campaign(sample_campaign_plan)

    def test_missing_dependencies_fails_stage(self, sample_campaign_plan: CampaignPlan) -> None:
        """Verify stage with unfulfilled dependency fails cleanly."""
        sample_campaign_plan.stages[0].dependencies = ["STAGE-NONEXISTENT"]

        engine = ExecutionEngine()
        record = engine.execute_campaign(sample_campaign_plan)

        assert record.status == ExecutionStatus.FAILED
        assert record.completed_stages == 0
        assert record.failed_stages == 1
        assert "missing required prerequisite stages" in str(record.error)

    def test_cancellation_halts_subsequent_stages(self, sample_campaign_plan: CampaignPlan) -> None:
        """Verify manual cancellation stops subsequent stages."""
        engine = ExecutionEngine()
        # Pre-register cancellation
        engine.cancel_campaign(sample_campaign_plan.run_id)

        record = engine.execute_campaign(sample_campaign_plan)
        assert record.status == ExecutionStatus.CANCELLED
        assert record.completed_stages == 0

    def test_in_memory_runner_availability(self) -> None:
        """Verify InMemorySimulatorRunner is always available."""
        runner = InMemorySimulatorRunner()
        assert runner.is_available() is True
        assert runner.runner_name == "in_memory_simulator"


class TestDockerRunner:
    """Test suite for Docker containerized runner containment and availability guarantees."""

    def test_docker_runner_unavailable_when_daemon_offline(self) -> None:
        """Verify DockerRunner reports is_available == False when daemon is offline."""
        runner = DockerRunner()
        mock_docker = MagicMock()
        mock_docker.from_env.side_effect = Exception("Docker daemon not running")
        with patch.dict("sys.modules", {"docker": mock_docker}):
            assert runner.is_available() is False

    def test_docker_runner_raises_unavailable_error_honestly(
        self, sample_campaign_plan: CampaignPlan
    ) -> None:
        """Verify DockerRunner refuses unisolated fallback and raises DockerRuntimeUnavailableError."""
        runner = DockerRunner()
        with patch.object(runner, "is_available", return_value=False):
            with pytest.raises(DockerRuntimeUnavailableError, match="Docker container runtime is unavailable"):
                runner.execute_stage(
                    stage=sample_campaign_plan.stages[0],
                    run_id="RUN-TEST-001",
                    mode=ExecutionMode.DRY_RUN,
                )

    def test_docker_runner_configures_containment_flags_when_online(
        self, sample_campaign_plan: CampaignPlan
    ) -> None:
        """Verify DockerRunner applies dropped caps, read-only rootfs, and memory limits when online."""
        runner = DockerRunner()
        mock_client = MagicMock()
        mock_container = MagicMock()
        mock_container.wait.return_value = {"StatusCode": 0}
        mock_container.logs.return_value = b'{"event_id": "SIM-01", "technique_id": "T1526", "tactic": "Discovery", "target_resource_id": "target", "status": "EMULATED_BENIGN"}'
        mock_client.containers.create.return_value = mock_container

        with patch.object(runner, "is_available", return_value=True):
            runner._docker_client = mock_client
            event = runner.execute_stage(
                stage=sample_campaign_plan.stages[0],
                run_id="RUN-TEST-CONTAINER",
                mode=ExecutionMode.DRY_RUN,
            )

            assert event.technique_id == "T1526"
            mock_client.containers.create.assert_called_once()
            call_kwargs = mock_client.containers.create.call_args.kwargs
            assert call_kwargs["cap_drop"] == ["ALL"]
            assert call_kwargs["read_only"] is True
            assert call_kwargs["user"] == "10001:10001"
            assert call_kwargs["mem_limit"] == "256m"
            mock_container.start.assert_called_once()
            mock_container.remove.assert_called_once_with(force=True)

    def test_docker_runner_live_real_container_execution(
        self, sample_campaign_plan: CampaignPlan
    ) -> None:
        """Verify real container sandbox execution on live Docker engine if available."""
        runner = DockerRunner()
        if not runner.is_available():
            pytest.skip("Docker daemon not running on host")

        event = runner.execute_stage(
            stage=sample_campaign_plan.stages[0],
            run_id="RUN-TEST-LIVE-CONTAINER",
            mode=ExecutionMode.DRY_RUN,
        )
        assert event.technique_id == "T1526"
        assert event.status == "EMULATED_BENIGN"
        assert "sandbox_uid_10001" in (event.output_marker or "")

    def test_docker_runner_real_host_probe_graceful(self) -> None:
        """Verify real DockerRunner probe on host returns boolean without unhandled exception."""
        runner = DockerRunner()
        res = runner.is_available()
        assert isinstance(res, bool)


class TestKubernetesRunner:
    """Test suite for Kubernetes Jobs container runner adapter (NFR-P4)."""

    def test_k8s_runner_unavailable_by_default(self) -> None:
        """Verify KubernetesJobRunner reports False when cluster is unreachable."""
        from backend.app.orchestrator.kubernetes_runner import KubernetesJobRunner

        runner = KubernetesJobRunner()
        with patch.dict("sys.modules", {"kubernetes": None}):
            assert runner.is_available() is False
        assert runner.runner_name == "kubernetes_job"

    def test_k8s_manifest_generation_containment(self, sample_campaign_plan: CampaignPlan) -> None:
        """Verify K8s Job manifest enforces dropped capabilities, non-root UID, and memory quotas."""
        from backend.app.orchestrator.kubernetes_runner import KubernetesJobRunner

        runner = KubernetesJobRunner(namespace="test-sandbox")
        manifest = runner.build_job_manifest(
            stage=sample_campaign_plan.stages[0],
            run_id="RUN-K8S-01",
            mode=ExecutionMode.DRY_RUN,
        )

        assert manifest["kind"] == "Job"
        assert manifest["metadata"]["namespace"] == "test-sandbox"
        pod_spec = manifest["spec"]["template"]["spec"]
        assert pod_spec["securityContext"]["runAsNonRoot"] is True
        assert pod_spec["securityContext"]["runAsUser"] == 10001

        container = pod_spec["containers"][0]
        assert container["securityContext"]["readOnlyRootFilesystem"] is True
        assert container["securityContext"]["capabilities"]["drop"] == ["ALL"]
        assert container["resources"]["limits"]["memory"] == "256Mi"

    def test_k8s_runner_refuses_execution_when_offline(self, sample_campaign_plan: CampaignPlan) -> None:
        """Verify KubernetesJobRunner raises KubernetesRuntimeUnavailableError when cluster is offline."""
        from backend.app.orchestrator.kubernetes_runner import (
            KubernetesJobRunner,
            KubernetesRuntimeUnavailableError,
        )

        runner = KubernetesJobRunner()
        with patch.object(runner, "is_available", return_value=False):
            with pytest.raises(KubernetesRuntimeUnavailableError, match="Kubernetes cluster runtime is unreachable"):
                runner.execute_stage(
                    stage=sample_campaign_plan.stages[0],
                    run_id="RUN-K8S-01",
                    mode=ExecutionMode.DRY_RUN,
                )

    def test_k8s_runner_execution_when_online(self, sample_campaign_plan: CampaignPlan) -> None:
        """Verify KubernetesJobRunner returns structured SimulationEvent when cluster is online."""
        from backend.app.orchestrator.kubernetes_runner import KubernetesJobRunner

        runner = KubernetesJobRunner()
        with patch.object(runner, "is_available", return_value=True):
            event = runner.execute_stage(
                stage=sample_campaign_plan.stages[0],
                run_id="RUN-K8S-01",
                mode=ExecutionMode.DRY_RUN,
            )
            assert event.technique_id == "T1526"
            assert event.status == "EMULATED_BENIGN"
            assert "k8s_runner" in (event.output_marker or "")
