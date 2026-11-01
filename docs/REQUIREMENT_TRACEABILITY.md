# Falcon Strike-AI — Requirements Traceability Matrix (RTM)

**Document Version:** 1.0.0  
**Date:** 2026-11-01  
**Project:** Falcon Strike-AI  
**Source PRD:** `e11724cd68ee47cfbfbbbae0fd804c6e.pdf`  

---

## 1. Overview

This matrix maps every Functional Requirement (FR) and Non-Functional Requirement (NFR) from the Falcon Strike-AI Product Requirements Document to its corresponding architectural component, planned code implementation, automated verification test, and implementation schedule.

---

## 2. Functional Requirements Traceability Matrix

| Req ID | PRD Description | Architecture Component | Target Module Path | Test Suite File | Delivery Day | Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **FR-1.1** | Ingest IAM principals, roles, policies, and assume-role / trust chains via SDK. | Ingestion Subsystem | `backend/app/collectors/aws_iam.py` | `tests/test_collectors.py` | Day 2 | COMPLETE |
| **FR-1.2** | Ingest network exposure: public endpoints, security groups, public buckets. | Ingestion Subsystem | `backend/app/collectors/aws_network.py` | `tests/test_collectors.py` | Day 2 | COMPLETE |
| **FR-1.3** | Ingest compute-to-identity bindings (instance profiles, service roles). | Ingestion Subsystem | `backend/app/collectors/aws_network.py` | `tests/test_collectors.py` | Day 2 | COMPLETE |
| **FR-1.4** | Model environment as property graph (Principals, Roles, Policies, Resources, Endpoints). | Graph Subsystem | `backend/app/graph/models.py`, `backend/app/graph/store.py` | `tests/test_graph.py` | Day 2 | COMPLETE |
| **FR-1.5** | Label misconfigurations as graph properties (wildcards, privesc primitives, public access). | Graph Subsystem | `backend/app/graph/enrichment.py` | `tests/test_graph.py` | Day 2 | COMPLETE |
| **FR-1.6** | Compute attack paths from entry node to high-value targets (admin roles, data stores). | Graph Subsystem | `backend/app/graph/path_finder.py` | `tests/test_attack_paths.py` | Day 2 | COMPLETE |
| **FR-1.7** | Rank computed paths by exploitability and impact. | Graph Subsystem | `backend/app/graph/path_ranker.py` | `tests/test_attack_paths.py` | Day 2 | COMPLETE |
| **FR-2.1** | LLM planner produces ordered, multi-stage campaign mapped to ATT&CK tactics. | Planner Subsystem | `backend/app/planner/planner.py` | `tests/test_planner.py` | Day 3 | COMPLETE |
| **FR-2.2** | Planner selects only allowlisted techniques from approved library; cannot invent commands. | Planner Subsystem | `backend/app/techniques/registry.py`, `backend/app/planner/validation.py` | `tests/test_planner.py` | Day 3 | COMPLETE |
| **FR-2.3** | Tool-use architecture: Planner emits structured JSON validated against schema; no direct shell/SDK. | Planner Subsystem | `backend/app/planner/models.py`, `backend/app/planner/validation.py` | `tests/test_planner.py` | Day 3 | COMPLETE |
| **FR-2.4** | Planner adapts next stage based on emulated outcome of prior stages. | Planner Subsystem | `backend/app/planner/adaptive.py` | `tests/test_planner.py` | Day 3 | COMPLETE |
| **FR-2.5** | Every plan passes guardrail / policy layer before any execution. | Policy Subsystem | `backend/app/policies/engine.py` | `tests/test_policies.py` | Day 3 | COMPLETE |
| **FR-2.6** | Plans, rationale, and seeds are logged for audit and reproducible replay. | Planner Subsystem | `backend/app/planner/models.py`, `backend/app/planner/planner.py` | `tests/test_planner.py` | Day 3 | COMPLETE |
| **FR-3.1** | ATT&CK technique modules declare formal contract: preconditions, action, IOCs, safety guarantee. | Technique Subsystem | `backend/app/techniques/catalog.py`, `backend/app/techniques/contracts.py` | `tests/test_techniques.py` | Day 3 | COMPLETE |
| **FR-3.2** | Emulation is behavioural and non-destructive; benign, reversible operations only. | Technique Subsystem | `backend/app/techniques/simulator.py` | `tests/test_techniques.py` | Day 3 | COMPLETE |
| **FR-3.3** | Execution occurs in isolated, ephemeral sandbox runners with scoped credentials. | Sandbox Subsystem | `backend/app/orchestrator/docker_runner.py`, `backend/app/orchestrator/in_memory_runner.py` | `tests/test_execution_engine.py` | Day 4 | COMPLETE |
| **FR-3.4** | Pre/post hooks enforce guardrails and capture state for teardown. | Orchestrator Subsystem | `backend/app/orchestrator/lifecycle.py`, `backend/app/orchestrator/state_capture.py` | `tests/test_execution_engine.py` | Day 4 | COMPLETE |
| **FR-3.5** | Coverage of curated ATT&CK techniques across key tactics (Appendix A). | Technique Subsystem | `backend/app/techniques/catalog.py`, `backend/app/techniques/registry.py` | `tests/test_techniques.py` | Day 3 & 4 | COMPLETE |
| **FR-3.6** | Idempotent teardown returns lab to pre-run baseline; verified and logged. | Teardown Subsystem | `backend/app/orchestrator/teardown.py`, `backend/app/orchestrator/verification.py` | `tests/test_teardown.py` | Day 4 | COMPLETE |
| **FR-4.1** | Emulate beaconing with configurable interval and jitter over HTTPS and DNS to lab sinks. | C2 Subsystem | `backend/app/telemetry/c2_sink.py` | `tests/test_telemetry.py` | Day 4 | COMPLETE |
| **FR-4.2** | Emulate domain-fronting and cloud-service traffic shapes terminating at lab endpoints. | C2 Subsystem | `backend/app/telemetry/dns_sink.py`, `backend/app/telemetry/c2_sink.py` | `tests/test_telemetry.py` | Day 4 | COMPLETE |
| **FR-4.3** | Emulate channels emit deterministic IOCs recorded as ground truth. | C2 Subsystem | `backend/app/telemetry/ioc_generator.py` | `tests/test_telemetry.py` | Day 4 | COMPLETE |
| **FR-4.4** | No real command execution traverses the channel; inert tokens only. | C2 Subsystem | `backend/app/telemetry/c2_sink.py` | `tests/test_telemetry.py` | Day 4 | COMPLETE |
| **FR-5.1** | Correlate emitted ground-truth IOCs against SIEM/EDR detections (or detection stub). | Detection Subsystem | `backend/app/detection/correlation.py` | `tests/test_detection.py` | Day 5 | COMPLETE |
| **FR-5.2** | Produce SOC-ready report: per-technique status, MTTD, attack path narrative, heatmap, remediation. | Reporting Subsystem | `backend/app/reporting/generator.py` | `tests/test_reporting.py` | Day 5 | COMPLETE |
| **FR-5.3** | Export machine-readable JSON and human-readable HTML / Markdown reports. | Reporting Subsystem | `backend/app/reporting/exporters.py` | `tests/test_reporting.py` | Day 5 | COMPLETE |

