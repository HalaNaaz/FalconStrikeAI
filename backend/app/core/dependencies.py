"""FastAPI authentication and authorization dependencies for Falcon Strike-AI."""

from datetime import UTC, datetime, timedelta
from typing import Annotated

from fastapi import Depends, HTTPException, Security, status
from fastapi.security import APIKeyHeader, HTTPAuthorizationCredentials, HTTPBearer, SecurityScopes

from backend.app.core.config import settings
from backend.app.core.exceptions import AuthenticationError
from backend.app.core.security import (
    OperatorRole,
    OperatorSession,
    constant_time_compare,
    verify_access_token,
)

bearer_scheme = HTTPBearer(auto_error=False)
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


async def get_current_operator(
    security_scopes: SecurityScopes,
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)] = None,
    api_key: Annotated[str | None, Security(api_key_header)] = None,
) -> OperatorSession:
    """Validate Bearer JWT or X-API-Key and return authenticated OperatorSession.

    Enforces:
    - 401 Unauthorized on missing, expired, or invalid credentials.
    - 403 Forbidden on insufficient role or scope permissions.
    - Constant-time comparison for API keys.
    """
    # 1. Bearer Token Authentication
    if credentials and credentials.scheme.lower() == "bearer":
        token = credentials.credentials
        try:
            session = verify_access_token(
                token=token,
                secret_key=settings.auth_secret_key,
                expected_issuer=settings.jwt_issuer,
            )
        except AuthenticationError as exc:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=str(exc),
                headers={"WWW-Authenticate": "Bearer"},
            ) from exc

        # Check required security scopes / roles if specified
        if security_scopes.scopes:
            for scope in security_scopes.scopes:
                if not session.has_role(scope) and scope not in session.scopes:
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail=f"Forbidden: Insufficient privileges. Required scope/role: '{scope}'",
                    )
        return session

    # 2. API Key Authentication (Service-to-Service)
    if api_key:
        if not settings.api_key:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="API Key authentication is not enabled on this server.",
                headers={"WWW-Authenticate": "Bearer"},
            )

        if not constant_time_compare(api_key, settings.api_key):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid API Key.",
                headers={"WWW-Authenticate": "Bearer"},
            )

        now = datetime.now(UTC)
        return OperatorSession(
            operator_id="service-account",
            role=OperatorRole.ADMIN.value,
            target_account=settings.target_account_id,
            scopes=["read", "write", "admin", "operator"],
            issued_at=now,
            expires_at=now + timedelta(hours=24),
        )

    # 3. Missing Credentials
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Authentication required. Provide a valid Bearer token or X-API-Key header.",
        headers={"WWW-Authenticate": "Bearer"},
    )


def require_role(*roles: str | OperatorRole):
    """Factory creating dependency enforcing specific operator roles."""
    role_strs = [r.value if isinstance(r, OperatorRole) else str(r) for r in roles]

    async def _role_verifier(
        session: Annotated[OperatorSession, Security(get_current_operator, scopes=role_strs)],
    ) -> OperatorSession:
        return session

    return _role_verifier
