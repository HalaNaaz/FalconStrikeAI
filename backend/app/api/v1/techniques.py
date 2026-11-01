"""API endpoints for MITRE ATT&CK technique catalog and contracts (FR-2.2, FR-3.1)."""

from fastapi import APIRouter, HTTPException

from backend.app.techniques.models import TechniqueContract
from backend.app.techniques.registry import technique_registry

router = APIRouter(prefix="/techniques", tags=["Technique Registry"])


@router.get("", response_model=list[TechniqueContract])
async def list_techniques() -> list[TechniqueContract]:
    """Retrieve all approved MITRE ATT&CK techniques in the safe emulation registry."""
    return technique_registry.list_all()


@router.get("/{technique_id}", response_model=TechniqueContract)
async def get_technique(technique_id: str) -> TechniqueContract:
    """Retrieve contract and safety specifications for an individual technique."""
    contract = technique_registry.get(technique_id.strip())
    if not contract:
        raise HTTPException(
            status_code=404,
            detail=f"Technique ID '{technique_id}' is not an approved technique in the registry.",
        )
    return contract

