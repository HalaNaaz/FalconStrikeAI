"""API endpoints for attack path discovery and ranking."""

import time
from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel, Field

from backend.app.core.state import app_state
from backend.app.graph.attack_path_models import AttackPath, AttackPathDiscoveryResponse
from backend.app.graph.path_finder import AttackPathFinder

router = APIRouter(tags=["Attack Paths"])


class DiscoverPathsRequest(BaseModel):
    """Query parameters for attack path discovery."""

    entry_node_id: str | None = Field(default=None, description="Optional explicit entry node ID")
    target_node_id: str | None = Field(
        default=None, description="Optional explicit target crown jewel ID"
    )
    max_depth: int = Field(default=6, ge=1, le=10, description="Maximum traversal depth")


@router.post("/attack-paths/discover", response_model=AttackPathDiscoveryResponse)
async def discover_attack_paths(request: DiscoverPathsRequest) -> dict[str, Any]:
    """Execute bounded attack path discovery and return ranked, explainable paths."""
    start_time = time.perf_counter()
    finder = AttackPathFinder(app_state.graph_store)
    paths = finder.discover_paths(
        entry_node_id=request.entry_node_id,
        target_node_id=request.target_node_id,
        max_depth=request.max_depth,
        findings=app_state.findings,
    )
    duration_ms = (time.perf_counter() - start_time) * 1000.0

    # Cache paths in app_state
    app_state.cached_attack_paths = paths

    return {
        "total_paths": len(paths),
        "search_depth": request.max_depth,
        "paths": paths,
        "execution_time_ms": round(duration_ms, 2),
    }


@router.get("/attack-paths", response_model=list[AttackPath])
async def get_cached_attack_paths() -> list[AttackPath]:
    """Retrieve the most recently discovered and ranked attack paths."""
    if not app_state.cached_attack_paths:
        # Run discovery if cache is empty
        finder = AttackPathFinder(app_state.graph_store)
        app_state.cached_attack_paths = finder.discover_paths(findings=app_state.findings)
    return app_state.cached_attack_paths
