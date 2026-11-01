"""Unit and integration tests for detection correlation, detection stub, and SIEM adapters (FR-5.1)."""

import pytest

from backend.app.core.exceptions import FalconSecurityException
from backend.app.detection.adapters import (
    CrowdStrikeFalconAdapter,
    ElasticSecurityAdapter,
    QRadarAdapter,
    SentinelAdapter,
    SplunkAdapter,
)
from backend.app.detection.correlation import DetectionCorrelationEngine
from backend.app.detection.detection_stub import DetectionStub
from backend.app.detection.metrics import DetectionMetricsCalculator
from backend.app.detection.models import (
    CorrelatedTechniqueResult,
    DetectionSourceType,
    DetectionStatus,
    SecurityDetectionEvent,
)
from backend.app.techniques.models import AttackTactic, SimulationEvent
from backend.app.telemetry.ioc_generator import SyntheticIOCGenerator
from backend.app.telemetry.models import IOCType, TelemetryExportPackage


@pytest.fixture
def sample_telemetry_package() -> TelemetryExportPackage:
    """Fixture providing a deterministic telemetry export package with 3 techniques."""
    run_id = "RUN-DET-TEST-001"
    campaign_id = "CAMP-DET-001"

    ev1 = SimulationEvent(
        event_id="SIM-01",
        technique_id="T1526",
        tactic=AttackTactic.DISCOVERY,
        target_resource_id="target-role-01",
        timestamp="2026-11-01T10:00:00+00:00",
    )
    ev2 = SimulationEvent(
        event_id="SIM-02",
        technique_id="T1078",
        tactic=AttackTactic.PRIVILEGE_ESCALATION,
        target_resource_id="target-role-admin",
        timestamp="2026-11-01T10:00:10+00:00",
    )
    ev3 = SimulationEvent(
        event_id="SIM-03",
        technique_id="T1071",
        tactic=AttackTactic.COMMAND_AND_CONTROL,
        target_resource_id="target-c2-channel",
        timestamp="2026-11-01T10:00:20+00:00",
    )

    iocs1 = SyntheticIOCGenerator.generate_iocs_for_stage(run_id, "T1526", "target-role-01")
    iocs2 = SyntheticIOCGenerator.generate_iocs_for_stage(run_id, "T1078", "target-role-admin")
    iocs3 = SyntheticIOCGenerator.generate_iocs_for_stage(run_id, "T1071", "target-c2-channel")

    all_iocs = iocs1 + iocs2 + iocs3

    return TelemetryExportPackage(
        run_id=run_id,
        campaign_id=campaign_id,
        raw_events=[ev1, ev2, ev3],
        iocs=all_iocs,
        total_events=len(all_iocs) + 3,
    )


