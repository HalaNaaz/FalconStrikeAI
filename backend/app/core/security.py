"""Security and cryptographic primitives for Falcon Strike-AI authorization."""

from datetime import UTC, datetime, timedelta
from typing import Any

import jwt

from backend.app.core.exceptions import AuthorizationTokenError


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
