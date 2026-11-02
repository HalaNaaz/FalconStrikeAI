# Falcon Strike-AI: Final Functional Requirements (FR) Compliance Matrix
**Document Version:** 1.0.0  
**Audit Date:** November 2, 2026  
**Auditor:** Principal Software Architect & QA Auditor  
**Authoritative Reference:** CrowdStrike Adversary Emulation PRD v1.0, Section 6 (Pages 8–11)  

---

## 1. Executive Summary

This matrix assesses the complete implementation of all 26 Functional Requirements (FR-1.1 through FR-5.3) defined in Section 6 of the original PRD. Each requirement is mapped to its exact source file, automated test file, live execution result, and closure status.

---

## 2. Domain 1: Attack-Path Graphing (FR-1.1 to FR-1.7)

| Req ID | PRD Requirement Text | Priority | Status | Source File | Test File & Result | Evidence & Notes |
| :--- | :--- | :---: | :---: | :--- | :--- | :--- |
| **FR-1.1** | Ingest IAM principals, roles, policies and assume-role / trust relationships via official cloud SDKs (read-only). | **MUST** | **PASS** | `backend/app/collectors/aws_iam.py` | `test_collectors.py` (PASS) | Uses `boto3.client("iam")`. Discovered 12 IAM roles in live account `318432260788`. Offline synthetic fallback verified. |
| **FR-1.2** | Ingest network exposure: public endpoints, security-group rules, open ports, public buckets/objects and exposed services. | **MUST** | **PASS** | `backend/app/collectors/aws_network.py`, `aws_s3.py` | `test_collectors.py` (PASS) | Discovered SG `sg-0a6f7e0285f302ed5` in live AWS account. Synthetic provider handles public S3 & EC2 endpoints. |
| **FR-1.3** | Ingest compute-to-identity bindings (instance profiles, service roles) linking workloads to permissions. | **MUST** | **PASS** | `backend/app/collectors/aws_network.py` | `test_collectors.py` (PASS) | Parses `IamInstanceProfile` associations and links EC2 instance nodes to IAM Roles via `RUNS_AS` edges. |
| **FR-1.4** | Model the environment as a property graph — nodes (principals, roles, policies, resources, endpoints) and edges (can-assume, has-permission, trusts, exposes, bound-to, member-of). | **MUST** | **PASS** | `backend/app/graph/models.py`, `store.py` | `test_graph.py` (PASS) | Property graph supports 10 node types and 8 relationship types using NetworkX in-memory and Neo4j Cypher export. |
| **FR-1.5** | Label misconfiguration patterns as graph properties/edges: wildcard permissions, known privilege-escalation primitives, and public exposure. | **MUST** | **PASS** | `backend/app/graph/enrichment.py` | `test_graph.py` (PASS) | Detects wildcard actions (`*`), Rhino Security Labs privesc primitives (`iam:PassRole`, `iam:CreatePolicyVersion`), open SGs. |
| **FR-1.6** | Compute attack paths from a defined low-privilege / internet-reachable entry node to high-value targets (admin roles, sensitive data stores). | **MUST** | **PASS** | `backend/app/graph/path_finder.py` | `test_attack_paths.py` (PASS) | Breadth-first / depth-first traversal discovers multi-hop paths to crown jewel nodes with cycle protection. |
| **FR-1.7** | Rank computed paths by exploitability and impact, producing a prioritised list for the planner. | **SHOULD**| **PASS** | `backend/app/graph/path_ranker.py` | `test_attack_paths.py` (PASS) | Composite scoring algorithm penalizes hop distance, weights target criticality, and scores permission severity (0-100 scale). |

---

## 3. Domain 2: Autonomous Campaign Generation (LLM Agent) (FR-2.1 to FR-2.6)

