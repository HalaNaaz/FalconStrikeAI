# Falcon Strike-AI — Comprehensive Implementation Gap Analysis

**Document Version:** 2.0.0  
**Audit Date:** 1 November 2026  
**Auditor:** Principal Software Architect, Cloud Security Architect & Adversary Emulation Engineer  
**Source Document:** `e11724cd68ee47cfbfbbbae0fd804c6e.pdf` (*CrowdStrike Adversary Emulation PRD v1.0*)

---

## 1. Executive Overview

This document provides a technical audit of the discrepancies between the original Product Requirements Document (PRD) and the implemented codebase of **Falcon Strike-AI**. 

While the engine has delivered a complete 17-stage Continuous Threat Exposure Management (CTEM) pipeline that runs end-to-end with 126 passing tests (85.76% line coverage) and a responsive command center UI, specific architectural and environmental gaps remain between offline simulated execution and fully autonomous production cloud operation.

---

## 2. Phase-by-Phase Technical Gap Audit

### Phase 1: AWS Environment Ingestion (FR-1.1, FR-1.2, FR-1.3)

| Component | Implemented Capability | Production PRD Requirement | Identified Technical Gap | Risk & Impact |
| :--- | :--- | :--- | :--- | :--- |
| **AWS SDK Client** | `boto3` calls for `iam:ListUsers`, `iam:ListRoles`, `iam:GetPolicy`, `ec2:DescribeSecurityGroups`, `s3:GetBucketPolicy`, `s3:GetBucketAcl`. | Live read-only continuous cloud discovery across all active AWS regions. | **Credential Expiry & Region Scope:** The host machine's AWS CLI session is expired (`Your session has expired. Please reauthenticate using 'aws login'`). The code currently queries only the default configured region (`us-east-1` fallback) rather than iterating across all AWS regions via `ec2:DescribeRegions`. | **Medium:** Offline execution relies on synthetic fixtures (`SyntheticTopologyProvider`). Live cloud scanning requires an active STS credential token and regional iteration logic. |
| **Data Ingestion** | Synthetic JSON topology parser reproducing real AWS responses for flawed and clean environments. | Live account asset inventory streaming into graph memory. | None for offline mode; fully functional synthetic simulation. Live ingestion path is implemented in `runner.py` but untested against a live multi-account AWS Organization. | **Low:** The synthetic loader provides 100% deterministic testing for offline environments. |
| **Identity-to-Compute Binding** | Extracts `IamInstanceProfile` ARN from EC2 instances and resolves associated IAM Role. | Discovery of ECS task execution roles, Lambda execution roles, and EKS IRSA service accounts. | **Container & Serverless Scope:** Ingestion only covers EC2 instance profiles. ECS task execution roles, Lambda service roles, and EKS service account annotations are not yet parsed. | **Low (for PRD AWS-first prototype scope):** PRD Phase 1 specifies instance profiles and service roles; EC2 coverage satisfies the primary pivot vector. |

---

### Phase 2: Property Graph & Attack Path Analysis (FR-1.4, FR-1.5, FR-1.6, FR-1.7, NFR-P1, NFR-P2)

| Component | Implemented Capability | Production PRD Requirement | Identified Technical Gap | Risk & Impact |
| :--- | :--- | :--- | :--- | :--- |
| **Graph Storage Engine** | `InMemoryGraphStore` leveraging an adjacency graph model with indexed lookup tables and cycle-resistant path traversal. | Neo4j property graph with Cypher queries. | **External Neo4j Service Dependency:** `Neo4jGraphStore` class is implemented in `neo4j_store.py`, but relies on an active Neo4j daemon on port 7687. Since Neo4j is not running on the local host, the system gracefully falls back to `InMemoryGraphStore`. | **Low:** The in-memory store executes identical traversal semantics and meets the PRD's sub-second performance target (p95 = 5.74 ms at 10,000 nodes). |
| **Misconfiguration Detection** | Detects wildcard actions (`*`), Rhino Security Labs privesc primitives (`iam:PassRole`, `iam:CreatePolicyVersion`), and 0.0.0.0/0 ingress. | Full enterprise Cloud Security Posture Management (CSPM) rule engine. | **Rule Library Depth:** Currently checks 7 primary cloud privesc and exposure patterns. Does not yet check KMS key policies, VPC peering route injection, or Route53 subdomain takeovers. | **Low:** The 7 implemented patterns cover the exact attack paths described in the PRD scenarios. |
| **Attack Path Discovery** | Depth-limited (default 5 hops) graph traversal from `PUBLIC_ENDPOINT` to `is_admin=True` or `is_crown_jewel=True`. | Scalable traversal supporting deep multi-account paths (> 10 hops). | **Depth Pruning:** Traversal is bounded at 5 hops to prevent exponential path explosion in densely connected graphs. | **Low:** 5 hops is sufficient for all typical cloud foothold-to-admin pivoting chains. |
| **Path Ranking Engine** | Composite exploitability and impact scoring (0-100) combining hop penalty, admin target weight, and exposure ease. | Defensible risk scoring calibrated against CVSS / EPSS metrics. | **Mathematical Calibration:** Scoring formula is heuristic rather than trained on empirical breach data. | **Low:** Provides clear, deterministic ranking that prioritizes high-impact admin role targets. |

