"""Read-only AWS EC2 and Network Collector for live environments."""

from typing import Any

from botocore.exceptions import BotoCoreError, ClientError

from backend.app.collectors.base import BaseCollector
from backend.app.collectors.models import (
    CollectionError,
    CollectionSourceType,
    EC2InstanceMetadata,
    SecurityGroupMetadata,
    SecurityGroupRule,
)


class AWSNetworkCollector(BaseCollector):
    """Read-only collector for EC2 instances, security groups, and public exposure (FR-1.2, FR-1.3)."""

    def __init__(self, session: Any = None) -> None:
        super().__init__(source_type=CollectionSourceType.AWS_LIVE)
        self.session = session
        self._ec2_client: Any = None

    @property
    def service_name(self) -> str:
        return "ec2"

    def _get_client(self) -> Any:
        if self._ec2_client is None:
            if self.session is not None:
                self._ec2_client = self.session.client("ec2")
            else:
                import boto3

                self._ec2_client = boto3.client("ec2")
        return self._ec2_client

    def _parse_ip_permissions(self, raw_perms: list[dict[str, Any]]) -> list[SecurityGroupRule]:
        """Convert EC2 IP permission dictionaries to normalized SecurityGroupRule models."""
        rules: list[SecurityGroupRule] = []
        for p in raw_perms:
            proto = p.get("IpProtocol", "-1")
            from_port = p.get("FromPort")
            to_port = p.get("ToPort")
            cidr_ipv4 = [r.get("CidrIp", "") for r in p.get("IpRanges", []) if r.get("CidrIp")]
            cidr_ipv6 = [
                r.get("CidrIpv6", "") for r in p.get("Ipv6Ranges", []) if r.get("CidrIpv6")
            ]

            rules.append(
                SecurityGroupRule(
                    ip_protocol=proto,
                    from_port=from_port,
                    to_port=to_port,
                    cidr_ipv4=cidr_ipv4,
                    cidr_ipv6=cidr_ipv6,
                )
            )
        return rules

    def collect(self, account_id: str) -> tuple[dict[str, list[Any]], list[CollectionError]]:
        """Collect EC2 instances and Security Groups using read-only Describe APIs."""
        self.validate_scope(account_id)
        instances: list[EC2InstanceMetadata] = []
        security_groups: list[SecurityGroupMetadata] = []
        errors: list[CollectionError] = []

        try:
            client = self._get_client()
        except Exception as exc:
            errors.append(
                CollectionError(
                    service="ec2",
                    operation="get_client",
                    error_type=type(exc).__name__,
                    message=f"Failed to initialize EC2 client: {exc}",
                )
            )
            return {"instances": instances, "security_groups": security_groups}, errors

        # 1. Collect Security Groups
        try:
            paginator = client.get_paginator("describe_security_groups")
            for page in paginator.paginate():
                for sg in page.get("SecurityGroups", []):
                    sg_id = sg["GroupId"]
                    sg_name = sg.get("GroupName", sg_id)
                    desc = sg.get("Description", "")
                    vpc_id = sg.get("VpcId")
                    inbound = self._parse_ip_permissions(sg.get("IpPermissions", []))
                    outbound = self._parse_ip_permissions(sg.get("IpPermissionsEgress", []))

                    security_groups.append(
                        SecurityGroupMetadata(
                            group_id=sg_id,
                            group_name=sg_name,
                            description=desc,
                            vpc_id=vpc_id,
                            inbound_rules=inbound,
                            outbound_rules=outbound,
                        )
                    )
        except (ClientError, BotoCoreError) as exc:
            errors.append(
                CollectionError(
                    service="ec2",
                    operation="describe_security_groups",
                    error_type=type(exc).__name__,
                    message=str(exc),
                )
            )

        # 2. Collect EC2 Instances
        try:
            paginator = client.get_paginator("describe_instances")
            for page in paginator.paginate():
                for res in page.get("Reservations", []):
                    for inst in res.get("Instances", []):
                        i_id = inst["InstanceId"]
                        i_type = inst.get("InstanceType", "unknown")
                        state = inst.get("State", {}).get("Name", "unknown")
                        priv_ip = inst.get("PrivateIpAddress")
                        pub_ip = inst.get("PublicIpAddress")
                        pub_dns = inst.get("PublicDnsName")
                        vpc_id = inst.get("VpcId")
                        subnet_id = inst.get("SubnetId")
                        sg_ids = [
                            g["GroupId"] for g in inst.get("SecurityGroups", []) if "GroupId" in g
                        ]

                        # Compute-to-identity binding (instance profile)
                        profile_block = inst.get("IamInstanceProfile", {})
                        profile_arn = profile_block.get("Arn")
                        profile_name = profile_arn.split("/")[-1] if profile_arn else None

                        instances.append(
                            EC2InstanceMetadata(
                                instance_id=i_id,
                                instance_type=i_type,
                                state=state,
                                private_ip=priv_ip,
                                public_ip=pub_ip,
                                public_dns=pub_dns,
                                vpc_id=vpc_id,
                                subnet_id=subnet_id,
                                security_group_ids=sg_ids,
                                instance_profile_arn=profile_arn,
                                instance_profile_name=profile_name,
                            )
                        )
        except (ClientError, BotoCoreError) as exc:
            errors.append(
                CollectionError(
                    service="ec2",
                    operation="describe_instances",
                    error_type=type(exc).__name__,
                    message=str(exc),
                )
            )

        return {"instances": instances, "security_groups": security_groups}, errors
