"""Unit and integration tests for REST API authentication, authorization, and role enforcement."""

from datetime import UTC, datetime, timedelta

import jwt
import pytest
from httpx import AsyncClient

from backend.app.core.config import settings
from backend.app.core.security import OperatorRole, create_access_token


@pytest.mark.asyncio
async def test_health_endpoints_accessible_without_auth(
    unauthenticated_client: AsyncClient,
) -> None:
    """Verify health endpoints remain publicly accessible for monitoring/load-balancers."""
    res_root = await unauthenticated_client.get("/health")
    assert res_root.status_code == 200
    assert res_root.json()["status"] == "healthy"

    res_v1 = await unauthenticated_client.get("/api/v1/health")
    assert res_v1.status_code == 200
    assert res_v1.json()["status"] == "healthy"


@pytest.mark.asyncio
async def test_protected_endpoint_rejects_missing_auth(
    unauthenticated_client: AsyncClient,
) -> None:
    """Verify protected route returns HTTP 401 when no credentials are provided."""
    res = await unauthenticated_client.get("/api/v1/collectors/status")
    assert res.status_code == 401
    assert "Authentication required" in res.json()["detail"]
    assert "WWW-Authenticate" in res.headers


@pytest.mark.asyncio
async def test_protected_endpoint_rejects_invalid_token(
    unauthenticated_client: AsyncClient,
) -> None:
    """Verify protected route returns HTTP 401 on malformed or garbage token."""
    res = await unauthenticated_client.get(
        "/api/v1/collectors/status",
        headers={"Authorization": "Bearer totally-invalid-token-string"},
    )
    assert res.status_code == 401
    assert "Invalid authentication token" in res.json()["detail"]


@pytest.mark.asyncio
async def test_protected_endpoint_rejects_expired_token(
    unauthenticated_client: AsyncClient,
) -> None:
    """Verify protected route returns HTTP 401 when token is expired."""
    expired_time = datetime.now(UTC) - timedelta(hours=2)
    payload = {
        "sub": "expired-operator",
        "role": "operator",
        "target_account": "000000000000",
        "scopes": ["read", "write"],
        "iss": settings.jwt_issuer,
        "iat": int((expired_time - timedelta(minutes=5)).timestamp()),
        "exp": int(expired_time.timestamp()),
    }
    expired_token = jwt.encode(payload, settings.auth_secret_key, algorithm="HS256")

    res = await unauthenticated_client.get(
        "/api/v1/collectors/status",
        headers={"Authorization": f"Bearer {expired_token}"},
    )
    assert res.status_code == 401
    assert "expired" in res.json()["detail"].lower()


@pytest.mark.asyncio
async def test_protected_endpoint_rejects_wrong_issuer(
    unauthenticated_client: AsyncClient,
) -> None:
    """Verify token from untrusted issuer is rejected with HTTP 401."""
    now = datetime.now(UTC)
    payload = {
        "sub": "rogue-operator",
        "role": "admin",
        "target_account": "000000000000",
        "scopes": ["read", "write"],
        "iss": "rogue-issuer-corp",
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(hours=1)).timestamp()),
    }
    rogue_token = jwt.encode(payload, settings.auth_secret_key, algorithm="HS256")

    res = await unauthenticated_client.get(
        "/api/v1/collectors/status",
        headers={"Authorization": f"Bearer {rogue_token}"},
    )
    assert res.status_code == 401
    assert "Invalid token issuer" in res.json()["detail"]


@pytest.mark.asyncio
async def test_protected_endpoint_accepts_valid_token(
    unauthenticated_client: AsyncClient,
) -> None:
    """Verify protected route succeeds with HTTP 200 on valid signed Bearer token."""
    valid_token = create_access_token(
        operator_id="secops-lead",
        role=OperatorRole.SECOPS,
        target_account_id="000000000000",
        secret_key=settings.auth_secret_key,
        issuer=settings.jwt_issuer,
    )
    res = await unauthenticated_client.get(
        "/api/v1/collectors/status",
        headers={"Authorization": f"Bearer {valid_token}"},
    )
    assert res.status_code == 200
    assert "available_collectors" in res.json()


@pytest.mark.asyncio
async def test_auth_login_generates_valid_token(
    unauthenticated_client: AsyncClient,
) -> None:
    """Verify POST /api/v1/auth/token mints a valid session JWT for allowlisted account."""
    req = {
        "operator_id": "auditor-01",
        "role": "viewer",
        "target_account_id": "000000000000",
        "valid_duration_seconds": 1800,
    }
    res = await unauthenticated_client.post("/api/v1/auth/token", json=req)
    assert res.status_code == 200
    data = res.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["operator_id"] == "auditor-01"

    # Use minted token to fetch session profile
    me_res = await unauthenticated_client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {data['access_token']}"},
    )
    assert me_res.status_code == 200
    me_data = me_res.json()
    assert me_data["operator_id"] == "auditor-01"
    assert me_data["role"] == "viewer"


@pytest.mark.asyncio
async def test_auth_login_rejects_unallowlisted_account(
    unauthenticated_client: AsyncClient,
) -> None:
    """Verify POST /api/v1/auth/token refuses token creation for unapproved accounts."""
    req = {
        "operator_id": "intruder",
        "role": "admin",
        "target_account_id": "999888777666",
    }
    res = await unauthenticated_client.post("/api/v1/auth/token", json=req)
    assert res.status_code == 403
    assert "not in the compiled allowlist" in res.json()["detail"]


@pytest.mark.asyncio
async def test_api_key_authentication_success_and_failure(
    unauthenticated_client: AsyncClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verify X-API-Key authentication works with constant-time comparison."""
    # 1. When API key is not enabled on server
    monkeypatch.setattr(settings, "api_key", None)
    res_disabled = await unauthenticated_client.get(
        "/api/v1/collectors/status",
        headers={"X-API-Key": "some-random-key"},
    )
    assert res_disabled.status_code == 401
    assert "not enabled" in res_disabled.json()["detail"]

    # 2. When API key is configured
    valid_key = "fsk_service_account_secure_key_123456789"
    monkeypatch.setattr(settings, "api_key", valid_key)

    # Valid key -> 200
    res_valid = await unauthenticated_client.get(
        "/api/v1/collectors/status",
        headers={"X-API-Key": valid_key},
    )
    assert res_valid.status_code == 200

    # Invalid key -> 401
    res_invalid = await unauthenticated_client.get(
        "/api/v1/collectors/status",
        headers={"X-API-Key": "wrong-key-value"},
    )
    assert res_invalid.status_code == 401
    assert "Invalid API Key" in res_invalid.json()["detail"]
