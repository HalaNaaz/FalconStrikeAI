"""Misconfiguration analyzer and exposure detector for property graph assets."""

from backend.app.collectors.models import NormalizedEnvironmentData
from backend.app.graph.models import (
    FindingCategory,
    FindingSeverity,
    MisconfigurationFinding,
    NodeType,
    RelationshipType,
)
from backend.app.graph.store import GraphStore


class MisconfigurationAnalyzer:
    """Detects security posture risks, wildcard permissions, and exposure paths in the graph."""

    def __init__(self, store: GraphStore) -> None:
        self.store = store

    def analyze(
        self, raw_env_data: NormalizedEnvironmentData | None = None
    ) -> list[MisconfigurationFinding]:
        """Run all misconfiguration detection rules against graph and environment state."""
        findings: list[MisconfigurationFinding] = []

        # 1. Analyze Wildcard IAM Policies & Excessive Privileges
        policy_nodes = self.store.get_nodes_by_type(NodeType.POLICY)
        for p_node in policy_nodes:
            if p_node.properties.get("is_admin"):
                findings.append(
                    MisconfigurationFinding(
                        resource_id=p_node.id,
                        category=FindingCategory.WILDCARD_PERMISSIONS,
                        severity=FindingSeverity.CRITICAL,
                        explanation=f"Policy '{p_node.name}' grants full administrative access with wildcard Action:* on Resource:*.",
                        evidence={"policy_name": p_node.name, "is_admin": True},
                        remediation="Apply least-privilege scoping to restrict actions and resource ARNs.",
                    )
                )

        # 2. Analyze Public EC2 Instances & Ingress Exposure
        ec2_nodes = self.store.get_nodes_by_type(NodeType.EC2_INSTANCE)
        for inst_node in ec2_nodes:
            # Check for EXPOSED_TO_INTERNET incoming edge
            in_edges = self.store.get_in_edges(inst_node.id)
            if any(e.type == RelationshipType.EXPOSED_TO_INTERNET for e in in_edges):
                pub_ip = inst_node.properties.get("public_ip")
                findings.append(
                    MisconfigurationFinding(
                        resource_id=inst_node.id,
                        category=FindingCategory.PUBLIC_EXPOSURE,
                        severity=FindingSeverity.HIGH,
                        explanation=f"Compute instance '{inst_node.name}' is directly exposed to the public internet.",
                        evidence={"public_ip": pub_ip, "instance_id": inst_node.id},
                        remediation="Place compute workloads inside private subnets behind an Application Load Balancer or NAT Gateway.",
                    )
                )

        # 3. Analyze Public S3 Buckets
        s3_nodes = self.store.get_nodes_by_type(NodeType.S3_BUCKET)
        for s3_node in s3_nodes:
            if s3_node.properties.get("is_public"):
                findings.append(
                    MisconfigurationFinding(
                        resource_id=s3_node.id,
                        category=FindingCategory.PUBLIC_STORAGE,
                        severity=FindingSeverity.HIGH,
                        explanation=f"S3 Storage Bucket '{s3_node.name}' allows unauthenticated public access.",
                        evidence={
                            "bucket_name": s3_node.name,
                            "public_access_block_enabled": s3_node.properties.get(
                                "public_access_block_enabled"
                            ),
                        },
                        remediation="Enable S3 Block Public Access at the bucket and account level.",
                    )
                )

        # 4. Analyze Risky Trust Relationships & Privilege Escalation Paths
        role_nodes = self.store.get_nodes_by_type(NodeType.IAM_ROLE)
        for role_node in role_nodes:
            trusted = role_node.properties.get("trusted_principals", [])
            for princ in trusted:
                # Wildcard principal
                if princ == "*":
                    findings.append(
                        MisconfigurationFinding(
                            resource_id=role_node.id,
                            category=FindingCategory.RISKY_TRUST_RELATIONSHIP,
                            severity=FindingSeverity.CRITICAL,
                            explanation=f"IAM Role '{role_node.name}' trusts wildcard principal (*). Any AWS entity can assume this role.",
                            evidence={"role_name": role_node.name, "principal": "*"},
                            remediation="Scope trust policy Principal to explicit, audited accounts or services.",
                        )
                    )

            # Check if role can assume higher privilege role (role chaining privesc)
            out_edges = self.store.get_out_edges(role_node.id)
            for edge in out_edges:
                if edge.type == RelationshipType.ASSUMES_ROLE:
                    target_role = self.store.get_node(edge.target_id)
                    if target_role:
                        # Check if target role has admin policy attached
                        target_out = self.store.get_out_edges(target_role.id)
                        has_admin_policy = any(
                            self.store.get_node(e.target_id)
                            and self.store.get_node(e.target_id).properties.get("is_admin")
                            for e in target_out
                            if e.type == RelationshipType.HAS_POLICY
                        )
                        if has_admin_policy:
                            findings.append(
                                MisconfigurationFinding(
                                    resource_id=role_node.id,
                                    category=FindingCategory.PRIVILEGE_ESCALATION,
                                    severity=FindingSeverity.CRITICAL,
                                    explanation=(
                                        f"IAM Role '{role_node.name}' can assume role '{target_role.name}', "
                                        "which possesses full Administrator privileges (Privilege Escalation path)."
                                    ),
                                    evidence={
                                        "source_role": role_node.id,
                                        "target_role": target_role.id,
                                        "mechanism": "sts:AssumeRole",
                                    },
                                    remediation="Remove sts:AssumeRole permission or enforce session policies and MFA.",
                                )
                            )

        return findings
