"""Unit tests for configuration management, allowlists, and safety invariants."""

import pytest

from backend.app.core.config import Settings
from backend.app.core.exceptions import (
    AccountNotAllowlistedError,
    AuthorizationTokenError,
)


def test_dry_run_is_default() -> None:
    """SAFETY INVARIANT: Verify dry-run defaults to True (NFR-S4)."""
    cfg = Settings()
    assert cfg.dry_run is True, "Default execution mode MUST be dry_run=True"


def test_allowlist_check_success(test_settings: Settings) -> None:
    """Verify an allowlisted account passes verification (NFR-S1)."""
    # Should not raise exception
    test_settings.assert_account_allowlisted("000000000000")
    test_settings.assert_account_allowlisted("123456789012")


def test_allowlist_check_fails_on_unauthorized_account(test_settings: Settings) -> None:
    """SAFETY INVARIANT: Verify unapproved account raises AccountNotAllowlistedError (NFR-S1)."""
    with pytest.raises(AccountNotAllowlistedError) as exc_info:
        test_settings.assert_account_allowlisted("999888777666")

    assert "999888777666" in str(exc_info.value)
    assert "not in the compiled allowlist" in str(exc_info.value)


def test_live_execution_requires_auth_token() -> None:
    """SAFETY INVARIANT: Verify exiting dry-run without token raises AuthorizationTokenError (NFR-S2)."""
    live_cfg = Settings(dry_run=False, auth_token=None, target_account_id="000000000000")
    with pytest.raises(AuthorizationTokenError) as exc_info:
        live_cfg.assert_live_execution_permitted("000000000000")

    assert "no authorization token provided" in str(exc_info.value)


def test_custom_comma_separated_allowlist() -> None:
    """Verify comma-separated allowlist parsing in configuration."""
    cfg = Settings(allowlisted_accounts="111111111111,222222222222")
    assert "111111111111" in cfg.allowlisted_accounts
    assert "222222222222" in cfg.allowlisted_accounts