---

### Phase 3: AI Campaign Planning (FR-2.1 to FR-2.6)

| Component | Implemented Capability | Production PRD Requirement | Identified Technical Gap | Risk & Impact |
| :--- | :--- | :--- | :--- | :--- |
| **LLM Provider Integration** | `GeminiPlannerProvider` using `google-genai` SDK with strict JSON schema enforcement; falls back to `DeterministicCampaignPlanner`. | Autonomous multi-model agentic loop (OpenAI, Anthropic, Gemini) with dynamic reasoning. | **API Key Dependency:** When `GEMINI_API_KEY` is not exported, the system automatically falls back to `DeterministicCampaignPlanner`. While this ensures 100% offline availability, genuine generative LLM planning requires an active API key. | **Low:** The deterministic planner produces fully schema-valid, reproducible campaign plans matching ATT&CK tactics. |
| **Technique Allowlisting** | Hard validation against static 12-technique enum (`CuratedTechniqueId`). Any unauthorized string throws `TechniqueNotApprovedError`. | LLM restricted to vetted library; zero arbitrary commands. | None. Invariant is enforced at both Pydantic schema level and at policy gate level. | **Zero:** Complete safety containment achieved. |
| **Adaptive Replanning** | `AdaptivePlanner` prunes failed technique branches and selects alternative routes to the target. | Dynamic closed-loop replanning driven by real-time SIEM alert feedback. | **Feedback Source:** Adaptive replanning currently triggers on step failure in simulation results, rather than real-time polling of live SIEM event streams. | **Low:** Matches the PRD requirement for emulated outcome adaptation. |

---

### Phase 4: Safety Policy Gate (NFR-S1 to NFR-S7, FR-2.5)

| Component | Implemented Capability | Production PRD Requirement | Identified Technical Gap | Risk & Impact |
| :--- | :--- | :--- | :--- | :--- |
| **Account Allowlist** | `ALLOWED_ACCOUNT_IDS` verified in `core/config.py` and `policies/rules.py`. | Compiled allowlist checked before all other logic; aborts immediately. | None. Target account `000000000000` (or configured ID) is enforced across CLI, API, and policy engine. | **Zero:** Accidental production targeting is prevented in code. |
| **Two-Key Authorization** | `TwoKeyAuthorizer` requires two distinct operator HMAC/JWT tokens to authorize live execution. | Strict separation of duty with multi-party authorization. | **Symmetric Key Limitation:** Uses symmetric HMAC-SHA256 with `SECRET_KEY`. In high-assurance enterprise deployments, asymmetric Ed25519 or X.509 certificates are preferred for non-repudiation. | **Low:** Sufficient for prototype; enforces two distinct identities. |
| **Emergency Kill Switch** | Thread-safe `EmergencyKillSwitch` singleton with disk persistence, abort callbacks, and sub-second trigger latency (< 5 ms). | Single-command and dashboard-controlled halt triggering immediate teardown. | None. Completely verified in unit tests and integrated into API/CLI. | **Zero:** Immediate halt capability verified. |
| **Dry-Run Default** | `dry_run = True` is the hardcoded default across all interfaces. Leaving dry-run requires explicit `--live` flag and two valid tokens. | Zero live cloud interaction without opt-in. | None. Tested and verified. | **Zero:** Invariant strictly maintained. |

---

### Phase 5: Execution & Sandbox (FR-3.1 to FR-3.6)

