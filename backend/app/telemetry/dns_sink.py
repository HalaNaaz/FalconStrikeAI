"""Benign DNS covert-channel and signalling sink (FR-3.4)."""

import re

from backend.app.core.exceptions import FalconSecurityException
from backend.app.core.logging import logger
from backend.app.telemetry.models import DNSSignallingEvent


class BenignDNSSink:
    """Simulates adversary DNS signalling queries strictly contained within internal lab zones.

    Security Guarantees:
    - Never generates real public recursive DNS traffic.
    - Destination domains must match *.internal or lab domain patterns.
    - Query records are stored locally for detection engineering verification.
    """

    ALLOWED_DOMAIN_PATTERNS = [
        re.compile(r"^.*\.lab\.falconstrike\.internal$"),
        re.compile(r"^.*\.internal$"),
        re.compile(r"^localhost$"),
    ]

    def __init__(self) -> None:
        self._recorded_queries: list[DNSSignallingEvent] = []

    def is_domain_allowed(self, domain: str) -> bool:
        """Check whether destination domain matches lab safety allowlists."""
        domain_lower = domain.lower()
        return any(pattern.match(domain_lower) for pattern in self.ALLOWED_DOMAIN_PATTERNS)

    def record_query(
        self,
        run_id: str,
        technique_id: str,
        subdomain_token: str,
        base_domain: str = "c2.lab.falconstrike.internal",
        query_type: str = "TXT",
    ) -> DNSSignallingEvent:
        """Record and resolve a simulated benign DNS signalling query."""
        full_query = f"{subdomain_token}.{base_domain}"

        if not self.is_domain_allowed(full_query):
            raise FalconSecurityException(
                f"DNS signalling blocked: Query domain '{full_query}' is outside the authorized lab domain allowlist."
            )

        marker_token = f"FALCON_DNS_TOKEN_{subdomain_token.upper()}"
        simulated_response = f"v=falcon-ack;status=acknowledged;marker={marker_token}"

        event = DNSSignallingEvent(
            run_id=run_id,
            technique_id=technique_id,
            query_name=full_query,
            query_type=query_type,
            simulated_response=simulated_response,
            marker_token=marker_token,
        )

        self._recorded_queries.append(event)
        logger.info(
            f"Benign DNS Signalling query recorded: {query_type} {full_query} -> {simulated_response} [run_id={run_id}]"
        )
        return event

    def get_queries_for_run(self, run_id: str) -> list[DNSSignallingEvent]:
        """Retrieve recorded DNS queries for a given run ID."""
        return [q for q in self._recorded_queries if q.run_id == run_id]

    def list_all_queries(self) -> list[DNSSignallingEvent]:
        """Retrieve all recorded DNS queries."""
        return list(self._recorded_queries)

    def clear(self) -> None:
        """Clear recorded DNS query history."""
        self._recorded_queries.clear()


dns_sink = BenignDNSSink()
