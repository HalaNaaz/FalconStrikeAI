"""Unit tests for hash-chained tamper-evident audit logging and verification (NFR-A1, NFR-A2, NFR-A3)."""

from concurrent.futures import ThreadPoolExecutor

from backend.app.core.audit import HashChainedAuditLogger, sanitize_audit_details
from backend.app.core.audit_models import GENESIS_HASH
from backend.app.core.audit_verifier import AuditChainVerifier


class TestHashChainedAuditLogger:
    """Test suite for HashChainedAuditLogger and AuditChainVerifier."""

    def test_valid_chain_verification_succeeds(self) -> None:
        """Verify normal sequential event logging produces a mathematically verified chain."""
        logger = HashChainedAuditLogger()
        run_id = "RUN-AUDIT-001"
        camp_id = "CAMP-001"

        logger.log_event(run_id, camp_id, "Planner", "PLAN_GENERATED")
        logger.log_event(run_id, camp_id, "PolicyGate", "POLICY_EVALUATED", outcome="APPROVED")
        logger.log_event(run_id, camp_id, "ExecutionEngine", "STAGE_EXECUTED", technique_id="T1526")
        logger.log_event(run_id, camp_id, "TeardownEngine", "TEARDOWN_COMPLETED")

        chain = logger.get_chain(run_id)
        assert len(chain) == 4
        assert chain[0].previous_record_hash == GENESIS_HASH
        assert chain[1].previous_record_hash == chain[0].current_record_hash
        assert chain[2].previous_record_hash == chain[1].current_record_hash
        assert chain[3].previous_record_hash == chain[2].current_record_hash

        result = AuditChainVerifier.verify_chain(chain, expected_run_id=run_id)
        assert result.is_valid is True
        assert result.total_records == 4
        assert result.verified_records == 4
        assert len(result.discrepancies) == 0

    def test_tampered_content_detected(self) -> None:
        """Verify modifying any content field breaks cryptographic verification."""
        logger = HashChainedAuditLogger()
        run_id = "RUN-TAMPER-001"
        camp_id = "CAMP-001"

        logger.log_event(run_id, camp_id, "PolicyGate", "POLICY_EVALUATED", outcome="DENIED")
        logger.log_event(run_id, camp_id, "ExecutionEngine", "STAGE_EXECUTED")

        chain = logger.get_chain(run_id)

        # Adversary attempts to forge audit log: change outcome from DENIED to APPROVED
        tampered_record = chain[0].model_copy(update={"outcome": "APPROVED"})
        tampered_chain = [tampered_record, chain[1]]

        result = AuditChainVerifier.verify_chain(tampered_chain, expected_run_id=run_id)
        assert result.is_valid is False
        assert result.broken_link_index == 0
        assert any("Tampered content" in d for d in result.discrepancies)

    def test_deleted_record_detected(self) -> None:
        """Verify removing a record from the sequence triggers sequence and link mismatch."""
        logger = HashChainedAuditLogger()
        run_id = "RUN-DELETE-001"
        camp_id = "CAMP-001"

        logger.log_event(run_id, camp_id, "Actor1", "EVENT_0")
        logger.log_event(run_id, camp_id, "Actor2", "EVENT_1_TO_DELETE")
        logger.log_event(run_id, camp_id, "Actor3", "EVENT_2")

        chain = logger.get_chain(run_id)

        # Adversary deletes middle record (EVENT_1)
        truncated_chain = [chain[0], chain[2]]

        result = AuditChainVerifier.verify_chain(truncated_chain, expected_run_id=run_id)
        assert result.is_valid is False
        assert result.broken_link_index == 1
        assert any("Sequence discontinuity" in d for d in result.discrepancies)

    def test_reordered_records_detected(self) -> None:
        """Verify swapping adjacent records breaks the hash chain."""
        logger = HashChainedAuditLogger()
        run_id = "RUN-REORDER-001"
        camp_id = "CAMP-001"

        logger.log_event(run_id, camp_id, "Actor1", "EVENT_0")
        logger.log_event(run_id, camp_id, "Actor2", "EVENT_1")

        chain = logger.get_chain(run_id)
        reordered_chain = [chain[1], chain[0]]

        result = AuditChainVerifier.verify_chain(reordered_chain, expected_run_id=run_id)
        assert result.is_valid is False
        assert result.broken_link_index == 0

    def test_empty_chain_is_valid(self) -> None:
        """Verify empty chain returns valid result without error."""
        result = AuditChainVerifier.verify_chain([], expected_run_id="RUN-EMPTY")
        assert result.is_valid is True
        assert result.total_records == 0

    def test_secret_redaction_in_details(self) -> None:
        """Verify credentials and secret tokens are scrubbed before recording."""
        logger = HashChainedAuditLogger()
        run_id = "RUN-SECRET-001"

        record = logger.log_event(
            run_id=run_id,
            campaign_id="CAMP-001",
            actor="Operator",
            action="LOGIN",
            details={
                "operator_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.sensitive_payload",
                "client_secret": "my-ultra-secret-password-123",
                "safe_field": "public_username",
            },
        )

        assert record.details["operator_token"] == "[REDACTED_SECRET]"
        assert record.details["client_secret"] == "[REDACTED_SECRET]"
        assert record.details["safe_field"] == "public_username"

    def test_sanitize_audit_details_nested(self) -> None:
        """Verify recursive secret scrubbing handles nested dictionaries and lists."""
        nested = {
            "auth": {"api_key": "secret123", "user": "admin"},
            "tokens": [{"token": "abc"}, "normal_string"],
        }
        cleaned = sanitize_audit_details(nested)
        assert cleaned["auth"]["api_key"] == "[REDACTED_SECRET]"
        assert cleaned["auth"]["user"] == "admin"
        assert cleaned["tokens"][0]["token"] == "[REDACTED_SECRET]"
        assert cleaned["tokens"][1] == "normal_string"

    def test_jsonl_export(self, tmp_path: object) -> None:
        """Verify JSONL serialization exports valid line-delimited records."""
        logger = HashChainedAuditLogger()
        run_id = "RUN-JSONL-001"

        logger.log_event(run_id, "CAMP-01", "Planner", "ACTION_1")
        logger.log_event(run_id, "CAMP-01", "Executor", "ACTION_2")

        export_path = str(tmp_path) + "/audit.jsonl"
        content = logger.export_jsonl(run_id, file_path=export_path)

        lines = content.strip().split("\n")
        assert len(lines) == 2
        assert "ACTION_1" in lines[0]
        assert "ACTION_2" in lines[1]

    def test_concurrent_appends_thread_safety(self) -> None:
        """Verify multiple threads appending simultaneously maintain chain sequence integrity."""
        logger = HashChainedAuditLogger()
        run_id = "RUN-CONCURRENT-001"
        camp_id = "CAMP-001"

        def append_task(thread_id: int) -> None:
            for i in range(10):
                logger.log_event(
                    run_id=run_id,
                    campaign_id=camp_id,
                    actor=f"Thread-{thread_id}",
                    action=f"STEP-{i}",
                )

        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(append_task, tid) for tid in range(5)]
            for f in futures:
                f.result()

        chain = logger.get_chain(run_id)
        assert len(chain) == 50

        # Verify the entire multi-threaded chain
        result = AuditChainVerifier.verify_chain(chain, expected_run_id=run_id)
        assert result.is_valid is True
        assert result.total_records == 50
        assert result.verified_records == 50
