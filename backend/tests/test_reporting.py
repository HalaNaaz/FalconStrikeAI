"""Unit tests for SOC report generation, templates, and multi-format exporters (FR-5.2, FR-5.3)."""

from backend.app.core.audit_models import AuditChainVerificationResult
from backend.app.detection.models import (
    CorrelatedTechniqueResult,
    DetectionCorrelationReport,
    DetectionStatus,
)
from backend.app.orchestrator.models import (
    CampaignExecutionRecord,
    ExecutionMode,
    ExecutionStatus,
    TeardownResult,
)
from backend.app.planner.models import CampaignPlan, CampaignStage
from backend.app.reporting.exporters import ReportExporter
from backend.app.reporting.generator import SOCReportGenerator
from backend.app.reporting.models import SOCReportData
from backend.app.techniques.models import AttackTactic
from backend.app.telemetry.models import IOCType, SyntheticIOC


class TestSOCReporting:
    """Test suite for SOC report generator and exporters."""

    def test_complete_report_generation(self, tmp_path: object) -> None:
        """Verify full SOC report data compilation from all pipeline outputs."""
        run_id = "RUN-REP-TEST-01"
        camp_id = "CAMP-REP-01"

        plan = CampaignPlan(
            campaign_id=camp_id,
            run_id=run_id,
            source_attack_path_id="PATH-01",
            objective="Validate CloudTrail detection of privilege escalation",
            stages=[
                CampaignStage(
                    stage_id="S1",
                    stage_name="Recon",
                    tactic=AttackTactic.DISCOVERY,
                    technique_id="T1526",
                    technique_name="Cloud Service Discovery",
                    target_resource_id="arn:aws:iam::000000000000:role/ReadOnly",
                    expected_observation="ListRoles",
                ),
                CampaignStage(
                    stage_id="S2",
                    stage_name="Escalate",
                    tactic=AttackTactic.PRIVILEGE_ESCALATION,
                    technique_id="T1078",
                    technique_name="Valid Accounts",
                    target_resource_id="arn:aws:iam::000000000000:role/AdminRole",
                    expected_observation="AssumeRole",
                ),
            ],
            selected_techniques=["T1526", "T1078"],
            risk_summary="Low risk containment",
            planning_rationale="Emulation of IAM privilege escalation",
            approved_by_policy=True,
        )

        execution = CampaignExecutionRecord(
            run_id=run_id,
            campaign_id=camp_id,
            mode=ExecutionMode.DRY_RUN,
            status=ExecutionStatus.COMPLETED,
            total_stages=2,
            completed_stages=2,
            failed_stages=0,
            duration_ms=45.2,
        )

        tech_res1 = CorrelatedTechniqueResult(
            technique_id="T1526",
            technique_name="Cloud Service Discovery",
            tactic="Discovery",
            status=DetectionStatus.DETECTED,
            detection_latency_seconds=12.0,
            detection_count=1,
        )
        tech_res2 = CorrelatedTechniqueResult(
            technique_id="T1078",
            technique_name="Valid Accounts",
            tactic="Privilege Escalation",
            status=DetectionStatus.DETECTED,
            detection_latency_seconds=18.0,
            detection_count=2,
        )

        correlation = DetectionCorrelationReport(
            run_id=run_id,
            campaign_id=camp_id,
            total_executed_techniques=2,
            detected_count=2,
            partially_detected_count=0,
            missed_count=0,
            coverage_percentage=100.0,
            mean_time_to_detect_seconds=15.0,
            techniques=[tech_res1, tech_res2],
        )

        iocs = [
            SyntheticIOC(
                run_id=run_id,
                technique_id="T1078",
                ioc_type=IOCType.SHA256,
                value="e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
                detection_guidance="Alert on sha256 match",
            )
        ]

        teardown = TeardownResult(
            run_id=run_id,
            status="COMPLETED",
            actions_attempted=1,
            actions_succeeded=1,
            baseline_verified=True,
        )

        audit_verification = AuditChainVerificationResult(
            is_valid=True,
            run_id=run_id,
            total_records=5,
            verified_records=5,
        )

        report = SOCReportGenerator.generate_report(
            plan=plan,
            execution=execution,
            correlation=correlation,
            synthetic_iocs=iocs,
            teardown_result=teardown,
            audit_verification=audit_verification,
            target_account="000000000000",
            environment_provenance="SYNTHETIC_DATA",
            runner_provenance="IN_MEMORY_SIMULATION",
            detection_provenance="DETECTION_STUB",
        )

        assert isinstance(report, SOCReportData)
        assert report.run_id == run_id
        assert report.coverage_percentage == 100.0
        assert report.mean_time_to_detect_seconds == 15.0
        assert len(report.remediation_recommendations) == 2
        assert report.teardown_verification["baseline_verified"] is True
        assert report.audit_chain_verification["is_valid"] is True
        assert len(report.limitations_and_disclaimers) >= 3

        # Test Exporters
        base_path = str(tmp_path)
        json_file = f"{base_path}/report.json"
        md_file = f"{base_path}/report.md"
        html_file = f"{base_path}/report.html"

        # 1. JSON Export
        json_str = ReportExporter.export_json(report, file_path=json_file)
        assert f'"run_id": "{run_id}"' in json_str
        assert '"coverage_percentage": 100.0' in json_str

        # 2. Markdown Export
        md_str = ReportExporter.export_markdown(report, file_path=md_file)
        assert f"**Run ID**: `{run_id}`" in md_str
        assert "## 1. Provenance & Integrity Classification" in md_str
        assert "| `T1078` | Valid Accounts |" in md_str
        assert "15.0 seconds" in md_str

        # 3. HTML Export
        html_str = ReportExporter.export_html(report, file_path=html_file)
        assert "<!DOCTYPE html>" in html_str
        assert f"Falcon Strike-AI SOC Report - {run_id}" in html_str
        assert "100.0%" in html_str
        assert "15.0s" in html_str

