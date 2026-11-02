"""Read-only AWS IAM Collector for live environments."""

import json
from typing import Any

from backend.app.collectors.base import BaseCollector
from backend.app.collectors.models import (
    CollectionError,
    CollectionSourceType,
    IAMRoleMetadata,
    IAMUserMetadata,
    PolicyMetadata,
    PolicyStatement,
)


class AWSIAMCollector(BaseCollector):
    """Read-only collector for AWS IAM users, roles, policies, and trust relationships (FR-1.1)."""

    def __init__(self, session: Any = None) -> None:
        super().__init__(source_type=CollectionSourceType.AWS_LIVE)
        self.session = session
        self._client: Any = None

    @property
    def service_name(self) -> str:
        return "iam"

    def _get_client(self) -> Any:
        if self._client is None:
            if self.session is not None:
                self._client = self.session.client("iam")
            else:
                import boto3

                self._client = boto3.client("iam")
        return self._client

    def _parse_policy_document(self, doc: dict[str, Any] | str) -> list[PolicyStatement]:
        """Normalize IAM policy document statements into PolicyStatement models."""
        statements: list[PolicyStatement] = []
        if isinstance(doc, str):
            try:
                doc = json.loads(doc)
            except json.JSONDecodeError:
                return statements

        raw_stmts = doc.get("Statement", [])
        if isinstance(raw_stmts, dict):
            raw_stmts = [raw_stmts]

        for stmt in raw_stmts:
            actions = stmt.get("Action", [])
            if isinstance(actions, str):
                actions = [actions]

            resources = stmt.get("Resource", [])
            if isinstance(resources, str):
                resources = [resources]

            statements.append(
                PolicyStatement(
                    sid=stmt.get("Sid"),
                    effect=stmt.get("Effect", "Allow"),
                    actions=actions,
                    resources=resources,
                    conditions=stmt.get("Condition", {}),
                )
            )
        return statements

    def _extract_trusted_principals(self, trust_doc: dict[str, Any] | str) -> list[str]:
        """Extract trusted AWS principals and service principals from an assume role policy."""
        principals: list[str] = []
        if isinstance(trust_doc, str):
            try:
                trust_doc = json.loads(trust_doc)
            except json.JSONDecodeError:
                return principals

        raw_stmts = trust_doc.get("Statement", [])
        if isinstance(raw_stmts, dict):
            raw_stmts = [raw_stmts]

        for stmt in raw_stmts:
            if stmt.get("Effect", "").lower() != "allow":
                continue
            principal_block = stmt.get("Principal", {})
            if isinstance(principal_block, str):
                principals.append(principal_block)
            elif isinstance(principal_block, dict):
                for _p_type, p_val in principal_block.items():
                    if isinstance(p_val, list):
                        principals.extend(p_val)
                    elif isinstance(p_val, str):
                        principals.append(p_val)
        return principals

    def collect(self, account_id: str) -> tuple[dict[str, list[Any]], list[CollectionError]]:
        """Collect IAM users, roles, and policies using official read-only APIs."""
        self.validate_scope(account_id)
        users: list[IAMUserMetadata] = []
        roles: list[IAMRoleMetadata] = []
        policies: list[PolicyMetadata] = []
        errors: list[CollectionError] = []

        try:
            client = self._get_client()
        except Exception as exc:
            errors.append(
                CollectionError(
                    service="iam",
                    operation="get_client",
                    error_type=type(exc).__name__,
                    message=f"Failed to initialize IAM client: {exc}",
                )
            )
            return {"users": users, "roles": roles, "policies": policies}, errors

        # 1. Collect Users
        try:
            paginator = client.get_paginator("list_users")
            for page in paginator.paginate():
                for user_raw in page.get("Users", []):
                    u_name = user_raw["UserName"]
                    u_arn = user_raw["Arn"]
                    u_id = user_raw["UserId"]

                    # Attached policies
                    attached = []
                    try:
                        att_res = client.list_attached_user_policies(UserName=u_name)
                        attached = [p["PolicyArn"] for p in att_res.get("AttachedPolicies", [])]
                    except Exception as e:
                        errors.append(
                            CollectionError(
                                service="iam",
                                operation="list_attached_user_policies",
                                error_type=type(e).__name__,
                                message=str(e),
                            )
                        )

                    # Inline policies
                    inline_policies = []
                    try:
                        inl_res = client.list_user_policies(UserName=u_name)
                        for pol_name in inl_res.get("PolicyNames", []):
                            pol_doc_res = client.get_user_policy(
                                UserName=u_name, PolicyName=pol_name
                            )
                            doc = pol_doc_res.get("PolicyDocument", {})
                            inline_policies.append(
                                PolicyMetadata(
                                    policy_id=f"{u_name}-{pol_name}",
                                    policy_name=pol_name,
                                    is_inline=True,
                                    statements=self._parse_policy_document(doc),
                                    raw_document=doc,
                                )
                            )
                    except Exception as e:
                        errors.append(
                            CollectionError(
                                service="iam",
                                operation="list_user_policies",
                                error_type=type(e).__name__,
                                message=str(e),
                            )
                        )

                    users.append(
                        IAMUserMetadata(
                            user_id=u_id,
                            user_name=u_name,
                            arn=u_arn,
                            attached_policies=attached,
                            inline_policies=inline_policies,
                        )
                    )
        except Exception as exc:
            errors.append(
                CollectionError(
                    service="iam",
                    operation="list_users",
                    error_type=type(exc).__name__,
                    message=str(exc),
                )
            )

        # 2. Collect Roles
        try:
            paginator = client.get_paginator("list_roles")
            for page in paginator.paginate():
                for role_raw in page.get("Roles", []):
                    r_name = role_raw["RoleName"]
                    r_arn = role_raw["Arn"]
                    r_id = role_raw["RoleId"]
                    trust_doc = role_raw.get("AssumeRolePolicyDocument", {})
                    trusted = self._extract_trusted_principals(trust_doc)

                    # Attached policies
                    attached = []
                    try:
                        att_res = client.list_attached_role_policies(RoleName=r_name)
                        attached = [p["PolicyArn"] for p in att_res.get("AttachedPolicies", [])]
                    except Exception as e:
                        errors.append(
                            CollectionError(
                                service="iam",
                                operation="list_attached_role_policies",
                                error_type=type(e).__name__,
                                message=str(e),
                            )
                        )

                    # Inline policies
                    inline_policies = []
                    try:
                        inl_res = client.list_role_policies(RoleName=r_name)
                        for pol_name in inl_res.get("PolicyNames", []):
                            pol_doc_res = client.get_role_policy(
                                RoleName=r_name, PolicyName=pol_name
                            )
                            doc = pol_doc_res.get("PolicyDocument", {})
                            inline_policies.append(
                                PolicyMetadata(
                                    policy_id=f"{r_name}-{pol_name}",
                                    policy_name=pol_name,
                                    is_inline=True,
                                    statements=self._parse_policy_document(doc),
                                    raw_document=doc,
                                )
                            )
                    except Exception as e:
                        errors.append(
                            CollectionError(
                                service="iam",
                                operation="list_role_policies",
                                error_type=type(e).__name__,
                                message=str(e),
                            )
                        )

                    roles.append(
                        IAMRoleMetadata(
                            role_id=r_id,
                            role_name=r_name,
                            arn=r_arn,
                            assume_role_trust_policy=trust_doc
                            if isinstance(trust_doc, dict)
                            else {},
                            trusted_principals=trusted,
                            attached_policies=attached,
                            inline_policies=inline_policies,
                            is_instance_profile_role="ec2.amazonaws.com" in trusted,
                        )
                    )
        except Exception as exc:
            errors.append(
                CollectionError(
                    service="iam",
                    operation="list_roles",
                    error_type=type(exc).__name__,
                    message=str(exc),
                )
            )

        return {"users": users, "roles": roles, "policies": policies}, errors
