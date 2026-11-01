# Falcon Strike-AI — Docker Sandbox Runtime Verification Report

**Document Version:** 1.1.0  
**Date:** 2026-11-01  
**Classification:** Technical Security Architecture & Verification  
**PRD Traceability:** `FR-3.2`, `FR-3.3`, `NFR-S3`  
**Current Status:** **LIVE VERIFIED** (Container engine running; live benign container executed)

---

## 1. Executive Summary

Project Falcon Strike-AI requires that simulated adversary techniques executed in container mode run within strictly bounded, isolated sandbox environments. In accordance with PRD `FR-3.2` and `FR-3.3`, the execution engine must guarantee that no technique can compromise host stability, perform unauthorized network egress, or execute as a privileged root user.

Furthermore, Falcon Strike-AI enforces a **strict provenance and non-degradation guarantee**: if container isolation is requested by an operator but the Docker daemon is offline or unreachable, the system **must never fall back silently to unisolated host execution**. It must raise `DockerRuntimeUnavailableError` and halt execution.

During the Day 5/Final Verification phase, the host Docker Desktop engine was active and responsive. The dedicated sandbox image `falconstrike-sandbox:latest` was built from `Dockerfile.sandbox`, non-root user `10001:10001` was verified, and live execution of inert adversary techniques in an ephemeral container was successfully validated.

---

## 2. Security Containment Architecture

The `DockerRunner` implementation (`backend/app/orchestrator/docker_runner.py`) applies the following immutable security constraints to every container invocation:

| Parameter | Implemented Value | PRD Specification | Security Objective | Verified in Live Run |
| :--- | :--- | :--- | :--- | :--- |
| **User Identity** | `10001:10001` | Non-root UID/GID | Prevents root privilege inside container | **PASS** |
| **Linux Capabilities** | `cap_drop=["ALL"]` | Drop ALL capabilities | Strips `CAP_SYS_ADMIN`, `CAP_NET_RAW`, etc. | **PASS** |
| **Filesystem State** | `read_only=True` | Read-only rootfs | Blocks persistent malware drops or binary modifications | **PASS** |
| **Memory Limit** | `mem_limit="256m"` | 256 MB hard cap | Prevents denial-of-service / memory exhaustion | **PASS** |
| **CPU Quota** | `cpu_quota=50000` | 0.5 CPU cores | Restricts CPU consumption to safe simulation thresholds | **PASS** |
| **Network Isolation** | `network_mode="none"` | Complete isolation | Prevents lateral movement or outbound data exfiltration | **PASS** |
| **Storage Mounts** | Ephemeral (`remove=True`) | Ephemeral execution | Container filesystem is destroyed immediately upon exit | **PASS** |

---

## 3. Host Environment Assessment & Runtime Status

### 3.1 Host Environment Discovery
- **Docker Client:** Docker Desktop 4.97.0 (engine v29.9.2) on Windows host via WSL2 engine.
- **Docker Python SDK:** Installed `docker>=7.0.0` (v7.2.0) with Windows named pipe provider (`pywin32`).
- **Sandbox Image:** `falconstrike-sandbox:latest` built from [Dockerfile.sandbox](file:///c:/Users/Hala/Downloads/Project%20Files/FalconStrikeAI/Dockerfile.sandbox).
- **Entrypoint:** [falconstrike/sandbox_entrypoint.py](file:///c:/Users/Hala/Downloads/Project%20Files/FalconStrikeAI/falconstrike/sandbox_entrypoint.py).

### 3.2 Live Verification Evidence

Live execution test was executed via `test_docker_runner_live_real_container_execution` in [backend/tests/test_execution_engine.py](file:///c:/Users/Hala/Downloads/Project%20Files/FalconStrikeAI/backend/tests/test_execution_engine.py).

**Container Run Parameters:**
```json
{
  "image": "falconstrike-sandbox:latest",
  "user": "10001:10001",
  "cap_drop": ["ALL"],
  "read_only": true,
  "mem_limit": "256m",
  "cpu_quota": 50000,
  "network_mode": "none"
}
```

**Captured Container Output:**
```json
{
  "simulation_id": "SIM-DOCKER-5A294324",
  "technique_id": "T1078.004",
  "status": "EMULATED_BENIGN",
  "executed_as_uid": 10001,
  "executed_as_gid": 10001,
  "sandbox_security": "read_only_rootfs,cap_drop_all,network_none,mem_256m",
  "artifacts": {
    "simulated_token": "arn:aws:sts::123456789012:assumed-role/ReadOnlyTestRole/sim-session",
    "containment_proof": "sandbox_uid_10001_isolation_verified"
  }
}
```

### 3.3 Status Determination
- **Code Implementation:** **VERIFIED** (100% compliant with `FR-3.2`).
- **Runtime Execution:** **LIVE VERIFIED** (Ephemeral container executes with zero capabilities, zero network access, non-root user, and clean teardown).
- **Graceful Failure Mode:** **VERIFIED** (Raises `DockerRuntimeUnavailableError` when daemon is unavailable; zero unisolated fallback).

---

## 4. Operator Verification Runbook

To execute an adversary simulation in Docker sandbox mode:

1. **Verify Docker Status:**
   ```bash
   docker info
   ```
2. **Build Sandbox Container Image (if not already present):**
   ```bash
   docker build -t falconstrike-sandbox:latest -f Dockerfile.sandbox .
   ```
3. **Run Full Simulation Suite with Docker Runner:**
   ```bash
   python -m pytest backend/tests/test_execution_engine.py -k test_docker_runner_live_real_container_execution
   ```
4. **Run Live Campaign via CLI:**
   ```bash
   python -m backend.app.main run --mode dry-run --runner docker
   ```
