"""Deterministic synthetic IOC generator for detection engineering validation (FR-3.4)."""

import hashlib
from typing import Any

from backend.app.telemetry.models import IOCType, SyntheticIOC


class SyntheticIOCGenerator:
    """Generates verifiable, benign synthetic IOCs correlated with specific campaign stages and techniques."""

    @staticmethod
    def generate_iocs_for_stage(
        run_id: str,
        technique_id: str,
        target_resource_id: str,
        parameters: dict[str, Any] | None = None,
    ) -> list[SyntheticIOC]:
        """Generate a suite of safe, deterministic synthetic IOCs for an emulation stage."""
        iocs: list[SyntheticIOC] = []

        # 1. Deterministic benign SHA-256 hash
        seed_data = f"FALCON_BENIGN_PAYLOAD_{technique_id}_{run_id}"
        payload_hash = hashlib.sha256(seed_data.encode("utf-8")).hexdigest()
        iocs.append(
            SyntheticIOC(
                run_id=run_id,
                technique_id=technique_id,
                ioc_type=IOCType.SHA256,
                value=payload_hash,
                is_benign_marker=True,
                detection_guidance=f"Alert on file writes matching SHA256 '{payload_hash}' (benign emulation payload).",
            )
        )

        # 2. Benign User-Agent
        user_agent = f"FalconStrike-AI/1.0 (Emulation; Technique={technique_id}; Run={run_id})"
        iocs.append(
            SyntheticIOC(
                run_id=run_id,
                technique_id=technique_id,
                ioc_type=IOCType.USER_AGENT,
                value=user_agent,
                is_benign_marker=True,
                detection_guidance="Monitor CloudTrail and proxy logs for automated agent user agent header.",
            )
        )

        # 3. Safe RFC 5737 documentation IP
        rfc_ip = "192.0.2.55"  # TEST-NET-1 (RFC 5737) reserved strictly for documentation/testing
        iocs.append(
            SyntheticIOC(
                run_id=run_id,
                technique_id=technique_id,
                ioc_type=IOCType.IP_ADDRESS,
                value=rfc_ip,
                is_benign_marker=True,
                detection_guidance="Check VPC Flow logs or ingress logs for connection attempts from documentation IP.",
            )
        )

        # 4. Safe inert marker file path
        marker_path = f"/tmp/falcon_marker_{technique_id}_{run_id[:8]}.tmp"
        iocs.append(
            SyntheticIOC(
                run_id=run_id,
                technique_id=technique_id,
                ioc_type=IOCType.FILE_PATH,
                value=marker_path,
                is_benign_marker=True,
                detection_guidance="Audit endpoint EDR logs for file creation in /tmp matching benign marker prefix.",
            )
        )

        # 5. Simulated API call IOC
        api_call = f"AssumeRole:{target_resource_id}"
        iocs.append(
            SyntheticIOC(
                run_id=run_id,
                technique_id=technique_id,
                ioc_type=IOCType.API_CALL,
                value=api_call,
                is_benign_marker=True,
                detection_guidance="Flag unusual AssumeRole API calls targeting sensitive IAM role outside business hours.",
            )
        )

        return iocs

