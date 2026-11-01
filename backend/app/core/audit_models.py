"""Data models and schemas for cryptographic hash-chained audit logging (NFR-A1, NFR-A2, NFR-A3, NFR-A4)."""

import hashlib
import json
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field

GENESIS_HASH: str = "GENESIS_0000000000000000000000000000000000000000000000000000000000000000"


class AuditRecord(BaseModel):
    """Cryptographically linked, immutable audit record (NFR-A1, NFR-A2)."""

    record_id: str = Field(default_factory=lambda: f"AUD-{uuid4().hex[:8].upper()}")
    sequence_number: int = Field(ge=0, description="Strictly monotonic zero-indexed sequence integer")
    run_id: str = Field(description="Unique correlation ID spanning entire campaign run (NFR-A3)")
    campaign_id: str = Field(description="Campaign plan ID")
    timestamp: str = Field(default_factory=lambda: datetime.now(UTC).isoformat())
    actor: str = Field(description="Subsystem or identity: CampaignPlanner, ExecutionEngine, Operator, PolicyGate")
    action: str = Field(description="Action name (e.g., PLAN_GENERATED, STAGE_EXECUTED, KILL_SWITCH_ENGAGED)")
    technique_id: str | None = Field(default=None, description="MITRE ATT&CK technique ID if applicable")
    target_resource: str | None = Field(default=None, description="Resource ARN or target ID")
    outcome: str = Field(default="SUCCESS", description="SUCCESS, DENIED, FAILED, ABORTED")
    ioc_references: list[str] = Field(default_factory=list, description="Associated synthetic IOC IDs or values")
    details: dict[str, Any] = Field(default_factory=dict, description="Structured non-sensitive audit metadata")
    previous_record_hash: str = Field(description="SHA-256 hash of previous record in chain")
    current_record_hash: str = Field(default="", description="SHA-256 hash of this record's canonical contents")
    schema_version: str = Field(default="1.0.0", description="Published audit log schema version (NFR-A4)")

    def compute_hash(self) -> str:
        """Compute deterministic SHA-256 hash of canonicalized record content excluding current_record_hash."""
        canonical_dict = {
            "record_id": self.record_id,
            "sequence_number": self.sequence_number,
            "run_id": self.run_id,
            "campaign_id": self.campaign_id,
            "timestamp": self.timestamp,
            "actor": self.actor,
            "action": self.action,
            "technique_id": self.technique_id,
            "target_resource": self.target_resource,
            "outcome": self.outcome,
            "ioc_references": sorted(self.ioc_references),
            "details": self.details,
            "previous_record_hash": self.previous_record_hash,
            "schema_version": self.schema_version,
        }
        serialized = json.dumps(canonical_dict, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


class AuditChainVerificationResult(BaseModel):
    """Result of audit log hash-chain verification and integrity audit."""

    is_valid: bool
    run_id: str
    total_records: int = 0
    verified_records: int = 0
    broken_link_index: int | None = None
    discrepancies: list[str] = Field(default_factory=list)
    verified_at: str = Field(default_factory=lambda: datetime.now(UTC).isoformat())