class TestDetectionCorrelationEngine:
    """Test suite for DetectionCorrelationEngine."""

    def test_exact_ioc_and_technique_match(
        self, sample_telemetry_package: TelemetryExportPackage
    ) -> None:
        """Verify correlation accurately matches technique ID and IOC values."""
        run_id = sample_telemetry_package.run_id
        campaign_id = sample_telemetry_package.campaign_id

        # Target T1078 IOC
        t1078_iocs = [ioc for ioc in sample_telemetry_package.iocs if ioc.technique_id == "T1078"]
        target_ioc_value = t1078_iocs[0].value

        detection = SecurityDetectionEvent(
            run_id=run_id,
            campaign_id=campaign_id,
            technique_id="T1078",
            matched_ioc_value=target_ioc_value,
            matched_ioc_type=IOCType.SHA256,
            severity="HIGH",
            title="High Privesc Activity Detected",
            description="Alert triggered on benign test marker",
            detected_at="2026-11-01T10:00:25+00:00",
        )

        report = DetectionCorrelationEngine.correlate(
            export_package=sample_telemetry_package,
            detection_events=[detection],
        )

        assert report.run_id == run_id
        assert report.total_executed_techniques == 3

        # T1078 should be DETECTED with latency = 15s (10:00:25 - 10:00:10)
        t1078_res = next(t for t in report.techniques if t.technique_id == "T1078")
        assert t1078_res.status == DetectionStatus.DETECTED
        assert t1078_res.detection_latency_seconds == 15.0
        assert target_ioc_value in t1078_res.matched_iocs

        # T1526 and T1071 should be MISSED
        t1526_res = next(t for t in report.techniques if t.technique_id == "T1526")
        assert t1526_res.status == DetectionStatus.MISSED
        assert t1526_res.detection_latency_seconds is None

    def test_run_isolation_filters_cross_campaign_alerts(
        self, sample_telemetry_package: TelemetryExportPackage
    ) -> None:
        """Verify alerts from different run_ids are strictly ignored to prevent false matches."""
        # Alert with WRONG run_id
        alert_other_run = SecurityDetectionEvent(
            run_id="RUN-DISPARATE-999",
            campaign_id="CAMP-999",
            technique_id="T1078",
            matched_ioc_value="fake_val",
            title="Alert for other run",
            description="Description",
            detected_at="2026-11-01T10:00:30+00:00",
        )

        report = DetectionCorrelationEngine.correlate(
            export_package=sample_telemetry_package,
            detection_events=[alert_other_run],
        )

        # All techniques must be MISSED because alert belonged to another run
        assert report.detected_count == 0
        assert report.missed_count == 3
        assert report.mean_time_to_detect_seconds is None

    def test_empty_detection_input_reports_all_missed(
        self, sample_telemetry_package: TelemetryExportPackage
    ) -> None:
        """Verify empty alert list reports all techniques missed without inventing latency."""
        report = DetectionCorrelationEngine.correlate(
            export_package=sample_telemetry_package,
            detection_events=[],
        )

        assert report.detected_count == 0
        assert report.missed_count == 3
        assert report.coverage_percentage == 0.0
        assert report.mean_time_to_detect_seconds is None

    def test_partial_detection_classification(
        self, sample_telemetry_package: TelemetryExportPackage
    ) -> None:
        """Verify alerts flagged as partial or low severity classify technique as PARTIALLY_DETECTED."""
        run_id = sample_telemetry_package.run_id
        campaign_id = sample_telemetry_package.campaign_id

        partial_alert = SecurityDetectionEvent(
            run_id=run_id,
            campaign_id=campaign_id,
            technique_id="T1526",
            matched_ioc_value="some_partial_val",
            severity="LOW",
            title="Generic Suspicious Cloud Discovery",
            description="Low severity partial alert",
            detected_at="2026-11-01T10:00:12+00:00",
            raw_payload={"partial": True},
        )

        report = DetectionCorrelationEngine.correlate(
            export_package=sample_telemetry_package,
            detection_events=[partial_alert],
        )

        t1526 = next(t for t in report.techniques if t.technique_id == "T1526")
        assert t1526.status == DetectionStatus.PARTIALLY_DETECTED
        assert report.partially_detected_count == 1


class TestDetectionStub:
    """Test suite for local DetectionStub."""

    def test_detection_stub_full_coverage(
        self, sample_telemetry_package: TelemetryExportPackage
    ) -> None:
        """Verify DetectionStub generates alerts with correct metadata and labels."""
        stub = DetectionStub(profile="FULL_COVERAGE")
        assert stub.source_type == DetectionSourceType.DETECTION_STUB
        assert stub.adapter_name == "detection_stub"
        assert stub.is_connected() is True

        detections = stub.generate_detections_from_telemetry(
            export_package=sample_telemetry_package,
            latency_seconds=10.0,
        )

        assert len(detections) >= 3
        for d in detections:
            assert d.source_type == DetectionSourceType.DETECTION_STUB
            assert d.source_name == "detection_stub"
            assert d.run_id == sample_telemetry_package.run_id
            assert "[STUB]" in d.title

        # Correlate with engine
        report = DetectionCorrelationEngine.correlate(sample_telemetry_package, detections)
        assert report.detected_count == 3
        assert report.missed_count == 0
        assert report.coverage_percentage == 100.0
        assert report.mean_time_to_detect_seconds is not None
        assert report.mean_time_to_detect_seconds > 0.0

    def test_detection_stub_high_miss_rate(
        self, sample_telemetry_package: TelemetryExportPackage
    ) -> None:
        """Verify high miss rate profile produces missed techniques."""
        stub = DetectionStub(profile="HIGH_MISS_RATE")
        detections = stub.generate_detections_from_telemetry(sample_telemetry_package)

        report = DetectionCorrelationEngine.correlate(sample_telemetry_package, detections)
        assert report.missed_count >= 1
        assert report.coverage_percentage < 100.0


