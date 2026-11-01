"""Health check and system status endpoint."""

from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel, Field

from backend.app.core.config import settings

router = APIRouter(tags=["System Health"])


class ComponentStatus(BaseModel):
    """Component status health breakdown."""

    graph_store: str = Field(description="Active graph storage backend")
    policy_gate: str = Field(description="Safety policy enforcement status")
    audit_logger: str = Field(description="Tamper-evident audit logging status")
    c2_sink: str = Field(description="Local C2 beacon sink status")


class HealthResponse(BaseModel):
    """Structured response model for health checks."""

    status: str = Field(default="healthy", description="Overall health state")
    version: str = Field(default="0.1.0", description="Application version")
    timestamp: str = Field(description="Current UTC timestamp")
    environment: str = Field(description="Deployment environment name")
    dry_run: bool = Field(description="Safety dry-run mode invariant (default=True)")
    target_account_id: str = Field(description="Configured AWS Lab target account")
    allowlisted_accounts: list[str] = Field(description="List of permitted account IDs")
    components: ComponentStatus = Field(description="Subsystem health status")


@router.get("/health", response_model=HealthResponse)
async def get_health() -> dict[str, Any]:
    """Retrieve Falcon Strike-AI platform health and safety status."""
    return {
        "status": "healthy",
        "version": "0.1.0",
        "timestamp": datetime.now(UTC).isoformat(),
        "environment": settings.environment,
        "dry_run": settings.dry_run,
        "target_account_id": settings.target_account_id,
        "allowlisted_accounts": settings.allowlisted_accounts,
        "components": {
            "graph_store": "neo4j" if settings.neo4j_enabled else "in_memory_networkx",
            "policy_gate": "enforced",
            "audit_logger": "active",
            "c2_sink": "ready",
        },
    }
