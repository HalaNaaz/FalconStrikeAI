"""Unit tests for Phase 4 AWS Environment Collectors."""

from unittest.mock import MagicMock

import pytest

from backend.app.collectors.aws_iam import AWSIAMCollector
from backend.app.collectors.aws_network import AWSNetworkCollector
from backend.app.collectors.aws_s3 import AWSS3Collector
from backend.app.collectors.models import (
    CollectionSourceType,
    PolicyMetadata,
    PolicyStatement,
)
from backend.app.collectors.runner import CollectorOrchestrator
from backend.app.collectors.synthetic import SyntheticEnvironmentProvider
from backend.app.core.exceptions import AccountNotAllowlistedError


def test_synthetic_flawed_environment_collection() -> None:
    """Verify synthetic flawed collection generates rich topology with misconfigurations."""
    provider = SyntheticEnvironmentProvider()
    data = provider.generate_flawed_environment("000000000000")

    assert data.source_type == CollectionSourceType.SYNTHETIC
    assert data.account_id == "000000000000"
    assert len(data.iam_roles) == 3
    assert len(data.ec2_instances) == 1
    assert len(data.s3_buckets) == 1
    assert len(data.security_groups) == 1
    assert data.total_asset_count > 0

    # Verify public exposure flags
    ec2 = data.ec2_instances[0]
    assert ec2.is_publicly_exposed is True
    assert ec2.public_ip == "54.210.10.99"

    # Verify S3 public flags
    s3 = data.s3_buckets[0]
    assert s3.is_public is True
    assert s3.public_access_block_enabled is False


def test_synthetic_clean_environment_collection() -> None:
    """Verify clean environment contains no public exposure."""
    data = SyntheticEnvironmentProvider.generate_clean_environment("000000000000")
    assert len(data.ec2_instances) == 1
    assert data.ec2_instances[0].is_publicly_exposed is False
    assert data.s3_buckets[0].is_public is False
    assert data.s3_buckets[0].public_access_block_enabled is True


def test_collector_orchestrator_allowlist_enforcement() -> None:
    """Verify collector orchestrator rejects unapproved accounts."""
    orchestrator = CollectorOrchestrator()
    with pytest.raises(AccountNotAllowlistedError):
        orchestrator.run_collection(account_id="999999999999", force_synthetic=True)


def test_wildcard_permission_identification() -> None:
    """Verify wildcard actions and resources are accurately identified."""
    admin_stmt = PolicyStatement(effect="Allow", actions=["*"], resources=["*"])
    assert admin_stmt.has_wildcard_action is True
    assert admin_stmt.has_wildcard_resource is True

    pol = PolicyMetadata(policy_id="test-pol", policy_name="TestPol", statements=[admin_stmt])
    assert pol.has_admin_privileges is True

    scoped_stmt = PolicyStatement(
        effect="Allow", actions=["s3:GetObject"], resources=["arn:aws:s3:::mybucket/*"]
    )
    assert scoped_stmt.has_wildcard_action is False
    assert scoped_stmt.has_wildcard_resource is False


def test_iam_trust_relationship_normalization() -> None:
    """Verify IAM collector correctly normalizes trusted principals from assume role policies."""
    collector = AWSIAMCollector()
    trust_doc = {
        "Statement": [
            {
                "Effect": "Allow",
                "Principal": {"AWS": "arn:aws:iam::000000000000:role/PivotingRole"},
                "Action": "sts:AssumeRole",
            },
            {
                "Effect": "Allow",
                "Principal": {"Service": "ec2.amazonaws.com"},
                "Action": "sts:AssumeRole",
            },
        ]
    }
    principals = collector._extract_trusted_principals(trust_doc)
    assert "arn:aws:iam::000000000000:role/PivotingRole" in principals
    assert "ec2.amazonaws.com" in principals


def test_aws_collectors_graceful_missing_credentials() -> None:
    """Verify live AWS collectors handle unavailable credentials gracefully without crashing."""
    mock_session = MagicMock()
    mock_iam = MagicMock()
    mock_iam.get_paginator.side_effect = Exception("No credentials found")
    mock_session.client.return_value = mock_iam

    collector = AWSIAMCollector(session=mock_session)
    data, errors = collector.collect("000000000000")

    assert len(errors) >= 1
    assert "No credentials found" in errors[0].message
    assert all(e.service == "iam" for e in errors)


