"""API endpoints for cloud asset collection and collector status."""

from collections import Counter
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from backend.app.collectors.runner import CollectorOrchestrator
from backend.app.core.config import settings
from backend.app.core.exceptions import AccountNotAllowlistedError, AuthorizationTokenError
from backend.app.core.state import app_state
from backend.app.graph.models import MisconfigurationFinding

router = APIRouter(tags=["Collectors"])


class CollectorStatusResponse(BaseModel):
    """Status of cloud collection subsystem."""

    available_collectors: list[str] = Field(default_factory=lambda: ["iam", "ec2", "s3"])
    default_mode: str = "synthetic"
    dry_run: bool = True
    target_account: str
    allowlisted_accounts: list[str]


class CollectRequest(BaseModel):
    """Request payload for triggering asset collection."""

    account_id: str = Field(default="000000000000", description="Target AWS Account ID")
    force_synthetic: bool = Field(
        default=True,
        description="Whether to use synthetic environment generator (default=True)",
    )
    synthetic_topology_type: str = Field(
        default="flawed", description="Synthetic topology variant: flawed or clean"
    )


class CollectResponse(BaseModel):
    """Response summary after environment collection."""

    collection_id: str
    account_id: str
    source_type: str
    collected_at: str
    duration_ms: float
    total_assets: int
    asset_breakdown: dict[str, int]
    error_count: int


class CollectorFindingsResponse(BaseModel):
    """Response containing security misconfiguration findings detected in collected assets."""

    total_findings: int
    findings_by_severity: dict[str, int]
    findings: list[MisconfigurationFinding]


@router.get("/collectors/status", response_model=CollectorStatusResponse)
async def get_collector_status() -> dict[str, Any]:
    """Retrieve collector availability, active mode, and allowlist configuration."""
    return {
        "available_collectors": ["iam", "ec2", "s3"],
        "default_mode": "synthetic" if settings.dry_run else "aws_live",
        "dry_run": settings.dry_run,
        "target_account": settings.target_account_id,
        "allowlisted_accounts": settings.allowlisted_accounts,
    }


@router.post("/environment/collect", response_model=CollectResponse)
async def collect_environment(request: CollectRequest) -> dict[str, Any]:
    """Trigger read-only environment collection (synthetic or live AWS)."""
    orchestrator = CollectorOrchestrator()
    try:
        data = orchestrator.run_collection(
            account_id=request.account_id,
            force_synthetic=request.force_synthetic,
            synthetic_topology_type=request.synthetic_topology_type,
        )
    except AccountNotAllowlistedError as exc:
        raise HTTPException(status_code=403, detail=str(exc))
    except AuthorizationTokenError as exc:
        raise HTTPException(status_code=401, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Collection failed: {exc}")

    # Update global state and re-ingest graph
    app_state.update_environment(data)

    return {
        "collection_id": data.collection_id,
        "account_id": data.account_id,
        "source_type": data.source_type.value,
        "collected_at": data.collected_at,
        "duration_ms": data.duration_ms,
        "total_assets": data.total_asset_count,
        "asset_breakdown": {
            "iam_users": len(data.iam_users),
            "iam_roles": len(data.iam_roles),
            "policies": len(data.policies),
            "ec2_instances": len(data.ec2_instances),
            "security_groups": len(data.security_groups),
            "s3_buckets": len(data.s3_buckets),
        },
        "error_count": len(data.errors),
    }


@router.get("/collectors/findings", response_model=CollectorFindingsResponse)
async def get_collector_findings() -> dict[str, Any]:
    """Retrieve security misconfiguration findings for collected cloud infrastructure assets."""
    sev_counts = Counter(f.severity.value for f in app_state.findings)
    return {
        "total_findings": len(app_state.findings),
        "findings_by_severity": dict(sev_counts),
        "findings": app_state.findings,
    }
