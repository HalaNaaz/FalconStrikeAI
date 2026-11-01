"""Central telemetry collector aggregating C2 beacons, DNS signalling, and synthetic IOCs."""

import threading

from backend.app.core.logging import logger
from backend.app.techniques.models import SimulationEvent
from backend.app.telemetry.c2_sink import BenignC2Sink, c2_sink
from backend.app.telemetry.dns_sink import BenignDNSSink, dns_sink
from backend.app.telemetry.models import (
    C2BeaconEvent,
    DNSSignallingEvent,
    SyntheticIOC,
    TelemetryExportPackage,
)


class TelemetryCollector:
    """Thread-safe collector aggregating simulation events, C2 beacons, DNS queries, and IOCs."""

    def __init__(
        self,
        c2: BenignC2Sink | None = None,
        dns: BenignDNSSink | None = None,
    ) -> None:
        self._lock = threading.RLock()
        self.c2_sink = c2 or c2_sink
        self.dns_sink = dns or dns_sink
        # run_id -> list of SimulationEvent
        self._simulation_events: dict[str, list[SimulationEvent]] = {}
        # run_id -> list of SyntheticIOC
        self._synthetic_iocs: dict[str, list[SyntheticIOC]] = {}

    def record_simulation_event(self, run_id: str, event: SimulationEvent) -> None:
        """Store an observation event produced during stage execution."""
        with self._lock:
            if run_id not in self._simulation_events:
                self._simulation_events[run_id] = []
            self._simulation_events[run_id].append(event)
            logger.debug(f"Recorded simulation event {event.event_id} for run {run_id}")

    def record_iocs(self, run_id: str, iocs: list[SyntheticIOC]) -> None:
        """Store generated synthetic IOCs for a run."""
        with self._lock:
            if run_id not in self._synthetic_iocs:
                self._synthetic_iocs[run_id] = []
            self._synthetic_iocs[run_id].extend(iocs)
            logger.debug(f"Recorded {len(iocs)} synthetic IOCs for run {run_id}")

    def get_simulation_events(self, run_id: str) -> list[SimulationEvent]:
        """Retrieve simulation events for a run."""
        with self._lock:
            return list(self._simulation_events.get(run_id, []))

    def get_iocs(self, run_id: str) -> list[SyntheticIOC]:
        """Retrieve synthetic IOCs for a run."""
        with self._lock:
            return list(self._synthetic_iocs.get(run_id, []))

    def get_c2_beacons(self, run_id: str) -> list[C2BeaconEvent]:
        """Retrieve C2 beacons for a run."""
        return self.c2_sink.get_beacons_for_run(run_id)

    def get_dns_queries(self, run_id: str) -> list[DNSSignallingEvent]:
        """Retrieve DNS queries for a run."""
        return self.dns_sink.get_queries_for_run(run_id)

    def export_telemetry_package(
        self, run_id: str, campaign_id: str = "UNKNOWN"
    ) -> TelemetryExportPackage:
        """Generate a complete, consolidated telemetry export package."""
        with self._lock:
            raw_events = self.get_simulation_events(run_id)
            iocs = self.get_iocs(run_id)
            c2_beacons = self.get_c2_beacons(run_id)
            dns_queries = self.get_dns_queries(run_id)

            total_count = len(raw_events) + len(iocs) + len(c2_beacons) + len(dns_queries)

            summary = {
                "total_events": total_count,
                "raw_simulation_events": len(raw_events),
                "synthetic_iocs": len(iocs),
                "c2_beacons": len(c2_beacons),
                "dns_signalling_queries": len(dns_queries),
            }

            return TelemetryExportPackage(
                run_id=run_id,
                campaign_id=campaign_id,
                total_events=total_count,
                c2_beacons=c2_beacons,
                dns_queries=dns_queries,
                iocs=iocs,
                raw_events=raw_events,
                summary=summary,
            )

    def clear(self) -> None:
        """Clear all stored telemetry."""
        with self._lock:
            self._simulation_events.clear()
            self._synthetic_iocs.clear()
            self.c2_sink.clear()
            self.dns_sink.clear()


telemetry_collector = TelemetryCollector()
