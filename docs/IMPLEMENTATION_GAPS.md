# Falcon Strike-AI — Implementation Gap Analysis & Risk Assessment

**Document Version:** 1.0.0  
**Date:** 2026-11-01  
**Target Deadline:** 2026-11-06  
**Reference PRD:** `e11724cd68ee47cfbfbbbae0fd804c6e.pdf`

---

## 1. Executive Summary

This document details the delta between the current state of the workspace (clean baseline with PRD specification) and the required deliverables outlined in the Project Falcon Strike-AI PRD. The original PRD envisions a 4-week internship scope; however, our submission deadline is **6 November 2026 (5 development days remaining)**.

To deliver an uncompromised, verifiable, and production-shaped vertical slice by 6 November without cutting safety corners or faking deliverables, we explicitly map each subsystem, analyze capability gaps, classify risk, and establish realistic deliverables for the 5-day execution window.

---

## 2. Subsystem Gap Analysis

### 2.1 AWS Environment Ingestion (Collectors)
- **PRD Requirement:** Live read-only enumeration of IAM, network exposure, and compute-to-identity bindings via official SDK (FR-1.1, FR-1.2, FR-1.3).
- **Current State:** Zero code; AWS CLI session expired; no live lab account provisioned.
- **Identified Gap:** The system cannot rely exclusively on a live AWS account for testing and continuous evaluation.
- **5-Day Strategy:**
  - Build the real Boto3 collector with strict read-only calls (`iam:ListUsers`, `iam:ListRoles`, `iam:GetPolicy`, `ec2:DescribeSecurityGroups`, `s3:GetBucketPolicy`, etc.).
  - Implement a `SyntheticTopologyProvider` capable of loading realistic, intentionally-flawed enterprise cloud topologies (JSON/YAML) mirroring exact Boto3 responses.
  - Deliverable: Ingestion engine supporting both live Boto3 credentials and offline synthetic topologies.

### 2.2 Property Graph & Attack Path Analysis
- **PRD Requirement:** Neo4j property graph modeling principals, roles, resources, and endpoints; Cypher queries computing ranked attack paths; sub-second query performance at 10,000+ nodes (FR-1.4, FR-1.5, FR-1.6, FR-1.7, NFR-P1, NFR-P2).
- **Current State:** Zero code; Neo4j server not running on host; python `neo4j` driver not installed.
- **Identified Gap:** Running a full Neo4j cluster locally requires either running Docker Desktop or an external cloud instance (e.g. Neo4j AuraDB).
- **5-Day Strategy:**
  - Define an abstract `GraphStore` interface.
  - Implement `Neo4jGraphStore` using Cypher queries for live Neo4j instances.
  - Implement `InMemoryGraphStore` leveraging an adjacency graph model (using NetworkX or pure Python graph algorithms) with Cypher-compatible semantics.
  - Provide a scale benchmark script generating a 10,000+ node graph verifying p95 traversal latency < 1 second.

### 2.3 LLM Campaign Planner & Guardrail Policy Gate
- **PRD Requirement:** LLM planner consumes ranked paths and outputs schema-validated JSON campaigns from an approved library; guardrail policy engine enforces account allowlists, auth tokens, and destructiveness checks (FR-2.1 to FR-2.6, NFR-S1 to NFR-S5).
- **Current State:** Zero code.
- **Identified Gap:** External LLM APIs can be flaky, rate-limited, or unavailable without paid API keys.
- **5-Day Strategy:**
  - Develop a strict Pydantic campaign schema with full validation.
  - Create a dual-mode planner:
    1. `LLMCampaignPlanner`: Integrates with LLM APIs using structured outputs.
    2. `DeterministicCampaignPlanner`: Uses graph-driven rules to deterministically select optimal techniques from the allowlisted library.
  - Build the Policy Gate enforcing compiled allowlist checks, HMAC/JWT authorization tokens, and blast-radius caps in code before any action can be scheduled.

