"""API routes for SOC assessment report generation and exports (FR-5.2, FR-5.3)."""

from typing import Any

from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel, Field

from backend.app.core.audit import audit_logger
from backend.app.core.audit_verifier import AuditChainVerifier
from backend.app.core.state import app_state
from backend.app.detection.correlation import DetectionCorrelationEngine
from backend.app.detection.detection_stub import DetectionStub
from backend.app.reporting.exporters import ReportExporter
from backend.app.reporting.generator import SOCReportGenerator
from backend.app.reporting.models import SOCReportData

router = APIRouter(prefix="/reporting", tags=["SOC Reporting & Exports"])

_cached_soc_reports: dict[str, SOCReportData] = {}


class GenerateReportRequest(BaseModel):
    """Payload to trigger SOC report generation for a completed run."""

    run_id: str = Field(description="Campaign execution run ID")
    target_account: str = Field(default="000000000000")
    detection_profile: str = Field(default="FULL_COVERAGE")


@router.post(
    "/generate",
    response_model=SOCReportData,
    summary="Generate comprehensive SOC assessment report (FR-5.2)",
)
def generate_soc_report(req: GenerateReportRequest) -> SOCReportData:
    """Compile and export an end-to-end SOC assessment report."""
    run_id = req.run_id
    execution = app_state.execution_engine.get_execution(run_id)
    if not execution:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Execution record for run '{run_id}' not found.",
        )

    plan = app_state.get_campaign(execution.campaign_id)
    if not plan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Campaign plan '{execution.campaign_id}' not found.",
        )

    # 1. Telemetry and Detection
    export_pkg = app_state.telemetry_collector.export_telemetry_package(run_id, execution.campaign_id)
    stub = DetectionStub(profile=req.detection_profile)
    detections = stub.generate_detections_from_telemetry(export_pkg)
    correlation = DetectionCorrelationEngine.correlate(export_pkg, detections)

    # 2. Teardown
    teardown_res = app_state.execution_engine.teardown_engine.execute_teardown(
        run_id=run_id, current_environment=app_state.environment_data
    )

    # 3. Audit
    chain = audit_logger.get_chain(run_id)
    audit_ver = AuditChainVerifier.verify_chain(chain, expected_run_id=run_id)

    report = SOCReportGenerator.generate_report(
        plan=plan,
        execution=execution,
        correlation=correlation,
        synthetic_iocs=export_pkg.iocs,
        teardown_result=teardown_res,
        audit_verification=audit_ver,
        target_account=req.target_account,
    )

    _cached_soc_reports[run_id] = report
    return report


@router.get(
    "/{run_id}",
    response_model=SOCReportData,
    summary="Retrieve compiled SOC report by run ID",
)
def get_soc_report(run_id: str) -> SOCReportData:
    """Retrieve pre-generated SOC assessment report."""
    report = _cached_soc_reports.get(run_id)
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"SOC report for run '{run_id}' not found. Generate report first.",
        )
    return report


@router.get(
    "/{run_id}/export",
    summary="Export SOC report as Markdown or HTML",
)
def export_report_format(
    run_id: str,
    format: str = Query("markdown", description="Export format: markdown or html"),
) -> dict[str, Any]:
    """Retrieve formatted report text."""
    report = _cached_soc_reports.get(run_id)
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"SOC report for run '{run_id}' not found.",
        )

    if format.lower() == "html":
        content = ReportExporter.export_html(report)
        media_type = "text/html"
    else:
        content = ReportExporter.export_markdown(report)
        media_type = "text/markdown"

    return {
        "run_id": run_id,
        "format": format.lower(),
        "media_type": media_type,
        "content": content,
    }

