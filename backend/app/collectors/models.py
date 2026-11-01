"""Pydantic schemas and models for cloud asset collection and normalization."""

from datetime import UTC, datetime
from enum import StrEnum
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field


class CollectionSourceType(StrEnum):
    """Source of the collected environment data."""

    SYNTHETIC = "synthetic"
    AWS_LIVE = "aws_live"


class PolicyStatement(BaseModel):
    """Normalized representation of an IAM policy statement."""

    sid: str | None = None
    effect: str = Field(default="Allow", description="Allow or Deny")
    actions: list[str] = Field(default_factory=list, description="List of AWS action strings")
    resources: list[str] = Field(default_factory=list, description="List of AWS resource ARNs")
    conditions: dict[str, Any] = Field(default_factory=dict, description="Policy condition blocks")

    @property
    def has_wildcard_action(self) -> bool:
        """Check if statement grants wildcard actions."""
        return "*" in self.actions or any(a.endswith(":*") for a in self.actions)

    @property
    def has_wildcard_resource(self) -> bool:
        """Check if statement targets wildcard resources."""
        return "*" in self.resources


class PolicyMetadata(BaseModel):
    """Managed or inline policy metadata."""

    policy_id: str = Field(description="Policy name or unique ID")
    policy_name: str
    arn: str | None = None
    is_inline: bool = False
    statements: list[PolicyStatement] = Field(default_factory=list)
    raw_document: dict[str, Any] = Field(default_factory=dict)

    @property
    def has_admin_privileges(self) -> bool:
        """Detect full admin privileges (* on *)."""
        for stmt in self.statements:
            if stmt.effect.lower() == "allow" and "*" in stmt.actions and "*" in stmt.resources:
                return True
        return False


class IAMUserMetadata(BaseModel):
    """IAM User metadata."""

    user_id: str
    user_name: str
    arn: str
    attached_policies: list[str] = Field(default_factory=list, description="List of policy ARNs")
    inline_policies: list[PolicyMetadata] = Field(default_factory=list)
    groups: list[str] = Field(default_factory=list)


class IAMRoleMetadata(BaseModel):
    """IAM Role metadata including trust relationships."""

    role_id: str
    role_name: str
    arn: str
    assume_role_trust_policy: dict[str, Any] = Field(
        default_factory=dict, description="AssumeRole trust policy document"
    )
    trusted_principals: list[str] = Field(
        default_factory=list,
        description="Principals permitted to assume this role (e.g. ec2.amazonaws.com, ARNs)",
    )
    attached_policies: list[str] = Field(default_factory=list, description="List of policy ARNs")
    inline_policies: list[PolicyMetadata] = Field(default_factory=list)
    is_instance_profile_role: bool = False


class SecurityGroupRule(BaseModel):
    """Security group rule description."""

    ip_protocol: str = Field(description="tcp, udp, icmp, or -1 for all")
    from_port: int | None = None
    to_port: int | None = None
    cidr_ipv4: list[str] = Field(default_factory=list)
    cidr_ipv6: list[str] = Field(default_factory=list)

    @property
    def is_internet_open(self) -> bool:
        """Check if rule allows unrestricted ingress from anywhere."""
        return "0.0.0.0/0" in self.cidr_ipv4 or "::/0" in self.cidr_ipv6


class SecurityGroupMetadata(BaseModel):
    """Security group metadata."""

    group_id: str
    group_name: str
    description: str = ""
    vpc_id: str | None = None
    inbound_rules: list[SecurityGroupRule] = Field(default_factory=list)
    outbound_rules: list[SecurityGroupRule] = Field(default_factory=list)

    @property
    def allows_internet_ingress(self) -> bool:
        """Return True if any inbound rule permits 0.0.0.0/0."""
        return any(rule.is_internet_open for rule in self.inbound_rules)


class EC2InstanceMetadata(BaseModel):
    """EC2 instance metadata with compute-to-identity bindings."""

    instance_id: str
    instance_type: str = "t3.micro"
    state: str = "running"
    private_ip: str | None = None
    public_ip: str | None = None
    public_dns: str | None = None
    vpc_id: str | None = None
    subnet_id: str | None = None
    security_group_ids: list[str] = Field(default_factory=list)
    instance_profile_arn: str | None = None
    instance_profile_name: str | None = None
    associated_iam_role: str | None = None

    @property
    def is_publicly_exposed(self) -> bool:
        """Check if the instance has a public IP or DNS."""
        return bool(self.public_ip or self.public_dns)


class S3BucketMetadata(BaseModel):
    """S3 Bucket metadata and exposure flags."""

    bucket_name: str
    arn: str
    creation_date: str | None = None
    public_access_block_enabled: bool = True
    is_public: bool = False
    policy_allows_public: bool = False
    acl_allows_public: bool = False
    bucket_policy: dict[str, Any] = Field(default_factory=dict)


class CollectionError(BaseModel):
    """Structured record of an error during collector execution."""

    service: str
    operation: str
    error_type: str
    message: str
    timestamp: str = Field(default_factory=lambda: datetime.now(UTC).isoformat())


class NormalizedEnvironmentData(BaseModel):
    """Unified container for all collected cloud assets."""

    collection_id: str = Field(default_factory=lambda: str(uuid4()))
    account_id: str
    source_type: CollectionSourceType
    collected_at: str = Field(default_factory=lambda: datetime.now(UTC).isoformat())
    duration_ms: float = 0.0
    iam_users: list[IAMUserMetadata] = Field(default_factory=list)
    iam_roles: list[IAMRoleMetadata] = Field(default_factory=list)
    policies: list[PolicyMetadata] = Field(default_factory=list)
    ec2_instances: list[EC2InstanceMetadata] = Field(default_factory=list)
    security_groups: list[SecurityGroupMetadata] = Field(default_factory=list)
    s3_buckets: list[S3BucketMetadata] = Field(default_factory=list)
    errors: list[CollectionError] = Field(default_factory=list)

    @property
    def total_asset_count(self) -> int:
        """Count total individual assets collected."""
        return (
            len(self.iam_users)
            + len(self.iam_roles)
            + len(self.policies)
            + len(self.ec2_instances)
            + len(self.security_groups)
            + len(self.s3_buckets)
        )
