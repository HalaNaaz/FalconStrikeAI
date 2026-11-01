"""Security and cryptographic primitives for Falcon Strike-AI authorization."""

import hmac
from datetime import UTC, datetime, timedelta
from enum import StrEnum
from typing import Any

import jwt
from pydantic import BaseModel, Field

from backend.app.core.exceptions import AuthenticationError, AuthorizationTokenError


class OperatorRole(StrEnum):
    """RBAC operator roles for platform control plane access."""

    VIEWER = "viewer"
    OPERATOR = "operator"
    RED_TEAM = "RedTeam"
    SECOPS = "SecOps"
    ADMIN = "admin"
    LEAD_ENGINEER = "LeadSecurityEngineer"


class OperatorSession(BaseModel):
    """Authenticated operator context injected into protected route dependencies."""

    operator_id: str
    role: str
    target_account: str
    scopes: list[str] = Field(default_factory=list)
    issued_at: datetime
    expires_at: datetime

    def has_role(self, *allowed_roles: str | OperatorRole) -> bool:
        """Check if current operator possesses any of the required roles."""
        role_values = {r.value if isinstance(r, OperatorRole) else str(r) for r in allowed_roles}
        if self.role == OperatorRole.ADMIN or OperatorRole.ADMIN.value in role_values:
            return True
        return self.role in role_values


def constant_time_compare(val1: str, val2: str) -> bool:
    """Perform constant-time comparison to prevent timing attacks."""
    if not val1 or not val2:
        return False
    return hmac.compare_digest(val1.encode("utf-8"), val2.encode("utf-8"))


def create_access_token(
    operator_id: str,
    role: str | OperatorRole,
    target_account_id: str,
    secret_key: str,
    valid_duration_seconds: int = 3600,
    scopes: list[str] | None = None,
    issuer: str = "falcon-strike-ai",
) -> str:
    """Generate a signed Bearer JWT token for operator API session authentication."""
    now = datetime.now(UTC)
    role_str = role.value if isinstance(role, OperatorRole) else str(role)
    payload = {
        "sub": operator_id,
        "role": role_str,
        "target_account": target_account_id,
        "scopes": scopes or ["read", "write"],
        "iss": issuer,
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(seconds=valid_duration_seconds)).timestamp()),
        "purpose": "falcon_strike_api_authentication",
    }
    return jwt.encode(payload, secret_key, algorithm="HS256")


def verify_access_token(
    token: str,
    secret_key: str,
    expected_issuer: str = "falcon-strike-ai",
) -> OperatorSession:
    """Verify session JWT token signature, expiration, issuer, and return operator session."""
    if not token or not token.strip():
        raise AuthenticationError("Authentication token is missing.")

    try:
        payload = jwt.decode(
            token.strip(),
            secret_key,
            algorithms=["HS256"],
            issuer=expected_issuer,
            options={"require": ["exp", "iat", "sub", "role"]},
        )
    except jwt.ExpiredSignatureError as exc:
        raise AuthenticationError("Authentication token has expired.") from exc
    except jwt.InvalidIssuerError as exc:
        raise AuthenticationError(f"Invalid token issuer: {exc}") from exc
    except jwt.InvalidTokenError as exc:
        raise AuthenticationError(f"Invalid authentication token: {exc}") from exc

    return OperatorSession(
        operator_id=payload["sub"],
        role=payload["role"],
        target_account=payload.get("target_account", "000000000000"),
        scopes=payload.get("scopes", []),
        issued_at=datetime.fromtimestamp(payload["iat"], tz=UTC),
        expires_at=datetime.fromtimestamp(payload["exp"], tz=UTC),
    )


def create_authorization_token(
    operator_id: str,
    target_account_id: str,
    secret_key: str,
    valid_duration_seconds: int = 3600,
    role: str = "LeadSecurityEngineer",
) -> str:
    """Generate a signed, time-boxed authorization token required to exit dry-run (NFR-S2)."""
    now = datetime.now(UTC)
    payload = {
        "sub": operator_id,
        "target_account": target_account_id,
        "role": role,
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(seconds=valid_duration_seconds)).timestamp()),
        "purpose": "falcon_strike_live_emulation_authorization",
    }
    return jwt.encode(payload, secret_key, algorithm="HS256")


def verify_authorization_token(
    token: str,
    expected_account_id: str,
    secret_key: str,
) -> dict[str, Any]:
    """Verify authorization token validity, expiration, and account binding."""
    if not token:
        raise AuthorizationTokenError("Authorization token is missing.")

    try:
        payload = jwt.decode(token, secret_key, algorithms=["HS256"])
    except jwt.ExpiredSignatureError as exc:
        raise AuthorizationTokenError("Authorization token has expired.") from exc
    except jwt.InvalidTokenError as exc:
        raise AuthorizationTokenError(f"Invalid authorization token: {exc}") from exc

    token_account = payload.get("target_account")
    if token_account != expected_account_id:
        raise AuthorizationTokenError(
            f"Authorization token is scoped for account '{token_account}', "
            f"not target account '{expected_account_id}'."
        )

    return payload
