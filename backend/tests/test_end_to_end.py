"""End-to-end integration test verifying the full 17-stage emulation and CTEM pipeline."""

from pathlib import Path

from backend.app.core.audit import audit_logger
from backend.app.core.audit_verifier import AuditChainVerifier
from backend.app.workflow import EndToEndWorkflow, WorkflowExecutionResult


class TestEndToEndWorkflow:
    """Test suite for full automated closed-loop workflow execution."""

    def test_complete_synthetic_dry_run_pipeline(self, tmp_path: object) -> None:
        """Verify the complete 17-stage workflow executes cleanly and produces all verified artifacts."""
        workflow = EndToEndWorkflow(artifacts_dir=tmp_path)
        custom_run_id = "RUN-E2E-TEST-VERIFY-001"

        result = workflow.run(
            mode="synthetic",
            dry_run=True,
            target_account="000000000000",
            custom_run_id=custom_run_id,
            detection_profile="FULL_COVERAGE",
            planner_provider="deterministic",
        )

        assert isinstance(result, WorkflowExecutionResult)
        # 1. Verify single correlated run_id
        assert result.run_id == custom_run_id
        assert result.status == "COMPLETED"
        assert result.summary["stages_successful"] == 17

        # 2. Verify graph and path discovery
        assert result.environment_nodes_count >= 10
        assert result.attack_paths_found_count >= 1

        # 3. Verify stage execution
        assert result.executed_stages_count >= 3

        # 4. Verify detection metrics & MTTD
        assert result.detection_coverage_pct == 100.0
        assert result.mttd_seconds is not None
        assert result.mttd_seconds > 0.0

        # 5. Verify teardown and baseline recovery
        assert result.teardown_verified is True

        # 6. Verify cryptographic audit chain integrity
        assert result.audit_chain_verified is True
        chain = audit_logger.get_chain(custom_run_id)
        assert len(chain) >= 6
        audit_ver = AuditChainVerifier.verify_chain(chain, expected_run_id=custom_run_id)
        assert audit_ver.is_valid is True

        # 7. Verify all artifacts exist on disk
        for artifact_key, file_path_str in result.artifacts.items():
            artifact_file = Path(file_path_str)
            assert artifact_file.exists(), f"Artifact {artifact_key} at {file_path_str} was not written to disk."
            assert artifact_file.stat().st_size > 50, f"Artifact {artifact_key} is unexpectedly empty."

        # Verify JSON report content
        json_report_content = Path(result.artifacts["json_report"]).read_text(encoding="utf-8")
        assert custom_run_id in json_report_content
        assert "SYNTHETIC_DATA" in json_report_content
        assert "DETECTION_STUB" in json_report_content

        # Verify Markdown report content
        md_report_content = Path(result.artifacts["markdown_report"]).read_text(encoding="utf-8")
        assert f"**Run ID**: `{custom_run_id}`" in md_report_content
        assert "## 1. Provenance & Integrity Classification" in md_report_content

        # Verify HTML report content
        html_report_content = Path(result.artifacts["html_report"]).read_text(encoding="utf-8")
        assert "<!DOCTYPE html>" in html_report_content
        assert custom_run_id in html_report_content

        # Verify Audit JSONL content
        audit_jsonl_content = Path(result.artifacts["audit_chain_jsonl"]).read_text(encoding="utf-8")
        assert "PIPELINE_STARTED" in audit_jsonl_content
        assert "CAMPAIGN_EXECUTED" in audit_jsonl_content

