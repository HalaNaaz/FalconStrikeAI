"""API routes for adversary detection correlation and MTTD analysis (FR-5.1)."""


from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from backend.app.core.state import app_state
from backend.app.detection.correlation import DetectionCorrelationEngine
from backend.app.detection.detection_stub import DetectionStub
from backend.app.detection.models import (
    DetectionCorrelationReport,
    DetectionSourceType,
    SecurityDetectionEvent,
)

router = APIRouter(prefix="/detection", tags=["Detection Correlation & MTTD"])

# Cache for correlation reports: run_id -> DetectionCorrelationReport
_cached_correlation_reports: dict[str, DetectionCorrelationReport] = {}


class DetectionCorrelateRequest(BaseModel):
    """Payload to trigger correlation of ground-truth telemetry with alert feeds."""

    run_id: str = Field(description="Campaign run ID to correlate")
    detection_profile: str = Field(
        default="FULL_COVERAGE",
        description="Profile for synthetic alert stub: FULL_COVERAGE, PARTIAL_COVERAGE, HIGH_MISS_RATE",
    )
    custom_alerts: list[SecurityDetectionEvent] | None = Field(
        default=None, description="Optional custom alerts to correlate instead of stub"
    )


@router.post(
    "/correlate",
    response_model=DetectionCorrelationReport,
    summary="Correlate ground-truth telemetry against detection alerts (FR-5.1)",
)
def correlate_detections(req: DetectionCorrelateRequest) -> DetectionCorrelationReport:
    """Evaluate detection coverage, identify missed/partial techniques, and calculate MTTD."""
    execution = app_state.execution_engine.get_execution(req.run_id)
    campaign_id = execution.campaign_id if execution else "UNKNOWN"

    export_pkg = app_state.telemetry_collector.export_telemetry_package(
        run_id=req.run_id, campaign_id=campaign_id
    )

    if not export_pkg.raw_events:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No telemetry events found for run '{req.run_id}'. Execute campaign first.",
        )

    if req.custom_alerts is not None:
        alerts = req.custom_alerts
        source_name = "custom_feed"
        source_type = DetectionSourceType.TEST_FIXTURE
    else:
        stub = DetectionStub(profile=req.detection_profile)
        alerts = stub.generate_detections_from_telemetry(export_pkg)
        source_name = stub.adapter_name
        source_type = stub.source_type

    report = DetectionCorrelationEngine.correlate(
        export_package=export_pkg,
        detection_events=alerts,
        source_name=source_name,
        source_type=source_type,
    )

    _cached_correlation_reports[req.run_id] = report
    return report


@router.get(
    "/reports/{run_id}",
    response_model=DetectionCorrelationReport,
    summary="Retrieve detection correlation report by run ID",
)
def get_correlation_report(run_id: str) -> DetectionCorrelationReport:
    """Retrieve pre-computed correlation report."""
    report = _cached_correlation_reports.get(run_id)
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Correlation report for run '{run_id}' not found. Run correlation first.",
        )
    return report
