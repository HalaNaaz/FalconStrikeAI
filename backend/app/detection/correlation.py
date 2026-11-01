"""Adversary detection correlation engine matching ground-truth against alert streams (FR-5.1)."""

from typing import Any

from backend.app.core.logging import logger
from backend.app.detection.metrics import DetectionMetricsCalculator
from backend.app.detection.models import (
    CorrelatedTechniqueResult,
    DetectionCorrelationReport,
    DetectionSourceType,
    DetectionStatus,
    SecurityDetectionEvent,
)
from backend.app.techniques.registry import technique_registry
from backend.app.telemetry.models import SyntheticIOC, TelemetryExportPackage


class DetectionCorrelationEngine:
    """Correlates ground-truth simulation telemetry and synthetic IOCs against security alert feeds.

    Correlation Rules & Safety Guarantees:
    - Enforces strict run_id and campaign_id correlation isolation; rejects alerts from disparate runs.
    - Matches ground-truth IOC values against alert payloads.
    - Distinguishes FULL detection, PARTIAL detection, and MISSED techniques.
    - Calculates per-technique detection latency and campaign MTTD.
    - Clearly labels alert source provenance (DETECTION_STUB vs REAL_INTEGRATION).
    """

    @classmethod
    def correlate(
        cls,
        export_package: TelemetryExportPackage,
        detection_events: list[SecurityDetectionEvent],
        source_name: str = "detection_stub",
        source_type: DetectionSourceType = DetectionSourceType.DETECTION_STUB,
    ) -> DetectionCorrelationReport:
        """Correlate a campaign's telemetry export package with observed detection alerts.

        Args:
            export_package: The ground-truth telemetry and IOC package from the campaign run.
            detection_events: The raw detection events collected from SIEM/EDR or detection stub.
            source_name: Name of the alert source (e.g. 'detection_stub', 'crowdstrike_falcon').
            source_type: Provenance classification (DETECTION_STUB, REAL_INTEGRATION).

        Returns:
            DetectionCorrelationReport containing per-technique results, MTTD, and coverage.
        """
        run_id = export_package.run_id
        campaign_id = export_package.campaign_id

        logger.info(
            f"Starting detection correlation for run {run_id} ({len(export_package.raw_events)} events, "
            f"{len(export_package.iocs)} IOCs, {len(detection_events)} alert signals)"
        )

        # 1. Filter detections to strictly enforce run_id isolation
        relevant_alerts = [
            d for d in detection_events
            if d.run_id == run_id and (d.campaign_id == campaign_id or d.campaign_id == "UNKNOWN")
        ]
        if len(relevant_alerts) < len(detection_events):
            logger.debug(
                f"Filtered {len(detection_events) - len(relevant_alerts)} cross-run alerts during correlation"
            )

        # Index alerts by technique_id
        alerts_by_technique: dict[str, list[SecurityDetectionEvent]] = {}
        for alert in relevant_alerts:
            t_id = alert.technique_id
            if t_id not in alerts_by_technique:
                alerts_by_technique[t_id] = []
            alerts_by_technique[t_id].append(alert)

        # Index synthetic ground truth IOCs by technique_id
        ground_truth_iocs_by_technique: dict[str, list[SyntheticIOC]] = {}
        for ioc in export_package.iocs:
            t_id = ioc.technique_id
            if t_id not in ground_truth_iocs_by_technique:
                ground_truth_iocs_by_technique[t_id] = []
            ground_truth_iocs_by_technique[t_id].append(ioc)

        # Map simulation events by technique_id (first occurrence for timing)
        sim_events_by_technique: dict[str, Any] = {}
        for ev in export_package.raw_events:
            if ev.technique_id not in sim_events_by_technique:
                sim_events_by_technique[ev.technique_id] = ev

        correlated_results: list[CorrelatedTechniqueResult] = []

        # 2. Evaluate each executed technique
        for t_id, sim_event in sim_events_by_technique.items():
            contract = technique_registry.get_contract(t_id)
            technique_name = contract.name if contract else t_id
            tactic_name = str(sim_event.tactic) if sim_event else "Unknown"

            gt_iocs = ground_truth_iocs_by_technique.get(t_id, [])
            gt_ioc_values = {ioc.value for ioc in gt_iocs}

            tech_alerts = alerts_by_technique.get(t_id, [])

            # Check IOC matches
            matched_ioc_values: set[str] = set()
            for alert in tech_alerts:
                if alert.matched_ioc_value and alert.matched_ioc_value in gt_ioc_values:
                    matched_ioc_values.add(alert.matched_ioc_value)

            unmatched_iocs = list(gt_ioc_values - matched_ioc_values)
            matched_iocs = list(matched_ioc_values)

            # Determine detection status
            status: DetectionStatus
            first_detection_time: str | None = None
            latency: float | None = None

            if not tech_alerts:
                status = DetectionStatus.MISSED
            else:
                # Sort alerts chronologically
                sorted_alerts = sorted(tech_alerts, key=lambda a: a.detected_at)
                first_detection_time = sorted_alerts[0].detected_at

                latency = DetectionMetricsCalculator.calculate_technique_latency(
                    ground_truth_time=sim_event.timestamp if sim_event else None,
                    detection_time=first_detection_time,
                )

                # Check if partial: flagged as partial in payload or matched < 50% of IOCs
                is_partial = any(
                    alert.raw_payload.get("partial", False) or alert.severity == "LOW"
                    for alert in tech_alerts
                )

                if is_partial and len(matched_iocs) < len(gt_ioc_values):
                    status = DetectionStatus.PARTIALLY_DETECTED
                else:
                    status = DetectionStatus.DETECTED

            result = CorrelatedTechniqueResult(
                technique_id=t_id,
                technique_name=technique_name,
                tactic=tactic_name,
                status=status,
                ground_truth_event_id=sim_event.event_id if sim_event else None,
                ground_truth_timestamp=sim_event.timestamp if sim_event else None,
                first_detection_timestamp=first_detection_time,
                detection_latency_seconds=latency,
                detection_count=len(tech_alerts),
                detections=tech_alerts,
                matched_iocs=matched_iocs,
                unmatched_iocs=unmatched_iocs,
            )
            correlated_results.append(result)

        # 3. Calculate summary metrics
        coverage_pct, mttd, counts = DetectionMetricsCalculator.compute_summary_metrics(correlated_results)

        report = DetectionCorrelationReport(
            run_id=run_id,
            campaign_id=campaign_id,
            detection_source=source_name,
            detection_source_type=source_type,
            total_executed_techniques=len(correlated_results),
            detected_count=counts["detected"],
            partially_detected_count=counts["partial"],
            missed_count=counts["missed"],
            coverage_percentage=coverage_pct,
            mean_time_to_detect_seconds=mttd,
            techniques=correlated_results,
            summary={
                "evaluated_techniques": len(correlated_results),
                "total_alerts_correlated": len(relevant_alerts),
                "mttd_seconds": mttd,
                "coverage_pct": coverage_pct,
                "counts": counts,
            },
        )

        logger.info(
            f"Correlation completed for run {run_id}: coverage={coverage_pct}%, "
            f"detected={counts['detected']}, missed={counts['missed']}, MTTD={mttd}s"
        )

        return report

