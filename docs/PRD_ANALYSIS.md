# Falcon Strike-AI — PRD Analysis & Requirements Specification

**Document Version:** 1.0.0  
**Date:** 2026-11-01  
**Project Codename:** Falcon Strike-AI  
**Target Submission Deadline:** 2026-11-06 (5-Day Delivery Window)  
**Author:** Lead Software Architect, Senior Python Engineer & Security Implementer  
**Primary Source of Truth:** `e11724cd68ee47cfbfbbbae0fd804c6e.pdf` (CrowdStrike Adversary Emulation PRD v1.0)

---

## 1. Executive Summary & Product Workflow

Project **Falcon Strike-AI** is an autonomous, agentic breach-and-attack simulation (BAS) and Continuous Threat Exposure Management (CTEM) engine. Modern enterprise cloud environments (starting with AWS) suffer from silent detection decay and continuous configuration drift. Falcon Strike-AI continuously discovers cloud identity and exposure posture, constructs an attack graph, computes high-risk multi-stage attack paths, leverages a constrained LLM-driven planner to assemble ordered, ATT&CK-mapped campaigns, executes benign behavioral emulations within sandboxed runners, simulates C2 beacon traffic, and generates SOC-ready detection validation reports with measured Mean Time to Detect (MTTD) and coverage heatmaps.

### 1.1 The Complete 7-Stage Product Workflow

The engine strictly operates in a closed loop through seven sequential, gated stages:

```
[ Stage 1: Ingestion ] 
    │ Official read-only cloud SDK calls (IAM, security groups, public exposure, compute bindings)
    ▼
[ Stage 2: Graph Construction & Attack Path Analysis ]
    │ Normalized property graph in Neo4j; Cypher shortest/most-permissive path traversal
    ▼
[ Stage 3: Autonomous Campaign Planning (LLM Agent) ]
    │ Model consumes ranked path + lab facts; outputs schema-validated JSON plan from vetted library
    ▼
[ Stage 4: Safety & Guardrail Policy Gate ]
    │ Compiled account allowlist, signed JWT auth token, destructiveness check, rate caps
    ▼
[ Stage 5: Ephemeral Sandbox Emulation & C2 Signalling ]
    │ Isolated runner executes vetted modules; emits jittered HTTPS/DNS beaconing with inert markers
    ▼
[ Stage 6: Telemetry Collection & Detection Correlation ]
    │ Ground-truth IOCs & OTel traces correlated with SIEM/EDR (or local detection stub)
    ▼
[ Stage 7: SOC Reporting & Verified Teardown ]
    │ ATT&CK heatmap, MTTD calculation, prioritised remediation; guaranteed baseline reversion
```

---

## 2. Functional Requirements (FR) Classification

Requirements are extracted verbatim from PRD Section 6 and categorized using the **MoSCoW** framework (Must Have, Should Have, Could Have).

### 2.1 Attack-Path Graphing (Domain 1)

| Requirement ID | Description | Priority | 5-Day Delivery Viability | Notes & Constraints |
| :--- | :--- | :--- | :--- | :--- |
| **FR-1.1** | Ingest IAM principals, roles, policies, and assume-role / trust relationships via official cloud SDKs (read-only). | **MUST** | **High** | Support offline mock/fixture ingestion when live AWS credentials are not configured. |
| **FR-1.2** | Ingest network exposure: public endpoints, security-group rules, open ports, public buckets/objects, and exposed services. | **MUST** | **High** | EC2 security groups, S3 bucket policies/ACLs, and public route tables. |
| **FR-1.3** | Ingest compute-to-identity bindings (instance profiles, service roles) linking workloads to permissions. | **MUST** | **High** | Critical for establishing pivot edges from external endpoints to IAM roles. |
| **FR-1.4** | Model the environment as a property graph — nodes (`Principal`, `Role`, `Policy`, `Resource`, `Endpoint`) and edges (`CAN_ASSUME`, `HAS_PERMISSION`, `TRUSTS`, `EXPOSES`, `BOUND_TO`, `MEMBER_OF`). | **MUST** | **High** | Schema must support Neo4j Cypher and local in-memory fallback for local unit testing. |
| **FR-1.5** | Label misconfiguration patterns as graph properties/edges: wildcard permissions (`*`), known privilege-escalation primitives, and public exposure. | **MUST** | **High** | Implement pattern detectors for Rhino Security Labs / Bishop Fox cloud privesc primitives. |
| **FR-1.6** | Compute attack paths from a defined low-privilege / internet-reachable entry node to high-value targets (admin roles, sensitive data stores). | **MUST** | **High** | Traversal queries with depth limits and target filtering in Cypher. |
| **FR-1.7** | Rank computed paths by exploitability and impact, producing a prioritised list for the planner. | **SHOULD** | **High** | Score paths based on hop length, permission risk weighting, and asset criticality. |

