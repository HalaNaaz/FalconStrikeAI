"""Pydantic models for discovered and ranked attack paths."""

from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field

from backend.app.graph.models import FindingSeverity, GraphEdge, GraphNode


class AttackPath(BaseModel):
    """An explainable, ordered path of graph traversals from an entry point to a target asset."""

    path_id: str = Field(default_factory=lambda: f"PATH-{uuid4().hex[:8].upper()}")
    entry_point: GraphNode = Field(
        description="Starting node (e.g., Public Internet, compromised user)"
    )
    target_resource: GraphNode = Field(
        description="Target crown jewel (e.g., Admin Role, S3 data store)"
    )
    ordered_nodes: list[GraphNode] = Field(default_factory=list)
    ordered_relationships: list[GraphEdge] = Field(default_factory=list)
    hop_count: int = Field(default=0, description="Total relationship hops from entry to target")
    risk_score: float = Field(
        default=0.0, ge=0.0, le=100.0, description="Calculated risk score between 0 and 100"
    )
    severity: FindingSeverity = Field(default=FindingSeverity.MEDIUM)
    ranking_explanation: str = Field(description="Detailed transparent justification of the score")
    supporting_findings: list[str] = Field(
        default_factory=list, description="IDs of misconfiguration findings along this path"
    )
    evidence_provenance: dict[str, Any] = Field(
        default_factory=dict, description="Metadata linking graph edges to collector findings"
    )


class AttackPathDiscoveryResponse(BaseModel):
    """Structured response container for attack path discovery queries."""

    total_paths: int = 0
    search_depth: int = 6
    paths: list[AttackPath] = Field(default_factory=list)
    execution_time_ms: float = 0.0
