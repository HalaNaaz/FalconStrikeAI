"""Unit tests for benign C2 signalling, DNS covert channel, and synthetic IOCs (FR-3.4)."""

import pytest

from backend.app.core.exceptions import FalconSecurityException
from backend.app.techniques.models import AttackTactic, SimulationEvent
from backend.app.telemetry.c2_sink import BenignC2Sink
from backend.app.telemetry.collector import TelemetryCollector
from backend.app.telemetry.dns_sink import BenignDNSSink
from backend.app.telemetry.ioc_generator import SyntheticIOCGenerator
from backend.app.telemetry.models import IOCType


class TestBenignC2Sink:
    """Test suite for BenignC2Sink."""

    def test_jitter_delay_stays_within_bounds(self) -> None:
        """Verify calculated delay remains strictly within [base * (1 - jitter), base * (1 + jitter)]."""
        base = 5.0
        jitter_pct = 20.0  # delay must be within [4.0, 6.0]

        for seed in range(50):
            delay = BenignC2Sink.calculate_jitter_delay(base, jitter_pct, seed=seed)
            assert 4.0 <= delay <= 6.0

    def test_destination_allowlist_enforcement(self) -> None:
        """Verify unauthorized external C2 addresses are blocked."""
        sink = BenignC2Sink()

        # Localhost is allowed
        beacon = sink.emit_beacon(
            run_id="RUN-C2-01",
            technique_id="T1071",
            destination_host="127.0.0.1",
        )
        assert beacon.destination_host == "127.0.0.1"
        assert "FALCON_BENIGN_MARKER_T1071_RUN-C2-01" in beacon.marker_payload

        # External destination raises FalconSecurityException
        with pytest.raises(FalconSecurityException, match="outside the authorized lab allowlist"):
            sink.emit_beacon(
                run_id="RUN-C2-02",
                technique_id="T1071",
                destination_host="evil-command-and-control.com",
            )

    def test_retrieve_beacons_for_run(self) -> None:
        """Verify querying beacons by run_id."""
        sink = BenignC2Sink()
        sink.emit_beacon(run_id="RUN-A", technique_id="T1071")
        sink.emit_beacon(run_id="RUN-B", technique_id="T1071")

        beacons_a = sink.get_beacons_for_run("RUN-A")
        assert len(beacons_a) == 1
        assert beacons_a[0].run_id == "RUN-A"


class TestBenignDNSSink:
    """Test suite for BenignDNSSink."""

    def test_domain_allowlist_rules(self) -> None:
        """Verify internal vs external domain matching."""
        dns = BenignDNSSink()
        assert dns.is_domain_allowed("query.lab.falconstrike.internal") is True
        assert dns.is_domain_allowed("beacon.internal") is True
        assert dns.is_domain_allowed("localhost") is True
        assert dns.is_domain_allowed("google.com") is False
        assert dns.is_domain_allowed("evil.attacker.net") is False

    def test_record_dns_query_success(self) -> None:
        """Verify recorded DNS query contains benign TXT response."""
        dns = BenignDNSSink()
        event = dns.record_query(
            run_id="RUN-DNS-01",
            technique_id="T1071.004",
            subdomain_token="stage01",
        )

        assert event.query_name == "stage01.c2.lab.falconstrike.internal"
        assert "v=falcon-ack" in event.simulated_response
        assert "FALCON_DNS_TOKEN_STAGE01" in event.marker_token

    def test_external_dns_rejected(self) -> None:
        """Verify DNS queries with external base domains are blocked."""
        dns = BenignDNSSink()
        with pytest.raises(FalconSecurityException, match="outside the authorized lab domain allowlist"):
            dns.record_query(
                run_id="RUN-DNS-BAD",
                technique_id="T1071.004",
                subdomain_token="test",
                base_domain="external-internet-dns.com",
            )


class TestSyntheticIOCGenerator:
    """Test suite for SyntheticIOCGenerator."""

    def test_generates_all_expected_ioc_types(self) -> None:
        """Verify SHA256, User-Agent, IP, File Path, and API Call IOCs are generated."""
        iocs = SyntheticIOCGenerator.generate_iocs_for_stage(
            run_id="RUN-IOC-01",
            technique_id="T1078",
            target_resource_id="arn:aws:iam::000000000000:role/AdminRole",
        )

        types_generated = {ioc.ioc_type for ioc in iocs}
        assert IOCType.SHA256 in types_generated
        assert IOCType.USER_AGENT in types_generated
        assert IOCType.IP_ADDRESS in types_generated
        assert IOCType.FILE_PATH in types_generated
        assert IOCType.API_CALL in types_generated

        for ioc in iocs:
            assert ioc.is_benign_marker is True
            assert ioc.run_id == "RUN-IOC-01"
            assert ioc.technique_id == "T1078"
            assert len(ioc.detection_guidance) > 10


class TestTelemetryCollector:
    """Test suite for TelemetryCollector."""

    def test_export_package_assembly(self) -> None:
        """Verify TelemetryCollector compiles simulation events, IOCs, beacons, and DNS queries."""
        c2 = BenignC2Sink()
        dns = BenignDNSSink()
        collector = TelemetryCollector(c2=c2, dns=dns)

        run_id = "RUN-EXPORT-01"

        # Record simulation event
        sim_event = SimulationEvent(
            technique_id="T1526",
            tactic=AttackTactic.DISCOVERY,
            target_resource_id="target-01",
        )
        collector.record_simulation_event(run_id, sim_event)

        # Record IOCs
        iocs = SyntheticIOCGenerator.generate_iocs_for_stage(run_id, "T1526", "target-01")
        collector.record_iocs(run_id, iocs)

        # Emit C2 beacon & DNS query
        c2.emit_beacon(run_id=run_id, technique_id="T1071")
        dns.record_query(run_id=run_id, technique_id="T1071.004", subdomain_token="stage01")

        # Export package
        pkg = collector.export_telemetry_package(run_id=run_id, campaign_id="CAMP-01")

        assert pkg.run_id == run_id
        assert pkg.campaign_id == "CAMP-01"
        assert len(pkg.raw_events) == 1
        assert len(pkg.iocs) == 5
        assert len(pkg.c2_beacons) == 1
        assert len(pkg.dns_queries) == 1
        assert pkg.total_events == 8
        assert pkg.summary["total_events"] == 8

