"""High-level orchestrator for cloud asset collection."""

import time
from typing import Any

from backend.app.collectors.aws_iam import AWSIAMCollector
from backend.app.collectors.aws_network import AWSNetworkCollector
from backend.app.collectors.aws_s3 import AWSS3Collector
from backend.app.collectors.models import (
    CollectionError,
    CollectionSourceType,
    NormalizedEnvironmentData,
)
from backend.app.collectors.synthetic import SyntheticEnvironmentProvider
from backend.app.core.config import settings
from backend.app.core.logging import logger


class CollectorOrchestrator:
    """Manages multi-service cloud asset collection from synthetic or live sources."""

    def __init__(self, session: Any = None) -> None:
        self.session = session

    def run_collection(
        self,
        account_id: str | None = None,
        force_synthetic: bool = True,
        synthetic_topology_type: str = "flawed",
    ) -> NormalizedEnvironmentData:
        """Run cloud collection across IAM, EC2, and S3.

        Defaults to synthetic collection unless force_synthetic=False and live execution is permitted.
        """
        target_account = account_id or settings.target_account_id
        settings.assert_account_allowlisted(target_account)

        # Enforce synthetic mode if configured or if dry_run is active
        if force_synthetic or settings.dry_run:
            logger.info(
                f"Running offline synthetic collection for account {target_account} (topology={synthetic_topology_type})"
            )
            if synthetic_topology_type == "clean":
                return SyntheticEnvironmentProvider.generate_clean_environment(target_account)
            return SyntheticEnvironmentProvider.generate_flawed_environment(target_account)

        # Live AWS Collection requires two-key authorization check
        settings.assert_live_execution_permitted(target_account)
        logger.info(f"Initiating LIVE read-only AWS collection for account {target_account}")

        start_time = time.perf_counter()
        errors: list[CollectionError] = []

        # 1. IAM Collector
        iam_collector = AWSIAMCollector(session=self.session)
        iam_data, iam_errs = iam_collector.collect(target_account)
        errors.extend(iam_errs)

        # 2. Network / EC2 Collector
        net_collector = AWSNetworkCollector(session=self.session)
        net_data, net_errs = net_collector.collect(target_account)
        errors.extend(net_errs)

        # 3. S3 Collector
        s3_collector = AWSS3Collector(session=self.session)
        s3_data, s3_errs = s3_collector.collect(target_account)
        errors.extend(s3_errs)

        duration_ms = (time.perf_counter() - start_time) * 1000.0

        return NormalizedEnvironmentData(
            account_id=target_account,
            source_type=CollectionSourceType.AWS_LIVE,
            duration_ms=duration_ms,
            iam_users=iam_data.get("users", []),
            iam_roles=iam_data.get("roles", []),
            policies=iam_data.get("policies", []),
            ec2_instances=net_data.get("instances", []),
            security_groups=net_data.get("security_groups", []),
            s3_buckets=s3_data,
            errors=errors,
        )
