"""Cryptographic verification engine for tamper-evident audit chains (NFR-A2)."""

from backend.app.core.audit_models import (
    GENESIS_HASH,
    AuditChainVerificationResult,
    AuditRecord,
)
from backend.app.core.logging import logger


class AuditChainVerifier:
    """Verifies integrity, cryptographic linking, and ordering of hash-chained audit logs.

    Integrity Checks Performed:
    1. Monotonic sequence continuity (no deleted or inserted records).
    2. Genesis record hash anchor verification.
    3. Content hash verification (detects modified payloads, actors, or outcomes).
    4. Linkage verification: record[i].previous_record_hash == record[i-1].current_record_hash.
    5. Run correlation consistency (all records belong to specified run_id).

    Security Limitation Disclaimer:
    Application-level hash chaining proves that records have not been altered or deleted
    without breaking the chain. However, an attacker with full root access who rewrites
    the entire storage medium and re-computes all hashes can forge a valid alternate chain.
    For legally indisputable non-repudiation, logs must be streamed to write-once-read-many (WORM)
    storage or anchored to external immutable ledgers.
    """

    @classmethod
    def verify_chain(
        cls,
        records: list[AuditRecord],
        expected_run_id: str | None = None,
    ) -> AuditChainVerificationResult:
        """Verify complete hash chain integrity for an audit log sequence.

        Args:
            records: List of AuditRecord instances to inspect.
            expected_run_id: Optional expected run ID for isolation validation.

        Returns:
            AuditChainVerificationResult indicating whether the chain is unbroken.
        """
        run_id = expected_run_id or (records[0].run_id if records else "EMPTY_RUN")
        discrepancies: list[str] = []

        if not records:
            return AuditChainVerificationResult(
                is_valid=True,
                run_id=run_id,
                total_records=0,
                verified_records=0,
                discrepancies=[],
            )

        broken_index: int | None = None

        for idx, record in enumerate(records):
            # 1. Check sequence monotonicity
            if record.sequence_number != idx:
                msg = (
                    f"Sequence discontinuity at index {idx}: expected sequence_number={idx}, "
                    f"found {record.sequence_number}. Possible deletion or reordering."
                )
                discrepancies.append(msg)
                if broken_index is None:
                    broken_index = idx

            # 2. Check run_id isolation
            if expected_run_id and record.run_id != expected_run_id:
                msg = f"Run ID mismatch at index {idx}: expected '{expected_run_id}', found '{record.run_id}'."
                discrepancies.append(msg)
                if broken_index is None:
                    broken_index = idx

            # 3. Check genesis hash on first record
            if idx == 0:
                if record.previous_record_hash != GENESIS_HASH:
                    msg = (
                        f"Genesis hash invalid at index 0: expected '{GENESIS_HASH[:16]}...', "
                        f"found '{record.previous_record_hash[:16]}...'."
                    )
                    discrepancies.append(msg)
                    if broken_index is None:
                        broken_index = idx
            else:
                # 4. Check linkage to preceding record
                preceding_record = records[idx - 1]
                if record.previous_record_hash != preceding_record.current_record_hash:
                    msg = (
                        f"Broken chain link at index {idx}: previous_record_hash '{record.previous_record_hash[:16]}...' "
                        f"does not match preceding record's current_record_hash '{preceding_record.current_record_hash[:16]}...'."
                    )
                    discrepancies.append(msg)
                    if broken_index is None:
                        broken_index = idx

            # 5. Recompute and verify current record hash
            computed_hash = record.compute_hash()
            if record.current_record_hash != computed_hash:
                msg = (
                    f"Tampered content at index {idx}: recorded hash '{record.current_record_hash[:16]}...' "
                    f"does not match recomputed hash '{computed_hash[:16]}...'. Record was modified."
                )
                discrepancies.append(msg)
                if broken_index is None:
                    broken_index = idx

        is_valid = len(discrepancies) == 0
        verified_count = len(records) if is_valid else (broken_index or 0)

        if not is_valid:
            logger.warning(
                f"Audit chain verification FAILED for run {run_id} at index {broken_index}: {len(discrepancies)} errors"
            )
        else:
            logger.info(f"Audit chain verification PASSED for run {run_id} ({len(records)} records verified)")

        return AuditChainVerificationResult(
            is_valid=is_valid,
            run_id=run_id,
            total_records=len(records),
            verified_records=verified_count,
            broken_link_index=broken_index,
            discrepancies=discrepancies,
        )

