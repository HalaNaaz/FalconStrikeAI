"""Environment baseline state recorder for pre-run and post-run verification (FR-3.5)."""

import hashlib
import json
from datetime import UTC, datetime

from backend.app.collectors.models import NormalizedEnvironmentData
from backend.app.orchestrator.models import BaselineSnapshot


class BaselineRecorder:
    """Captures and fingerprints the state of environment resources prior to execution."""

    @staticmethod
    def capture(
        run_id: str,
        environment_data: NormalizedEnvironmentData | None,
        account_id: str = "000000000000",
    ) -> BaselineSnapshot:
        """Capture a deterministic snapshot and SHA-256 fingerprint of the environment."""
        if not environment_data:
            # Empty environment snapshot
            empty_fingerprint = hashlib.sha256(b"EMPTY_ENVIRONMENT").hexdigest()
            return BaselineSnapshot(
                run_id=run_id,
                account_id=account_id,
                resource_counts={"iam_users": 0, "iam_roles": 0, "ec2_instances": 0, "s3_buckets": 0},
                resource_ids=[],
                state_fingerprint=empty_fingerprint,
                details={},
            )

        # Collect resource IDs and counts
        iam_users = [u.arn for u in environment_data.iam_users]
        iam_roles = [r.arn for r in environment_data.iam_roles]
        ec2_instances = [i.instance_id for i in environment_data.ec2_instances]
        s3_buckets = [b.arn for b in environment_data.s3_buckets]
        security_groups = [sg.group_id for sg in environment_data.security_groups]

        all_ids = sorted(iam_users + iam_roles + ec2_instances + s3_buckets + security_groups)

        counts = {
            "iam_users": len(iam_users),
            "iam_roles": len(iam_roles),
            "ec2_instances": len(ec2_instances),
            "s3_buckets": len(s3_buckets),
            "security_groups": len(security_groups),
            "total_resources": len(all_ids),
        }

        # Deterministic serialization for SHA-256 hash
        serialized_state = json.dumps(
            {
                "account_id": environment_data.account_id or account_id,
                "counts": counts,
                "resource_ids": all_ids,
            },
            sort_keys=True,
        )
        fingerprint = hashlib.sha256(serialized_state.encode("utf-8")).hexdigest()

        return BaselineSnapshot(
            run_id=run_id,
            timestamp=datetime.now(UTC).isoformat(),
            account_id=environment_data.account_id or account_id,
            resource_counts=counts,
            resource_ids=all_ids,
            state_fingerprint=fingerprint,
            details={
                "iam_roles": iam_roles,
                "ec2_instances": ec2_instances,
                "s3_buckets": s3_buckets,
            },
        )
