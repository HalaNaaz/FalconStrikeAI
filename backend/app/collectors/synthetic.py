"""Synthetic AWS environment generator for offline development and testing."""

from backend.app.collectors.models import (
    CollectionSourceType,
    EC2InstanceMetadata,
    IAMRoleMetadata,
    IAMUserMetadata,
    NormalizedEnvironmentData,
    PolicyMetadata,
    PolicyStatement,
    S3BucketMetadata,
    SecurityGroupMetadata,
    SecurityGroupRule,
)


class SyntheticEnvironmentProvider:
    """Generates realistic, deterministic AWS cloud topology fixtures."""

    @staticmethod
    def generate_flawed_environment(account_id: str = "000000000000") -> NormalizedEnvironmentData:
        """Generate an intentionally flawed AWS lab topology containing attack paths to crown jewels.

        Topology features:
        1. Internet-exposed web server (EC2) with Security Group allowing 0.0.0.0/0 on port 80/443/22.
        2. EC2 instance is bound via Instance Profile to 'WebServerInstanceRole'.
        3. 'WebServerInstanceRole' can assume 'InternalDevRole'.
        4. 'InternalDevRole' has wildcard privilege escalation capability to assume 'CloudAdminRole'.
        5. 'CloudAdminRole' has full AdministratorAccess (* on *).
        6. A public S3 bucket 'falcon-lab-confidential-data' with public read access.
        """
        # Policies
        admin_policy = PolicyMetadata(
            policy_id="pol-admin-01",
            policy_name="AdministratorAccess",
            arn=f"arn:aws:iam::{account_id}:policy/AdministratorAccess",
            statements=[
                PolicyStatement(
                    sid="FullAdmin",
                    effect="Allow",
                    actions=["*"],
                    resources=["*"],
                )
            ],
        )

        assume_dev_policy = PolicyMetadata(
            policy_id="pol-assume-dev-01",
            policy_name="AssumeInternalDevPolicy",
            arn=f"arn:aws:iam::{account_id}:policy/AssumeInternalDevPolicy",
            statements=[
                PolicyStatement(
                    sid="AllowAssumeDev",
                    effect="Allow",
                    actions=["sts:AssumeRole"],
                    resources=[f"arn:aws:iam::{account_id}:role/InternalDevRole"],
                )
            ],
        )

        assume_admin_policy = PolicyMetadata(
            policy_id="pol-assume-admin-01",
            policy_name="AssumeAdminPolicy",
            arn=f"arn:aws:iam::{account_id}:policy/AssumeAdminPolicy",
            statements=[
                PolicyStatement(
                    sid="AllowAssumeAdmin",
                    effect="Allow",
                    actions=["sts:AssumeRole"],
                    resources=[f"arn:aws:iam::{account_id}:role/CloudAdminRole"],
                )
            ],
        )

        s3_read_policy = PolicyMetadata(
            policy_id="pol-s3-read-01",
            policy_name="ReadOnlyS3Policy",
            arn=f"arn:aws:iam::{account_id}:policy/ReadOnlyS3Policy",
            statements=[
                PolicyStatement(
                    sid="AllowS3Read",
                    effect="Allow",
                    actions=["s3:GetObject", "s3:ListBucket"],
                    resources=[
                        "arn:aws:s3:::falcon-lab-confidential-data",
                        "arn:aws:s3:::falcon-lab-confidential-data/*",
                    ],
                )
            ],
        )

        # IAM Roles
        web_instance_role = IAMRoleMetadata(
            role_id="role-web-instance-01",
            role_name="WebServerInstanceRole",
            arn=f"arn:aws:iam::{account_id}:role/WebServerInstanceRole",
            assume_role_trust_policy={
                "Statement": [
                    {
                        "Effect": "Allow",
                        "Principal": {"Service": "ec2.amazonaws.com"},
                        "Action": "sts:AssumeRole",
                    }
                ]
            },
            trusted_principals=["ec2.amazonaws.com"],
            attached_policies=[assume_dev_policy.arn],
            is_instance_profile_role=True,
        )

        internal_dev_role = IAMRoleMetadata(
            role_id="role-internal-dev-01",
            role_name="InternalDevRole",
            arn=f"arn:aws:iam::{account_id}:role/InternalDevRole",
            assume_role_trust_policy={
                "Statement": [
                    {
                        "Effect": "Allow",
                        "Principal": {"AWS": web_instance_role.arn},
                        "Action": "sts:AssumeRole",
                    }
                ]
            },
            trusted_principals=[web_instance_role.arn],
            attached_policies=[assume_admin_policy.arn, s3_read_policy.arn],
        )

        cloud_admin_role = IAMRoleMetadata(
            role_id="role-cloud-admin-01",
            role_name="CloudAdminRole",
            arn=f"arn:aws:iam::{account_id}:role/CloudAdminRole",
            assume_role_trust_policy={
                "Statement": [
                    {
                        "Effect": "Allow",
                        "Principal": {"AWS": internal_dev_role.arn},
                        "Action": "sts:AssumeRole",
                    }
                ]
            },
            trusted_principals=[internal_dev_role.arn],
            attached_policies=[admin_policy.arn],
        )

        # IAM Users
        developer_user = IAMUserMetadata(
            user_id="user-dev-alice",
            user_name="alice-developer",
            arn=f"arn:aws:iam::{account_id}:user/alice-developer",
            attached_policies=[assume_dev_policy.arn],
        )

        # Security Groups
        public_web_sg = SecurityGroupMetadata(
            group_id="sg-web-public-01",
            group_name="PublicWebServerSG",
            description="Allows inbound HTTP and SSH from public internet",
            vpc_id="vpc-lab-main",
            inbound_rules=[
                SecurityGroupRule(
                    ip_protocol="tcp",
                    from_port=80,
                    to_port=80,
                    cidr_ipv4=["0.0.0.0/0"],
                ),
                SecurityGroupRule(
                    ip_protocol="tcp",
                    from_port=443,
                    to_port=443,
                    cidr_ipv4=["0.0.0.0/0"],
                ),
                SecurityGroupRule(
                    ip_protocol="tcp",
                    from_port=22,
                    to_port=22,
                    cidr_ipv4=["0.0.0.0/0"],
                ),
            ],
            outbound_rules=[
                SecurityGroupRule(
                    ip_protocol="-1",
                    cidr_ipv4=["0.0.0.0/0"],
                )
            ],
        )

        # EC2 Instances
        web_server_instance = EC2InstanceMetadata(
            instance_id="i-web-prod-01",
            instance_type="t3.large",
            state="running",
            private_ip="10.0.1.15",
            public_ip="54.210.10.99",
            public_dns="ec2-54-210-10-99.compute-1.amazonaws.com",
            vpc_id="vpc-lab-main",
            subnet_id="subnet-public-1a",
            security_group_ids=[public_web_sg.group_id],
            instance_profile_arn=f"arn:aws:iam::{account_id}:instance-profile/WebServerInstanceProfile",
            instance_profile_name="WebServerInstanceProfile",
            associated_iam_role=web_instance_role.role_name,
        )

        # S3 Buckets
        public_confidential_bucket = S3BucketMetadata(
            bucket_name="falcon-lab-confidential-data",
            arn="arn:aws:s3:::falcon-lab-confidential-data",
            creation_date="2026-01-15T00:00:00Z",
            public_access_block_enabled=False,
            is_public=True,
            policy_allows_public=True,
            bucket_policy={
                "Statement": [
                    {
                        "Sid": "PublicReadAccess",
                        "Effect": "Allow",
                        "Principal": "*",
                        "Action": "s3:GetObject",
                        "Resource": "arn:aws:s3:::falcon-lab-confidential-data/*",
                    }
                ]
            },
        )

        return NormalizedEnvironmentData(
            account_id=account_id,
            source_type=CollectionSourceType.SYNTHETIC,
            iam_users=[developer_user],
            iam_roles=[web_instance_role, internal_dev_role, cloud_admin_role],
            policies=[admin_policy, assume_dev_policy, assume_admin_policy, s3_read_policy],
            ec2_instances=[web_server_instance],
            security_groups=[public_web_sg],
            s3_buckets=[public_confidential_bucket],
            errors=[],
        )

    @staticmethod
    def generate_clean_environment(account_id: str = "000000000000") -> NormalizedEnvironmentData:
        """Generate a well-architected AWS lab topology following least privilege."""
        least_priv_policy = PolicyMetadata(
            policy_id="pol-app-least-priv",
            policy_name="AppLeastPrivilege",
            arn=f"arn:aws:iam::{account_id}:policy/AppLeastPrivilege",
            statements=[
                PolicyStatement(
                    sid="ScopedAccess",
                    effect="Allow",
                    actions=["s3:GetObject"],
                    resources=["arn:aws:s3:::falcon-secure-app-data/*"],
                )
            ],
        )

        app_role = IAMRoleMetadata(
            role_id="role-app-secure",
            role_name="SecureAppRole",
            arn=f"arn:aws:iam::{account_id}:role/SecureAppRole",
            trusted_principals=["ec2.amazonaws.com"],
            attached_policies=[least_priv_policy.arn],
            is_instance_profile_role=True,
        )

        private_sg = SecurityGroupMetadata(
            group_id="sg-internal-only",
            group_name="InternalAppSG",
            description="Internal VPC ingress only",
            vpc_id="vpc-lab-main",
            inbound_rules=[
                SecurityGroupRule(
                    ip_protocol="tcp",
                    from_port=443,
                    to_port=443,
                    cidr_ipv4=["10.0.0.0/16"],
                )
            ],
        )

        internal_instance = EC2InstanceMetadata(
            instance_id="i-internal-app-01",
            instance_type="t3.micro",
            state="running",
            private_ip="10.0.2.20",
            public_ip=None,
            public_dns=None,
            vpc_id="vpc-lab-main",
            security_group_ids=[private_sg.group_id],
            associated_iam_role=app_role.role_name,
        )

        secure_bucket = S3BucketMetadata(
            bucket_name="falcon-secure-app-data",
            arn="arn:aws:s3:::falcon-secure-app-data",
            public_access_block_enabled=True,
            is_public=False,
            policy_allows_public=False,
        )

        return NormalizedEnvironmentData(
            account_id=account_id,
            source_type=CollectionSourceType.SYNTHETIC,
            iam_users=[],
            iam_roles=[app_role],
            policies=[least_priv_policy],
            ec2_instances=[internal_instance],
            security_groups=[private_sg],
            s3_buckets=[secure_bucket],
            errors=[],
        )
