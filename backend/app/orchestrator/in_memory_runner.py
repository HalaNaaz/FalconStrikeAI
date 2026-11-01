"""Safe in-memory technique emulation runner (FR-3.3)."""

from typing import Any

from backend.app.core.exceptions import FalconSecurityException
from backend.app.core.logging import logger
from backend.app.orchestrator.interfaces import BaseRunner
from backend.app.orchestrator.models import ExecutionMode
from backend.app.planner.models import CampaignStage
from backend.app.techniques.models import SimulationEvent
from backend.app.techniques.registry import technique_registry
from backend.app.techniques.simulator import TechniqueSimulator


class InMemorySimulatorRunner(BaseRunner):
    """Executes safe, inert, behavioural emulation completely in-memory (FR-3.3).

    Key Characteristics:
    - Zero host process execution
    - Zero live cloud infrastructure mutations
    - Fully deterministic, producing verifiable telemetry and benign IOCs
    - Safe fallback when container environments are offline
    """

    @property
    def runner_name(self) -> str:
        return "in_memory_simulator"

    def is_available(self) -> bool:
        """In-memory runner is always available."""
        return True

    def execute_stage(
        self,
        stage: CampaignStage,
        run_id: str,
        mode: ExecutionMode,
        context: dict[str, Any] | None = None,
    ) -> SimulationEvent:
        """Simulate an approved technique stage in memory without mutating cloud assets."""
        contract = technique_registry.get_contract(stage.technique_id)
        if not contract:
            raise FalconSecurityException(
                f"Execution rejected: Technique {stage.technique_id} is not present in the approved registry."
            )

        logger.info(
            f"Executing in-memory simulation for stage {stage.stage_id} ({stage.technique_id}) "
            f"in mode={mode} [run_id={run_id}]"
        )

        params = dict(stage.action_parameters)
        params["run_id"] = run_id
        params["execution_mode"] = str(mode)

        # Execute safe, inert simulation via TechniqueSimulator
        event = TechniqueSimulator.simulate(
            contract=contract,
            target_resource_id=stage.target_resource_id,
            parameters=params,
        )

        return event

