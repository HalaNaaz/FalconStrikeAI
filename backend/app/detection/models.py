"""Data models and schemas for detection correlation, SIEM adapters, and MTTD metrics (FR-5.1)."""

from datetime import UTC, datetime
from enum import StrEnum
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field

from backend.app.telemetry.models import IOCType


class DetectionStatus(StrEnum):
    """Correlation verdict for an individual emulated technique."""

    DETECTED = "DETECTED"
    PARTIALLY_DETECTED = "PARTIALLY_DETECTED"
    MISSED = "MISSED"


class DetectionSourceType(StrEnum):
    """Provenance and classification of the security alert source."""

    REAL_INTEGRATION = "REAL_INTEGRATION"
    DETECTION_STUB = "DETECTION_STUB"
    TEST_FIXTURE = "TEST_FIXTURE"


class SecurityDetectionEvent(BaseModel):
    """An alert or telemetry finding received from a SIEM, EDR, or detection stub."""

    detection_id: str = Field(default_factory=lambda: f"DET-{uuid4().hex[:8].upper()}")
    run_id: str = Field(description="Run correlation ID")
    campaign_id: str = Field(description="Campaign correlation ID")
    technique_id: str = Field(description="MITRE ATT&CK technique ID (e.g., T1078)")
    matched_ioc_value: str | None = Field(default=None, description="Exact IOC string that triggered detection")
    matched_ioc_type: IOCType | None = Field(default=None, description="Type of IOC matched")
    severity: str = Field(default="MEDIUM", description="Severity tier: LOW, MEDIUM, HIGH, CRITICAL")
    title: str = Field(description="Security alert title")
    description: str = Field(description="Alert explanation or detection rule name")
    source_type: DetectionSourceType = Field(default=DetectionSourceType.DETECTION_STUB)
    source_name: str = Field(default="detection_stub", description="SIEM or sensor name (e.g., falcon_edr, splunk)")
    detected_at: str = Field(default_factory=lambda: datetime.now(UTC).isoformat())
    raw_payload: dict[str, Any] = Field(default_factory=dict)


class CorrelatedTechniqueResult(BaseModel):
    """Correlation findings for an individual executed technique."""

    technique_id: str
    technique_name: str
    tactic: str
    status: DetectionStatus
    ground_truth_event_id: str | None = None
    ground_truth_timestamp: str | None = None
    first_detection_timestamp: str | None = None
    detection_latency_seconds: float | None = None
    detection_count: int = 0
    detections: list[SecurityDetectionEvent] = Field(default_factory=list)
    matched_iocs: list[str] = Field(default_factory=list)
    unmatched_iocs: list[str] = Field(default_factory=list)


class DetectionCorrelationReport(BaseModel):
    """Consolidated adversary detection correlation report (FR-5.1)."""

    report_id: str = Field(default_factory=lambda: f"CORR-{uuid4().hex[:8].upper()}")
    run_id: str
    campaign_id: str
    evaluated_at: str = Field(default_factory=lambda: datetime.now(UTC).isoformat())
    detection_source: str = "detection_stub"
    detection_source_type: DetectionSourceType = DetectionSourceType.DETECTION_STUB
    total_executed_techniques: int = 0
    detected_count: int = 0
    partially_detected_count: int = 0
    missed_count: int = 0
    coverage_percentage: float = 0.0
    mean_time_to_detect_seconds: float | None = None
    techniques: list[CorrelatedTechniqueResult] = Field(default_factory=list)
    summary: dict[str, Any] = Field(default_factory=dict)

