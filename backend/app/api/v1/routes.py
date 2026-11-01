"""API v1 root router aggregating all functional endpoints."""

from fastapi import APIRouter

from backend.app.api.v1.attack_paths import router as attack_paths_router
from backend.app.api.v1.audit import router as audit_router
from backend.app.api.v1.collectors import router as collectors_router
from backend.app.api.v1.detection import router as detection_router
from backend.app.api.v1.executions import router as executions_router
from backend.app.api.v1.graph import router as graph_router
from backend.app.api.v1.health import router as health_router
from backend.app.api.v1.planner import router as planner_router
from backend.app.api.v1.policies import router as policies_router
from backend.app.api.v1.reporting import router as reporting_router
from backend.app.api.v1.system import router as system_router
from backend.app.api.v1.techniques import router as techniques_router
from backend.app.api.v1.telemetry import router as telemetry_router
from backend.app.api.v1.workflow import router as workflow_router

api_v1_router = APIRouter(prefix="/api/v1")

# Mount all domain routers
api_v1_router.include_router(health_router)
api_v1_router.include_router(collectors_router)
api_v1_router.include_router(graph_router)
api_v1_router.include_router(attack_paths_router)
api_v1_router.include_router(planner_router)
api_v1_router.include_router(techniques_router)
api_v1_router.include_router(policies_router)
api_v1_router.include_router(executions_router)
api_v1_router.include_router(telemetry_router)
api_v1_router.include_router(system_router)
api_v1_router.include_router(detection_router)
api_v1_router.include_router(audit_router)
api_v1_router.include_router(reporting_router)
api_v1_router.include_router(workflow_router)
