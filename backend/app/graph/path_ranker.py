"""Deterministic and explainable attack path ranking engine."""

from backend.app.graph.attack_path_models import AttackPath
from backend.app.graph.models import (
    FindingCategory,
    FindingSeverity,
    GraphEdge,
    GraphNode,
    MisconfigurationFinding,
    NodeType,
)


class AttackPathRanker:
    """Calculates deterministic, defensible risk scores for discovered attack paths (FR-1.7)."""

    def rank_path(
        self,
        entry_node: GraphNode,
        target_node: GraphNode,
        ordered_nodes: list[GraphNode],
        ordered_edges: list[GraphEdge],
        findings: list[MisconfigurationFinding],
    ) -> AttackPath:
        """Score an attack path based on exposure, target criticality, path length, and findings."""
        score_breakdown: list[str] = []
        raw_score = 0.0

        # 1. Entry Point Exposure Factor (Max 30 points)
        if entry_node.type == NodeType.PUBLIC_ENDPOINT:
            raw_score += 30.0
            score_breakdown.append(
                "+30 pts: Entry point is unauthenticated Public Internet (0.0.0.0/0)."
            )
        elif entry_node.properties.get("is_public"):
            raw_score += 25.0
            score_breakdown.append("+25 pts: Entry resource is directly publicly exposed.")
        else:
            raw_score += 15.0
            score_breakdown.append(
                "+15 pts: Entry resource requires internal or authenticated access."
            )

        # 2. Target Crown Jewel Criticality (Max 35 points)
        if target_node.type == NodeType.IAM_ROLE:
            if "admin" in target_node.name.lower() or target_node.properties.get("is_admin"):
                raw_score += 35.0
                score_breakdown.append(
                    "+35 pts: Target is Cloud Administrator Role with full administrative control."
                )
            else:
                raw_score += 20.0
                score_breakdown.append("+20 pts: Target is a privileged IAM Role.")
        elif target_node.type == NodeType.S3_BUCKET:
            if "confidential" in target_node.name.lower() or target_node.properties.get(
                "is_public"
            ):
                raw_score += 30.0
                score_breakdown.append(
                    "+30 pts: Target is high-value Confidential Data Store (S3 bucket)."
                )
            else:
                raw_score += 15.0
                score_breakdown.append("+15 pts: Target is an S3 storage resource.")
        else:
            raw_score += 10.0
            score_breakdown.append("+10 pts: Target is standard cloud resource.")

        # 3. Path Hop Efficiency (Max 15 points)
        hop_count = len(ordered_edges)
        if hop_count <= 2:
            raw_score += 15.0
            score_breakdown.append(
                f"+15 pts: Highly direct path with minimal pivot friction ({hop_count} hops)."
            )
        elif hop_count <= 4:
            raw_score += 10.0
            score_breakdown.append(f"+10 pts: Moderate chain complexity ({hop_count} hops).")
        else:
            raw_score += 5.0
            score_breakdown.append(f"+5 pts: Deep multi-hop chain ({hop_count} hops).")

        # 4. Correlation with Misconfiguration Findings (Max 20 points)
        node_ids_in_path = {n.id for n in ordered_nodes}
        matching_findings = [f for f in findings if f.resource_id in node_ids_in_path]
        supporting_finding_ids = [f.finding_id for f in matching_findings]

        privesc_present = any(
            f.category == FindingCategory.PRIVILEGE_ESCALATION for f in matching_findings
        )
        wildcard_present = any(
            f.category == FindingCategory.WILDCARD_PERMISSIONS for f in matching_findings
        )
        public_storage = any(
            f.category == FindingCategory.PUBLIC_STORAGE for f in matching_findings
        )

        if privesc_present:
            raw_score += 10.0
            score_breakdown.append(
                "+10 pts: Corroborated by active Privilege Escalation finding on path."
            )
        if wildcard_present:
            raw_score += 5.0
            score_breakdown.append(
                "+5 pts: Corroborated by Wildcard Permission finding along path."
            )
        if public_storage:
            raw_score += 5.0
            score_breakdown.append("+5 pts: Corroborated by Public Storage exposure finding.")

        # Cap score between 0.0 and 100.0
        final_score = min(max(raw_score, 0.0), 100.0)

        # Determine Severity
        if final_score >= 80.0:
            severity = FindingSeverity.CRITICAL
        elif final_score >= 60.0:
            severity = FindingSeverity.HIGH
        elif final_score >= 40.0:
            severity = FindingSeverity.MEDIUM
        else:
            severity = FindingSeverity.LOW

        explanation = f"Risk Score {final_score:.1f}/100 ({severity.value}): " + " ".join(
            score_breakdown
        )

        evidence_provenance = {
            "entry_type": entry_node.type.value,
            "target_type": target_node.type.value,
            "hop_count": hop_count,
            "matched_findings_count": len(matching_findings),
        }

        return AttackPath(
            entry_point=entry_node,
            target_resource=target_node,
            ordered_nodes=ordered_nodes,
            ordered_relationships=ordered_edges,
            hop_count=hop_count,
            risk_score=final_score,
            severity=severity,
            ranking_explanation=explanation,
            supporting_findings=supporting_finding_ids,
            evidence_provenance=evidence_provenance,
        )
