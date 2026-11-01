"""Data models and schemas for MITRE ATT&CK technique catalog and contracts."""

from datetime import UTC, datetime
from enum import StrEnum
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field


class AttackTactic(StrEnum):
    """MITRE ATT&CK Tactics represented in Falcon Strike-AI."""

    INITIAL_ACCESS = "Initial Access"
    DISCOVERY = "Discovery"
    PRIVILEGE_ESCALATION = "Privilege Escalation"
    PERSISTENCE = "Persistence"
    CREDENTIAL_ACCESS = "Credential Access"
    DEFENSE_EVASION = "Defense Evasion"
    COMMAND_AND_CONTROL = "Command and Control"
    EXFILTRATION = "Exfiltration"


class TechniqueRiskLevel(StrEnum):
    """Risk tier of the emulated technique."""

    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class TechniqueContract(BaseModel):
    """Declared safety, observable, and execution contract for an emulation technique (FR-3.1)."""

    technique_id: str = Field(description="MITRE ATT&CK technique ID (e.g., T1078, T1071.004)")
    subtechnique_id: str | None = Field(default=None, description="Subtechnique ID if applicable")
    name: str = Field(description="Descriptive name of the technique")
    tactic: AttackTactic = Field(description="Primary ATT&CK tactic")
    description: str = Field(description="Operational description of observable behavior")
    required_resource_types: list[str] = Field(
        default_factory=list,
        description="Target resource types required (e.g. IAM_ROLE, EC2_INSTANCE)",
    )
    preconditions: list[str] = Field(
        default_factory=list, description="State conditions required before emulation can run"
    )
    expected_telemetry: list[str] = Field(
        default_factory=list, description="CloudTrail, VPC Flow, or system events expected"
    )
    expected_iocs: list[str] = Field(
        default_factory=list, description="Deterministic benign IOC signatures emitted"
    )
    risk_level: TechniqueRiskLevel = Field(default=TechniqueRiskLevel.LOW)
    safety_constraints: list[str] = Field(
        default_factory=list,
        description="Guaranteed behavioral bounds (e.g. read-only, benign marker only)",
    )
    teardown_required: bool = Field(
        default=False,
        description="Whether this technique alters state requiring post-run reversion",
    )
    teardown_instructions: str = Field(
        default="No persistent state created; zero teardown action required.",
        description="Reversion instructions for teardown engine",
    )


class SimulationEvent(BaseModel):
    """Deterministic, benign observation event produced during technique simulation (FR-3.2)."""

    event_id: str = Field(default_factory=lambda: f"SIM-{uuid4().hex[:8].upper()}")
    technique_id: str
    tactic: AttackTactic
    target_resource_id: str
    timestamp: str = Field(default_factory=lambda: datetime.now(UTC).isoformat())
    status: str = Field(default="EMULATED_BENIGN")
    simulated_api_call: str | None = None
    emitted_iocs: list[dict[str, Any]] = Field(default_factory=list)
    emitted_telemetry: list[dict[str, Any]] = Field(default_factory=list)
    output_marker: str | None = None
    duration_ms: float = 0.0