def test_aws_iam_collector_mocked_success() -> None:
    """Verify live AWS IAM collector parses users, roles, and policies with paginators."""
    mock_session = MagicMock()
    mock_iam = MagicMock()
    mock_session.client.return_value = mock_iam

    # Mock list_users paginator
    user_paginator = MagicMock()
    user_paginator.paginate.return_value = [
        {
            "Users": [
                {
                    "UserName": "test-user",
                    "UserId": "UID123",
                    "Arn": "arn:aws:iam::000000000000:user/test-user",
                }
            ]
        }
    ]
    # Mock list_roles paginator
    role_paginator = MagicMock()
    role_paginator.paginate.return_value = [
        {
            "Roles": [
                {
                    "RoleName": "test-role",
                    "RoleId": "RID123",
                    "Arn": "arn:aws:iam::000000000000:role/test-role",
                    "AssumeRolePolicyDocument": {
                        "Statement": [
                            {
                                "Effect": "Allow",
                                "Principal": {"Service": "ec2.amazonaws.com"},
                                "Action": "sts:AssumeRole",
                            }
                        ]
                    },
                }
            ]
        }
    ]

    def paginator_side_effect(operation: str) -> MagicMock:
        if operation == "list_users":
            return user_paginator
        return role_paginator

    mock_iam.get_paginator.side_effect = paginator_side_effect
    mock_iam.list_attached_user_policies.return_value = {
        "AttachedPolicies": [{"PolicyArn": "arn:aws:iam::aws:policy/ReadOnlyAccess"}]
    }
    mock_iam.list_user_policies.return_value = {"PolicyNames": ["InlinePol"]}
    mock_iam.get_user_policy.return_value = {
        "PolicyDocument": {
            "Statement": [{"Effect": "Allow", "Action": "s3:ListBucket", "Resource": "*"}]
        }
    }
    mock_iam.list_attached_role_policies.return_value = {"AttachedPolicies": []}
    mock_iam.list_role_policies.return_value = {"PolicyNames": []}

    collector = AWSIAMCollector(session=mock_session)
    data, errors = collector.collect("000000000000")

    assert len(errors) == 0
    assert len(data["users"]) == 1
    assert data["users"][0].user_name == "test-user"
    assert len(data["users"][0].inline_policies) == 1
    assert len(data["roles"]) == 1
    assert data["roles"][0].role_name == "test-role"


def test_aws_network_collector_mocked_success() -> None:
    """Verify live AWS network collector parses EC2 instances and security groups."""
    mock_session = MagicMock()
    mock_ec2 = MagicMock()
    mock_session.client.return_value = mock_ec2

    sg_paginator = MagicMock()
    sg_paginator.paginate.return_value = [
        {
            "SecurityGroups": [
                {
                    "GroupId": "sg-12345",
                    "GroupName": "web-sg",
                    "Description": "test sg",
                    "VpcId": "vpc-1",
                    "IpPermissions": [
                        {
                            "IpProtocol": "tcp",
                            "FromPort": 80,
                            "ToPort": 80,
                            "IpRanges": [{"CidrIp": "0.0.0.0/0"}],
                        }
                    ],
                    "IpPermissionsEgress": [],
                }
            ]
        }
    ]

    inst_paginator = MagicMock()
    inst_paginator.paginate.return_value = [
        {
            "Reservations": [
                {
                    "Instances": [
                        {
                            "InstanceId": "i-99999",
                            "InstanceType": "t3.micro",
                            "State": {"Name": "running"},
                            "PrivateIpAddress": "10.0.0.5",
                            "PublicIpAddress": "198.51.100.1",
                            "SecurityGroups": [{"GroupId": "sg-12345"}],
                            "IamInstanceProfile": {
                                "Arn": "arn:aws:iam::000000000000:instance-profile/WebProfile"
                            },
                        }
                    ]
                }
            ]
        }
    ]

    def paginator_side_effect(op: str) -> MagicMock:
        if op == "describe_security_groups":
            return sg_paginator
        return inst_paginator

    mock_ec2.get_paginator.side_effect = paginator_side_effect

    collector = AWSNetworkCollector(session=mock_session)
    data, errors = collector.collect("000000000000")

    assert len(errors) == 0
    assert len(data["security_groups"]) == 1
    assert data["security_groups"][0].allows_internet_ingress is True
    assert len(data["instances"]) == 1
    assert data["instances"][0].is_publicly_exposed is True
    assert data["instances"][0].instance_profile_name == "WebProfile"


def test_aws_s3_collector_mocked_success() -> None:
    """Verify live AWS S3 collector parses buckets, public access blocks, and bucket policies."""
    mock_session = MagicMock()
    mock_s3 = MagicMock()
    mock_session.client.return_value = mock_s3

    mock_s3.list_buckets.return_value = {
        "Buckets": [
            {
                "Name": "test-public-bucket",
                "CreationDate": "2026-01-01T00:00:00Z",
            }
        ]
    }
    mock_s3.get_public_access_block.return_value = {
        "PublicAccessBlockConfiguration": {
            "BlockPublicAcls": False,
            "IgnorePublicAcls": False,
            "BlockPublicPolicy": False,
            "RestrictPublicBuckets": False,
        }
    }
    mock_s3.get_bucket_policy.return_value = {
        "Policy": (
            '{"Statement": [{"Effect": "Allow", "Principal": "*", '
            '"Action": "s3:GetObject", "Resource": "arn:aws:s3:::test-public-bucket/*"}]}'
        )
    }

    collector = AWSS3Collector(session=mock_session)
    buckets, errors = collector.collect("000000000000")

    assert len(errors) == 0
    assert len(buckets) == 1
    assert buckets[0].bucket_name == "test-public-bucket"
    assert buckets[0].is_public is True
    assert buckets[0].policy_allows_public is True


def test_collectors_invoke_zero_write_operations() -> None:
    """SECURITY TEST: Verify AWS collectors invoke only read/describe/list operations."""
    mock_session = MagicMock()
    mock_ec2 = MagicMock()
    mock_session.client.return_value = mock_ec2

    collector = AWSNetworkCollector(session=mock_session)
    collector.collect("000000000000")

    # Inspect all calls made to mock_ec2
    for call in mock_ec2.method_calls:
        method_name = call[0]
        # Must only call describe_* or get_* APIs
        assert (
            method_name.startswith("describe_")
            or method_name.startswith("get_")
            or method_name == "get_paginator"
        ), f"Unsafe mutating method invoked: {method_name}"
