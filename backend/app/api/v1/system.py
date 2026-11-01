"""System management and emergency kill switch API routes (FR-3.6, NFR-S3)."""

from typing import Any

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from backend.app.core.state import app_state
from backend.app.orchestrator.kill_switch import KillSwitchRecord

router = APIRouter(prefix="/system", tags=["System & Emergency Controls"])


class KillSwitchTriggerRequest(BaseModel):
    """Payload for triggering the central emergency kill switch."""

    reason: str = Field(description="Operational rationale for emergency halt")
    operator_id: str = Field(default="security-admin", description="Operator identifier")
    run_id: str | None = Field(default=None, description="Optional specific run ID to target")


class KillSwitchResetRequest(BaseModel):
    """Payload for resetting the emergency kill switch."""

    authorized_token: str = Field(description="Cryptographic administrative reset token")
    operator_id: str = Field(default="security-admin", description="Operator identifier")


@router.post(
    "/kill-switch",
    response_model=KillSwitchRecord,
    status_code=status.HTTP_200_OK,
    summary="Trigger central emergency kill switch (< 2 second halt)",
)
def trigger_emergency_kill_switch(req: KillSwitchTriggerRequest) -> KillSwitchRecord:
    """Engage central emergency kill switch, halting all active emulation immediately (FR-3.6, NFR-S3)."""
    record = app_state.kill_switch.trigger(
        reason=req.reason,
        operator_id=req.operator_id,
        run_id=req.run_id,
    )
    return record


@router.post(
    "/kill-switch/reset",
    status_code=status.HTTP_200_OK,
    summary="Reset central emergency kill switch (requires authorized token)",
)
def reset_emergency_kill_switch(req: KillSwitchResetRequest) -> dict[str, Any]:
    """Deactivate emergency kill switch and restore emulation capabilities."""
    try:
        app_state.kill_switch.reset(
            authorized_token=req.authorized_token,
            operator_id=req.operator_id,
        )
        return {
            "status": "RESET_SUCCESSFUL",
            "message": "Emergency Kill Switch has been reset. Emulation operations restored.",
            "operator_id": req.operator_id,
        }
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc


@router.get(
    "/kill-switch",
    summary="Get operational status and telemetry of emergency kill switch",
)
def get_kill_switch_status() -> dict[str, Any]:
    """Retrieve active status, latency metrics, and audit history of the kill switch (FR-3.6)."""
    return app_state.kill_switch.get_status()

