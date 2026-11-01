# Falcon Strike-AI — Test & Evidence Generation Plan

**Document Version:** 1.0.0  
**Date:** 2026-11-01  
**Project:** Falcon Strike-AI  
**Target Submission Deadline:** 2026-11-06  
**Reference PRD:** `e11724cd68ee47cfbfbbbae0fd804c6e.pdf` (Sections 11 & 12)  

---

## 1. Quality Strategy & Testing Pyramid

Falcon Strike-AI is an adversary emulation engine operating in sensitive environments; software reliability and safety assurance are paramount. The testing architecture is structured in five rigorous tiers:

```
                  ┌───────────────────────┐
                  │      End-to-End       │ (1-Command Full Pipeline)
                  ├───────────────────────┤
                  │   Security & Safety   │ (Allowlist, Token, Kill-Switch, Teardown)
                  ├───────────────────────┤
                  │   Scale & Benchmark   │ (10,000+ Nodes, p95 < 1s)
                  ├───────────────────────┤
                  │      Integration      │ (Collector ➔ Graph ➔ Planner ➔ Emulation)
                  ├───────────────────────┤
                  │       Unit Tests      │ (Config, Schemas, Hash-Chain, Modules)
                  └───────────────────────┘
```

---

## 2. Test Suites Specification

### 2.1 Unit Tests (`backend/tests/unit/`)
- **Configuration & Invariants (`test_config.py`):**
  - Verify default mode is always `DRY_RUN=True`.
  - Verify unlisted account IDs throw `SafetyConfigurationError`.
  - Verify environment variable overrides function correctly via Pydantic Settings.
- **Audit Logging & Hash Chaining (`test_hash_chain.py`):**
  - Verify sequential SHA-256 block calculation: `H_n = sha256(H_{n-1} + payload)`.
  - Verify tampering with an intermediate record breaks chain verification.
  - Verify RFC-3339 UTC timestamp serialization.
- **Pydantic Schema Validation (`test_schemas.py`):**
  - Verify valid campaign JSON parses cleanly into `CampaignPlan`.
  - Verify injection of arbitrary shell commands or unknown ATT&CK technique IDs is rejected with schema validation errors.
- **Technique Module Contracts (`test_techniques.py`):**
  - Verify all 12 curated technique modules conform to `TechniqueModule` interface.
  - Verify each module declares non-destructive guarantees, expected IOCs, and teardown logic.

### 2.2 Security & Safety Guardrail Tests (`backend/tests/security/`)
- **Account Allowlist Enforcement (`test_allowlist.py`):**
  - Attempt campaign planning and execution against unapproved AWS Account `999999999999`.
  - Verify execution fails immediately with `AccountNotAllowlistedError` before any network or runner operation.
- **Authorization Token Verification (`test_token_auth.py`):**
  - Execute with missing token → Fails.
  - Execute with expired token → Fails.
  - Execute with signature-tampered token → Fails.
  - Execute with valid two-key token → Permitted.
- **Emergency Kill-Switch (`test_kill_switch.py`):**
  - Start an active emulation run.
  - Trigger kill-switch signal/API call.
  - Verify execution terminates within < 2 seconds and triggers `TeardownEngine.revert()`.
- **Teardown & Baseline Reversion (`test_teardown.py`):**
  - Snapshot environment baseline state.
  - Execute benign emulation (creating temporary marker file and tagged role).
  - Execute teardown.
  - Verify post-run state is bit-for-bit identical to recorded baseline.

### 2.3 Performance & Scale Benchmark (`backend/tests/scale/`)
- **10,000+ Node Graph Benchmark (`test_scale_benchmark.py`):**
  - Generate synthetic enterprise graph with 10,000+ nodes and 50,000+ edges.
  - Execute 100 randomized attack path queries from external endpoints to target admin roles.
  - Compute p50, p90, and p95 latencies.
  - Assert `p95 < 1.0` second (verifying NFR-P2).

### 2.4 End-to-End Pipeline Integration (`backend/tests/e2e/`)
- **Full Campaign Run (`test_e2e_pipeline.py`):**
  - Ingest synthetic enterprise cloud topology.
  - Build graph and compute ranked attack paths.
  - Plan multi-stage campaign using Planner.
  - Validate plan against Policy Gate.
  - Run benign emulation in sandbox runner.
  - Emit jittered C2 beacons to local sink.
  - Correlate IOCs against Detection Stub.
  - Generate SOC detection report (Markdown, JSON, HTML).
  - Verify teardown and validate hash-chain audit log.

---

## 3. Required Evidence Artifacts (PRD Section 11 Mapping)

To satisfy the PRD acceptance criteria without requiring reviewers to re-execute in their own cloud accounts, Falcon Strike-AI will automatically generate and package the following tangible evidence artifacts into the `artifacts/` directory:

| Evidence Item | Required Content & Format | Generation Script / Target | PRD Reference |
| :--- | :--- | :--- | :--- |
| **1. Source Repository & Runbook** | Clean modular git repo, clear documentation, complete README.md and runbook. | `README.md`, `docs/RUNBOOK.md` | PRD Section 10 & 11 |
| **2. Architecture Diagram** | High-resolution embedded Mermaid diagram and architectural specification. | `docs/ARCHITECTURE.md` | PRD Section 11.2 |
| **3. Sample Hash-Chained Audit Logs** | JSONL audit log from real campaign showing SHA-256 chain, run ID, timestamps, IOCs. | `artifacts/sample_audit_log.jsonl` | PRD Section 11.3 |
| **4. SOC Detection-Validation Report** | Complete SOC report with ATT&CK heatmap, MTTD calculations, and remediation advice. | `artifacts/soc_report.html`, `.json`, `.md` | PRD Section 11.4 |
| **5. Performance & Scale Report** | Benchmark execution output proving >=10,000 nodes and p95 path-query latency < 1.0s. | `artifacts/scale_benchmark_report.json` | PRD Section 11.6 |
| **6. Guardrail & Kill-Switch Logs** | Verified test logs proving blocked out-of-scope actions and instant kill-switch abort. | `artifacts/guardrail_evidence.log` | PRD Section 11.7 |
| **7. Teardown-Verified Baseline Log** | State diff output proving pre-run baseline equals post-run state after cleanup. | `artifacts/teardown_verification.json` | PRD Section 11.8 |
| **8. Test Coverage Report** | Pytest HTML and text coverage report demonstrating >80% coverage on core modules. | `artifacts/coverage/index.html` | PRD Section 11.9 |

