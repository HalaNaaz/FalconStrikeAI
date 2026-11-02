"""Regression and contract tests for MisconfigurationFinding and findings endpoints."""

import pytest
from fastapi.testclient import TestClient

from backend.app.core.config import settings
from backend.app.core.security import create_access_token
from backend.app.graph.models import FindingCategory, FindingSeverity, MisconfigurationFinding
from backend.app.main import app


@pytest.fixture
def auth_headers() -> dict[str, str]:
    token = create_access_token(
        operator_id="test-operator",
        role="admin",
        target_account_id="000000000000",
        secret_key=settings.auth_secret_key,
    )
    return {"Authorization": f"Bearer {token}"}


def test_misconfiguration_finding_synchronizes_contract_aliases():
    """Verify that backend Pydantic model automatically populates contract alias fields."""
    # Constructed with backend-native fields
    finding = MisconfigurationFinding(
        resource_id="i-0abcd1234ef56789a",
        category=FindingCategory.PUBLIC_EXPOSURE,
        severity=FindingSeverity.HIGH,
        explanation="Compute instance directly exposed to internet.",
        evidence={"public_ip": "54.200.10.15"},
        remediation="Move to private subnet.",
    )

    data = finding.model_dump()

    # Both backend and frontend contract fields must be populated
    assert data["resource_id"] == "i-0abcd1234ef56789a"
    assert data["target_node_id"] == "i-0abcd1234ef56789a"
    assert data["explanation"] == "Compute instance directly exposed to internet."
    assert data["description"] == "Compute instance directly exposed to internet."
    assert data["category"] == "PUBLIC_EXPOSURE"
    assert data["rule_name"] == "PUBLIC_EXPOSURE"
    assert data["rule_id"] == "RULE-PUBLIC_EXPOSURE"
    assert data["evidence"] == {"public_ip": "54.200.10.15"}
    assert data["details"] == {"public_ip": "54.200.10.15"}


def test_misconfiguration_finding_accepts_frontend_aliases():
    """Verify that backend Pydantic model accepts frontend contract fields and populates native ones."""
    # Constructed with frontend field names
    raw = {
        "target_node_id": "arn:aws:s3:::sensitive-bucket",
        "rule_name": "PUBLIC_STORAGE",
        "severity": "HIGH",
        "description": "Bucket allows unauthenticated read access.",
        "details": {"bucket_name": "sensitive-bucket"},
        "remediation": "Enable S3 Block Public Access.",
    }

    finding = MisconfigurationFinding.model_validate(raw)

    assert finding.resource_id == "arn:aws:s3:::sensitive-bucket"
    assert finding.target_node_id == "arn:aws:s3:::sensitive-bucket"
    assert finding.explanation == "Bucket allows unauthenticated read access."
    assert finding.description == "Bucket allows unauthenticated read access."
    assert finding.category == FindingCategory.PUBLIC_STORAGE
    assert finding.rule_name == "PUBLIC_STORAGE"


def test_get_collector_findings_endpoint(auth_headers):
    """Verify GET /api/v1/collectors/findings returns 200 and schema-valid findings."""
    client = TestClient(app)
    response = client.get("/api/v1/collectors/findings", headers=auth_headers)

    assert response.status_code == 200
    data = response.json()
    assert "total_findings" in data
    assert "findings_by_severity" in data
    assert "findings" in data
    assert isinstance(data["findings"], list)

    for item in data["findings"]:
        assert "target_node_id" in item
        assert "resource_id" in item
        assert "description" in item
        assert "explanation" in item
        assert "rule_name" in item


def test_get_graph_findings_endpoint(auth_headers):
    """Verify GET /api/v1/graph/findings returns 200 and schema-valid findings."""
    client = TestClient(app)
    response = client.get("/api/v1/graph/findings", headers=auth_headers)

    assert response.status_code == 200
    data = response.json()
    assert "total_findings" in data
    assert "findings" in data
