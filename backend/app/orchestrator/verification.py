"""Baseline verification engine comparing pre-run and post-run environment states (FR-3.5)."""


from backend.app.core.logging import logger
from backend.app.orchestrator.models import BaselineSnapshot


class BaselineVerifier:
    """Verifies that an environment has returned exactly to its pre-run baseline state."""

    @staticmethod
    def verify(
        pre_run: BaselineSnapshot,
        post_run: BaselineSnapshot,
    ) -> tuple[bool, list[str]]:
        """Compare pre-run and post-run snapshots.

        Returns:
            (is_verified, discrepancies)
        """
        discrepancies: list[str] = []

        # 1. State fingerprint comparison
        if pre_run.state_fingerprint == post_run.state_fingerprint:
            logger.info(
                f"Baseline verification PASSED for run {pre_run.run_id}: Fingerprints match ({pre_run.state_fingerprint[:12]}...)"
            )
            return True, []

        # 2. Identify resource count differences
        for key, pre_count in pre_run.resource_counts.items():
            post_count = post_run.resource_counts.get(key, 0)
            if pre_count != post_count:
                discrepancies.append(
                    f"Count mismatch for '{key}': pre-run had {pre_count}, post-run has {post_count}"
                )

        # 3. Identify added or missing resources
        pre_set = set(pre_run.resource_ids)
        post_set = set(post_run.resource_ids)

        added = post_set - pre_set
        missing = pre_set - post_set

        for r_id in sorted(added):
            discrepancies.append(f"Residual resource detected post-run (uncleaned): {r_id}")

        for r_id in sorted(missing):
            discrepancies.append(f"Missing resource detected post-run (unintended deletion): {r_id}")

        logger.warning(
            f"Baseline verification FAILED for run {pre_run.run_id} with {len(discrepancies)} discrepancies"
        )
        return False, discrepancies
