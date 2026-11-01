"""Data models and schemas for SOC adversary emulation assessment reports (FR-5.2, FR-5.3)."""

from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field

from backend.app.detection.models import CorrelatedTechniqueResult
from backend.app.telemetry.models import SyntheticIOC


class RemediationItem(BaseModel):
    """Specific defensive remediation guidance mapped to discovered misconfiguration or technique."""

    remediation_id: str = Field(default_factory=lambda: f"REM-{uuid4().hex[:6].upper()}")
    technique_id: str
    target_resource_id: str
    priority: str = Field(default="HIGH", description="CRITICAL, HIGH, MEDIUM, LOW")
    recommendation: str
    rationale: str
    aws_cli_remediation_command: str | None = None


class SOCReportData(BaseModel):
    """Complete, consolidated SOC assessment report data structure (FR-5.2)."""

    report_id: str = Field(default_factory=lambda: f"SOC-REP-{uuid4().hex[:8].upper()}")
    run_id: str = Field(description="Unique campaign correlation run ID")
    campaign_id: str
    target_account_id: str = "000000000000"
    generated_at: str = Field(default_factory=lambda: datetime.now(UTC).isoformat())

    # Strict Provenance Labelling (No False Claims)
    environment_provenance: str = Field(
        default="SYNTHETIC_DATA",
        description="SYNTHETIC_DATA (deterministic offline fixture) or LIVE_AWS (real authenticated scan)",
    )
    runner_provenance: str = Field(
        default="IN_MEMORY_SIMULATION",
        description="IN_MEMORY_SIMULATION (pure Python) or CONTAINER_SANDBOX (Docker isolated)",
    )
    detection_provenance: str = Field(
        default="DETECTION_STUB",
        description="DETECTION_STUB (local simulated sensor) or REAL_SIEM_INTEGRATION (CrowdStrike/Splunk)",
    )

    executive_summary: str
    objective: str
    attack_path_narrative: str
    attack_path_hops: list[dict[str, Any]] = Field(default_factory=list)

    # Technique & Detection Metrics
    total_executed_techniques: int = 0
    detected_count: int = 0
    partially_detected_count: int = 0
    missed_count: int = 0
    coverage_percentage: float = 0.0
    mean_time_to_detect_seconds: float | None = None

    techniques: list[CorrelatedTechniqueResult] = Field(default_factory=list)
    synthetic_iocs: list[SyntheticIOC] = Field(default_factory=list)
    remediation_recommendations: list[RemediationItem] = Field(default_factory=list)

    # Verifications
    teardown_verification: dict[str, Any] = Field(default_factory=dict)
    audit_chain_verification: dict[str, Any] = Field(default_factory=dict)

    limitations_and_disclaimers: list[str] = Field(default_factory=list)