### 2.2 Autonomous Campaign Generation (LLM Agent) (Domain 2)

| Requirement ID | Description | Priority | 5-Day Delivery Viability | Notes & Constraints |
| :--- | :--- | :--- | :--- | :--- |
| **FR-2.1** | An LLM planner consumes a ranked attack path and environment facts and produces an ordered, multi-stage campaign mapped to ATT&CK tactics and techniques. | **MUST** | **High** | Structured prompting with strict system instructions and Pydantic output schemas. |
| **FR-2.2** | The planner may select only techniques present in the approved, safe technique library (allowlist); it cannot invent, request, or execute arbitrary commands. | **MUST** | **High** | Hard validation against static technique registry enum. Any unknown technique is rejected. |
| **FR-2.3** | Tool-use architecture: the planner emits structured actions (JSON) validated against a schema; an executor resolves each to a vetted module. The model never runs shell or SDK calls directly. | **MUST** | **High** | Strict separation: Planner generates data; Orchestrator maps to code; Sandboxes execute. |
| **FR-2.4** | The planner adapts the next stage based on the emulated outcome of prior stages (success / failure / telemetry), enabling dynamic multi-step planning. | **SHOULD** | **Medium** | Re-evaluation loop fed with stage execution results. |
| **FR-2.5** | Every generated plan passes the guardrail / policy layer (authorisation, scope, destructiveness) before any execution. | **MUST** | **High** | Invariant policy gate with zero-bypass architecture. |
| **FR-2.6** | Plans, the planner’s rationale, and seeds are logged for audit and reproducible replay. | **SHOULD** | **High** | Deterministic temperature=0 / fixed seed replay support. |

### 2.3 Safe Payload Execution & Emulation Engine (Domain 3)

| Requirement ID | Description | Priority | 5-Day Delivery Viability | Notes & Constraints |
| :--- | :--- | :--- | :--- | :--- |
| **FR-3.1** | Each ATT&CK technique is a self-contained module declaring a contract: preconditions, emulated action, expected telemetry/IOCs, and a non-destructive guarantee. | **MUST** | **High** | Formal Python interface / base class specifying standard lifecycle methods. |
| **FR-3.2** | Emulation is behavioural, not exploitative — modules reproduce observable signals using benign, reversible operations; no exploit code is used. | **MUST** | **High** | Strictly benign marker files, test role assumption, harmless read API calls. |
| **FR-3.3** | Execution occurs inside isolated, ephemeral sandbox runners with constrained egress and scoped, short-lived credentials. | **MUST** | **High** | Ephemeral Docker container runners with local mock / dry-run execution fallbacks. |
| **FR-3.4** | Pre/post hooks enforce guardrails and capture state required for teardown. | **MUST** | **High** | State snapshotting prior to execution; mandatory registration in cleanup stack. |
| **FR-3.5** | Technique coverage spans Initial Access, Execution, Discovery, Privilege Escalation, Persistence, Credential Access, C2, and (benign) Exfiltration (12–15 techniques). | **MUST** | **High** | Implement 12 curated ATT&CK modules mapping exactly to PRD Appendix A. |
| **FR-3.6** | Idempotent teardown returns the lab to its pre-run baseline; teardown is verified and logged. | **MUST** | **High** | `finally` block execution; baseline comparison check after cleanup. |

### 2.4 Command-and-Control (C2) Traffic Emulation (Domain 4)

| Requirement ID | Description | Priority | 5-Day Delivery Viability | Notes & Constraints |
| :--- | :--- | :--- | :--- | :--- |
| **FR-4.1** | Emulate beaconing for detection testing: periodic callbacks with configurable interval and jitter over HTTPS, and DNS-based signalling patterns to lab-owned sinks with inert markers. | **MUST** | **High** | Built-in local HTTP/DNS sink service; jitter calculation algorithm. |
| **FR-4.2** | Emulate domain-fronting-style and cloud-service-domain traffic shapes for detection validation without abusing third-party services. | **SHOULD** | **Medium** | Simulated HTTP Host header mismatch against local mock proxy. |
| **FR-4.3** | Each emulated channel emits deterministic IOCs (domains/records, timing signatures, TLS characteristics) recorded as ground truth for detection validation. | **MUST** | **High** | Export ground truth IOC artifact JSON for correlation. |
| **FR-4.4** | No real command execution traverses the channel; “commands” are inert tokens that advance the emulation state machine only. | **MUST** | **High** | Token validation engine with fixed state transitions (e.g. `TOKEN_ADVANCE_STAGE_2`). |

### 2.5 Detection Validation & Reporting (Domain 5)