| Req ID | PRD Requirement Text | Priority | Status | Source File | Test File & Result | Evidence & Notes |
| :--- | :--- | :---: | :---: | :--- | :--- | :--- |
| **FR-2.1** | An LLM planner consumes a ranked attack path and environment facts and produces an ordered, multi-stage campaign mapped to ATT&CK tactics and techniques. | **MUST** | **PASS** | `backend/app/planner/planner.py`, `providers.py` | `test_planner.py` (PASS) | Dual-mode: Google Gemini API via official `google-genai` SDK (`gemini-flash-latest`) + deterministic offline heuristic engine. |
| **FR-2.2** | The planner may select only techniques present in the approved, safe technique library (allowlist); it cannot invent, request, or execute arbitrary commands. | **MUST** | **PASS** | `backend/app/planner/validation.py`, `techniques/registry.py` | `test_planner.py` (PASS) | Static 16-technique enum validation. Unknown technique strings immediately raise `SafetyPolicyViolationError`. |
| **FR-2.3** | Tool-use architecture: the planner emits structured actions (JSON) validated against a schema; an executor resolves each to a vetted module. The model never runs shell or SDK calls directly. | **MUST** | **PASS** | `backend/app/planner/models.py` | `test_planner.py` (PASS) | Strict Pydantic v2 schemas (`CampaignPlan`, `CampaignStage`). Model outputs structured JSON; execution engine maps ID to code. |
| **FR-2.4** | The planner adapts the next stage based on the emulated outcome of prior stages (success / failure / telemetry), enabling dynamic multi-step planning. | **SHOULD**| **PASS** | `backend/app/planner/adaptive.py` | `test_planner.py` (PASS) | Re-evaluates graph on stage failure; prunes dead paths and selects alternative technique branches dynamically. |
| **FR-2.5** | Every generated plan passes the guardrail / policy layer (authorisation, scope, destructiveness) before any execution. | **MUST** | **PASS** | `backend/app/policies/gate.py` | `test_policies.py` (PASS) | Mandatory pre-execution policy checkpoint verifying allowlisted account, blast radius, dual-key auth, and safety invariants. |
| **FR-2.6** | Plans, the planner’s rationale, and seeds are logged for audit and reproducible replay. | **SHOULD**| **PASS** | `backend/app/planner/models.py` | `test_planner.py`, `test_audit.py` (PASS) | Plans include `seed: int`, `planning_rationale: str`, and `assumptions: list[str]`. Logged to SHA-256 ledger. |

---

## 4. Domain 3: Safe Payload Execution & Emulation Engine (FR-3.1 to FR-3.6)

| Req ID | PRD Requirement Text | Priority | Status | Source File | Test File & Result | Evidence & Notes |
| :--- | :--- | :---: | :---: | :--- | :--- | :--- |
| **FR-3.1** | Each ATT&CK technique is a self-contained module declaring a contract: preconditions, emulated action, expected telemetry/IOCs, and a non-destructive guarantee. | **MUST** | **PASS** | `backend/app/techniques/contracts/base.py` | `test_techniques.py` (PASS) | Every technique subclasses `BaseTechniqueExecutor` declaring explicit inputs, observables, and inert payload parameters. |
| **FR-3.2** | Emulation is behavioural, not exploitative — modules reproduce observable signals using benign, reversible operations; no exploit code is used. | **MUST** | **PASS** | `backend/app/techniques/contracts/` | `test_techniques.py` (PASS) | Strictly benign marker files (`falcon-marker.txt`), harmless enumeration calls, simulated beacon signals. Zero live exploits. |
| **FR-3.3** | Execution occurs inside isolated, ephemeral sandbox runners with constrained egress and scoped, short-lived credentials. | **MUST** | **PASS** | `backend/app/orchestrator/runners.py`, `kubernetes_runner.py` | `test_execution_engine.py` (PASS) | Ephemeral execution in Subprocess, Docker, or Kubernetes Batch/v1 Jobs with non-root UID 10001 and dropped capabilities (ALL). |
| **FR-3.4** | Pre/post hooks enforce guardrails and capture state required for teardown. | **MUST** | **PASS** | `backend/app/orchestrator/engine.py` | `test_execution_engine.py` (PASS) | Captures pre-run baseline state; queues rollback actions into LIFO teardown stack before stage execution. |
| **FR-3.5** | Technique coverage spans Initial Access, Execution, Discovery, Privilege Escalation, Persistence, Credential Access, C2 and (benign) Exfiltration. | **MUST** | **PASS** | `backend/app/techniques/registry.py` | `test_techniques.py` (PASS) | 16 curated techniques covering all required tactics from PRD Appendix A. |
| **FR-3.6** | Idempotent teardown returns the lab to its pre-run baseline; teardown is verified and logged. | **MUST** | **PASS** | `backend/app/teardown/engine.py` | `test_teardown.py` (PASS) | Executes rollback actions in reverse order; executes post-run graph diff verifying zero residual drift. |

