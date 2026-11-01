"""API endpoints for agentic campaign planning (FR-2.1, FR-2.3)."""

from fastapi import APIRouter, HTTPException

from backend.app.core.state import app_state
from backend.app.graph.path_finder import AttackPathFinder
from backend.app.planner.models import CampaignGenerationRequest, CampaignPlan
from backend.app.planner.planner import CampaignPlanner

router = APIRouter(prefix="/planner", tags=["Campaign Planner"])


@router.post("/generate", response_model=CampaignPlan)
async def generate_campaign(request: CampaignGenerationRequest) -> CampaignPlan:
    """Generate a structured adversary emulation campaign from an attack path."""
    # Retrieve attack path
    target_path = None
    if request.attack_path_id:
        target_path = next(
            (p for p in app_state.cached_attack_paths if p.path_id == request.attack_path_id), None
        )

    if not target_path:
        # Run discovery if none cached or specified
        if not app_state.cached_attack_paths:
            finder = AttackPathFinder(app_state.graph_store)
            app_state.cached_attack_paths = finder.discover_paths(findings=app_state.findings)

        if not app_state.cached_attack_paths:
            raise HTTPException(
                status_code=400,
                detail="No attack paths available to plan against. Ingest environment first.",
            )
        target_path = app_state.cached_attack_paths[0]

    planner = CampaignPlanner(provider_name=request.provider)
    try:
        plan = planner.plan_campaign(
            path=target_path,
            findings=app_state.findings,
            run_id=request.run_id,
        )
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Campaign planning failed: {exc}")

    # Register in global app_state
    app_state.cache_campaign(plan)
    return plan


@router.get("/campaigns", response_model=list[CampaignPlan])
async def list_campaigns() -> list[CampaignPlan]:
    """List all formulated campaign plans."""
    return app_state.planner.list_campaigns()


@router.get("/campaigns/{campaign_id}", response_model=CampaignPlan)
async def get_campaign(campaign_id: str) -> CampaignPlan:
    """Retrieve a formulated campaign plan by ID."""
    plan = app_state.get_campaign(campaign_id)
    if not plan:
        raise HTTPException(status_code=404, detail=f"Campaign '{campaign_id}' not found.")
    return plan
