"""API routes for tamper-evident hash-chained audit logging and verification (NFR-A1, NFR-A2)."""

from typing import Any

from fastapi import APIRouter, HTTPException, status

from backend.app.core.audit import audit_logger
from backend.app.core.audit_models import AuditChainVerificationResult, AuditRecord
from backend.app.core.audit_verifier import AuditChainVerifier

router = APIRouter(prefix="/audit", tags=["Tamper-Evident Audit Chain"])


@router.get(
    "/chain/{run_id}",
    response_model=list[AuditRecord],
    summary="Retrieve complete hash-chained audit records for a run ID",
)
def get_audit_chain(run_id: str) -> list[AuditRecord]:
    """Retrieve all sealed, immutable audit log records for the campaign run."""
    records = audit_logger.get_chain(run_id)
    if not records:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No audit records found for run '{run_id}'.",
        )
    return records


@router.post(
    "/verify/{run_id}",
    response_model=AuditChainVerificationResult,
    summary="Verify cryptographic hash-chain integrity for a run ID",
)
def verify_audit_chain(run_id: str) -> AuditChainVerificationResult:
    """Verify cryptographic SHA-256 linking and sequence monotonicity of audit records (NFR-A2)."""
    records = audit_logger.get_chain(run_id)
    result = AuditChainVerifier.verify_chain(records=records, expected_run_id=run_id)
    return result


@router.get(
    "/export/{run_id}",
    summary="Export audit records in JSONL format",
)
def export_audit_jsonl(run_id: str) -> dict[str, Any]:
    """Export the sealed audit chain as JSONL text."""
    records = audit_logger.get_chain(run_id)
    if not records:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No audit records found for run '{run_id}'.",
        )
    jsonl_text = audit_logger.export_jsonl(run_id)
    return {
        "run_id": run_id,
        "total_records": len(records),
        "jsonl_content": jsonl_text,
    }
