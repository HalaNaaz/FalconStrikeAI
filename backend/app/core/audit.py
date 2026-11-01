"""Thread-safe, append-only cryptographic hash-chained audit logger (NFR-A1, NFR-A2, NFR-A3)."""

import json
import threading
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from backend.app.core.audit_models import GENESIS_HASH, AuditRecord
from backend.app.core.logging import logger

SENSITIVE_KEYS: set[str] = {
    "token",
    "secret",
    "password",
    "api_key",
    "client_secret",
    "auth_secret_key",
    "private_key",
    "operator_token",
    "secondary_approver_token",
    "authorized_token",
}


def sanitize_audit_details(data: dict[str, Any]) -> dict[str, Any]:
    """Recursively scrub sensitive credential and key fields from audit records."""
    sanitized: dict[str, Any] = {}
    for key, val in data.items():
        key_lower = key.lower()
        is_sensitive = key_lower in SENSITIVE_KEYS or any(
            key_lower.endswith(f"_{s}") or key_lower.startswith(f"{s}_") for s in SENSITIVE_KEYS
        )
        if is_sensitive:
            sanitized[key] = "[REDACTED_SECRET]"
        elif isinstance(val, dict):
            sanitized[key] = sanitize_audit_details(val)
        elif isinstance(val, list):
            sanitized[key] = [
                sanitize_audit_details(item) if isinstance(item, dict) else item for item in val
            ]
        else:
            sanitized[key] = val
    return sanitized


class HashChainedAuditLogger:
    """Thread-safe append-only audit logger enforcing cryptographic SHA-256 hash chaining (NFR-A2).

    Integrity Guarantees:
    - Strictly monotonic sequence numbering per run_id.
    - Each record seals the SHA-256 hash of its predecessor.
    - Sensitive token and credential fields are automatically redacted before hashing.
    - Application-level append-only guarantees.
    """

    def __init__(self, artifacts_dir: Path | str | None = None) -> None:
        self._lock = threading.RLock()
        # Map of run_id -> list[AuditRecord]
        self._chains: dict[str, list[AuditRecord]] = {}
        self.artifacts_dir = Path(artifacts_dir or "artifacts/audit")

    def log_event(
        self,
        run_id: str,
        campaign_id: str,
        actor: str,
        action: str,
        technique_id: str | None = None,
        target_resource: str | None = None,
        outcome: str = "SUCCESS",
        ioc_references: list[str] | None = None,
        details: dict[str, Any] | None = None,
        timestamp: str | None = None,
    ) -> AuditRecord:
        """Append a new sealed, hash-chained audit record."""
        with self._lock:
            if run_id not in self._chains:
                self._chains[run_id] = []

            chain = self._chains[run_id]
            seq_num = len(chain)

            # Determine previous hash: genesis if first record, else predecessor's hash
            prev_hash = chain[-1].current_record_hash if chain else GENESIS_HASH

            # Sanitize details to guarantee zero secret leakage
            safe_details = sanitize_audit_details(details or {})

            record = AuditRecord(
                sequence_number=seq_num,
                run_id=run_id,
                campaign_id=campaign_id,
                timestamp=timestamp or datetime.now(UTC).isoformat(),
                actor=actor,
                action=action,
                technique_id=technique_id,
                target_resource=target_resource,
                outcome=outcome,
                ioc_references=ioc_references or [],
                details=safe_details,
                previous_record_hash=prev_hash,
            )

            # Seal record with SHA-256 hash of canonical content
            record.current_record_hash = record.compute_hash()
            chain.append(record)

            logger.info(
                f"Audit record sealed: seq={seq_num}, actor={actor}, action={action}, "
                f"hash={record.current_record_hash[:12]}... [run_id={run_id}]"
            )

            return record

    def get_chain(self, run_id: str) -> list[AuditRecord]:
        """Retrieve all audit records for a run in sequence order."""
        with self._lock:
            return list(self._chains.get(run_id, []))

    def export_jsonl(self, run_id: str, file_path: Path | str | None = None) -> str:
        """Serialize audit chain to JSONL format and optionally persist to disk."""
        with self._lock:
            records = self.get_chain(run_id)
            lines = [json.dumps(record.model_dump(), sort_keys=True) for record in records]
            jsonl_content = "\n".join(lines) + ("\n" if lines else "")

            if file_path:
                target_path = Path(file_path)
                target_path.parent.mkdir(parents=True, exist_ok=True)
                target_path.write_text(jsonl_content, encoding="utf-8")
                logger.info(f"Exported {len(records)} audit records to {target_path}")

            return jsonl_content

    def clear(self) -> None:
        """Clear the in-memory audit chains."""
        with self._lock:
            self._chains.clear()


audit_logger = HashChainedAuditLogger()
