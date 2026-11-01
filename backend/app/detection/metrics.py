"""Metrics calculator for detection coverage, latency, and MTTD (FR-5.1)."""

from datetime import datetime

from backend.app.core.logging import logger
from backend.app.detection.models import CorrelatedTechniqueResult, DetectionStatus


class DetectionMetricsCalculator:
    """Calculates coverage percentages, per-technique latency, and Mean Time to Detect (MTTD).

    Mathematical Rigor & Grounding:
    - MTTD is calculated strictly from the difference between ground-truth event timestamps
      and the first verified detection timestamp:
          Latency_i = t_detected,i - t_groundtruth,i (in seconds)
          MTTD = (1 / N) * SUM(Latency_i)
    - Unobserved / missed techniques are excluded from latency calculations and never assigned synthetic delays.
    - If zero techniques are detected, MTTD evaluates to None (never fabricated as 0.0).
    - Coverage percentage is calculated as:
          Coverage% = (Detected_Techniques / Total_Executed_Techniques) * 100
      with partial detections accounted for in the summary breakdown.
    """

    @staticmethod
    def parse_iso_timestamp(ts: str | None) -> datetime | None:
        """Parse ISO timestamp safely, normalizing UTC timezones."""
        if not ts:
            return None
        try:
            return datetime.fromisoformat(ts.replace("Z", "+00:00"))
        except Exception as exc:
            logger.warning(f"Failed to parse timestamp '{ts}': {exc}")
            return None

    @classmethod
    def calculate_technique_latency(
        cls,
        ground_truth_time: str | None,
        detection_time: str | None,
    ) -> float | None:
        """Calculate the delta in seconds between ground truth execution and alert detection."""
        gt_dt = cls.parse_iso_timestamp(ground_truth_time)
        det_dt = cls.parse_iso_timestamp(detection_time)

        if not gt_dt or not det_dt:
            return None

        delta_seconds = (det_dt - gt_dt).total_seconds()
        # Return non-negative latency (if clock skew occurs, floor to 0.0)
        return max(0.0, round(delta_seconds, 2))

    @classmethod
    def compute_summary_metrics(
        cls,
        technique_results: list[CorrelatedTechniqueResult],
    ) -> tuple[float, float | None, dict[str, int]]:
        """Compute coverage percentage, MTTD, and status counts across evaluated techniques.

        Returns:
            tuple: (coverage_percentage, mean_time_to_detect_seconds, counts_dict)
        """
        total_executed = len(technique_results)
        if total_executed == 0:
            return 0.0, None, {"detected": 0, "partial": 0, "missed": 0, "total": 0}

        detected_count = sum(1 for t in technique_results if t.status == DetectionStatus.DETECTED)
        partial_count = sum(1 for t in technique_results if t.status == DetectionStatus.PARTIALLY_DETECTED)
        missed_count = sum(1 for t in technique_results if t.status == DetectionStatus.MISSED)

        # Explicit coverage calculation: (detected + 0.5 * partial) / total
        effective_detected = detected_count + (0.5 * partial_count)
        coverage_pct = round((effective_detected / float(total_executed)) * 100.0, 2)

        # Collect valid latencies for MTTD calculation
        valid_latencies: list[float] = []
        for t in technique_results:
            if t.detection_latency_seconds is not None:
                valid_latencies.append(t.detection_latency_seconds)

        mttd: float | None = None
        if valid_latencies:
            mttd = round(sum(valid_latencies) / float(len(valid_latencies)), 2)

        counts = {
            "detected": detected_count,
            "partial": partial_count,
            "missed": missed_count,
            "total": total_executed,
        }

        return coverage_pct, mttd, counts

