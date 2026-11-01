"""Integration tests for Day 2 API endpoints."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_get_collector_status(async_client: AsyncClient) -> None:
    """Verify GET /api/v1/collectors/status returns collector metadata."""
    res = await async_client.get("/api/v1/collectors/status")
    assert res.status_code == 200
    data = res.json()
    assert "iam" in data["available_collectors"]
    assert data["default_mode"] == "synthetic"
    assert "000000000000" in data["allowlisted_accounts"]


@pytest.mark.asyncio
async def test_post_environment_collect_synthetic(async_client: AsyncClient) -> None:
    """Verify POST /api/v1/environment/collect successfully ingests synthetic topology."""
    payload = {
        "account_id": "000000000000",
        "force_synthetic": True,
        "synthetic_topology_type": "flawed",
    }
    res = await async_client.post("/api/v1/environment/collect", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["account_id"] == "000000000000"
    assert data["source_type"] == "synthetic"
    assert data["total_assets"] > 0
    assert data["asset_breakdown"]["iam_roles"] >= 3


@pytest.mark.asyncio
async def test_post_environment_collect_rejects_unallowlisted(async_client: AsyncClient) -> None:
    """Verify POST /api/v1/environment/collect rejects unapproved account IDs."""
    payload = {
        "account_id": "999999999999",
        "force_synthetic": True,
    }
    res = await async_client.post("/api/v1/environment/collect", json=payload)
    assert res.status_code == 403
    assert "not in the compiled allowlist" in res.json()["detail"]


@pytest.mark.asyncio
async def test_get_graph_summary(async_client: AsyncClient) -> None:
    """Verify GET /api/v1/graph/summary returns graph statistics."""
    res = await async_client.get("/api/v1/graph/summary")
    assert res.status_code == 200
    data = res.json()
    assert data["total_nodes"] > 0
    assert data["total_edges"] > 0
    assert "IAM_ROLE" in data["node_counts_by_type"]


@pytest.mark.asyncio
async def test_get_graph_export(async_client: AsyncClient) -> None:
    """Verify GET /api/v1/graph/export returns full graph representation."""
    res = await async_client.get("/api/v1/graph/export")
    assert res.status_code == 200
    data = res.json()
    assert "nodes" in data
    assert "edges" in data
    assert len(data["nodes"]) > 0


@pytest.mark.asyncio
async def test_post_graph_analyze(async_client: AsyncClient) -> None:
    """Verify POST /api/v1/graph/analyze returns misconfiguration findings."""
    res = await async_client.post("/api/v1/graph/analyze")
    assert res.status_code == 200
    data = res.json()
    assert data["total_findings"] > 0
    assert "CRITICAL" in data["findings_by_severity"]


@pytest.mark.asyncio
async def test_post_attack_paths_discover(async_client: AsyncClient) -> None:
    """Verify POST /api/v1/attack-paths/discover returns ranked paths with explanations."""
    payload = {
        "max_depth": 6,
    }
    res = await async_client.post("/api/v1/attack-paths/discover", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["total_paths"] >= 2
    top_path = data["paths"][0]
    assert "risk_score" in top_path
    assert "ranking_explanation" in top_path
    assert top_path["risk_score"] > 50.0


@pytest.mark.asyncio
async def test_get_cached_attack_paths(async_client: AsyncClient) -> None:
    """Verify GET /api/v1/attack-paths returns list of cached attack paths."""
    res = await async_client.get("/api/v1/attack-paths")
    assert res.status_code == 200
    paths = res.json()
    assert isinstance(paths, list)
    assert len(paths) >= 1


@pytest.mark.asyncio
async def test_planner_generate_and_get_campaign(async_client: AsyncClient) -> None:
    """Verify POST /api/v1/planner/generate and GET /api/v1/planner/campaigns endpoints."""
    # 1. Generate campaign
    gen_res = await async_client.post(
        "/api/v1/planner/generate",
        json={"provider": "deterministic", "run_id": "api-test-run-01"},
    )
    assert gen_res.status_code == 200
    plan_data = gen_res.json()
    assert plan_data["run_id"] == "api-test-run-01"
    assert len(plan_data["stages"]) >= 3
    camp_id = plan_data["campaign_id"]

    # 2. Retrieve campaign by ID
    get_res = await async_client.get(f"/api/v1/planner/campaigns/{camp_id}")
    assert get_res.status_code == 200
    assert get_res.json()["campaign_id"] == camp_id

    # 3. List campaigns
    list_res = await async_client.get("/api/v1/planner/campaigns")
    assert list_res.status_code == 200
    assert len(list_res.json()) >= 1


@pytest.mark.asyncio
async def test_techniques_endpoints(async_client: AsyncClient) -> None:
    """Verify GET /api/v1/techniques and GET /api/v1/techniques/{id}."""
    list_res = await async_client.get("/api/v1/techniques")
    assert list_res.status_code == 200
    techs = list_res.json()
    assert len(techs) >= 15

    # Get single valid technique
    t_res = await async_client.get("/api/v1/techniques/T1078")
    assert t_res.status_code == 200
    assert t_res.json()["technique_id"] == "T1078"

    # Get unknown technique -> 404
    bad_res = await async_client.get("/api/v1/techniques/T9999")
    assert bad_res.status_code == 404


@pytest.mark.asyncio
async def test_policies_status_and_evaluate(async_client: AsyncClient) -> None:
    """Verify GET /api/v1/policies/status and POST /api/v1/policies/evaluate."""
    # 1. Status
    status_res = await async_client.get("/api/v1/policies/status")
    assert status_res.status_code == 200
    data = status_res.json()
    assert "ACCOUNT_ALLOWLIST_CHECK" in data["active_rules"]
    assert data["dry_run_default"] is True

    # 2. Generate a plan first
    gen_res = await async_client.post(
        "/api/v1/planner/generate",
        json={"provider": "deterministic"},
    )
    plan_data = gen_res.json()

    # 3. Evaluate plan for dry-run
    eval_req = {
        "campaign_plan": plan_data,
        "target_account_id": "000000000000",
        "request_live_execution": False,
    }
    eval_res = await async_client.post("/api/v1/policies/evaluate", json=eval_req)
    assert eval_res.status_code == 200
    decision = eval_res.json()
    assert decision["approved"] is True
    assert decision["decision"] == "APPROVED_FOR_DRY_RUN"


@pytest.mark.asyncio
async def test_executions_endpoints(async_client: AsyncClient) -> None:
    """Verify POST /api/v1/executions/dry-run, GET /api/v1/executions, and teardown."""
    # 1. Generate plan
    gen_res = await async_client.post(
        "/api/v1/planner/generate",
        json={"provider": "deterministic", "run_id": "api-exec-run-01"},
    )
    assert gen_res.status_code == 200
    plan_data = gen_res.json()
    camp_id = plan_data["campaign_id"]

    # 2. Trigger dry-run
    exec_res = await async_client.post(
        "/api/v1/executions/dry-run",
        json={"campaign_id": camp_id, "prefer_docker": False},
    )
    assert exec_res.status_code == 200
    exec_record = exec_res.json()
    assert exec_record["status"] == "COMPLETED"
    assert exec_record["mode"] == "DRY_RUN"
    assert exec_record["run_id"] == "api-exec-run-01"
    assert exec_record["completed_stages"] >= 3

    # 3. Retrieve execution by run_id
    get_exec = await async_client.get("/api/v1/executions/api-exec-run-01")
    assert get_exec.status_code == 200
    assert get_exec.json()["run_id"] == "api-exec-run-01"

    # 4. List executions
    list_execs = await async_client.get("/api/v1/executions")
    assert list_execs.status_code == 200
    assert len(list_execs.json()) >= 1

    # 5. Get execution events
    events_res = await async_client.get("/api/v1/executions/api-exec-run-01/events")
    assert events_res.status_code == 200
    assert len(events_res.json()) >= 3

    # 6. Trigger teardown explicitly
    teardown_res = await async_client.post("/api/v1/executions/api-exec-run-01/teardown")
    assert teardown_res.status_code == 200
    assert teardown_res.json()["status"] == "COMPLETED"


@pytest.mark.asyncio
async def test_live_execution_with_two_key_tokens(async_client: AsyncClient) -> None:
    """Verify POST /api/v1/executions/live requires valid two-key tokens."""
    from backend.app.core.config import settings
    from backend.app.core.security import create_authorization_token

    # 1. Generate plan
    gen_res = await async_client.post(
        "/api/v1/planner/generate",
        json={"provider": "deterministic", "run_id": "api-live-run-01"},
    )
    camp_id = gen_res.json()["campaign_id"]

    # 2. Call live execution with missing tokens -> rejected (403)
    bad_res = await async_client.post(
        "/api/v1/executions/live",
        json={"campaign_id": camp_id},
    )
    assert bad_res.status_code == 403

    # 3. Generate two valid distinct tokens
    op_token = create_authorization_token("operator-01", "000000000000", settings.auth_secret_key)
    sec_token = create_authorization_token("secondary-approver-02", "000000000000", settings.auth_secret_key)

    # 4. Call live execution with valid tokens -> success (200)
    good_res = await async_client.post(
        "/api/v1/executions/live",
        json={
            "campaign_id": camp_id,
            "operator_token": op_token,
            "secondary_approver_token": sec_token,
        },
    )
    assert good_res.status_code == 200
    record = good_res.json()
    assert record["mode"] == "LIVE_SIMULATION"
    assert record["status"] == "COMPLETED"


@pytest.mark.asyncio
async def test_telemetry_endpoints(async_client: AsyncClient) -> None:
    """Verify telemetry, C2 beacons, DNS queries, and export package endpoints."""
    # 1. Generate and dry-run a plan to populate telemetry
    gen_res = await async_client.post(
        "/api/v1/planner/generate",
        json={"provider": "deterministic", "run_id": "api-telemetry-run"},
    )
    plan_data = gen_res.json()
    await async_client.post(
        "/api/v1/executions/dry-run",
        json={"campaign_id": plan_data["campaign_id"]},
    )

    # 2. Get telemetry events
    events_res = await async_client.get("/api/v1/telemetry/events?run_id=api-telemetry-run")
    assert events_res.status_code == 200
    assert len(events_res.json()) >= 1

    # 3. Get synthetic IOCs
    iocs_res = await async_client.get("/api/v1/telemetry/iocs?run_id=api-telemetry-run")
    assert iocs_res.status_code == 200
    iocs = iocs_res.json()
    assert len(iocs) >= 1
    assert iocs[0]["is_benign_marker"] is True

    # 4. Get C2 beacons
    c2_res = await async_client.get("/api/v1/telemetry/c2-beacons")
    assert c2_res.status_code == 200

    # 5. Get DNS queries
    dns_res = await async_client.get("/api/v1/telemetry/dns-queries")
    assert dns_res.status_code == 200

    # 6. Export telemetry package
    exp_res = await async_client.get("/api/v1/telemetry/export?run_id=api-telemetry-run")
    assert exp_res.status_code == 200
    exp_pkg = exp_res.json()
    assert exp_pkg["run_id"] == "api-telemetry-run"
    assert exp_pkg["total_events"] >= 1


@pytest.mark.asyncio
async def test_system_kill_switch_api(async_client: AsyncClient) -> None:
    """Verify /api/v1/system/kill-switch endpoints."""
    # 1. Initial status
    status_res = await async_client.get("/api/v1/system/kill-switch")
    assert status_res.status_code == 200
    assert "active" in status_res.json()

    # 2. Trigger kill switch
    trig_res = await async_client.post(
        "/api/v1/system/kill-switch",
        json={"reason": "API trigger test", "operator_id": "api-operator"},
    )
    assert trig_res.status_code == 200
    assert trig_res.json()["reason"] == "API trigger test"
    assert trig_res.json()["response_time_ms"] < 2000.0

    # Verify active status
    status_active = await async_client.get("/api/v1/system/kill-switch")
    assert status_active.json()["active"] is True

    # 3. Reset kill switch
    reset_res = await async_client.post(
        "/api/v1/system/kill-switch/reset",
        json={
            "authorized_token": "ADMIN_EMERGENCY_RESET_KEY_SECURE_2026",
            "operator_id": "api-operator",
        },
    )
    assert reset_res.status_code == 200
    assert reset_res.json()["status"] == "RESET_SUCCESSFUL"

    # Verify restored inactive status
    status_restored = await async_client.get("/api/v1/system/kill-switch")
    assert status_restored.json()["active"] is False


@pytest.mark.asyncio
async def test_detection_api_endpoints(async_client: AsyncClient) -> None:
    """Verify POST /api/v1/detection/correlate and GET /api/v1/detection/reports/{run_id}."""
    # 1. Generate & dry-run campaign
    gen_res = await async_client.post(
        "/api/v1/planner/generate",
        json={"provider": "deterministic", "run_id": "api-det-corr-run"},
    )
    camp_id = gen_res.json()["campaign_id"]
    await async_client.post("/api/v1/executions/dry-run", json={"campaign_id": camp_id})

    # 2. Correlate detections
    corr_res = await async_client.post(
        "/api/v1/detection/correlate",
        json={"run_id": "api-det-corr-run", "detection_profile": "FULL_COVERAGE"},
    )
    assert corr_res.status_code == 200
    corr_data = corr_res.json()
    assert corr_data["run_id"] == "api-det-corr-run"
    assert corr_data["detected_count"] >= 1
    assert corr_data["coverage_percentage"] > 0.0

    # 3. Retrieve pre-computed report
    get_res = await async_client.get("/api/v1/detection/reports/api-det-corr-run")
    assert get_res.status_code == 200
    assert get_res.json()["run_id"] == "api-det-corr-run"


@pytest.mark.asyncio
async def test_audit_api_endpoints(async_client: AsyncClient) -> None:
    """Verify audit chain retrieval, verification, and JSONL export endpoints."""
    from backend.app.core.audit import audit_logger

    run_id = "api-audit-test-run"
    audit_logger.log_event(run_id, "CAMP-01", "Planner", "PLAN_GENERATED")
    audit_logger.log_event(run_id, "CAMP-01", "Executor", "STAGE_RUN")

    # 1. Get chain
    chain_res = await async_client.get(f"/api/v1/audit/chain/{run_id}")
    assert chain_res.status_code == 200
    records = chain_res.json()
    assert len(records) == 2

    # 2. Verify chain
    ver_res = await async_client.post(f"/api/v1/audit/verify/{run_id}")
    assert ver_res.status_code == 200
    ver_data = ver_res.json()
    assert ver_data["is_valid"] is True
    assert ver_data["total_records"] == 2

    # 3. Export JSONL
    exp_res = await async_client.get(f"/api/v1/audit/export/{run_id}")
    assert exp_res.status_code == 200
    assert exp_res.json()["total_records"] == 2
    assert "PLAN_GENERATED" in exp_res.json()["jsonl_content"]


@pytest.mark.asyncio
async def test_reporting_api_endpoints(async_client: AsyncClient) -> None:
    """Verify POST /api/v1/reporting/generate and export endpoints."""
    # 1. Setup execution
    gen_res = await async_client.post(
        "/api/v1/planner/generate",
        json={"provider": "deterministic", "run_id": "api-rep-run-01"},
    )
    camp_id = gen_res.json()["campaign_id"]
    await async_client.post("/api/v1/executions/dry-run", json={"campaign_id": camp_id})

    # 2. Generate report
    rep_res = await async_client.post(
        "/api/v1/reporting/generate",
        json={"run_id": "api-rep-run-01", "target_account": "000000000000"},
    )
    assert rep_res.status_code == 200
    rep_data = rep_res.json()
    assert rep_data["run_id"] == "api-rep-run-01"
    assert rep_data["coverage_percentage"] > 0.0

    # 3. Get report by ID
    get_res = await async_client.get("/api/v1/reporting/api-rep-run-01")
    assert get_res.status_code == 200
    assert get_res.json()["run_id"] == "api-rep-run-01"

    # 4. Export Markdown format
    md_res = await async_client.get("/api/v1/reporting/api-rep-run-01/export?format=markdown")
    assert md_res.status_code == 200
    assert "# Falcon Strike-AI" in md_res.json()["content"]

    # 5. Export HTML format
    html_res = await async_client.get("/api/v1/reporting/api-rep-run-01/export?format=html")
    assert html_res.status_code == 200
    assert "<!DOCTYPE html>" in html_res.json()["content"]


@pytest.mark.asyncio
async def test_workflow_pipeline_api(async_client: AsyncClient) -> None:
    """Verify POST /api/v1/workflow/run executes all 17 stages."""
    wf_res = await async_client.post(
        "/api/v1/workflow/run",
        json={
            "mode": "synthetic",
            "dry_run": True,
            "target_account": "000000000000",
            "detection_profile": "FULL_COVERAGE",
            "planner_provider": "deterministic",
        },
    )
    assert wf_res.status_code == 200
    wf_data = wf_res.json()
    assert wf_data["status"] == "COMPLETED"
    assert wf_data["executed_stages_count"] >= 3
    assert wf_data["detection_coverage_pct"] > 0.0
    assert wf_data["teardown_verified"] is True
    assert wf_data["audit_chain_verified"] is True
    assert "json_report" in wf_data["artifacts"]
