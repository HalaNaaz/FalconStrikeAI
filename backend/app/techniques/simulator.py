"""Inert, deterministic technique simulation engine producing structured observations (FR-3.2)."""

import time
from typing import Any
from uuid import uuid4

from backend.app.core.logging import logger
from backend.app.techniques.models import SimulationEvent, TechniqueContract


class TechniqueSimulator:
    """Executes safe, inert, behavioural emulation producing observable telemetry."""

    @staticmethod
    def simulate(
        contract: TechniqueContract,
        target_resource_id: str,
        parameters: dict[str, Any] | None = None,
    ) -> SimulationEvent:
        """Simulate an ATT&CK technique safely without modifying cloud resources."""
        params = parameters or {}
        start_time = time.perf_counter()

        logger.info(
            f"Simulating technique {contract.technique_id} ({contract.name}) against target {target_resource_id}"
        )

        # Deterministic benign marker generation
        marker_id = f"FALCON_BENIGN_MARKER_{contract.technique_id}_{uuid4().hex[:6].upper()}"

        # Generate benign IOCs based on declared contract
        emitted_iocs: list[dict[str, Any]] = []
        for ioc_str in contract.expected_iocs:
            parts = ioc_str.split(": ", 1)
            if len(parts) == 2:
                emitted_iocs.append({"type": parts[0], "value": parts[1], "marker_id": marker_id})
            else:
                emitted_iocs.append({"type": "signature", "value": ioc_str, "marker_id": marker_id})

        # Generate telemetry events
        emitted_telemetry: list[dict[str, Any]] = []
        for tel_str in contract.expected_telemetry:
            emitted_telemetry.append(
                {
                    "source": "simulated_cloudtrail"
                    if "CloudTrail" in tel_str
                    else "simulated_vpc_flow",
                    "event_pattern": tel_str,
                    "target_resource": target_resource_id,
                    "parameters": params,
                }
            )

        duration_ms = (time.perf_counter() - start_time) * 1000.0

        return SimulationEvent(
            technique_id=contract.technique_id,
            tactic=contract.tactic,
            target_resource_id=target_resource_id,
            status="EMULATED_BENIGN",
            simulated_api_call=contract.expected_telemetry[0]
            if contract.expected_telemetry
            else "None",
            emitted_iocs=emitted_iocs,
            emitted_telemetry=emitted_telemetry,
            output_marker=marker_id,
            duration_ms=round(duration_ms, 2),
        )
