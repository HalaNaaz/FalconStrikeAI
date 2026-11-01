"""Benign Command & Control (C2) signalling sink with configurable beaconing and jitter (FR-3.4)."""

import random

from backend.app.core.exceptions import FalconSecurityException
from backend.app.core.logging import logger
from backend.app.telemetry.models import C2BeaconEvent


class BenignC2Sink:
    """Simulates benign adversary C2 communications strictly contained within lab environments.

    Containment Guarantees:
    - Never communicates with external, non-whitelisted internet addresses.
    - Default destination is restricted to localhost (127.0.0.1).
    - All payloads carry unmistakable benign identification markers.
    - Zero data exfiltration capability.
    """

    ALLOWED_DESTINATIONS: set[str] = {"127.0.0.1", "localhost", "c2.lab.falconstrike.internal"}

    def __init__(
        self,
        default_interval_seconds: float = 5.0,
        default_jitter_percentage: float = 20.0,
    ) -> None:
        self.default_interval = default_interval_seconds
        self.default_jitter = default_jitter_percentage
        self._recorded_beacons: list[C2BeaconEvent] = []

    @staticmethod
    def calculate_jitter_delay(
        base_interval: float,
        jitter_percentage: float,
        seed: int | None = None,
    ) -> float:
        """Calculate next beacon delay applying bounded jitter.

        Formula:
            delay = base_interval * (1 + delta)
            where delta in [-jitter_percentage / 100, +jitter_percentage / 100]
        """
        rng = random.Random(seed) if seed is not None else random
        max_delta = max(0.0, min(100.0, jitter_percentage)) / 100.0
        delta = rng.uniform(-max_delta, max_delta)
        delay = base_interval * (1.0 + delta)
        return max(0.1, round(delay, 3))

    def emit_beacon(
        self,
        run_id: str,
        technique_id: str,
        destination_host: str = "127.0.0.1",
        destination_port: int = 8443,
        protocol: str = "HTTPS",
        interval_seconds: float | None = None,
        jitter_percentage: float | None = None,
        seed: int | None = None,
    ) -> C2BeaconEvent:
        """Emit a simulated benign beacon to the local sink."""
        # Enforce destination containment
        if destination_host not in self.ALLOWED_DESTINATIONS:
            raise FalconSecurityException(
                f"C2 egress blocked: Destination host '{destination_host}' is outside the authorized lab allowlist."
            )

        interval = interval_seconds if interval_seconds is not None else self.default_interval
        jitter = jitter_percentage if jitter_percentage is not None else self.default_jitter
        actual_delay = self.calculate_jitter_delay(interval, jitter, seed=seed)

        marker_payload = f"FALCON_BENIGN_MARKER_{technique_id}_{run_id}"

        beacon = C2BeaconEvent(
            run_id=run_id,
            technique_id=technique_id,
            destination_host=destination_host,
            destination_port=destination_port,
            protocol=protocol,
            interval_seconds=interval,
            jitter_percentage=jitter,
            actual_delay_seconds=actual_delay,
            marker_payload=marker_payload,
        )

        self._recorded_beacons.append(beacon)
        logger.info(
            f"Benign C2 Beacon recorded: technique={technique_id}, dst={destination_host}:{destination_port}, "
            f"interval={interval}s, delay={actual_delay}s [run_id={run_id}]"
        )
        return beacon

    def get_beacons_for_run(self, run_id: str) -> list[C2BeaconEvent]:
        """Retrieve all recorded beacons for a specific campaign run."""
        return [b for b in self._recorded_beacons if b.run_id == run_id]

    def list_all_beacons(self) -> list[C2BeaconEvent]:
        """Retrieve all recorded beacons."""
        return list(self._recorded_beacons)

    def clear(self) -> None:
        """Clear the in-memory beacon sink."""
        self._recorded_beacons.clear()


c2_sink = BenignC2Sink()
