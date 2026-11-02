"""Pydantic graph models for normalized cloud property graph nodes and edges."""

from enum import StrEnum
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field, model_validator


class NodeType(StrEnum):
    """Allowed node types in the Falcon Strike-AI property graph."""

    ACCOUNT = "ACCOUNT"
    IAM_USER = "IAM_USER"
    IAM_ROLE = "IAM_ROLE"
    POLICY = "POLICY"
    EC2_INSTANCE = "EC2_INSTANCE"
    INSTANCE_PROFILE = "INSTANCE_PROFILE"
    SECURITY_GROUP = "SECURITY_GROUP"
    S3_BUCKET = "S3_BUCKET"
    PUBLIC_ENDPOINT = "PUBLIC_ENDPOINT"


class RelationshipType(StrEnum):
    """Allowed directed relationship types between nodes."""

    CONTAINS = "CONTAINS"
    ASSUMES_ROLE = "ASSUMES_ROLE"
    HAS_POLICY = "HAS_POLICY"
    ATTACHED_TO = "ATTACHED_TO"
    EXPOSED_TO_INTERNET = "EXPOSED_TO_INTERNET"
    RUNS_AS = "RUNS_AS"
    CAN_ACCESS = "CAN_ACCESS"
    TRUSTS = "TRUSTS"


class GraphNode(BaseModel):
    """A node representing a cloud resource, principal, or boundary."""

    id: str = Field(description="Unique identifier for the node (e.g., ARN, ID, or URI)")
    type: NodeType = Field(description="Normalized node type")
    name: str = Field(description="Human-readable resource name")
    account_id: str = Field(description="Owning AWS account ID")
    properties: dict[str, Any] = Field(
        default_factory=dict, description="Arbitrary resource properties"
    )

    def __hash__(self) -> int:
        return hash(self.id)


class GraphEdge(BaseModel):
    """A directed edge representing permissions, containment, or exposure."""

    id: str = Field(default_factory=lambda: str(uuid4()))
    source_id: str = Field(description="Source node ID")
    target_id: str = Field(description="Target node ID")
    type: RelationshipType = Field(description="Relationship type")
    properties: dict[str, Any] = Field(
        default_factory=dict, description="Edge properties (e.g., actions, port)"
    )

    def __hash__(self) -> int:
        return hash((self.source_id, self.target_id, self.type))


class FindingCategory(StrEnum):
    """Categories of configuration-based findings."""

    WILDCARD_PERMISSIONS = "WILDCARD_PERMISSIONS"
    EXCESSIVE_PRIVILEGES = "EXCESSIVE_PRIVILEGES"
    PUBLIC_EXPOSURE = "PUBLIC_EXPOSURE"
    RISKY_TRUST_RELATIONSHIP = "RISKY_TRUST_RELATIONSHIP"
    PUBLIC_STORAGE = "PUBLIC_STORAGE"
    PRIVILEGE_ESCALATION = "PRIVILEGE_ESCALATION"


class FindingSeverity(StrEnum):
    """Severity classification for exposure findings."""

    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    INFORMATIONAL = "INFORMATIONAL"


class MisconfigurationFinding(BaseModel):
    """Configuration-based exposure finding (not proof of exploitation)."""

    finding_id: str = Field(default_factory=lambda: f"FIND-{uuid4().hex[:8].upper()}")
    resource_id: str = Field(description="Resource ID or ARN where finding was detected")
    target_node_id: str = Field(default="", description="Graph target node ID or ARN (contract alias)")
    category: FindingCategory
    rule_id: str = Field(default="", description="Identifier of the detection rule")
    rule_name: str = Field(default="", description="Human-readable rule name")
    severity: FindingSeverity
    explanation: str = Field(description="Concise description of the exposure condition")
    description: str = Field(default="", description="Concise description (contract alias)")
    evidence: dict[str, Any] = Field(
        default_factory=dict, description="Supporting configuration facts"
    )
    details: dict[str, Any] = Field(
        default_factory=dict, description="Supporting configuration facts (contract alias)"
    )
    remediation: str = Field(description="Recommended corrective action")
    source_provenance: str = Field(
        default="graph_misconfiguration_analyzer", description="Detector provenance"
    )

    @model_validator(mode="before")
    @classmethod
    def populate_contract_aliases(cls, data: Any) -> Any:
        """Ensure full compatibility between backend and frontend data contract fields."""
        if isinstance(data, dict):
            # Target ID synchronization
            res_id = data.get("resource_id") or data.get("target_node_id") or ""
            data["resource_id"] = str(res_id)
            data["target_node_id"] = str(res_id)

            # Description synchronization
            desc = data.get("explanation") or data.get("description") or ""
            data["explanation"] = str(desc)
            data["description"] = str(desc)

            # Category and rule identification
            cat = data.get("category") or data.get("rule_name") or "WILDCARD_PERMISSIONS"
            if isinstance(cat, FindingCategory):
                cat_str = cat.value
            else:
                cat_str = str(cat)
            data["category"] = cat_str
            data["rule_name"] = data.get("rule_name") or cat_str
            data["rule_id"] = data.get("rule_id") or f"RULE-{cat_str}"

            # Evidence and details dictionary synchronization
            ev = data.get("evidence") or data.get("details") or {}
            data["evidence"] = ev
            data["details"] = ev

        return data


class GraphSummary(BaseModel):
    """High-level statistics and metadata for the property graph."""

    total_nodes: int = 0
    total_edges: int = 0
    node_counts_by_type: dict[str, int] = Field(default_factory=dict)
    edge_counts_by_type: dict[str, int] = Field(default_factory=dict)
    total_findings: int = 0
    findings_by_severity: dict[str, int] = Field(default_factory=dict)
