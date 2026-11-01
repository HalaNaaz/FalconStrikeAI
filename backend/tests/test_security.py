"""Unit tests for token authorization and two-key confirmation (NFR-S2)."""

import pytest

from backend.app.core.exceptions import AuthorizationTokenError
from backend.app.core.security import (
    create_authorization_token,
    verify_authorization_token,
)


def test_create_and_verify_valid_token() -> None:
    """Verify that a freshly created token verifies successfully with correct account."""
    secret = "my-test-secret-that-is-at-least-32-bytes-long-for-hmac-sha256"
    target_account = "123456789012"
    token = create_authorization_token(
        operator_id="Engineer-01",
        target_account_id=target_account,
        secret_key=secret,
        valid_duration_seconds=300,
    )

    claims = verify_authorization_token(
        token=token,
        expected_account_id=target_account,
        secret_key=secret,
    )

    assert claims["sub"] == "Engineer-01"
    assert claims["target_account"] == target_account
    assert claims["role"] == "LeadSecurityEngineer"


def test_token_fails_on_wrong_account() -> None:
    """Verify token created for one account is rejected when used for another."""
    secret = "my-test-secret-that-is-at-least-32-bytes-long-for-hmac-sha256"
    token = create_authorization_token(
        operator_id="Engineer-01",
        target_account_id="123456789012",
        secret_key=secret,
    )

    with pytest.raises(AuthorizationTokenError) as exc_info:
        verify_authorization_token(
            token=token,
            expected_account_id="000000000000",
            secret_key=secret,
        )

    assert "not target account '000000000000'" in str(exc_info.value)


def test_token_fails_when_expired() -> None:
    """Verify expired token is rejected."""
    secret = "my-test-secret-that-is-at-least-32-bytes-long-for-hmac-sha256"
    token = create_authorization_token(
        operator_id="Engineer-01",
        target_account_id="123456789012",
        secret_key=secret,
        valid_duration_seconds=-10,  # Expired in past
    )

    with pytest.raises(AuthorizationTokenError) as exc_info:
        verify_authorization_token(
            token=token,
            expected_account_id="123456789012",
            secret_key=secret,
        )

    assert "has expired" in str(exc_info.value)
