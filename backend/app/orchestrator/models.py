"""Data models and schemas for execution orchestration, lifecycle, and teardown."""

from datetime import UTC, datetime
from enum import StrEnum
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field

from backend.app.techniques.models import AttackTactic, SimulationEvent


class ExecutionMode(StrEnum):
    """Execution mode for adversary emulation campaigns."""

    DRY_RUN = "DRY_RUN"
    LIVE_SIMULATION = "LIVE_SIMULATION"


class ExecutionStatus(StrEnum):
    """Lifecycle status of a campaign or stage execution."""

    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"
    ABORTED_BY_KILL_SWITCH = "ABORTED_BY_KILL_SWITCH"


class StageExecutionRecord(BaseModel):
    """Audit and operational record of an individual stage execution."""

    stage_id: str
    stage_name: str
    tactic: AttackTactic
    technique_id: str
    technique_name: str
    target_resource_id: str
    status: ExecutionStatus = ExecutionStatus.PENDING
    start_time: str | None = None
    end_time: str | None = None
    duration_ms: float = 0.0
    simulation_event: SimulationEvent | None = None
    error: str | None = None
    teardown_required: bool = False
    teardown_status: str | None = None
    runner_type: str = "in_memory"


class CampaignExecutionRecord(BaseModel):
    """Comprehensive execution summary for a multi-stage campaign run (NFR-A3)."""

    execution_id: str = Field(default_factory=lambda: f"EXEC-{uuid4().hex[:8].upper()}")
    run_id: str = Field(description="Unique correlation ID spanning entire campaign lifecycle")
    campaign_id: str
    mode: ExecutionMode = ExecutionMode.DRY_RUN
    status: ExecutionStatus = ExecutionStatus.PENDING
    start_time: str = Field(default_factory=lambda: datetime.now(UTC).isoformat())
    end_time: str | None = None
    duration_ms: float = 0.0
    total_stages: int = 0
    completed_stages: int = 0
    failed_stages: int = 0
    stages: list[StageExecutionRecord] = Field(default_factory=list)
    teardown_status: str = "NOT_STARTED"
    error: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class BaselineSnapshot(BaseModel):
    """Captured environment state prior to campaign execution for post-run verification (FR-3.5)."""

    snapshot_id: str = Field(default_factory=lambda: f"BASE-{uuid4().hex[:8].upper()}")
    run_id: str
    timestamp: str = Field(default_factory=lambda: datetime.now(UTC).isoformat())
    account_id: str
    resource_counts: dict[str, int] = Field(default_factory=dict)
    resource_ids: list[str] = Field(default_factory=list)
    state_fingerprint: str = Field(description="SHA-256 hash of serialized normalized resource state")
    details: dict[str, Any] = Field(default_factory=dict)


class TeardownAction(BaseModel):
    """An individual state-reversion action registered for post-run teardown."""

    action_id: str = Field(default_factory=lambda: f"TEAR-{uuid4().hex[:6].upper()}")
    stage_id: str
    technique_id: str
    target_resource_id: str
    action_type: str
    description: str
    parameters: dict[str, Any] = Field(default_factory=dict)
    executed: bool = False
    success: bool = False
    error: str | None = None


class TeardownResult(BaseModel):
    """Result of post-execution teardown and baseline verification (FR-3.5)."""

    run_id: str
    status: str = "PENDING"
    timestamp: str = Field(default_factory=lambda: datetime.now(UTC).isoformat())
    actions_attempted: int = 0
    actions_succeeded: int = 0
    actions_failed: int = 0
    actions: list[TeardownAction] = Field(default_factory=list)
    baseline_verified: bool = False
    discrepancies: list[str] = Field(default_factory=list)
    duration_ms: float = 0.0

