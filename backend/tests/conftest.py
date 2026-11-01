"""Pytest configuration and shared test fixtures."""

import os
from collections.abc import AsyncGenerator

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from backend.app.core.config import Settings
from backend.app.core.security import create_access_token
from backend.app.main import create_app


@pytest.fixture(autouse=True)
def reset_env() -> None:
    """Ensure clean test environment without lingering secrets."""
    # Ensure dry-run is always true during testing
    os.environ["FALCON_DRY_RUN"] = "true"
    os.environ["FALCON_TARGET_ACCOUNT_ID"] = "000000000000"
    os.environ["FALCON_ENVIRONMENT"] = "test"


@pytest.fixture
def test_settings() -> Settings:
    """Provide a fresh Settings instance for testing."""
    return Settings(
        environment="test",
        dry_run=True,
        target_account_id="000000000000",
        allowlisted_accounts=["000000000000", "123456789012"],
        auth_secret_key="test-secret-key-123",
    )


@pytest_asyncio.fixture
async def async_client() -> AsyncGenerator[AsyncClient, None]:
    """Async HTTP client for testing FastAPI endpoints with valid default operator credentials."""
    app = create_app()
    transport = ASGITransport(app=app)
    token = create_access_token(
        operator_id="test-operator",
        role="admin",
        target_account_id="000000000000",
        secret_key="falcon-strike-dev-secret-do-not-use-in-production",
    )
    async with AsyncClient(
        transport=transport,
        base_url="http://test",
        headers={"Authorization": f"Bearer {token}"},
    ) as client:
        yield client


@pytest_asyncio.fixture
async def unauthenticated_client() -> AsyncGenerator[AsyncClient, None]:
    """Async HTTP client without any authentication credentials."""
    app = create_app()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client
