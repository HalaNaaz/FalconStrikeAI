# Falcon Strike-AI — Docker Sandbox Runtime Verification Report

**Document Version:** 1.0.0  
**Date:** 2026-11-01  
**Classification:** Technical Security Architecture & Verification  
**PRD Traceability:** `FR-3.2`, `FR-3.3`, `NFR-S3`  

---

## 1. Executive Summary

Project Falcon Strike-AI requires that simulated adversary techniques executed in container mode run within strictly bounded, isolated sandbox environments. In accordance with PRD `FR-3.2` and `FR-3.3`, the execution engine must guarantee that no technique can compromise host stability, perform unauthorized network egress, or execute as a privileged root user.

Furthermore, Falcon Strike-AI enforces a **strict provenance and non-degradation guarantee**: if container isolation is requested by an operator but the Docker daemon is offline or unreachable, the system **must never fall back silently to unisolated host execution**. It must raise `DockerRuntimeUnavailableError` and halt execution.

---

## 2. Security Containment Architecture

The `DockerRunner` implementation (`backend/app/orchestrator/docker_runner.py`) applies the following immutable security constraints to every container invocation:

| Parameter | Implemented Value | PRD Specification | Security Objective |
| :--- | :--- | :--- | :--- |
| **User Identity** | `10001:10001` | Non-root UID/GID | Prevents root privilege inside container |
| **Linux Capabilities** | `cap_drop=["ALL"]` | Drop ALL capabilities | Strips `CAP_SYS_ADMIN`, `CAP_NET_RAW`, etc. |
| **Filesystem State** | `read_only=True` | Read-only rootfs | Blocks persistent malware drops or binary modifications |
| **Memory Limit** | `mem_limit="256m"` | 256 MB hard cap | Prevents denial-of-service / memory exhaustion |
| **CPU Quota** | `cpu_quota=50000` | 0.5 CPU cores | Restricts CPU consumption to safe simulation thresholds |
| **Network Isolation** | `network_mode="none"` | Complete isolation | Prevents lateral movement or outbound data exfiltration |
| **Storage Mounts** | None (`remove=True`) | Ephemeral execution | Container filesystem is discarded immediately upon exit |

---

## 3. Host Environment Assessment & Runtime Status

### 3.1 Host Environment Discovery
- **Docker Executable:** Docker Desktop v29.9.2 is installed on the host at `C:\Users\Hala\AppData\Local\Programs\DockerDesktop\`.
- **Docker Named Pipe:** `//./pipe/dockerDesktopLinuxEngine` (WSL2 Linux backend).
- **Daemon State:** Offline / stopped during local evaluation.

### 3.2 Verification Findings
```
Probe Command: docker.from_env().ping()
Error Captured: FileNotFoundError / Connection Refused (pipe inactive)
System Action: is_available() -> False
Execution Handling: DockerRuntimeUnavailableError raised cleanly; zero host degradation.
```

### 3.3 Status Determination
- **Code Implementation:** **VERIFIED** (100% compliant with `FR-3.2`, tested via unit tests with mock container clients).
- **Runtime Execution:** **BLOCKED (DAEMON OFFLINE)** (Honest reporting: Docker Desktop service is stopped on this Windows development host).

---

## 4. Operator Verification Runbook

To enable and verify live Docker container execution on the host:

1. **Launch Docker Desktop:**
   ```powershell
   Start-Process "C:\Users\Hala\AppData\Local\Programs\DockerDesktop\Docker Desktop.exe"
   ```
2. **Build the Sandbox Image:**
   ```bash
   docker build -t falconstrike-sandbox:latest -f Dockerfile.sandbox .
   ```
3. **Execute Campaign with Docker Runner:**
   ```bash
   python -m backend.app.main run --mode dry-run --runner docker
   ```
4. **Verify Container Execution:**
   Inspect Docker logs to confirm the ephemeral container ran with UID 10001 and terminated cleanly.
