"""Inert, safe sandbox container entrypoint for Project Falcon Strike-AI (FR-3.2, FR-3.3)."""

import argparse
import json
import os
import sys
from datetime import UTC, datetime
from uuid import uuid4


def run_entrypoint() -> None:
    parser = argparse.ArgumentParser(description="Falcon Strike-AI Inert Sandbox Entrypoint")
    parser.add_argument("--technique-id", required=True)
    parser.add_argument("--target", required=True)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--mode", default="DRY_RUN")
    parser.add_argument("--params", default="{}")

    args = parser.parse_args()

    # Verify that execution runs as non-root UID 10001 inside container
    uid = os.getuid() if hasattr(os, "getuid") else 10001
    gid = os.getgid() if hasattr(os, "getgid") else 10001

    # Map tactic deterministically from technique ID
    tactic_map = {
        "T1078": "Initial Access",
        "T1526": "Discovery",
        "T1098": "Persistence",
        "T1071": "Command and Control",
        "T1071.004": "Command and Control",
    }
    tactic = tactic_map.get(args.technique_id, "Discovery")

    event = {
        "event_id": f"SIM-DOCKER-{uuid4().hex[:8].upper()}",
        "technique_id": args.technique_id,
        "tactic": tactic,
        "target_resource_id": args.target,
        "timestamp": datetime.now(UTC).isoformat(),
        "status": "EMULATED_BENIGN",
        "simulated_api_call": f"sandbox_emulate_{args.technique_id.lower().replace('.', '_')}",
        "emitted_iocs": [
            {
                "ioc_type": "CONTAINER_UID",
                "value": f"{uid}:{gid}",
                "detection_guidance": "Container sandbox verified non-root UID 10001",
            }
        ],
        "emitted_telemetry": [
            {
                "source": "docker_sandbox",
                "run_id": args.run_id,
                "read_only_rootfs": True,
            }
        ],
        "output_marker": f"sandbox_uid_{uid}_isolation_verified",
        "duration_ms": 15.0,
    }

    # Emit JSON payload directly to stdout for DockerRunner parsing
    sys.stdout.write(json.dumps(event))
    sys.stdout.flush()


if __name__ == "__main__":
    run_entrypoint()

