"""Unit tests for configuration management, allowlists, and safety invariants."""

import pytest

from backend.app.core.config import Settings
from backend.app.core.exceptions import (
    AccountNotAllowlistedError,
    AuthorizationTokenError,
    InsecureConfigurationError,
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


# Phase 2: Production Secret Key Guard Tests


def test_production_rejects_missing_secret() -> None:
    """Verify production mode rejects empty or whitespace-only secret."""
    with pytest.raises(InsecureConfigurationError) as exc:
        Settings(environment="production", auth_secret_key="")
    assert "missing or empty" in str(exc.value)


def test_production_rejects_default_secret() -> None:
    """Verify production mode rejects known default/development fallback secrets."""
    with pytest.raises(InsecureConfigurationError) as exc:
        Settings(
            environment="production",
            auth_secret_key="falcon-strike-dev-secret-do-not-use-in-production",
        )
    assert "cannot use default or development values" in str(exc.value)


def test_production_rejects_weak_secret() -> None:
    """Verify production mode rejects secrets with less than 32 characters."""
    with pytest.raises(InsecureConfigurationError) as exc:
        Settings(
            environment="production",
            auth_secret_key="short-secret-only-24-bytes",
        )
    assert "minimum key length of 32 characters" in str(exc.value)


def test_production_accepts_strong_secret() -> None:
    """Verify production mode accepts an independently generated high-entropy secret >= 32 chars."""
    strong_key = "prod-super-secure-high-entropy-secret-key-998877"
    cfg = Settings(
        environment="production",
        auth_secret_key=strong_key,
        api_debug=False,
    )
    assert cfg.environment == "production"
    assert cfg.auth_secret_key == strong_key


def test_production_rejects_api_debug() -> None:
    """Verify production mode rejects enabled debug mode."""
    strong_key = "prod-super-secure-high-entropy-secret-key-998877"
    with pytest.raises(InsecureConfigurationError) as exc:
        Settings(
            environment="production",
            auth_secret_key=strong_key,
            api_debug=True,
        )
    assert "FALCON_API_DEBUG cannot be enabled in production" in str(exc.value)


def test_development_mode_permits_dev_secret() -> None:
    """Verify development mode permits development fallback secret for local ergonomics."""
    cfg = Settings(environment="development")
    assert cfg.auth_secret_key == "falcon-strike-dev-secret-do-not-use-in-production"


def test_test_mode_permits_test_secret() -> None:
    """Verify test mode permits documented test secret."""
    cfg = Settings(environment="test", auth_secret_key="test-secret-key-123")
    assert cfg.auth_secret_key == "test-secret-key-123"