class TestDetectionMetricsCalculator:
    """Test suite for DetectionMetricsCalculator."""

    def test_mttd_calculation_with_valid_and_invalid_timestamps(self) -> None:
        """Verify MTTD calculation handles valid timestamps and ignores invalid ones."""
        # 1. Valid delta = 20.0 seconds
        lat1 = DetectionMetricsCalculator.calculate_technique_latency(
            "2026-11-01T10:00:00+00:00", "2026-11-01T10:00:20+00:00"
        )
        assert lat1 == 20.0

        # 2. Invalid timestamp format returns None safely
        lat2 = DetectionMetricsCalculator.calculate_technique_latency(
            "INVALID_TIMESTAMP", "2026-11-01T10:00:20+00:00"
        )
        assert lat2 is None

        # 3. None input returns None safely
        assert DetectionMetricsCalculator.calculate_technique_latency(None, None) is None

    def test_summary_metrics_math(self) -> None:
        """Verify coverage percentage formula and MTTD averaging."""
        results = [
            CorrelatedTechniqueResult(
                technique_id="T1",
                technique_name="T1",
                tactic="Discovery",
                status=DetectionStatus.DETECTED,
                detection_latency_seconds=10.0,
            ),
            CorrelatedTechniqueResult(
                technique_id="T2",
                technique_name="T2",
                tactic="Discovery",
                status=DetectionStatus.PARTIALLY_DETECTED,
                detection_latency_seconds=20.0,
            ),
            CorrelatedTechniqueResult(
                technique_id="T3",
                technique_name="T3",
                tactic="Discovery",
                status=DetectionStatus.MISSED,
                detection_latency_seconds=None,
            ),
        ]

        cov_pct, mttd, counts = DetectionMetricsCalculator.compute_summary_metrics(results)

        # 1 detected + 0.5 * 1 partial = 1.5 out of 3 = 50.0%
        assert cov_pct == 50.0
        # Average of (10.0 + 20.0) / 2 = 15.0s
        assert mttd == 15.0
        assert counts["detected"] == 1
        assert counts["partial"] == 1
        assert counts["missed"] == 1


class TestRealSIEMAdaptersDisconnectedState:
    """Test suite verifying SIEM adapters report disconnected state honestly."""

    def test_falcon_adapter_disconnected_without_credentials(self) -> None:
        """Verify CrowdStrikeFalconAdapter reports disconnected and refuses query when unconfigured."""
        adapter = CrowdStrikeFalconAdapter(client_id=None, client_secret=None)
        assert adapter.is_connected() is False
        assert adapter.source_type == DetectionSourceType.REAL_INTEGRATION
        with pytest.raises(FalconSecurityException, match="not connected"):
            adapter.query_detections("RUN-01", "2026-11-01T10:00:00Z")

    def test_splunk_adapter_disconnected_without_credentials(self) -> None:
        """Verify SplunkAdapter reports disconnected when unconfigured."""
        adapter = SplunkAdapter(host=None, token=None)
        assert adapter.is_connected() is False
        with pytest.raises(FalconSecurityException, match="not connected"):
            adapter.query_detections("RUN-01", "2026-11-01T10:00:00Z")

    def test_sentinel_adapter_disconnected(self) -> None:
        adapter = SentinelAdapter(tenant_id=None, client_id=None)
        assert adapter.is_connected() is False
        with pytest.raises(FalconSecurityException, match="credentials missing"):
            adapter.query_detections("RUN-01", "2026-11-01T10:00:00Z")

    def test_elastic_adapter_disconnected(self) -> None:
        adapter = ElasticSecurityAdapter(cloud_id=None, api_key=None)
        assert adapter.is_connected() is False
        with pytest.raises(FalconSecurityException, match="credentials missing"):
            adapter.query_detections("RUN-01", "2026-11-01T10:00:00Z")

    def test_qradar_adapter_disconnected(self) -> None:
        adapter = QRadarAdapter(host=None, sec_token=None)
        assert adapter.is_connected() is False
        with pytest.raises(FalconSecurityException, match="credentials missing"):
            adapter.query_detections("RUN-01", "2026-11-01T10:00:00Z")