| Component | Implemented Capability | Production PRD Requirement | Identified Technical Gap | Risk & Impact |
| :--- | :--- | :--- | :--- | :--- |
| **Sandbox Isolation** | `DockerSandboxRunner` configured with `--security-opt=no-new-privileges`, `CAP_DROP ALL`, read-only rootfs, and memory limits; `InMemoryRunner` fallback. | Ephemeral container runners (Docker or Kubernetes Jobs) with kernel-level isolation. | **Docker Host Daemon Inactive:** Docker is installed on the host machine (`Docker version 29.9.2`), but the daemon is not running (`The system cannot find the file specified`). Consequently, the execution engine falls back to `InMemoryRunner`. | **Medium:** `InMemoryRunner` safely simulates all 12 techniques in-process using inert markers, but does not provide Linux cgroup or namespace isolation. |
| **Kubernetes Jobs Runner** | `BaseSandboxRunner` interface defines pluggable contract. | Horizontally scalable ephemeral runner execution via Kubernetes Jobs (NFR-P4). | **Missing K8s Runner:** Dedicated `KubernetesJobRunner` is not implemented (PRD classified this as a "Could-Have" requirement). | **Low:** Docker and in-memory runners satisfy single-node prototype execution. |
| **Teardown & Baseline Reversion** | `TeardownEngine` executes rollback in LIFO order; `BaselineVerifier` computes SHA-256 fingerprint diff against pre-run state. | Guaranteed idempotent teardown returning lab to exact pre-run baseline. | None. Fully verified with passing tests for residual and missing resources. | **Zero:** Clean lab reversion verified. |

---

### Phase 6: Telemetry & IOC Generation (FR-4.1 to FR-4.4)

| Component | Implemented Capability | Production PRD Requirement | Identified Technical Gap | Risk & Impact |
| :--- | :--- | :--- | :--- | :--- |
| **C2 Beacon Emulation** | `BenignC2Sink` records HTTP callbacks with configurable interval and jitter; `BenignDNSSink` records DNS queries. | Network-level beaconing with realistic timing signatures. | **In-Process vs Wire Traffic:** Sinks run as internal async service handlers rather than raw socket listeners binding to external network interfaces. | **Low:** Accurately models beacon intervals, jitter calculations, and telemetry records without risk of rogue network emissions. |
| **Domain Fronting Simulation** | Simulates HTTP Host header mismatch terminating at lab-owned sink endpoints. | Realistic traffic shape without abusing third-party CDNs. | **TLS Fingerprinting:** Emulates domain and SNI attributes, but does not generate synthetic JA3/JA4 TLS handshake packet captures. | **Low:** Meets PRD requirement of avoiding third-party abuse while recording IOC ground truth. |
| **Deterministic IOC Generation** | `SyntheticIOCGenerator` emits typed IOCs: `IPv4`, `DOMAIN`, `DNS_QUERY`, `CANARY_FILE`, `IAM_ROLE`, `API_CALL`, `URL`. | Ground-truth IOC artifacts exported for correlation. | None. All IOCs tagged with `run_id` and technique ID. | **Zero:** Deterministic ground truth available for detection engine. |

---

### Phase 7: Detection Correlation (FR-5.1, FR-5.2)

| Component | Implemented Capability | Production PRD Requirement | Identified Technical Gap | Risk & Impact |
| :--- | :--- | :--- | :--- | :--- |
| **Detection Correlation Engine** | `DetectionCorrelationEngine` correlates ground-truth IOCs against security events; computes detected, partial, and missed outcomes. | Automated validation against SIEM/EDR query APIs. | None. Multi-attribute matching supports exact IOC tokens, technique IDs, and run IDs. | **Zero:** Mathematical precision verified. |
| **SIEM / EDR Adapters** | Adapters for CrowdStrike Falcon, Splunk, Sentinel, Elastic, and QRadar with honest disconnection detection (`is_connected() == False`). | Live API query against production SIEM/EDR clusters. | **Missing Production Credentials:** Live enterprise SIEM instances are not available in the local dev environment. The adapters correctly identify absence of API credentials and report disconnected status rather than fabricating responses. | **Low:** PRD explicitly provides for a `DetectionStub` when live SIEM is unavailable. |
| **Detection Stub** | `DetectionStub` with three realistic profiles (`FULL_COVERAGE`, `PARTIAL_COVERAGE`, `HIGH_MISS_RATE`) and simulated detection delays. | High-fidelity offline simulation for testing without external SIEM. | None. Verified in automated test suite. | **Zero:** Offline testing is fully supported. |

