"""Docker containerized runtime runner with strict security containment (FR-3.2)."""

import json
from typing import Any

from backend.app.core.exceptions import FalconSecurityException
from backend.app.core.logging import logger
from backend.app.orchestrator.interfaces import BaseRunner
from backend.app.orchestrator.models import ExecutionMode
from backend.app.planner.models import CampaignStage
from backend.app.techniques.models import SimulationEvent
from backend.app.techniques.registry import technique_registry


class DockerRuntimeUnavailableError(FalconSecurityException):
    """Raised when container isolation is requested but Docker daemon is offline."""

    pass


class DockerRunner(BaseRunner):
    """Executes emulation techniques within isolated, restricted Docker containers (FR-3.2).

    Security Containment Guarantees (when Docker is active):
    - Non-root user (UID 10001 / nobody)
    - Dropped Linux capabilities (--cap-drop=ALL)
    - Read-only root filesystem (--read-only)
    - Memory cap (256MB) and CPU quota (0.5 cores)
    - Isolated network with egress prohibited except to lab C2 sinks
    - No persistent volume mounts

    Integrity Guarantee:
    - Never degrades into an unisolated host subprocess.
    - If Docker daemon is unavailable, reports is_available() == False honestly.
    """

    def __init__(self, image_name: str = "falconstrike-sandbox:latest") -> None:
        self.image_name = image_name
        self._docker_client = None
        self._init_checked = False
        self._available = False

    @property
    def runner_name(self) -> str:
        return "docker_container"

    def is_available(self) -> bool:
        """Check if Docker daemon is responsive without crashing."""
        try:
            import docker  # type: ignore

            client = docker.from_env()
            client.ping()
            self._docker_client = client
            self._available = True
            return True
        except Exception as exc:
            logger.debug(f"Docker daemon unavailable: {exc}")
            self._available = False
            self._docker_client = None
            return False

    def execute_stage(
        self,
        stage: CampaignStage,
        run_id: str,
        mode: ExecutionMode,
        context: dict[str, Any] | None = None,
    ) -> SimulationEvent:
        """Execute stage inside an isolated Docker sandbox."""
        if not self.is_available():
            raise DockerRuntimeUnavailableError(
                "Docker container runtime is unavailable. Falcon Strike-AI refuses to execute "
                "in unisolated host space when container sandbox mode is selected."
            )

        contract = technique_registry.get_contract(stage.technique_id)
        if not contract:
            raise ValueError(f"Technique {stage.technique_id} is not in the approved registry.")

        # If Docker is available, run container with strict security bounds
        client = self._docker_client
        logger.info(
            f"Launching containerized sandbox execution for technique {stage.technique_id} in run {run_id}"
        )

        container_cmd = [
            "python",
            "-m",
            "falconstrike.sandbox_entrypoint",
            "--technique-id",
            stage.technique_id,
            "--target",
            stage.target_resource_id,
            "--run-id",
            run_id,
            "--mode",
            str(mode),
            "--params",
            json.dumps(stage.action_parameters),
        ]

        try:
            container = client.containers.create(  # type: ignore
                image=self.image_name,
                command=container_cmd,
                user="10001:10001",
                cap_drop=["ALL"],
                read_only=True,
                mem_limit="256m",
                cpu_quota=50000,
                network_mode="none",
            )
            try:
                container.start()
                wait_res = container.wait(timeout=30)
                status_code = wait_res.get("StatusCode", 0) if isinstance(wait_res, dict) else int(wait_res)
                logs_bytes = container.logs(stdout=True, stderr=True)
                raw_output = logs_bytes.decode("utf-8") if isinstance(logs_bytes, bytes) else str(logs_bytes)
                if status_code != 0:
                    raise RuntimeError(f"Container exited with non-zero status {status_code}: {raw_output}")
                parsed_result = json.loads(raw_output)
                return SimulationEvent(**parsed_result)
            finally:
                try:
                    container.remove(force=True)
                except Exception:
                    pass
        except Exception as exc:
            logger.error(f"Container execution failed: {exc}")
            raise RuntimeError(f"Containerized stage execution failed: {exc}") from exc

