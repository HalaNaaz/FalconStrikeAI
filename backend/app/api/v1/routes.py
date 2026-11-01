"""API v1 root router aggregating all functional endpoints with centralized authentication."""

from fastapi import APIRouter, Depends

from backend.app.api.v1.attack_paths import router as attack_paths_router
from backend.app.api.v1.audit import router as audit_router
from backend.app.api.v1.auth import router as auth_router
from backend.app.api.v1.collectors import router as collectors_router
from backend.app.api.v1.detection import router as detection_router
from backend.app.api.v1.executions import router as executions_router
from backend.app.api.v1.graph import router as graph_router
from backend.app.api.v1.health import router as health_router
from backend.app.api.v1.integrations import router as integrations_router
from backend.app.api.v1.planner import router as planner_router
from backend.app.api.v1.policies import router as policies_router
from backend.app.api.v1.reporting import router as reporting_router
from backend.app.api.v1.system import router as system_router
from backend.app.api.v1.techniques import router as techniques_router
from backend.app.api.v1.telemetry import router as telemetry_router
from backend.app.api.v1.workflow import router as workflow_router
from backend.app.core.dependencies import get_current_operator

api_v1_router = APIRouter(prefix="/api/v1")

# 1. Unauthenticated endpoints (Health, readiness, auth login, integrations status)
api_v1_router.include_router(health_router)
api_v1_router.include_router(auth_router)
api_v1_router.include_router(integrations_router)

# 2. Authenticated endpoints (Require valid Bearer JWT or X-API-Key)
auth_dep = [Depends(get_current_operator)]

api_v1_router.include_router(collectors_router, dependencies=auth_dep)
api_v1_router.include_router(graph_router, dependencies=auth_dep)
api_v1_router.include_router(attack_paths_router, dependencies=auth_dep)
api_v1_router.include_router(planner_router, dependencies=auth_dep)
api_v1_router.include_router(techniques_router, dependencies=auth_dep)
api_v1_router.include_router(policies_router, dependencies=auth_dep)
api_v1_router.include_router(executions_router, dependencies=auth_dep)
api_v1_router.include_router(telemetry_router, dependencies=auth_dep)
api_v1_router.include_router(system_router, dependencies=auth_dep)
api_v1_router.include_router(detection_router, dependencies=auth_dep)
api_v1_router.include_router(audit_router, dependencies=auth_dep)
api_v1_router.include_router(reporting_router, dependencies=auth_dep)
api_v1_router.include_router(workflow_router, dependencies=auth_dep)