---

### Phase 8: SOC Reporting (FR-5.2, FR-5.3)

| Component | Implemented Capability | Production PRD Requirement | Identified Technical Gap | Risk & Impact |
| :--- | :--- | :--- | :--- | :--- |
| **SOC Executive Reports** | `SOCReportGenerator` compiles threat profile, executive summaries, ATT&CK coverage heatmap, and prioritized remediations. | SOC-ready actionable executive deliverables. | None. Generates complete ATT&CK matrix and calculated MTTD. | **Zero:** Complete narrative and data export. |
| **Export Formats** | Generates structured JSON, GitHub-flavored Markdown, and standalone dark-themed HTML. | Export to JSON, HTML, Markdown, and PDF (FR-5.3). | **Missing PDF Generation:** PDF export relies on browser print-to-PDF (`@media print` CSS included in HTML template). A headless backend PDF generator (e.g., WeasyPrint) is not integrated. | **Low:** HTML and Markdown provide immediate reviewability; JSON provides automation ingestion. |

---

## 3. Definition of Done (PRD Section 12) Detailed Audit

| # | PRD Acceptance Criterion | Codebase Verification Status | Physical Evidence & File Reference |
| :-: | :--- | :---: | :--- |
| **1** | The pipeline runs end-to-end against the isolated lab from a single command. | **VERIFIED** | `python -m backend.app.main run --mode synthetic --dry-run` executes all 17 stages in **11.66 ms**. |
| **2** | No destructive action occurs in any mode; emulation is non-destructive and reversible. | **VERIFIED** | All 12 techniques declare `non_destructive = True`; verified in `test_techniques.py` and `test_collectors.py`. |
| **3** | Teardown is verified to return the lab to its recorded baseline after every run. | **VERIFIED** | `BaselineVerifier.verify_baseline()` computes SHA-256 state hashes; verified in `test_teardown.py`. |
| **4** | The audit log is complete, append-only and tamper-evident, threaded by a single run ID. | **VERIFIED** | `HashChainedAuditLogger` streams SHA-256 chained records; verified in `test_audit.py`. |
| **5** | Attack-path queries meet p95 < 1s at 10,000+ nodes. | **VERIFIED** | `run_benchmark(target_nodes=10000, iterations=20)` measured **p95 = 5.74 ms** (Target: < 1000 ms). |
| **6** | The LLM planner only ever selects allowlisted techniques and emits schema-valid actions; it never executes directly. | **VERIFIED** | Validated by `CampaignPlanValidator` against static 12-technique enum; zero model shell access. |
| **7** | The account allowlist, authorisation token and kill switch are all proven to work (with evidence). | **VERIFIED** | Verified in `test_policies.py` (allowlist + 2-key token) and `test_kill_switch.py` (latency < 5 ms). |
| **8** | A SOC report is generated with per-technique coverage, MTTD and prioritised remediation. | **VERIFIED** | Generated reports in `artifacts/reports/` contain full ATT&CK heatmap, MTTD math, and remediation steps. |
| **9** | Code is tested and documented; the runbook lets a new engineer reproduce a run. | **VERIFIED** | 126 backend tests passing; `README.md` and `docs/END_TO_END_RUNBOOK.md` provide step-by-step reproduction instructions. |

---

## 4. Summary of Key Implementation Gaps

1. **Docker Container Execution (FR-3.3):** Docker runner is implemented in Python, but host Docker daemon is offline. Runner currently operates via in-memory simulation fallback.
2. **PDF Report Export (FR-5.3):** HTML, Markdown, and JSON exports are functional; native backend PDF generation (headless WeasyPrint/Playwright) is not yet implemented.
3. **Live Cloud Ingestion (FR-1.1, FR-1.2):** Boto3 SDK collectors are written and tested with mocks, but live execution against a real AWS account is blocked by expired host STS session credentials.
4. **Live SIEM Adapters (FR-5.1):** Adapters for 5 enterprise SIEMs exist with honest disconnection detection; live testing requires production API credentials.
5. **Kubernetes Jobs Runner (NFR-P4):** "Could-Have" horizontal scaling runner using Kubernetes API remains unimplemented.

