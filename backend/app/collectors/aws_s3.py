"""Read-only AWS S3 Collector for live environments."""

import json
from typing import Any

from botocore.exceptions import BotoCoreError, ClientError

from backend.app.collectors.base import BaseCollector
from backend.app.collectors.models import (
    CollectionError,
    CollectionSourceType,
    S3BucketMetadata,
)


class AWSS3Collector(BaseCollector):
    """Read-only collector for S3 buckets, policies, and public exposure (FR-1.2)."""

    def __init__(self, session: Any = None) -> None:
        super().__init__(source_type=CollectionSourceType.AWS_LIVE)
        self.session = session
        self._s3_client: Any = None

    @property
    def service_name(self) -> str:
        return "s3"

    def _get_client(self) -> Any:
        if self._s3_client is None:
            if self.session is not None:
                self._s3_client = self.session.client("s3")
            else:
                import boto3

                self._s3_client = boto3.client("s3")
        return self._s3_client

    def _inspect_policy_for_public(self, policy_doc: dict[str, Any] | str) -> bool:
        """Inspect bucket policy to determine if any Allow statement targets Principal *."""
        if isinstance(policy_doc, str):
            try:
                policy_doc = json.loads(policy_doc)
            except json.JSONDecodeError:
                return False

        stmts = policy_doc.get("Statement", [])
        if isinstance(stmts, dict):
            stmts = [stmts]

        for s in stmts:
            if s.get("Effect", "").lower() == "allow":
                p = s.get("Principal", "")
                if p == "*" or (isinstance(p, dict) and p.get("AWS") == "*"):
                    return True
        return False

    def collect(self, account_id: str) -> tuple[list[S3BucketMetadata], list[CollectionError]]:
        """Collect S3 buckets, public access blocks, and bucket policies using read-only APIs."""
        self.validate_scope(account_id)
        buckets: list[S3BucketMetadata] = []
        errors: list[CollectionError] = []

        try:
            client = self._get_client()
        except Exception as exc:
            errors.append(
                CollectionError(
                    service="s3",
                    operation="get_client",
                    error_type=type(exc).__name__,
                    message=f"Failed to initialize S3 client: {exc}",
                )
            )
            return buckets, errors

        try:
            resp = client.list_buckets()
            raw_buckets = resp.get("Buckets", [])
        except (ClientError, BotoCoreError) as exc:
            errors.append(
                CollectionError(
                    service="s3",
                    operation="list_buckets",
                    error_type=type(exc).__name__,
                    message=str(exc),
                )
            )
            return buckets, errors

        for b in raw_buckets:
            b_name = b["Name"]
            arn = f"arn:aws:s3:::{b_name}"
            creation_date = (
                b["CreationDate"].isoformat()
                if hasattr(b.get("CreationDate"), "isoformat")
                else None
            )

            # Public Access Block
            pab_enabled = True
            try:
                pab_res = client.get_public_access_block(Bucket=b_name)
                conf = pab_res.get("PublicAccessBlockConfiguration", {})
                pab_enabled = all(
                    [
                        conf.get("BlockPublicAcls", False),
                        conf.get("IgnorePublicAcls", False),
                        conf.get("BlockPublicPolicy", False),
                        conf.get("RestrictPublicBuckets", False),
                    ]
                )
            except ClientError as e:
                code = e.response.get("Error", {}).get("Code", "")
                if code == "NoSuchPublicAccessBlockConfiguration":
                    pab_enabled = False
                elif code != "AccessDenied":
                    errors.append(
                        CollectionError(
                            service="s3",
                            operation=f"get_public_access_block:{b_name}",
                            error_type=code,
                            message=str(e),
                        )
                    )

            # Bucket Policy
            policy_allows_public = False
            bucket_policy: dict[str, Any] = {}
            try:
                pol_res = client.get_bucket_policy(Bucket=b_name)
                raw_pol = pol_res.get("Policy", "{}")
                bucket_policy = json.loads(raw_pol) if isinstance(raw_pol, str) else raw_pol
                policy_allows_public = self._inspect_policy_for_public(bucket_policy)
            except ClientError as e:
                code = e.response.get("Error", {}).get("Code", "")
                if code not in ("NoSuchBucketPolicy", "AccessDenied"):
                    errors.append(
                        CollectionError(
                            service="s3",
                            operation=f"get_bucket_policy:{b_name}",
                            error_type=code,
                            message=str(e),
                        )
                    )

            is_public = (not pab_enabled) and policy_allows_public

            buckets.append(
                S3BucketMetadata(
                    bucket_name=b_name,
                    arn=arn,
                    creation_date=creation_date,
                    public_access_block_enabled=pab_enabled,
                    is_public=is_public,
                    policy_allows_public=policy_allows_public,
                    bucket_policy=bucket_policy,
                )
            )

        return buckets, errors
