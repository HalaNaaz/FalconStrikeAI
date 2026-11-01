"""Authentication API endpoints for Falcon Strike-AI operator sessions."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from backend.app.core.config import settings
from backend.app.core.dependencies import get_current_operator
from backend.app.core.security import (
    OperatorRole,
    OperatorSession,
    create_access_token,
)

router = APIRouter(prefix="/auth", tags=["Authentication"])


class LoginRequest(BaseModel):
    """Operator authentication / session initiation request."""

    operator_id: str = Field(..., description="Unique operator identifier, e.g. 'operator-01'")
    role: str = Field(
        default=OperatorRole.OPERATOR.value,
        description="Operator role: viewer, operator, RedTeam, SecOps, admin",
    )
    target_account_id: str = Field(
        default="000000000000",
        description="Target AWS Account ID bound to this session",
    )
    valid_duration_seconds: int = Field(
        default=3600,
        ge=60,
        le=86400,
        description="Requested token validity duration in seconds",
    )


class TokenResponse(BaseModel):
    """Bearer token response for authenticated sessions."""

    access_token: str
    token_type: str = "bearer"
    expires_in: int
    operator_id: str
    role: str
    target_account_id: str


@router.post("/token", response_model=TokenResponse, summary="Obtain operator session token")
@router.post("/login", response_model=TokenResponse, summary="Log in and obtain operator session token")
async def login_operator(request: LoginRequest) -> TokenResponse:
    """Issue a signed, scoped Bearer JWT token for platform operator interactions.

    Validates that the target account is in the allowlist.
    """
    if not settings.is_account_allowlisted(request.target_account_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Target account '{request.target_account_id}' is not in the compiled allowlist.",
        )

    token = create_access_token(
        operator_id=request.operator_id,
        role=request.role,
        target_account_id=request.target_account_id,
        secret_key=settings.auth_secret_key,
        valid_duration_seconds=request.valid_duration_seconds,
        issuer=settings.jwt_issuer,
    )

    return TokenResponse(
        access_token=token,
        token_type="bearer",
        expires_in=request.valid_duration_seconds,
        operator_id=request.operator_id,
        role=request.role,
        target_account_id=request.target_account_id,
    )


@router.get("/me", response_model=OperatorSession, summary="Get current operator session")
async def get_my_session(
    current_operator: Annotated[OperatorSession, Depends(get_current_operator)],
) -> OperatorSession:
    """Return identity and roles of the currently authenticated operator."""
    return current_operator
