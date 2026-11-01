"""API routes for telemetry retrieval, C2 beacon logs, and synthetic IOC export."""


from fastapi import APIRouter, Query

from backend.app.core.state import app_state
from backend.app.techniques.models import SimulationEvent
from backend.app.telemetry.models import (
    C2BeaconEvent,
    DNSSignallingEvent,
    SyntheticIOC,
    TelemetryExportPackage,
)

router = APIRouter(prefix="/telemetry", tags=["Telemetry & IOCs"])


@router.get(
    "/events",
    response_model=list[SimulationEvent],
    summary="Retrieve recorded simulation telemetry events",
)
def get_telemetry_events(
    run_id: str = Query(..., description="Run ID to filter simulation events")
) -> list[SimulationEvent]:
    """Retrieve raw simulation events for a specific execution run."""
    return app_state.telemetry_collector.get_simulation_events(run_id)


@router.get(
    "/iocs",
    response_model=list[SyntheticIOC],
    summary="Retrieve generated synthetic indicators of compromise (IOCs)",
)
def get_synthetic_iocs(
    run_id: str = Query(..., description="Run ID to filter synthetic IOCs")
) -> list[SyntheticIOC]:
    """Retrieve synthetic indicators of compromise for detection validation (FR-3.4)."""
    return app_state.telemetry_collector.get_iocs(run_id)


@router.get(
    "/c2-beacons",
    response_model=list[C2BeaconEvent],
    summary="Retrieve benign C2 heartbeat / beaconing logs",
)
def get_c2_beacons(
    run_id: str | None = Query(default=None, description="Optional run ID filter")
) -> list[C2BeaconEvent]:
    """Retrieve recorded benign C2 beacon signals (FR-3.4)."""
    if run_id:
        return app_state.telemetry_collector.get_c2_beacons(run_id)
    return app_state.telemetry_collector.c2_sink.list_all_beacons()


@router.get(
    "/dns-queries",
    response_model=list[DNSSignallingEvent],
    summary="Retrieve benign DNS covert-signalling query logs",
)
def get_dns_queries(
    run_id: str | None = Query(default=None, description="Optional run ID filter")
) -> list[DNSSignallingEvent]:
    """Retrieve recorded benign DNS signalling queries (FR-3.4)."""
    if run_id:
        return app_state.telemetry_collector.get_dns_queries(run_id)
    return app_state.telemetry_collector.dns_sink.list_all_queries()


@router.get(
    "/export",
    response_model=TelemetryExportPackage,
    summary="Export consolidated telemetry and IOC package as JSON",
)
def export_telemetry_package(
    run_id: str = Query(..., description="Run ID for the export package")
) -> TelemetryExportPackage:
    """Export a consolidated package of telemetry, C2 signals, and IOCs (FR-3.4)."""
    execution = app_state.execution_engine.get_execution(run_id)
    campaign_id = execution.campaign_id if execution else "UNKNOWN"
    return app_state.telemetry_collector.export_telemetry_package(
        run_id=run_id, campaign_id=campaign_id
    )
