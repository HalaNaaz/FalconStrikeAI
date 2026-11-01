"""API endpoints for property graph querying, export, and misconfiguration analysis."""

from collections import Counter
from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel

from backend.app.core.state import app_state
from backend.app.graph.models import GraphSummary, MisconfigurationFinding

router = APIRouter(tags=["Property Graph"])


class AnalyzeResponse(BaseModel):
    """Response containing security misconfiguration findings."""

    total_findings: int
    findings_by_severity: dict[str, int]
    findings: list[MisconfigurationFinding]


@router.get("/graph/summary", response_model=GraphSummary)
async def get_graph_summary() -> dict[str, Any]:
    """Retrieve statistical summary of the active property graph."""
    nodes = app_state.graph_store.get_all_nodes()
    edges = app_state.graph_store.get_all_edges()

    node_types = Counter(n.type.value for n in nodes)
    edge_types = Counter(e.type.value for e in edges)
    sev_counts = Counter(f.severity.value for f in app_state.findings)

    return {
        "total_nodes": len(nodes),
        "total_edges": len(edges),
        "node_counts_by_type": dict(node_types),
        "edge_counts_by_type": dict(edge_types),
        "total_findings": len(app_state.findings),
        "findings_by_severity": dict(sev_counts),
    }


@router.get("/graph/export")
async def export_graph() -> dict[str, Any]:
    """Export the entire property graph as a JSON payload."""
    return app_state.graph_store.to_dict()


@router.post("/graph/analyze", response_model=AnalyzeResponse)
async def analyze_graph() -> dict[str, Any]:
    """Run misconfiguration analysis and return exposure findings."""
    sev_counts = Counter(f.severity.value for f in app_state.findings)
    return {
        "total_findings": len(app_state.findings),
        "findings_by_severity": dict(sev_counts),
        "findings": app_state.findings,
    }