| Requirement ID | Description | Priority | 5-Day Delivery Viability | Notes & Constraints |
| :--- | :--- | :--- | :--- | :--- |
| **FR-5.1** | Correlate emitted ground-truth IOCs/TTPs against detections observed in the lab SIEM/EDR (or a detection stub) to compute per-technique coverage. | **MUST** | **High** | Comprehensive Detection Stub engine with Sigma rule parsing or simulated log queries. |
| **FR-5.2** | Produce a SOC-ready report: per-technique detection status (detected / missed / partial), MTTD, an attack-path narrative, an ATT&CK coverage heatmap, and prioritised remediation. | **MUST** | **High** | Generate Markdown, structured JSON, and HTML visual reports. |
| **FR-5.3** | Export both machine-readable results (JSON) and a human-readable report (HTML / PDF / Markdown). | **SHOULD** | **High** | HTML with embedded CSS heatmap and executive summary tables. |

---

## 3. Non-Functional Requirements (NFR) Classification

### 3.1 Safety Controls & Blast-Radius Containment

| NFR ID | Requirement & Target | Priority | Verification Method |
| :--- | :--- | :--- | :--- |
| **NFR-S1** | **Compiled Account Allowlist**: Refuses to run against any account ID not on allowlist. Aborts before any other logic. | **MUST** | Automated test attempting execution against unapproved account ID; confirms immediate abort. |
| **NFR-S2** | **Mandatory Authorisation Token**: Signed, time-boxed JWT authorization token required to leave dry-run; two-key confirmation. | **MUST** | Automated test with missing/expired/tampered token; confirms execution fails. |
| **NFR-S3** | **Kill Switch**: Halts all in-flight activity and triggers teardown from a single command or API call within seconds. | **MUST** | Asynchronous signal/event interrupt test verifying runner shutdown and teardown trigger. |
| **NFR-S4** | **Dry-Run by Default**: Default execution mode performs planning and simulation without touching live cloud resources. | **MUST** | Test invoking CLI without `--live` and `--auth-token`; verifies zero cloud API calls. |
| **NFR-S5** | **Blast-Radius Caps**: Hard limit on resources touched (e.g., max 5 resources/run), resource tags (`FalconStrike=True`), time-boxed runs. | **MUST** | Guardrail unit tests verifying policy denies plan exceeding resource limit. |
| **NFR-S6** | **Least-Privilege & Egress Allowlist**: Short-lived credentials, sandbox runners restricted to lab-owned endpoints. | **MUST** | Network egress filter and test verifying non-allowlisted destination traffic is blocked. |
| **NFR-S7** | **Automatic, Verified Teardown**: Baseline recorded pre-run; teardown restores and verifies post-run state equals baseline. | **MUST** | Test verifying residual test markers/principals are audited and removed. |

### 3.2 Performance & Scalability

| NFR ID | Requirement & Target | Priority | Verification Method |
| :--- | :--- | :--- | :--- |
| **NFR-P1** | **Large Environment Analysis**: Support analysis of environments with 10,000+ asset nodes in the graph. | **MUST** | Synthetic graph generator creating 10,000+ nodes and 50,000+ edges for benchmark testing. |
| **NFR-P2** | **Sub-Second Path Query**: p95 attack-path query latency < 1.0s at 10,000 nodes. | **MUST** | Benchmark script running indexed Cypher path traversals and recording p50, p95, p99 latencies. |
| **NFR-P3** | **Rapid Ingestion**: Full lab ingestion and graph build completes within minutes. | **SHOULD** | Profiling collector execution on benchmark topologies. |
| **NFR-P4** | **Horizontal Sandbox Scalability**: Ephemeral runner scaling via containerized jobs. | **COULD** | Abstract runner interface allowing local Docker runner or Kubernetes Job runner. |

### 3.3 Auditability & Logging

| NFR ID | Requirement & Target | Priority | Verification Method |
| :--- | :--- | :--- | :--- |
| **NFR-A1** | **Structured JSON Logs**: UTC RFC-3339 timestamps, run ID, actor, technique ID, ATT&CK reference, target, outcome, generated IOCs. | **MUST** | Schema validation on emitted log entries via Pydantic model. |
| **NFR-A2** | **Tamper-Evident Hash Chaining**: Append-only log where each record includes `sha256(prev_hash + current_record)`. | **MUST** | Verification function proving hash integrity from genesis record to terminal record. |
| **NFR-A3** | **Single Correlation ID**: Campaign-level `run_id` (UUIDv4) threading all logs, traces, IOCs, and reports. | **MUST** | Test verifying complete campaign reconstruction from single `run_id`. |
| **NFR-A4** | **Versioned Log Schema**: Published JSON Schema specification for audit logs. | **MUST** | Exported JSON schema file matching codebase logging models. |

---

## 4. Requirement Dependencies & Execution Flow

