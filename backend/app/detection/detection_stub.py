"""Deterministic local Detection Stub producing realistic, clearly labelled synthetic alerts (FR-5.1)."""

from datetime import UTC, datetime, timedelta

from backend.app.core.logging import logger
from backend.app.detection.interfaces import BaseSIEMAdapter
from backend.app.detection.models import DetectionSourceType, SecurityDetectionEvent
from backend.app.telemetry.models import SyntheticIOC, TelemetryExportPackage


class DetectionStub(BaseSIEMAdapter):
    """Generates deterministic, synthetic security detections based on ground-truth emulation artifacts.

    Integrity Guarantees:
    - Alerts are unequivocally tagged with source_type=DETECTION_STUB and source_name="detection_stub".
    - Never falsely attributes synthetic detections to CrowdStrike Falcon, Splunk, or external SIEMs.
    - Produces realistic alert metadata and valid timestamps offset by simulated SOC/EDR ingestion delays.
    """

    def __init__(self, profile: str = "FULL_COVERAGE") -> None:
        """Initialize stub with an evaluation profile: 'FULL_COVERAGE', 'PARTIAL_COVERAGE', 'HIGH_MISS_RATE'."""
        self.profile = profile
        self._custom_detections: list[SecurityDetectionEvent] = []

    @property
    def adapter_name(self) -> str:
        return "detection_stub"

    @property
    def source_type(self) -> DetectionSourceType:
        return DetectionSourceType.DETECTION_STUB

    def is_connected(self) -> bool:
        """The detection stub is always locally connected."""
        return True

    def inject_detection(self, detection: SecurityDetectionEvent) -> None:
        """Inject an explicit synthetic detection for test scenarios."""
        self._custom_detections.append(detection)

    def generate_detections_from_telemetry(
        self,
        export_package: TelemetryExportPackage,
        latency_seconds: float = 14.2,
    ) -> list[SecurityDetectionEvent]:
        """Generate synthetic detection alerts from an executed campaign's telemetry package.

        Args:
            export_package: The ground-truth telemetry export containing events and IOCs.
            latency_seconds: Synthetic detection latency added to ground-truth event timestamps.

        Returns:
            list[SecurityDetectionEvent] representing alerts detected by the simulated monitoring stack.
        """
        detections: list[SecurityDetectionEvent] = list(self._custom_detections)
        run_id = export_package.run_id
        campaign_id = export_package.campaign_id

        logger.info(
            f"DetectionStub synthesizing alerts for run {run_id} under profile '{self.profile}'"
        )

        # Index synthetic IOCs by technique_id
        iocs_by_technique: dict[str, list[SyntheticIOC]] = {}
        for ioc in export_package.iocs:
            if ioc.technique_id not in iocs_by_technique:
                iocs_by_technique[ioc.technique_id] = []
            iocs_by_technique[ioc.technique_id].append(ioc)

        # Process each simulated event
        for idx, event in enumerate(export_package.raw_events):
            technique_id = event.technique_id

            # Determine whether this technique triggers an alert based on profile
            should_detect = True
            partial_mode = False

            if self.profile == "HIGH_MISS_RATE":
                # Only detect 1 in 3 techniques
                should_detect = idx % 3 == 0
            elif self.profile == "PARTIAL_COVERAGE":
                if idx % 3 == 1:
                    partial_mode = True
                elif idx % 3 == 2:
                    should_detect = False

            if not should_detect:
                logger.debug(f"DetectionStub simulating MISSED alert for technique {technique_id}")
                continue

            # Parse ground truth timestamp to add realistic detection delay
            try:
                base_time = datetime.fromisoformat(event.timestamp.replace("Z", "+00:00"))
            except Exception:
                base_time = datetime.now(UTC)

            # Simulated detection timestamp
            detected_time = (base_time + timedelta(seconds=latency_seconds + (idx * 2.5))).isoformat()

            technique_iocs = iocs_by_technique.get(technique_id, [])

            if partial_mode and technique_iocs:
                # In partial mode, match only the first IOC and label as partial signal
                matched_ioc = technique_iocs[0]
                alert = SecurityDetectionEvent(
                    run_id=run_id,
                    campaign_id=campaign_id,
                    technique_id=technique_id,
                    matched_ioc_value=matched_ioc.value,
                    matched_ioc_type=matched_ioc.ioc_type,
                    severity="LOW",
                    title=f"[STUB] Generic Suspicious Activity: {technique_id}",
                    description=f"Synthetic partial alert triggered by marker {matched_ioc.value[:16]}...",
                    source_type=self.source_type,
                    source_name=self.adapter_name,
                    detected_at=detected_time,
                    raw_payload={
                        "rule_id": f"STUB-RULE-{technique_id}",
                        "confidence": "MEDIUM",
                        "partial": True,
                    },
                )
                detections.append(alert)
            else:
                # Full detection matching primary IOCs
                primary_ioc = technique_iocs[0] if technique_iocs else None
                alert = SecurityDetectionEvent(
                    run_id=run_id,
                    campaign_id=campaign_id,
                    technique_id=technique_id,
                    matched_ioc_value=primary_ioc.value if primary_ioc else None,
                    matched_ioc_type=primary_ioc.ioc_type if primary_ioc else None,
                    severity="HIGH" if "Privilege" in str(event.tactic) else "MEDIUM",
                    title=f"[STUB] High-Confidence Alert: {technique_id} ({event.tactic})",
                    description=f"Synthetic detection matching observable emulation for target {event.target_resource_id}",
                    source_type=self.source_type,
                    source_name=self.adapter_name,
                    detected_at=detected_time,
                    raw_payload={
                        "rule_id": f"STUB-RULE-{technique_id}-PRIMARY",
                        "confidence": "HIGH",
                        "event_ref": event.event_id,
                    },
                )
                detections.append(alert)

                # Add second alert if multiple IOCs exist (e.g. hash + user-agent)
                if len(technique_iocs) > 1:
                    secondary_ioc = technique_iocs[1]
                    sec_time = (base_time + timedelta(seconds=latency_seconds + 3.0)).isoformat()
                    detections.append(
                        SecurityDetectionEvent(
                            run_id=run_id,
                            campaign_id=campaign_id,
                            technique_id=technique_id,
                            matched_ioc_value=secondary_ioc.value,
                            matched_ioc_type=secondary_ioc.ioc_type,
                            severity="MEDIUM",
                            title=f"[STUB] Secondary Indicator Match: {technique_id}",
                            description=f"Correlated secondary IOC match for {secondary_ioc.ioc_type}",
                            source_type=self.source_type,
                            source_name=self.adapter_name,
                            detected_at=sec_time,
                            raw_payload={"secondary": True},
                        )
                    )

        return detections

    def query_detections(
        self,
        run_id: str,
        start_time: str,
        end_time: str | None = None,
    ) -> list[SecurityDetectionEvent]:
        """Query synthetic detections matching the run ID."""
        return [d for d in self._custom_detections if d.run_id == run_id]
