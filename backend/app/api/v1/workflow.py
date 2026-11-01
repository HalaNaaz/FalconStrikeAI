"""API route for triggering the unified end-to-end adversary emulation pipeline."""

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from backend.app.workflow import EndToEndWorkflow, WorkflowExecutionResult

router = APIRouter(prefix="/workflow", tags=["End-to-End Pipeline"])


class PipelineRunRequest(BaseModel):
    """Payload to trigger the full 17-stage automated adversary emulation workflow."""

    mode: str = Field(default="synthetic", description="Environment mode: synthetic or aws")
    dry_run: bool = Field(default=True, description="Enforce non-destructive dry-run mode")
    target_account: str = Field(default="000000000000", description="Target AWS account ID")
    detection_profile: str = Field(default="FULL_COVERAGE", description="Detection stub profile")
    planner_provider: str = Field(default="deterministic", description="Planning provider")


@router.post(
    "/run",
    response_model=WorkflowExecutionResult,
    status_code=status.HTTP_200_OK,
    summary="Execute full 17-stage automated adversary emulation and CTEM pipeline",
)
def run_end_to_end_pipeline(req: PipelineRunRequest) -> WorkflowExecutionResult:
    """Execute complete end-to-end workflow from collection through SOC reporting."""
    workflow = EndToEndWorkflow()
    try:
        result = workflow.run(
            mode=req.mode,
            dry_run=req.dry_run,
            target_account=req.target_account,
            detection_profile=req.detection_profile,
            planner_provider=req.planner_provider,
        )
        return result
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"End-to-end pipeline execution failed: {exc}",
        ) from exc