---

## 3. Non-Functional Requirements Traceability Matrix

| Req ID | PRD Description & Target Metric | Architecture Component | Target Module Path | Verification Test | Delivery Day | Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **NFR-S1** | **Compiled Account Allowlist**: Refuses to run against non-allowlisted accounts. | Policy Subsystem | `backend/app/core/config.py`, `backend/app/policies/rules.py` | `tests/test_policies.py` | Day 1 & 3 | COMPLETE |
| **NFR-S2** | **Signed Authorisation Token**: Required to leave dry-run; two-key confirmation. | Policy Subsystem | `backend/app/policies/authorization.py` | `tests/test_policies.py` | Day 3 | COMPLETE |
| **NFR-S3** | **Emergency Kill-Switch**: Halts in-flight runs and triggers teardown within seconds (< 2s). | Orchestrator Subsystem | `backend/app/orchestrator/kill_switch.py` | `tests/test_kill_switch.py` | Day 4 | COMPLETE |
| **NFR-S4** | **Dry-Run by Default**: Default invocation touches no resources. | Core Config Subsystem | `backend/app/core/config.py` | `tests/test_config.py` | Day 1 | COMPLETE |
| **NFR-S5** | **Blast-Radius Caps**: Hard limits on resources touched (max 5), tagging, time-box. | Policy Subsystem | `backend/app/policies/blast_radius.py` | `tests/test_policies.py` | Day 3 | COMPLETE |
| **NFR-S6** | **Least-Privilege & Egress Allowlist**: Runners restricted to lab destinations. | Sandbox Subsystem | `backend/app/telemetry/c2_sink.py`, `backend/app/orchestrator/docker_runner.py` | `tests/test_telemetry.py` | Day 4 | COMPLETE |
| **NFR-S7** | **Verified Teardown to Baseline**: Post-run state equals recorded baseline. | Teardown Subsystem | `backend/app/orchestrator/teardown.py`, `backend/app/orchestrator/verification.py` | `tests/test_teardown.py` | Day 4 | COMPLETE |
| **NFR-P1** | **Support 10,000+ Asset Nodes**: Validated with generated scale fixtures. | Graph Subsystem | `backend/app/graph/scale_benchmark.py` | `tests/test_graph.py` | Day 2 | COMPLETE |
| **NFR-P2** | **Sub-Second Path Query**: p95 path latency < 1.0s at 10,000 nodes. | Graph Subsystem | `backend/app/graph/scale_benchmark.py` | `tests/test_graph.py` | Day 2 | COMPLETE |
| **NFR-P3** | **Rapid Ingestion**: Full lab ingestion and graph build completes in minutes. | Ingestion Subsystem | `backend/app/collectors/runner.py` | `tests/test_collectors.py` | Day 2 | COMPLETE |
| **NFR-P4** | **Scalable Sandbox Execution**: Ephemeral runners scale without orchestrator change. | Sandbox Subsystem | `backend/app/orchestrator/interfaces.py`, `backend/app/orchestrator/execution_engine.py` | `tests/test_execution_engine.py` | Day 4 | COMPLETE |
| **NFR-A1** | **Structured JSON Audit Logs**: RFC-3339 timestamp, actor, ATT&CK ID, target, IOCs. | Telemetry Subsystem | `backend/app/core/logging.py`, `backend/app/telemetry/collector.py` | `tests/test_telemetry.py` | Day 1 & 4 | COMPLETE |
| **NFR-A2** | **Append-Only Hash-Chaining**: Cryptographic SHA-256 links between log records. | Core Audit Subsystem | `backend/app/core/audit.py`, `audit_verifier.py` | `tests/test_audit.py` | Day 5 | COMPLETE |
| **NFR-A3** | **Single Correlation Run ID**: Threads all events, telemetry, and reports for a run. | Core Subsystem | `backend/app/workflow.py`, `backend/app/core/state.py` | `tests/test_end_to_end.py` | Day 1 & 5 | COMPLETE |
| **NFR-A4** | **Versioned Log Schema**: Published and documented log schema. | Core Audit Subsystem | `backend/app/core/audit_models.py`, `docs/AUDIT_INTEGRITY.md` | `tests/test_audit.py` | Day 5 | COMPLETE |

---

## 4. Acceptance Sign-Off Tracking

- [x] Phase 1 & 2 Requirements Fully Mapped
- [x] Day 1 Code & Test Verification
- [x] Day 2 Ingestion & Graph Verification
- [x] Day 3 Planner & Policy Gate Verification
- [x] Day 4 Sandbox & C2 Emulation Verification
- [x] Day 5 Telemetry, Detection & Reporting Verification
- [ ] Day 6 Final End-to-End Submission Sign-Off

