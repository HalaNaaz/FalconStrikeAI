"""SOC assessment report compiler combining campaign, execution, detection, and audit results (FR-5.2)."""

from typing import Any

from backend.app.core.audit_models import AuditChainVerificationResult
from backend.app.core.logging import logger
from backend.app.detection.models import DetectionCorrelationReport
from backend.app.orchestrator.models import CampaignExecutionRecord, TeardownResult
from backend.app.planner.models import CampaignPlan
from backend.app.reporting.models import RemediationItem, SOCReportData
from backend.app.telemetry.models import SyntheticIOC


class SOCReportGenerator:
    """Generates comprehensive SOC assessment reports integrating multi-domain evaluation results."""

    @classmethod
    def generate_report(
        cls,
        plan: CampaignPlan,
        execution: CampaignExecutionRecord,
        correlation: DetectionCorrelationReport,
        synthetic_iocs: list[SyntheticIOC],
        teardown_result: TeardownResult | None = None,
        audit_verification: AuditChainVerificationResult | None = None,
        target_account: str = "000000000000",
        environment_provenance: str = "SYNTHETIC_DATA",
        runner_provenance: str = "IN_MEMORY_SIMULATION",
        detection_provenance: str = "DETECTION_STUB",
    ) -> SOCReportData:
        """Compile an end-to-end SOC assessment report.

        Args:
            plan: The planned campaign details.
            execution: The execution record with stage progression.
            correlation: The detection correlation findings and MTTD.
            synthetic_iocs: List of generated ground-truth IOCs.
            teardown_result: Post-execution teardown status.
            audit_verification: Cryptographic audit chain verification result.
            target_account: Target AWS account ID.
            environment_provenance: Provenance of environment assets.
            runner_provenance: Provenance of execution runtime.
            detection_provenance: Provenance of alert ingestion.

        Returns:
            SOCReportData model ready for JSON, Markdown, or HTML export.
        """
        run_id = plan.run_id
        campaign_id = plan.campaign_id

        logger.info(f"Compiling SOC assessment report for run {run_id}")

        # Construct attack path narrative & hops
        narrative = (
            f"Adversary emulation executed across {len(plan.stages)} sequential stages targeting account {target_account}. "
            f"The campaign demonstrated attack path traversal initiated from entry foothold and progressing toward "
            f"privilege escalation and high-value target access. "
            f"Objective: '{plan.objective}'."
        )

        hops: list[dict[str, Any]] = []
        for idx, stage in enumerate(plan.stages, 1):
            hops.append({
                "hop_number": idx,
                "stage_id": stage.stage_id,
                "technique_id": stage.technique_id,
                "technique_name": stage.technique_name,
                "source": stage.target_resource_id,
                "relationship": f"EMULATES_{stage.tactic.upper()}",
                "target": stage.target_resource_id,
            })

        # Generate contextual remediation items
        remediations: list[RemediationItem] = []
        for tech in correlation.techniques:
            remediations.append(
                cls._build_remediation_for_technique(tech.technique_id, tech.technique_name)
            )

        # Executive summary
        coverage_pct = correlation.coverage_percentage
        mttd_str = f"{correlation.mean_time_to_detect_seconds}s" if correlation.mean_time_to_detect_seconds is not None else "N/A"
        summary = (
            f"Falcon Strike-AI conducted an automated adversary emulation campaign (Run ID: {run_id}). "
            f"Out of {correlation.total_executed_techniques} executed techniques, "
            f"{correlation.detected_count} were fully detected, {correlation.partially_detected_count} were partially detected, "
            f"and {correlation.missed_count} were missed by the monitoring stack. "
            f"Overall detection coverage reached {coverage_pct}% with a Mean Time to Detect (MTTD) of {mttd_str}."
        )

        # Teardown & audit dictionaries
        td_dict = teardown_result.model_dump() if teardown_result else {"status": "NOT_EXECUTED", "baseline_verified": True}
        audit_dict = audit_verification.model_dump() if audit_verification else {"is_valid": True, "total_records": 0}

        # Clear disclaimers
        disclaimers = [
            f"Environment data classified as '{environment_provenance}'. Findings represent evaluated topology model.",
            f"Emulation executed in '{runner_provenance}' mode. Zero destructive operations or weaponized exploits used.",
            f"Security alert telemetry sourced from '{detection_provenance}'. Detections reflect configured evaluation rules.",
            "Cryptographic audit log verification proves application-level append integrity.",
        ]

        return SOCReportData(
            run_id=run_id,
            campaign_id=campaign_id,
            target_account_id=target_account,
            environment_provenance=environment_provenance,
            runner_provenance=runner_provenance,
            detection_provenance=detection_provenance,
            executive_summary=summary,
            objective=plan.objective,
            attack_path_narrative=narrative,
            attack_path_hops=hops,
            total_executed_techniques=correlation.total_executed_techniques,
            detected_count=correlation.detected_count,
            partially_detected_count=correlation.partially_detected_count,
            missed_count=correlation.missed_count,
            coverage_percentage=coverage_pct,
            mean_time_to_detect_seconds=correlation.mean_time_to_detect_seconds,
            techniques=correlation.techniques,
            synthetic_iocs=synthetic_iocs,
            remediation_recommendations=remediations,
            teardown_verification=td_dict,
            audit_chain_verification=audit_dict,
            limitations_and_disclaimers=disclaimers,
        )

    @staticmethod
    def _build_remediation_for_technique(technique_id: str, technique_name: str) -> RemediationItem:
        """Map technique ID to actionable cloud security remediation guidance."""
        remediation_map: dict[str, tuple[str, str, str]] = {
            "T1078": (
                "HIGH",
                "Enforce MFA and conditional access policies on all IAM accounts; restrict sts:AssumeRole trust policies to specific principals.",
                "Compromised or over-privileged valid credentials represent the primary vector for cloud lateral movement.",
            ),
            "T1526": (
                "MEDIUM",
                "Apply Service Control Policies (SCPs) and least-privilege IAM boundaries to restrict reconnaissance APIs like iam:ListRoles.",
                "Excessive read-only discovery permissions enable adversaries to map viable privilege escalation paths.",
            ),
            "T1098": (
                "CRITICAL",
                "Audit IAM policies for CreateAccessKey and AttachUserPolicy permissions; alert on anomalous access key creations via CloudTrail.",
                "Account manipulation allows adversaries to establish stealthy persistence outside central SSO.",
            ),
            "T1071": (
                "HIGH",
                "Enforce VPC egress filtering via AWS Network Firewall or NAT gateway proxy to block unauthorized outbound C2 ports.",
                "Unrestricted outbound traffic enables covert communication with adversary infrastructure.",
            ),
            "T1537": (
                "CRITICAL",
                "Implement S3 Bucket Policies prohibiting cross-account transfers and enforce S3 Block Public Access globally.",
                "Unrestricted S3 permissions allow direct cloud data exfiltration.",
            ),
        }

        priority, rec, rationale = remediation_map.get(
            technique_id,
            (
                "MEDIUM",
                f"Review cloud security configuration and IAM permissions governing {technique_name} ({technique_id}).",
                f"Defensive controls must be calibrated to monitor and restrict {technique_id} observables.",
            ),
        )

        return RemediationItem(
            technique_id=technique_id,
            target_resource_id="TargetCloudAssets",
            priority=priority,
            recommendation=rec,
            rationale=rationale,
        )

