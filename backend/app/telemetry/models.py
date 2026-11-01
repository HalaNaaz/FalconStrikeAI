"""Pydantic schemas and models for telemetry events, C2 signalling, and synthetic IOCs."""

from datetime import UTC, datetime
from enum import StrEnum
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field

from backend.app.techniques.models import SimulationEvent


class IOCType(StrEnum):
    """Categorization of synthetic indicators of compromise."""

    SHA256 = "SHA256"
    IP_ADDRESS = "IP_ADDRESS"
    DOMAIN = "DOMAIN"
    FILE_PATH = "FILE_PATH"
    USER_AGENT = "USER_AGENT"
    API_CALL = "API_CALL"
    PROCESS_NAME = "PROCESS_NAME"


class C2BeaconEvent(BaseModel):
    """Benign C2 signalling / beaconing heartbeat event (FR-3.4)."""

    beacon_id: str = Field(default_factory=lambda: f"BCN-{uuid4().hex[:8].upper()}")
    run_id: str
    technique_id: str
    destination_host: str = "127.0.0.1"
    destination_port: int = 8443
    protocol: str = "HTTPS"
    interval_seconds: float = 5.0
    jitter_percentage: float = 20.0
    actual_delay_seconds: float = 5.0
    marker_payload: str
    timestamp: str = Field(default_factory=lambda: datetime.now(UTC).isoformat())


class DNSSignallingEvent(BaseModel):
    """Benign DNS covert-channel / signalling query event (FR-3.4)."""

    query_id: str = Field(default_factory=lambda: f"DNS-{uuid4().hex[:8].upper()}")
    run_id: str
    technique_id: str
    query_name: str
    query_type: str = "TXT"
    simulated_response: str
    marker_token: str
    timestamp: str = Field(default_factory=lambda: datetime.now(UTC).isoformat())


class SyntheticIOC(BaseModel):
    """Safe, observable synthetic Indicator of Compromise tagged with benign markers."""

    ioc_id: str = Field(default_factory=lambda: f"IOC-{uuid4().hex[:8].upper()}")
    run_id: str
    technique_id: str
    ioc_type: IOCType
    value: str
    is_benign_marker: bool = True
    detection_guidance: str
    timestamp: str = Field(default_factory=lambda: datetime.now(UTC).isoformat())


class TelemetryExportPackage(BaseModel):
    """Consolidated telemetry and IOC package for detection engineering validation."""

    export_id: str = Field(default_factory=lambda: f"EXP-{uuid4().hex[:8].upper()}")
    run_id: str
    campaign_id: str
    generated_at: str = Field(default_factory=lambda: datetime.now(UTC).isoformat())
    total_events: int = 0
    c2_beacons: list[C2BeaconEvent] = Field(default_factory=list)
    dns_queries: list[DNSSignallingEvent] = Field(default_factory=list)
    iocs: list[SyntheticIOC] = Field(default_factory=list)
    raw_events: list[SimulationEvent] = Field(default_factory=list)
    summary: dict[str, Any] = Field(default_factory=dict)