---

## 5. Domain 4: Command-and-Control (C2) Traffic Emulation (FR-4.1 to FR-4.4)

| Req ID | PRD Requirement Text | Priority | Status | Source File | Test File & Result | Evidence & Notes |
| :--- | :--- | :---: | :---: | :--- | :--- | :--- |
| **FR-4.1** | Emulate beaconing for detection testing: periodic callbacks with configurable interval and jitter over HTTPS, and DNS-based signalling patterns to lab-owned sinks with inert markers. | **MUST** | **PASS** | `backend/app/telemetry/c2.py` | `test_telemetry.py` (PASS) | Emulates jittered HTTPS beaconing (interval 5s, jitter 20%) and DNS queries carrying inert tracking tokens to local sink. |
| **FR-4.2** | Emulate domain-fronting-style and cloud-service-domain traffic shapes for detection validation without abusing third-party services. | **SHOULD**| **PASS** | `backend/app/telemetry/c2.py` | `test_telemetry.py` (PASS) | Simulates HTTP Host-header mismatch against lab mock proxy endpoints without external service abuse. |
| **FR-4.3** | Each emulated channel emits deterministic IOCs (domains/records, timing signatures, TLS characteristics) recorded as ground truth for detection validation. | **MUST** | **PASS** | `backend/app/telemetry/c2.py` | `test_telemetry.py` (PASS) | Emits structured IOC records (domains, timestamps, IP endpoints) aggregated into campaign ground-truth package. |
| **FR-4.4** | No real command execution traverses the channel; “commands” are inert tokens that advance the emulation state machine only. | **MUST** | **PASS** | `backend/app/telemetry/c2.py` | `test_telemetry.py` (PASS) | Strictly tokenized payload validation (`TOKEN_ADVANCE_STAGE_X`). Zero arbitrary command parsing. |

---

## 6. Domain 5: Detection Validation & Reporting (FR-5.1 to FR-5.3)

| Req ID | PRD Requirement Text | Priority | Status | Source File | Test File & Result | Evidence & Notes |
| :--- | :--- | :---: | :---: | :--- | :--- | :--- |
| **FR-5.1** | Correlate emitted ground-truth IOCs/TTPs against detections observed in the lab SIEM/EDR (or a detection stub) to compute per-technique coverage. | **MUST** | **PASS** | `backend/app/detection/correlation.py` | `test_detection.py` (PASS) | Correlates execution events and IOCs against SIEM alerts; computes exact coverage percentage (e.g. 100.0%). |
| **FR-5.2** | Produce a SOC-ready report: per-technique detection status (detected / missed / partial), MTTD, an attack-path narrative, an ATT&CK coverage heatmap, and prioritised remediation. | **MUST** | **PASS** | `backend/app/reporting/soc_report.py` | `test_reporting.py` (PASS) | Generates executive report detailing MTTD (e.g. 16.32s), ATT&CK heatmap, and actionable remediation steps. |
| **FR-5.3** | Export both machine-readable results (JSON) and a human-readable report (HTML / PDF / Markdown). | **SHOULD**| **PASS** | `backend/app/reporting/soc_report.py` | `test_reporting.py` (PASS) | Exports structured JSON, clean Markdown, styled HTML, and native ReportLab PDF. |

---

## 7. Functional Requirements Verdict

**Total Functional Requirements:** 26  
**Passed & Verified:** 26 (100.0%)  
**Partial / Blocked / Failed:** 0 (0.0%)  
**FR Compliance Verdict:** **100% COMPLETE & VERIFIED**

