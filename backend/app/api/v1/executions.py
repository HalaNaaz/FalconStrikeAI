"""API routes for campaign execution orchestration, status, and teardown."""

from typing import Any

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from backend.app.core.state import app_state
from backend.app.orchestrator.models import (
    CampaignExecutionRecord,
    ExecutionMode,
    TeardownResult,
)
from backend.app.techniques.models import SimulationEvent

router = APIRouter(prefix="/executions", tags=["Executions & Orchestration"])


class DryRunExecutionRequest(BaseModel):
    """Request payload for triggering a dry-run execution."""

    campaign_id: str = Field(description="ID of the cached campaign plan to dry-run")
    prefer_docker: bool = Field(default=False, description="Whether to request Docker sandbox")


class LiveExecutionRequest(BaseModel):
    """Request payload for triggering live emulation simulation."""

    campaign_id: str = Field(description="ID of the policy-approved campaign plan")
    operator_token: str | None = Field(default=None, description="Cryptographic token for operator")
    secondary_approver_token: str | None = Field(
        default=None, description="Cryptographic token for secondary approver"
    )
    prefer_docker: bool = Field(default=False, description="Whether to request Docker sandbox")


@router.post(
    "/dry-run",
    response_model=CampaignExecutionRecord,
    status_code=status.HTTP_200_OK,
    summary="Execute dry-run adversary emulation campaign",
)
def run_dry_run(req: DryRunExecutionRequest) -> CampaignExecutionRecord:
    """Execute a validated campaign in non-destructive dry-run mode (FR-3.1)."""
    plan = app_state.get_campaign(req.campaign_id)
    if not plan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Campaign '{req.campaign_id}' not found in cached campaigns.",
        )

    try:
        record = app_state.execution_engine.execute_campaign(
            plan=plan,
            mode=ExecutionMode.DRY_RUN,
            environment_data=app_state.environment_data,
            prefer_docker=req.prefer_docker,
        )
        return record
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.post(
    "/live",
    response_model=CampaignExecutionRecord,
    status_code=status.HTTP_200_OK,
    summary="Execute live adversary emulation simulation (requires approval)",
)
def run_live_simulation(req: LiveExecutionRequest) -> CampaignExecutionRecord:
    """Execute a policy-approved campaign in live simulation mode (FR-3.1, NFR-S2)."""
    plan = app_state.get_campaign(req.campaign_id)
    if not plan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Campaign '{req.campaign_id}' not found in cached campaigns.",
        )

    # Verify policy approval if not already approved
    if not plan.approved_by_policy:
        target_account = app_state.environment_data.account_id if app_state.environment_data else "000000000000"
        context = {
            "request_live_execution": True,
            "operator_token": req.operator_token,
            "secondary_approver_token": req.secondary_approver_token,
        }
        decision = app_state.policy_engine.evaluate_campaign(
            plan=plan, target_account=target_account, context=context
        )
        if not decision.approved:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Live execution rejected by policy gate: {decision.rejected_rules or decision.evaluation_summary}",
            )
        plan.approved_by_policy = True

    try:
        record = app_state.execution_engine.execute_campaign(
            plan=plan,
            mode=ExecutionMode.LIVE_SIMULATION,
            environment_data=app_state.environment_data,
            prefer_docker=req.prefer_docker,
        )
        return record
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.get(
    "",
    response_model=list[CampaignExecutionRecord],
    summary="List all campaign execution records",
)
def list_executions() -> list[CampaignExecutionRecord]:
    """Retrieve all historic campaign executions."""
    return app_state.execution_engine.list_executions()


@router.get(
    "/{run_id}",
    response_model=CampaignExecutionRecord,
    summary="Retrieve campaign execution details by run ID",
)
def get_execution(run_id: str) -> CampaignExecutionRecord:
    """Retrieve details, status, and stages of a specific execution run."""
    record = app_state.execution_engine.get_execution(run_id)
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Execution record with run_id '{run_id}' not found.",
        )
    return record


@router.post(
    "/{run_id}/cancel",
    status_code=status.HTTP_200_OK,
    summary="Cancel in-progress campaign execution",
)
def cancel_execution(run_id: str) -> dict[str, Any]:
    """Cancel an active execution run."""
    success = app_state.execution_engine.cancel_campaign(run_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Execution run '{run_id}' not found or already completed.",
        )
    return {"run_id": run_id, "status": "CANCELLED_REQUESTED"}


@router.get(
    "/{run_id}/events",
    response_model=list[SimulationEvent],
    summary="Retrieve emitted simulation events for execution run",
)
def get_execution_events(run_id: str) -> list[SimulationEvent]:
    """Retrieve raw simulation events emitted during the run."""
    return app_state.telemetry_collector.get_simulation_events(run_id)


@router.post(
    "/{run_id}/teardown",
    response_model=TeardownResult,
    summary="Execute post-run teardown and baseline verification",
)
def trigger_teardown(run_id: str) -> TeardownResult:
    """Explicitly trigger teardown and baseline verification for a run (FR-3.5)."""
    result = app_state.execution_engine.teardown_engine.execute_teardown(
        run_id=run_id,
        current_environment=app_state.environment_data,
    )
    return result