```
[FR-1.1, FR-1.2, FR-1.3] (Collectors)
        │
        ▼
   [FR-1.4, FR-1.5] (Graph Modeling & Misconfig Labeling)
        │
        ▼
   [FR-1.6, FR-1.7] (Path Finding & Ranking)
        │
        ▼
   [FR-2.1, FR-2.2, FR-2.3] (LLM Campaign Planning)
        │
        ▼
   [NFR-S1, NFR-S2, NFR-S5, FR-2.5] (Safety & Policy Gate)
        │
        ▼
   [FR-3.1, FR-3.2, FR-3.3, FR-3.4, FR-3.5] (Vetted Emulation Modules)
        │
        ├────────────────────────────────┐
        ▼                                ▼
   [FR-4.1, FR-4.2, FR-4.3, FR-4.4] (C2 Emulation)    [NFR-S3, FR-3.6, NFR-S7] (Teardown & Baseline)
        │                                │
        └────────────────┬───────────────┘
                         ▼
             [FR-5.1, FR-5.2, FR-5.3] (Detection Correlation & SOC Report)
```

---

## 5. Scope Boundaries: Real vs. Simulated Integrations

Given the constraint that external AWS credentials, Neo4j enterprise clusters, and real enterprise SIEMs may not be provisioned or authenticated in local development:

| Component | Real Production-Grade Implementation | High-Fidelity Local Simulation / Fallback |
| :--- | :--- | :--- |
| **AWS Cloud Ingestion** | Boto3 SDK querying IAM, EC2, S3 APIs against allowlisted account. | Synthetic AWS JSON Topology loader replicating real Boto3 SDK output schemas. |
| **Graph Database** | Neo4j Community / Enterprise via official `neo4j` Python driver. | In-Memory Property Graph engine with Cypher-like traversal syntax for standalone execution. |
| **LLM Agent Planning** | OpenAI / Gemini API generating JSON campaign plans with temperature=0. | Deterministic Heuristic Planner & Offline Mock LLM returning valid validated campaign JSON. |
| **Sandbox Execution** | Ephemeral Docker container runners with drop-capabilities & host-isolation. | In-process Subprocess Sandbox with environment isolation and strict dry-run mode. |
| **C2 Signalling** | Asynchronous HTTP/DNS socket connections with jitter to lab endpoints. | Built-in Local Async HTTP/DNS Sink server capturing payloads and recording IOCs. |
| **SIEM / EDR** | Splunk / CrowdStrike Falcon / AWS GuardDuty API query integration. | Deterministic High-Fidelity Detection Stub with synthetic alert injection and MTTD calculation. |
| **Policy Engine** | Open Policy Agent (OPA) / Python Rego-equivalent engine. | Python-native Declarative Policy Engine evaluating Pydantic rules and constraints. |

---

## 6. Curated MITRE ATT&CK Techniques (PRD Appendix A)

The engine must support the following 12 curated techniques:

1. **T1078 (Valid Accounts)** — Initial Access: Authenticated API access from an unusual source/principal in-lab; observable as anomalous sign-in / AssumeRole.
2. **T1526 / T1087 (Cloud Service / Account Discovery)** — Discovery: Bursts of read-only describe/list calls; observable as enumeration activity.
3. **T1580 (Cloud Infrastructure Discovery)** — Discovery: Read-only inventory of lab infrastructure; observable as discovery API patterns.
4. **T1098 (Account Manipulation / Role Chaining)** — Privilege Escalation: Traversal of an assume-role edge to a higher-privilege lab role; observable as role chaining.
5. **T1136 (Create Account)** — Persistence: Creation of a tagged, benign, auto-expiring lab principal; fully reversed at teardown.
6. **T1053 (Scheduled Task / Job)** — Persistence: Creation of a benign scheduled job in-lab; observable as scheduler creation; removed at teardown.
7. **T1552 (Unsecured Credentials)** — Credential Access: Discovery of a planted, clearly-marked benign marker secret; observable as secret-access API call.
8. **T1555 (Credentials from Stores)** — Credential Access: Access pattern against a lab secret store using marker material only.
9. **T1550 (Use Alternate Authentication Material)** — Defense Evasion: Token-reuse pattern in-lab; observable as alternate-auth usage.
10. **T1071 / T1071.004 (Application Layer Protocol / DNS)** — Command & Control: Jittered HTTPS beacons and DNS-based signalling to lab sinks; inert markers only.
11. **T1572 / T1568 (Protocol Tunneling / Dynamic Resolution)** — Command & Control: Tunneling and dynamic-resolution traffic shapes for detection testing.
12. **T1537 (Transfer Data to Cloud Account)** — Exfiltration: Copy of a benign marker object to a lab-owned, allowlisted destination; reversible, no real data.

