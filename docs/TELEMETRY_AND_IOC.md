# Falcon Strike-AI: Telemetry, Benign C2 & Synthetic IOCs (Phase 11)

## Overview

Adversary emulation requires verifiable observable signals so that Detection Engineering teams and SOC analysts can validate security monitoring coverage. Under **FR-3.4**, Project Falcon Strike-AI provides an integrated telemetry, command-and-control (C2) signalling, and synthetic Indicator of Compromise (IOC) generation subsystem.

All telemetry generated is strictly benign, deterministic, and unmistakably flagged as lab emulation traffic to prevent confusion with authentic adversary activity.

---

## Architectural Components

```
┌────────────────────────────────────────────────────────────────────────┐
│                        Execution Engine Run                            │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │ Emits technique signals
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│                  Telemetry & Observable Collection                     │
├──────────────────────┬──────────────────────┬──────────────────────────┤
│    BenignC2Sink      │    BenignDNSSink     │  SyntheticIOCGenerator   │
│  (Periodic Beacons   │  (Simulated TXT/DNS  │ (Deterministic Artifacts │
│    with Jitter)      │    Covert Channel)   │       and Markers)       │
└──────────┬───────────┴──────────┬───────────┴────────────┬─────────────┘
           │                      │                        │
           └──────────────────────┼────────────────────────┘
                                  ▼
┌────────────────────────────────────────────────────────────────────────┐
│                          TelemetryCollector                            │
│                 (Thread-Safe In-Memory Event Sink)                     │
└─────────────────────────────────┬──────────────────────────────────────┘
                                  │ JSON Serialization
                                  ▼
┌────────────────────────────────────────────────────────────────────────┐
│                        TelemetryExportPackage                          │
│               (Consolidated Security Validation Export)                │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 1. Benign Command & Control (C2) Signalling (`backend/app/telemetry/c2_sink.py`)

Adversaries establish command-and-control channels characterized by periodic check-ins ("heartbeats" or "beacons") with randomized timing variations ("jitter") to evade beacon-detection algorithms.

### Safety Containment Guarantees
- **Localhost Bound**: By default, beacons target loopback `127.0.0.1:8443` or configured internal lab endpoints (`c2.lab.falconstrike.internal`).
- **Strict Destination Allowlist**: Any destination outside the allowlist raises `FalconSecurityException` and blocks egress immediately.
- **Zero Real Traffic**: Zero outbound connections to unauthorized external internet infrastructure.
- **Inert Markers**: Every beacon embeds an immutable benign marker: `FALCON_BENIGN_MARKER_<TECHNIQUE_ID>_<RUN_ID>`.

### Jitter Calculation
The next beacon delay is computed using bounded uniform randomization:
$$\text{Delay} = \text{BaseInterval} \times \left(1 + \delta\right)$$
where $\delta \in \left[-\frac{\text{JitterPct}}{100}, +\frac{\text{JitterPct}}{100}\right]$.

- Default Base Interval: $5.0\text{ seconds}$
- Default Jitter: $\pm 20.0\%$ (delays bounded between $4.0\text{s}$ and $6.0\text{s}$)
- Deterministic seed support is provided for unit testing and reproducible simulation scenarios.

---

## 2. Benign DNS Signalling Sink (`backend/app/telemetry/dns_sink.py`)

Covers MITRE ATT&CK techniques **T1071.004** (Application Layer Protocol: DNS) and **T1572** (Protocol Tunneling).

### Operational Characteristics
- Queries are constructed using format: `<marker_token>.<technique_id>.c2.lab.falconstrike.internal`.
- Validates all destination domain queries against an internal lab regex allowlist (`*.lab.falconstrike.internal`, `*.internal`, `localhost`).
- Resolves queries to simulated benign `TXT` response records:
  ```
  v=falcon-ack;status=acknowledged;marker=FALCON_DNS_TOKEN_<TOKEN>
  ```
- No public recursive DNS resolvers are queried.

---

## 3. Synthetic IOC Generator (`backend/app/telemetry/ioc_generator.py`)

Generates multi-attribute security observables tailored to each executed technique stage:

| IOC Type | Format / Example | Purpose / Detection Guidance |
| :--- | :--- | :--- |
| **`SHA256`** | `hashlib.sha256(b"FALCON_BENIGN_PAYLOAD_T1078_...").hexdigest()` | Alert on file write events matching synthetic payload fingerprint. |
| **`USER_AGENT`** | `FalconStrike-AI/1.0 (Emulation; Technique=T1078; Run=RUN-...)` | Check CloudTrail/web proxy logs for automated agent user-agent header. |
| **`IP_ADDRESS`** | `192.0.2.55` (RFC 5737 TEST-NET-1 documentation prefix) | Check VPC Flow logs for connection attempts from documentation IPs. |
| **`FILE_PATH`** | `/tmp/falcon_marker_T1078_RUN12345.tmp` | Monitor endpoint EDR logs for benign marker files in temporary paths. |
| **`API_CALL`** | `AssumeRole:arn:aws:iam::000000000000:role/AdminRole` | Flag unusual `AssumeRole` API calls targeting critical roles. |

Every synthetic IOC object sets `is_benign_marker=True` and includes an actionable detection engineering guidance string.

---

## 4. Telemetry Collector & Export Package (`backend/app/telemetry/collector.py`)

The `TelemetryCollector` aggregates:
1. Raw `SimulationEvent` records emitted during stage execution.
2. `C2BeaconEvent` logs from the C2 sink.
3. `DNSSignallingEvent` logs from the DNS sink.
4. `SyntheticIOC` records from the IOC generator.

### Export Format (`TelemetryExportPackage`)

```json
{
  "export_id": "EXP-B9E4C118",
  "run_id": "api-telemetry-run",
  "campaign_id": "CAMP-39867FB6",
  "generated_at": "2026-11-01T10:44:22.227981+00:00",
  "total_events": 8,
  "c2_beacons": [
    {
      "beacon_id": "BCN-1F92B3C4",
      "run_id": "api-telemetry-run",
      "technique_id": "T1071",
      "destination_host": "127.0.0.1",
      "destination_port": 8443,
      "protocol": "HTTPS",
      "interval_seconds": 5.0,
      "jitter_percentage": 20.0,
      "actual_delay_seconds": 5.14,
      "marker_payload": "FALCON_BENIGN_MARKER_T1071_api-telemetry-run",
      "timestamp": "2026-11-01T10:44:22.227482+00:00"
    }
  ],
  "dns_queries": [],
  "iocs": [
    {
      "ioc_id": "IOC-77A19B22",
      "run_id": "api-telemetry-run",
      "technique_id": "T1078",
      "ioc_type": "SHA256",
      "value": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
      "is_benign_marker": true,
      "detection_guidance": "Alert on file writes matching SHA256 (benign emulation payload)."
    }
  ],
  "raw_events": [],
  "summary": {
    "total_events": 8,
    "raw_simulation_events": 2,
    "synthetic_iocs": 5,
    "c2_beacons": 1,
    "dns_signalling_queries": 0
  }
}
```

---

## API Endpoints

- `GET /api/v1/telemetry/events?run_id={run_id}`: Query raw simulation telemetry for a run.
- `GET /api/v1/telemetry/iocs?run_id={run_id}`: Query synthetic IOCs.
- `GET /api/v1/telemetry/c2-beacons`: Query recorded C2 beacon events.
- `GET /api/v1/telemetry/dns-queries`: Query recorded DNS signalling queries.
- `GET /api/v1/telemetry/export?run_id={run_id}`: Export consolidated telemetry package as JSON.