### 2.4 Ephemeral Sandbox Execution & C2 Signalling
- **PRD Requirement:** Ephemeral container runners (Kubernetes Jobs / Docker) with constrained egress, scoped credentials, non-destructive behavioral emulation across 12-15 ATT&CK techniques, jittered HTTPS/DNS beaconing to lab sinks, and inert marker payloads (FR-3.1 to FR-4.4).
- **Current State:** Zero code; Docker daemon inactive on host.
- **Identified Gap:** Full Kubernetes cluster orchestration cannot be guaranteed in local development environments.
- **5-Day Strategy:**
  - Implement `SandboxRunner` abstraction.
  - Provide a Docker runner implementation and an isolated in-process `SubprocessRunner` with environment scrubbing and execution timeout controls.
  - Build the 12 curated ATT&CK technique modules using inert markers and reversible operations.
  - Implement an asynchronous local HTTP/DNS C2 sink service that collects jittered beacon callbacks and records ground-truth IOCs.

### 2.5 Telemetry, Detection Correlation & SOC Reporting
- **PRD Requirement:** OpenTelemetry tracing, append-only hash-chained JSON audit log, correlation with SIEM/EDR, and SOC detection-validation report with ATT&CK heatmap and MTTD (FR-5.1 to FR-5.3, NFR-A1 to NFR-A4).
- **Current State:** Zero code.
- **Identified Gap:** Production SIEM/EDR (CrowdStrike Falcon / Splunk) is not available locally.
- **5-Day Strategy:**
  - Implement the cryptographic hash-chained audit logger (SHA-256 blocks with sequence numbers and run IDs).
  - Build an embedded `DetectionStub` that matches emitted ground-truth IOCs and ATT&CK technique IDs against configurable detection rules (with simulated detection latencies).
  - Build a multi-format SOC Report Generator producing structured JSON, Markdown, and rich HTML with visual ATT&CK coverage heatmaps.

---

## 3. High-Risk Implementation Areas

| Risk Area | Severity | Root Cause | Mitigation |
| :--- | :--- | :--- | :--- |
| **1. Unsafe Cloud Execution** | **CRITICAL** | Accidental live operations against real accounts. | Hardcoded compiled account allowlist checked at process start; dry-run default; mandatory JWT auth token. |
| **2. Scale Latency (10k+ nodes)** | **HIGH** | Unindexed graph traversals causing timeouts. | Indexed node label lookups and breadth-first search path pruning with depth bounds. |
| **3. LLM Hallucination / Schema Drift** | **HIGH** | LLM generating arbitrary commands or invalid JSON. | Model plans as data only (no shell access); Pydantic schema validation rejects non-conforming responses immediately. |
| **4. Docker Daemon Dependency** | **MEDIUM** | Inability to run Docker containers if daemon is down. | Fallback runner executes in isolated, time-boxed local subprocess with inert marker cleanup. |
| **5. Audit Log Tampering** | **MEDIUM** | Log corruption or missing causality. | Cryptographic SHA-256 hash chaining where record `N` includes `hash(N-1)`. |

---

## 4. Five-Day Delivery Feasibility Matrix

```
┌───────────┬─────────────────────────────────────────────────────────────┬─────────────┐
│ Day       │ Planned Focus Area                                          │ Status      │
├───────────┼─────────────────────────────────────────────────────────────┼─────────────┤
│ **Day 1** │ PRD Analysis, Architecture Docs, Repo Foundation, Health API│ IN PROGRESS │
│ **Day 2** │ Cloud Collectors, Graph Modeling, Attack-Path Finder & Scale│ UPCOMING    │
│ **Day 3** │ LLM Planner, Technique Library (12 TTPs), Policy Gate Engine│ UPCOMING    │
│ **Day 4** │ Ephemeral Sandbox Runner, C2 Beacon Sink, Teardown Engine   │ UPCOMING    │
│ **Day 5** │ Hash-Chained Audit, Detection Stub, SOC Report, E2E Suite   │ UPCOMING    │
│ **Day 6** │ Final Verification, Performance Benchmarks & Submission Pack│ UPCOMING    │
└───────────┴─────────────────────────────────────────────────────────────┴─────────────┘
```

