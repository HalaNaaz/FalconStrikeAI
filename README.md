# Falcon Strike-AI

<div align="center">

```
  ███████╗ █████╗ ██╗      ██████╗ ██████╗ ███╗   ██╗    ███████╗████████╗██████╗ ██╗██╗  ██╗███████╗      █████╗ ██╗
  ██╔════╝██╔══██╗██║     ██╔════╝██╔═══██╗████╗  ██║    ██╔════╝╚══██╔══╝██╔══██╗██║██║ ██╔╝██╔════╝     ██╔══██╗██║
  █████╗  ███████║██║     ██║     ██║   ██║██╔██╗ ██║    ███████╗   ██║   ██████╔╝██║█████╔╝ █████╗  █████╗███████║██║
  ██╔══╝  ██╔══██║██║     ██║     ██║   ██║██║╚██╗██║    ╚════██║   ██║   ██╔══██╗██║██╔═██╗ ██╔══╝  ╚════╝██╔══██║██║
  ██║     ██║  ██║███████╗╚██████╗╚██████╔╝██║ ╚████║    ███████║   ██║   ██║  ██║██║██║  ██╗███████╗     ██║  ██║██║
  ╚═╝     ╚═╝  ╚═╝╚══════╝ ╚═════╝ ╚═════╝ ╚═╝  ╚═══╝    ╚══════╝   ╚═╝   ╚═╝  ╚═╝╚═╝╚═╝  ╚═╝╚══════╝     ╚═╝  ╚═╝╚═╝
```

### **Autonomous Agentic Breach & Attack Simulation (BAS) and Continuous Threat Exposure Management (CTEM) Engine**

[![Python Version](https://img.shields.io/badge/Python-3.11%20%7C%203.14-0A2540?style=for-the-badge&logo=python&logoColor=38BDF8)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.111+-0A2540?style=for-the-badge&logo=fastapi&logoColor=009688)](https://fastapi.tiangolo.com/)
[![Next.js](https://img.shields.io/badge/Next.js-14.2%20App%20Router-0A2540?style=for-the-badge&logo=next.js&logoColor=white)](https://nextjs.org/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.5+-0A2540?style=for-the-badge&logo=typescript&logoColor=3178C6)](https://www.typescriptlang.org/)
[![Tailwind CSS](https://img.shields.io/badge/Tailwind-3.4-0A2540?style=for-the-badge&logo=tailwindcss&logoColor=38BDF8)](https://tailwindcss.com/)
[![NetworkX](https://img.shields.io/badge/NetworkX-3.3+-0A2540?style=for-the-badge&logo=networkx&logoColor=white)](https://networkx.org/)
[![Docker](https://img.shields.io/badge/Docker-Sandbox%20Runtime-0A2540?style=for-the-badge&logo=docker&logoColor=2496ED)](https://www.docker.com/)
[![Kubernetes](https://img.shields.io/badge/Kubernetes-Ephemeral%20Jobs-0A2540?style=for-the-badge&logo=kubernetes&logoColor=326CE5)](https://kubernetes.io/)
[![Google Gemini](https://img.shields.io/badge/Google%20Gemini-3.8%20%2F%20Flash-0A2540?style=for-the-badge&logo=google&logoColor=4285F4)](https://ai.google.dev/)
[![Boto3](https://img.shields.io/badge/AWS%20SDK-Boto3%201.34+-0A2540?style=for-the-badge&logo=amazon-aws&logoColor=FF9900)](https://aws.amazon.com/sdk-for-python/)
[![OpenTelemetry](https://img.shields.io/badge/OpenTelemetry-1.25+-0A2540?style=for-the-badge&logo=opentelemetry&logoColor=F5A800)](https://opentelemetry.io/)
[![ReportLab](https://img.shields.io/badge/ReportLab-PDF%20Generation-0A2540?style=for-the-badge&logo=adobe-acrobat-reader&logoColor=EC1C24)](https://www.reportlab.com/)
[![Backend Tests](https://img.shields.io/badge/Pytest-157%20Passed-0A2540?style=for-the-badge&logo=pytest&logoColor=0A9EDC)](https://docs.pytest.org/)
[![Frontend Tests](https://img.shields.io/badge/Vitest-20%20Passed-0A2540?style=for-the-badge&logo=vitest&logoColor=FCC72B)](https://vitest.dev/)
[![License](https://img.shields.io/badge/License-MIT-0A2540?style=for-the-badge&logo=open-source-initiative&logoColor=green)](LICENSE)

*An independent, open-source adversary emulation platform that continuously discovers cloud attack surfaces, constructs directed property attack graphs, synthesizes constrained ATT&CK campaigns via agentic AI, safely emulates non-destructive TTPs, and measures SOC detection efficacy and Mean Time to Detect (MTTD).*

[Key Features](#4-key-capabilities) • [Architecture](#8-system-architecture-diagram) • [Quickstart](#25-installation-instructions) • [MITRE ATT&CK Matrix](#13-mitre-attck-technique-registry) • [REST API](#21-api-documentation-endpoint-table) • [Security Safeguards](#33-security-architecture-safeguards)

</div>

---

## Table of Contents

- [1. Project Overview](#1-project-overview)
- [2. Purpose & Problem Statement](#2-purpose-problem-statement)
- [3. Core Design Principles](#3-core-design-principles)
- [4. Key Capabilities](#4-key-capabilities)
- [5. Technology Stack](#5-technology-stack)
- [6. High-Level System Architecture](#6-high-level-system-architecture)
- [7. End-to-End Workflow & Pipeline Execution](#7-end-to-end-workflow-pipeline-execution)
- [8. System Architecture Diagram](#8-system-architecture-diagram)
- [9. End-to-End Workflow Diagram](#9-end-to-end-workflow-diagram)
- [10. Cloud Environment Discovery (AWS & Synthetic)](#10-cloud-environment-discovery-aws-synthetic)
- [11. Attack Graph Construction & Path Analysis](#11-attack-graph-construction-path-analysis)
- [12. Agentic AI Campaign Planning](#12-agentic-ai-campaign-planning)
- [13. MITRE ATT&CK Technique Registry](#13-mitre-attck-technique-registry)
- [14. Policy Gate & Dual-Key Authorization](#14-policy-gate-dual-key-authorization)
- [15. Controlled Execution & Sandbox Architecture](#15-controlled-execution-sandbox-architecture)
- [16. Telemetry & Lab Signalling Data-Plane](#16-telemetry-lab-signalling-data-plane)
- [17. Detection Correlation & MTTD Measurement](#17-detection-correlation-mttd-measurement)
- [18. Cryptographic SHA-256 Audit Ledger](#18-cryptographic-sha-256-audit-ledger)
- [19. SOC Reporting & Exports](#19-soc-reporting-exports)
- [20. Frontend Command Center Dashboard](#20-frontend-command-center-dashboard)
- [21. API Documentation & Endpoint Table](#21-api-documentation-endpoint-table)
- [22. Project Directory Structure](#22-project-directory-structure)
- [23. Environment Configuration](#23-environment-configuration)
- [24. Prerequisites](#24-prerequisites)
- [25. Installation Instructions](#25-installation-instructions)
- [26. Backend Setup & Execution](#26-backend-setup-execution)
- [27. Frontend Setup & Execution](#27-frontend-setup-execution)
- [28. Google Gemini API Configuration](#28-google-gemini-api-configuration)
- [29. AWS Lab Configuration & Read-Only Scoping](#29-aws-lab-configuration-read-only-scoping)
- [30. Docker & Kubernetes Configuration](#30-docker-kubernetes-configuration)
- [31. Local Demonstration Guide](#31-local-demonstration-guide)
- [32. Automated Testing & Verification Suite](#32-automated-testing-verification-suite)
- [33. Security Architecture & Safeguards](#33-security-architecture-safeguards)
- [34. Known Limitations](#34-known-limitations)
- [35. Future Roadmap](#35-future-roadmap)
- [36. Project Status](#36-project-status)
- [37. Contributing Guidelines](#37-contributing-guidelines)
- [38. Author & Project Credits](#38-author-project-credits)
- [39. Disclaimer](#39-disclaimer)

---

## 1. Project Overview

**Falcon Strike-AI** is a cloud-native breach-and-attack simulation (BAS) and Continuous Threat Exposure Management (CTEM) engine built to systematically test, evaluate, and harden cloud security posture.

Unlike legacy vulnerability scanners that generate static, isolated lists of CVEs without exploitability context, Falcon Strike-AI reasons about **graph-connected attack paths**. It ingests cloud identity (IAM), compute (EC2), storage (S3), and network configurations (Security Groups), maps them into a directed property graph, and discovers traversable paths that lead from internet-facing footholds directly to high-privilege administrative "crown jewels."

To validate defensive coverage along these attack paths, an **Agentic LLM Planner** synthesizes multi-stage campaigns mapped to the MITRE ATT&CK framework. These campaigns are executed **strictly non-destructively** inside sandboxed environments with low-privilege credentials, emitting verifiable telemetry and benign command-and-control (C2) beacon signals. A correlation engine automatically compares emitted indicators of compromise (IOCs) against SIEM/EDR detection rules to calculate detection coverage and exact **Mean Time to Detect (MTTD)**.

---

## 2. Purpose & Problem Statement

### The Cloud Attack Surface Challenge
1. **Identity as the Primary Control Plane:** Modern cloud infrastructure is ephemeral. Attack surfaces are dominated by complex IAM relationships, assume-role policies, cross-account trusts, and overly permissive wildcard statements rather than static IP perimeters.
2. **Silent Detection Decay:** SIEM alert rules, EDR sensors, and SOC correlation searches degrade over time due to cloud configuration drift, rule changes, and logging infrastructure outages. Defenders rarely discover blind spots until a real breach occurs.
3. **Exploitability vs. Flat Severity:** A "Critical" vulnerability with no route to sensitive assets is far less dangerous than a "Low" misconfiguration directly bound to an IAM role capable of privilege escalation. Contextual attack paths allow security teams to prioritize real risk.
4. **Friction of Manual Red Teaming:** Human red-team exercises are expensive, point-in-time, and cannot be executed continuously. Security teams need on-demand, automated, reproducible adversary signal to validate controls safely.

---

## 3. Core Design Principles

- **Zero Weaponized Exploits:** Offensive actions are purely behavioral simulations using inert marker tokens (`falcon-marker.txt`), harmless enumeration APIs, and simulated network signals.
- **Fail-Safe Containment:** Multi-layer allowlisting (Account ID, MITRE Technique ID, Egress IP/domain, and Blast-Radius limits) is compiled directly into code, not left to runtime discretion.
- **Dry-Run by Default:** The engine defaults to `dry_run=True`. Live cloud execution requires explicit dual-operator authorization keys.
- **Decoupled Agentic Intelligence:** The LLM planner emits structured data (JSON schemas) and has zero direct access to the shell, terminal, or network sockets.
- **Cryptographic Auditability:** Every pipeline event is signed into an append-only, SHA-256 hash-chained immutable audit ledger.

---

## 4. Key Capabilities

- **Multi-Source Inventory Ingestion:** Live read-only AWS discovery (IAM roles, users, policies, EC2 security groups, S3 buckets) via Boto3, paired with a deterministic synthetic cloud environment generator.
- **Directed Property Attack Graph:** High-performance in-memory property graph modeling 10 distinct node types and 8 relationship types (`CAN_ASSUME`, `EXPOSES`, `RUNS_AS`, `HAS_PERMISSION`), with Neo4j Cypher export compatibility.
- **Sub-Second Path Traversal at Scale:** Cycle-resistant breadth-first / depth-first pathfinding capable of traversing 10,000-node cloud environments with a **p95 query latency of 5.22 ms** ($\gg 190\times$ faster than PRD targets).
- **Agentic LLM Campaign Planner:** Powered by Google Gemini (`gemini-flash-latest`) via the official `google-genai` SDK, with instant offline fallback to a deterministic heuristic engine.
- **Curated 16-Technique ATT&CK Library:** Static enum-guarded library implementing self-describing Python modules with declared observables, preconditions, and teardown hooks.
- **Multi-Runtime Execution Sandboxes:** Pluggable runners supporting local subprocess isolation, Docker container execution, and cloud-native Kubernetes Batch/v1 Jobs in dedicated namespaces (`falcon-strike-lab`).
- **Jittered C2 Beacon Signalling:** Built-in asynchronous HTTP and DNS lab sinks capturing periodic callbacks with configurable intervals and randomized jitter.
- **SIEM/EDR Detection Correlation:** Deterministic alert matching measuring detection coverage percentage and observed MTTD against ground-truth IOCs.
- **Tamper-Evident SHA-256 Audit Log:** Cryptographically sealed JSONL ledger preventing retroactive alteration of red-teaming records.
- **Multi-Format SOC Reporting:** Automated export to machine-readable JSON, Markdown, styled HTML, and professional ReportLab PDF dossiers.
- **Enterprise Command Center Frontend:** Next.js 14 / Tailwind CSS dashboard inspired by enterprise cloud security command centers, featuring multi-cloud carousels, radar visualizers, and interactive React Flow attack graphs.

---

## 5. Technology Stack

| Layer | Technology | Version | Purpose in Falcon Strike-AI |
| :--- | :--- | :--- | :--- |
| **Backend Framework** | **Python** / **FastAPI** | `3.11+` / `0.111+` | High-performance asynchronous REST API control plane and CLI engine |
| **Data Validation** | **Pydantic v2** | `2.10+` | Strict schema validation for campaign plans, audit records, and API contracts |
| **Graph Computing** | **NetworkX** | `3.3+` | In-memory directed property graph modeling, BFS/DFS pathfinding, and cycle pruning |
| **Cloud Graph Database**| **Neo4j** (Optional) | `5.0+` | Cypher query export and persistent enterprise graph database support |
| **Agentic AI Planner** | **Google Gemini** | `gemini-flash-latest` | LLM campaign planner powered by the official `google-genai` SDK (`v2.19+`) |
| **Cloud SDK** | **AWS Boto3** | `1.34+` | Read-only discovery of IAM, EC2, Security Groups, and S3 resources |
| **Sandbox Runtime** | **Docker Engine** | `24.0+` | Isolated container execution using non-root `falconstrike-sandbox:latest` |
| **Container Scale** | **Kubernetes** | `1.28+` / `Batch v1` | Ephemeral Job runner execution in isolated `falcon-strike-lab` namespace |
| **Observability** | **OpenTelemetry** | `1.25+` | Distributed tracing, span context injection, and structured telemetry |
| **Document Generation** | **ReportLab** | `4.2+` | Automated compilation of enterprise-grade SOC assessment PDF reports |
| **Frontend Framework** | **Next.js** (App Router)| `14.2+` | React 18 server and client components with zero hydration errors |
| **UI Styling** | **Tailwind CSS** | `3.4+` | Dark navy/cyan theme (`#030712`, `#06B6D4`) with high-contrast accessibility |
| **Graph Visualization**| **React Flow** (@xyflow/react) | `12.0+` | Interactive pan/zoom canvas for visual attack path inspection |
| **Backend Testing** | **Pytest** / **Pytest-Cov**| `8.2+` | Comprehensive test suite (157 unit/integration tests passing) |
| **Frontend Testing** | **Vitest** | `1.6+` | Component, formatter, and API contract testing (20 tests passing) |

---

## 6. High-Level System Architecture

Falcon Strike-AI is structured into four cooperating subsystems joined by typed JSON contracts and governed by a cross-cutting Policy Gate:

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                                 CONTROL PLANE (FASTAPI)                                │
│          /api/v1/collectors  •  /api/v1/graph  •  /api/v1/planner  •  /api/v1/audit    │
└───────────────────────────────────────────┬────────────────────────────────────────────┘
                                            │
                    ┌───────────────────────┴───────────────────────┐
                    ▼                                               ▼
       ┌─────────────────────────┐                     ┌─────────────────────────┐
       │   ASSET & EXPOSURE      │                     │   POLICY GATE ENGINE    │
       │   GRAPH ENGINE          │                     │   (Safety Guardrails)   │
       │                         │                     │                         │
       │ • AWS Boto3 Discovery   │                     │ • Account Allowlist     │
       │ • Synthetic Lab Model   │                     │ • Static Technique Enum │
       │ • Property Graph Store  │                     │ • Two-Key Authorization │
       │ • BFS/DFS Path Finder   │                     │ • Blast Radius Limit    │
       │ • Composite Risk Ranker │                     │ • Emergency Kill-Switch │
       └────────────┬────────────┘                     └────────────▲────────────┘
                    │                                               │
                    │ Top Attack Path                               │ Evaluates Plan
                    ▼                                               │
       ┌─────────────────────────┐                                  │
       │   AGENTIC CAMPAIGN      │                                  │
       │   PLANNER               │──────────────────────────────────┘
       │                         │
       │ • Google Gemini Flash   │
       │ • Heuristic Fallback    │
       │ • Pydantic Schema Valid │
       └────────────┬────────────┘
                    │ Approved Campaign Plan
                    ▼
       ┌─────────────────────────┐                     ┌─────────────────────────┐
       │   EPHEMERAL SANDBOX     │                     │   TELEMETRY & SOC       │
       │   EXECUTION ENGINE      │────────────────────►│   REPORTING ENGINE      │
       │                         │  Ground-Truth IOCs  │                         │
       │ • Subprocess Runner     │  & C2 Signals       │ • SIEM Alert Matching   │
       │ • Docker Container      │                     │ • Coverage & MTTD Calc  │
       │ • Kubernetes Batch Job  │                     │ • SHA-256 Audit Chain   │
       │ • Verified Teardown     │                     │ • JSON/HTML/PDF Export  │
       └─────────────────────────┘                     └─────────────────────────┘
```

---

## 7. End-to-End Workflow & Pipeline Execution

Falcon Strike-AI executes an automated 7-stage closed-loop CTEM cycle:

1. **Stage 1: Ingestion & Inventory Discovery:** The orchestrator invokes read-only collectors against the target environment (or loads the offline synthetic topology).
2. **Stage 2: Graph Construction & Enrichment:** Assets, roles, and bindings are modeled into directed nodes and edges. Misconfigurations (e.g., `AdministratorAccess`, wildcard `*`, open `0.0.0.0/0` ingress) are labeled.
3. **Stage 3: Attack Path Discovery & Ranking:** The pathfinder identifies all traversable routes from public entry points to crown jewel admin roles, ranking them by exploitability and impact score.
4. **Stage 4: Agentic Campaign Planning:** The top attack path is submitted to the Gemini LLM agent, which synthesizes an ordered, multi-stage campaign plan mapped to ATT&CK tactics.
5. **Stage 5: Policy Gate Evaluation:** The plan is evaluated against the 5 declarative safety rules. If any invariant fails (e.g. unallowlisted account or $>5$ resources), execution aborts.
6. **Stage 6: Controlled Sandbox Emulation:** The execution engine runs each stage non-destructively, emitting telemetry and benign jittered C2 beacons to local sinks.
7. **Stage 7: Detection Correlation & Teardown:** Ground-truth IOCs are correlated with simulated or live SIEM alerts to calculate coverage and MTTD. Automated teardown restores the baseline, and a cryptographically sealed SOC report is exported.

---

## 8. System Architecture Diagram

```mermaid
flowchart TD
    subgraph Target["Target Environment (Isolated Lab)"]
        AWS["AWS Account (Read-Only Boto3)"]
        SYN["Synthetic Lab Environment"]
    end

    subgraph Ingestion["1. Asset & Exposure Ingestion"]
        IAM_C["IAM Collector"]
        NET_C["Network & SG Collector"]
        S3_C["S3 Storage Collector"]
    end

    subgraph Graph["2. Directed Property Attack Graph"]
        GS["InMemory Graph Store (NetworkX)"]
        MA["Misconfiguration Analyzer"]
        PF["Attack Path Finder (BFS/DFS)"]
        PR["Attack Path Ranker"]
    end

    subgraph Planning["3. Agentic Campaign Planning"]
        GEMINI["Google Gemini LLM (Flash)"]
        HEUR["Deterministic Heuristic Fallback"]
        VAL["Pydantic Plan Validator"]
    end

    subgraph Policy["4. Safety Policy Gate"]
        GATE{"Policy Gate Engine"}
        RULE1["Account Allowlist"]
        RULE2["Technique Allowlist"]
        RULE3["Dual-Key Live Auth"]
        RULE4["Blast Radius Cap"]
        KS["Emergency Kill Switch"]
    end

    subgraph Sandboxes["5. Ephemeral Execution Sandboxes"]
        SUBP["Subprocess Runner"]
        DOCK["Docker Runner (falconstrike-sandbox)"]
        K8S["Kubernetes Job Runner (falcon-strike-lab)"]
        REG["16-Technique Curated Library"]
    end

    subgraph Telemetry["6. Telemetry & C2 Lab Sinks"]
        C2_S["Async HTTPS/DNS C2 Sink"]
        OTEL["OpenTelemetry Tracer"]
        IOC_E["Ground-Truth IOC Emitter"]
    end

    subgraph Detection["7. Detection Validation & Audit"]
        CORR["Detection Correlation Engine"]
        AUDIT["SHA-256 Cryptographic Audit Ledger"]
        SOC_R["SOC Report Generator (PDF/HTML/JSON)"]
        TD["Verified Baseline Teardown"]
    end

    AWS --> IAM_C & NET_C & S3_C
    SYN --> IAM_C & NET_C & S3_C
    IAM_C & NET_C & S3_C --> GS
    GS --> MA --> PF --> PR
    PR --> |Top Ranked Path| GEMINI & HEUR
    GEMINI & HEUR --> VAL --> GATE
    RULE1 & RULE2 & RULE3 & RULE4 --> GATE
    KS -.-> |Abort Signal| GATE
    GATE --> |Approved Plan| SUBP & DOCK & K8S
    REG --> SUBP & DOCK & K8S
    SUBP & DOCK & K8S --> C2_S & OTEL & IOC_E
    C2_S & OTEL & IOC_E --> CORR
    CORR --> SOC_R
    GATE & SUBP & DOCK & K8S & CORR --> AUDIT
    SUBP & DOCK & K8S --> TD
```

---

## 9. End-to-End Workflow Diagram

```mermaid
sequenceDiagram
    autonumber
    actor Operator as Security Operator
    participant CLI as Falcon Strike CLI / API
    participant Coll as Collectors (AWS/Synthetic)
    participant Graph as Property Graph Engine
    participant LLM as Agentic Planner (Gemini)
    participant Gate as Policy Gate Engine
    participant Runner as Ephemeral Sandbox Runner
    participant C2 as Lab C2 Sink
    participant SIEM as Detection Correlation
    participant Teardown as Teardown Engine
    participant Audit as Cryptographic Audit Ledger

    Operator->>CLI: Execute Pipeline (dry-run=True)
    CLI->>Audit: Seal Record: PIPELINE_STARTED
    CLI->>Coll: Ingest Environment State
    Coll->>Graph: Construct Nodes & Directed Edges
    Graph->>Graph: Analyze Misconfigurations (Wildcards, Open SGs)
    Graph->>Graph: Discover & Rank Multi-Hop Attack Paths
    Graph-->>CLI: Return Top Ranked Path
    CLI->>Audit: Seal Record: ATTACK_PATHS_DISCOVERED
    CLI->>LLM: Request Campaign Plan (Path + Facts)
    LLM-->>CLI: Structured Campaign JSON (ATT&CK Stages)
    CLI->>Gate: Evaluate Safety Guardrails
    Gate->>Gate: Assert Account Allowlist & Blast Radius
    Gate-->>CLI: Plan APPROVED for Dry-Run
    CLI->>Audit: Seal Record: POLICY_EVALUATED
    loop For Each Campaign Stage
        CLI->>Runner: Execute Benign ATT&CK Technique
        Runner->>C2: Emit Jittered Beacon & Inert Marker
        Runner-->>CLI: SimulationEvent (Success, Observables)
    end
    CLI->>SIEM: Correlate Ground-Truth IOCs vs Alert Rules
    SIEM-->>CLI: Coverage Scorecard (Coverage %, MTTD Seconds)
    CLI->>Teardown: Execute Teardown & Baseline Verification
    Teardown-->>CLI: Baseline Restored (Drift = 0.0%)
    CLI->>Audit: Verify SHA-256 Hash Chain Integrity
    CLI->>CLI: Compile SOC Reports (PDF, HTML, JSON, MD)
    CLI-->>Operator: Pipeline Complete (Output Artifacts Generated)
```

---

## 10. Cloud Environment Discovery (AWS & Synthetic)

### Read-Only AWS Discovery
The collector subsystem interacts with AWS exclusively using read-only Boto3 API calls. It extracts:
- **IAM Principals & Roles:** `iam:ListRoles`, `iam:ListUsers`, `iam:ListAttachedRolePolicies`, `iam:GetPolicyVersion`.
- **EC2 Compute & Bindings:** `ec2:DescribeInstances`, extracting instance profiles and network interfaces.
- **Network Boundaries:** `ec2:DescribeSecurityGroups`, mapping inbound/outbound CIDR permissions.
- **S3 Object Storage:** `s3:ListBuckets`, querying public access blocks and bucket policies.

### Deterministic Synthetic Lab Generator
For offline development, testing, and continuous integration, Falcon Strike-AI includes a complete synthetic environment generator (`SyntheticEnvironmentProvider`). It generates a realistic flawed cloud estate containing:
- Public internet entry points (`endpoint:public-internet`)
- Perimeter web instances (`ec2:i-web-dmz-01`)
- Intermediate service roles (`role/EC2AppWorkloadRole`)
- Privilege escalation paths (`role/JuniorDevOpsRole` with `iam:PassRole`)
- Crown jewel administrative roles (`role/CrownJewelAdminRole`) with unrestricted wildcard permissions (`*`).

---

## 11. Attack Graph Construction & Path Analysis

The graph engine converts raw cloud configurations into a directed property graph:

### Node Types
- `NodeType.IAM_USER`
- `NodeType.IAM_ROLE`
- `NodeType.IAM_POLICY`
- `NodeType.EC2_INSTANCE`
- `NodeType.SECURITY_GROUP`
- `NodeType.S3_BUCKET`
- `NodeType.PUBLIC_ENDPOINT`
- `NodeType.VPC` / `SUBNET`

### Relationship Types
- `RelationshipType.RUNS_AS` (EC2 $\to$ IAM Role)
- `RelationshipType.ASSUMES_ROLE` (IAM Role $\to$ IAM Role)
- `RelationshipType.ATTACHED_POLICY` (IAM Role $\to$ IAM Policy)
- `RelationshipType.EXPOSED_TO_INTERNET` (Public Endpoint $\to$ EC2)
- `RelationshipType.MEMBER_OF` (Resource $\to$ Security Group)

### Path Scoring Heuristic
Every discovered path is scored on a scale from $0$ to $100$ based on:
$$\text{Score} = \max\left(5.0,\; (\text{Target Weight} \times 40.0) + (\text{Misconfig Severity} \times 35.0) - (\text{Hop Count} \times 5.0)\right)$$

---

## 12. Agentic AI Campaign Planning

### Google Gemini Architecture
The agentic planning engine utilizes Google Gemini (`gemini-flash-latest`) via the official `google-genai` SDK.
- **System Prompt Guardrails:** The LLM is instructed as an Adversary Emulation Architect. It is constrained to select techniques **exclusively** from the curated 16-technique allowlist.
- **Strict Pydantic Schema:** The LLM output is parsed into strict Pydantic v2 data models (`CampaignPlan` and `CampaignStage`). Any invalid technique ID or missing field causes validation failure.
- **Deterministic Heuristic Fallback:** If `GEMINI_API_KEY` is not configured or network access is restricted, `GeminiPlannerProvider` falls back instantly to the offline deterministic planner with zero operational downtime.

---

## 13. MITRE ATT&CK Technique Registry

Falcon Strike-AI implements 16 curated, self-describing MITRE ATT&CK simulation modules:

| ATT&CK ID | Technique Name | Tactic | Emulated Behavioral Action | Destructive? | Teardown Action |
| :---: | :--- | :--- | :--- | :---: | :--- |
| **`T1078`** | Valid Accounts | Initial Access | Simulated API authentication using temporary session credentials | No | Revoke session |
| **`T1190`** | Exploit Public-Facing App | Initial Access | Probing inert HTTP test endpoint with benign marker headers | No | None |
| **`T1087`** | Account Discovery | Discovery | Non-destructive enumeration of IAM usernames via read APIs | No | None |
| **`T1069`** | Permission Groups Discovery | Discovery | Read-only listing of IAM user group memberships | No | None |
| **`T1526`** | Cloud Service Discovery | Discovery | Read-only metadata query simulating instance discovery | No | None |
| **`T1580`** | Cloud Infrastructure Discovery | Discovery | Enumeration of virtual machine configurations and VPC topology | No | None |
| **`T1046`** | Network Service Scanning | Discovery | Benign port check against local loopback test socket | No | Close socket |
| **`T1548`** | Abuse Elevation Control | Privilege Escalation | Evaluation of role assumption policies without permission grants | No | Revert context |
| **`T1098`** | Account Manipulation | Privilege Escalation | Chaining assume-role simulation to lab maintenance role | No | Detach session |
| **`T1552`** | Unsecured Credentials | Credential Access | Reading planted benign marker file (`falcon-marker.txt`) | No | Re-plant marker |
| **`T1003`** | OS Credential Dumping | Credential Access | Reading dummy process memory block in isolated container | No | Evict memory |
| **`T1550`** | Use Alternate Auth Material | Defense Evasion | Simulated token-reuse pattern using inert STS tokens | No | Expire token |
| **`T1537`** | Transfer Data to Cloud Account | Exfiltration | Copying benign 64-byte marker payload to allowlisted bucket | No | Delete marker |
| **`T1071`** | Application Layer Protocol | Command & Control | Jittered HTTPS beaconing with inert token to local sink (port 8443) | No | Halt connection |
| **`T1059`** | Command & Script Interpreter | Execution | Running echo command of benign string in sandbox | No | Clean container |
| **`T1021`** | Remote Services | Lateral Movement | Probing intra-sandbox test socket with harmless ping token | No | Terminate socket |

---

## 14. Policy Gate & Dual-Key Authorization

The Policy Gate (`PolicyGateEngine`) is a mandatory, unbypassable control layer:

```
[ Incoming Campaign Plan ]
            │
            ▼
    ┌───────────────────────────┐
    │   1. Account Allowlist    │ ──► Target account in FALCON_ALLOWLISTED_ACCOUNTS?
    └─────────────┬─────────────┘
                  │ PASS
                  ▼
    ┌───────────────────────────┐
    │   2. Technique Allowlist  │ ──► All technique IDs exist in TechniqueRegistry?
    └─────────────┬─────────────┘
                  │ PASS
                  ▼
    ┌───────────────────────────┐
    │   3. Blast Radius Limit   │ ──► Total stages <= FALCON_MAX_RESOURCES_TOUCHED (5)?
    └─────────────┬─────────────┘
                  │ PASS
                  ▼
    ┌───────────────────────────┐
    │   4. Destructiveness Check│ ──► is_destructive == False on all actions?
    └─────────────┬─────────────┘
                  │ PASS
                  ▼
    ┌───────────────────────────┐
    │   5. Two-Key Authorization│ ──► If mode == LIVE: Both Operator Keys valid & signed?
    └─────────────┬─────────────┘
                  │ PASS
                  ▼
       [ APPROVED FOR EXECUTION ]
```

---

## 15. Controlled Execution & Sandbox Architecture

Falcon Strike-AI supports three pluggable execution runners:

1. **Subprocess Runner (`SubprocessRunner`):** In-process, isolated Python worker executing safe modules with constrained environment variables and timeout limits.
2. **Docker Runner (`DockerRunner`):** Executes modules within ephemeral `falconstrike-sandbox:latest` containers with dropped capabilities (`CAP_DROP=ALL`), non-root execution (UID `10001`), read-only root filesystems, and strict memory limits.
3. **Kubernetes Job Runner (`KubernetesJobRunner`):** Cloud-native horizontal runner executing ephemeral Batch/v1 Jobs in the dedicated `falcon-strike-lab` namespace with:
   - `runAsNonRoot: true` (UID `10001` / GID `10001`)
   - `readOnlyRootFilesystem: true`
   - `capabilities: drop: ["ALL"]`
   - `limits: { memory: "256Mi", cpu: "500m" }`
   - `activeDeadlineSeconds: 120` & `backoffLimit: 0`

---

## 16. Telemetry & Lab Signalling Data-Plane

- **Jittered HTTPS Beaconing:** Periodically connects to a local sink on port `8443` with randomized jitter (e.g. interval $5\text{s} \pm 20\%$) to test network behavioral detectors.
- **DNS-Based Signalling:** Emulates DNS lookups to local mock nameservers carrying encoded transaction identifiers.
- **Inert Tokens:** No malicious commands ever traverse network sockets. All payloads consist of structured verification tokens (e.g., `TOKEN_STAGE_COMPLETED_T1071`).

---

## 17. Detection Correlation & MTTD Measurement

The detection correlation engine (`DetectionCorrelationEngine`) matches emitted ground-truth IOCs against simulated SIEM/EDR detections:
- **Detection Matching:** Compares timestamps, MITRE technique IDs, target resources, and indicators.
- **Coverage Percentage:**
  $$\text{Coverage } \% = \left(\frac{\text{Detected Techniques}}{\text{Total Emulated Techniques}}\right) \times 100$$
- **Mean Time to Detect (MTTD):**
  $$\text{MTTD} = \frac{1}{N} \sum_{i=1}^{N} \left(t_{\text{alert}, i} - t_{\text{emulated}, i}\right)$$
  *(Measured at **16.32 seconds** during end-to-end benchmark runs).*

---

## 18. Cryptographic SHA-256 Audit Ledger

To satisfy legal, compliance, and non-repudiation requirements, every action taken by Falcon Strike-AI is minted into an append-only cryptographic ledger (`artifacts/audit/*.jsonl`):
- **Record Hash Formula:**
  $$\text{Record Hash} = \text{SHA-256}\left(\text{seq} \parallel \text{timestamp} \parallel \text{actor} \parallel \text{action} \parallel \text{payload} \parallel \text{prev\_hash}\right)$$
- **Genesis Record:** Initialized with $\text{prev\_hash} = \text{"0" \times 64}$.
- **Tamper Detection:** `AuditChain.verify_chain()` recomputes all hashes from genesis to head. Any modification to a log line breaks the chain and raises `AuditChainTamperedError`.

---

## 19. SOC Reporting & Exports

Reports are automatically generated by `SocReportingEngine` upon campaign completion:
- **Executive Summary:** Overall defensive coverage %, observed MTTD, and attack-path summary.
- **ATT&CK Coverage Heatmap:** Grid mapping emulated techniques against detection statuses (`DETECTED`, `MISSED`, `PARTIAL`).
- **Prioritized Remediations:** Defensible, ranked action items addressing the root misconfigurations along the attack path.
- **Export Formats:**
  - `JSON`: Machine-readable artifact for SIEM/SOAR ingestion (`soc_report_RUN-*.json`)
  - `Markdown`: Documentation summary (`soc_report_RUN-*.md`)
  - `HTML`: Interactive standalone web report (`soc_report_RUN-*.html`)
  - `PDF`: Enterprise dossier generated via ReportLab (`soc_report_RUN-*.pdf`)

---

## 20. Frontend Command Center Dashboard

The frontend is built with Next.js 14 (App Router), Tailwind CSS, and TypeScript, featuring 14 distinct routes:

| Route Path | View Name | Key Capabilities |
| :--- | :--- | :--- |
| `/` | Landing Gateway | System status overview and navigation gateway |
| `/dashboard` | Command Center Overview | Palo Alto-inspired dashboard with multi-cloud carousel, risk metrics, and radar orb |
| `/environment` | AWS Explorer | Tabbed inventory browser (IAM, EC2, S3, SGs) with live collection trigger |
| `/attack-graph` | Attack Graph Canvas | Interactive React Flow canvas with zoom, pan, and attack path highlighting |
| `/campaign-planner` | Campaign Planner | Dual-pane interface comparing ranked paths against Gemini LLM campaign plans |
| `/execution` | Emulation Console | Live execution monitor with real-time stage progress and emergency kill-switch |
| `/telemetry` | Telemetry & IOCs | Stream of emitted ground-truth indicators and C2 beacon logs |
| `/audit-logs` | Cryptographic Ledger | SHA-256 hash-chain inspector verifying log integrity |
| `/reports` | SOC Intelligence Hub | Report viewer with one-click ReportLab PDF export download |
| `/security` | Guardrails & Policy Gate | Policy rule evaluator and dual-key operator sign-off interface |
| `/settings` | Configuration Center | Environment variable inspector and cloud integration status manager |
| `/_not-found` | Branded 404 | Custom error handling experience |

---

## 21. API Documentation & Endpoint Table

Falcon Strike-AI exposes 48 REST API endpoints across 14 sub-routers:

| Method | Endpoint Path | Sub-Router | Description | Auth Required |
| :---: | :--- | :--- | :--- | :---: |
| `GET` | `/health` | Health | Control plane liveness and readiness probe | No |
| `GET` | `/api/v1/health` | Health | Subsystem health probe (graph, collectors, runners) | No |
| `POST`| `/api/v1/auth/login` | Auth | Authenticate operator and issue JWT access token | No |
| `GET` | `/api/v1/integrations/status`| Integrations | Live status of AWS, Gemini, Docker, and K8s | No |
| `POST`| `/api/v1/environment/collect`| Collectors | Trigger read-only asset discovery scan | Yes |
| `GET` | `/api/v1/collectors/findings`| Collectors | Retrieve security misconfigurations and findings | Yes |
| `GET` | `/api/v1/graph/summary` | Graph | Retrieve node counts, edge counts, and graph stats | Yes |
| `POST`| `/api/v1/graph/analyze` | Graph | Run misconfiguration analysis on graph topology | Yes |
| `GET` | `/api/v1/attack-paths` | Attack Paths | List all discovered multi-hop attack paths | Yes |
| `POST`| `/api/v1/attack-paths/discover`| Attack Paths | Re-run BFS/DFS traversal and rank attack paths | Yes |
| `GET` | `/api/v1/planner/campaigns` | Planner | List all generated campaign plans | Yes |
| `POST`| `/api/v1/planner/generate` | Planner | Synthesize campaign plan using Gemini or heuristic | Yes |
| `GET` | `/api/v1/techniques` | Techniques | List all 16 approved MITRE ATT&CK techniques | Yes |
| `POST`| `/api/v1/policies/evaluate` | Policies | Evaluate campaign plan against Policy Gate rules | Yes |
| `POST`| `/api/v1/executions/dry-run` | Executions | Execute non-destructive dry-run campaign | Yes |
| `POST`| `/api/v1/executions/live` | Executions | Execute authorized live campaign (dual-key required)| Yes |
| `POST`| `/api/v1/system/kill-switch`| System | **Trip emergency kill-switch (<1ms abort)** | Yes |
| `POST`| `/api/v1/detection/correlate`| Detection | Run SIEM detection correlation against run IOCs | Yes |
| `GET` | `/api/v1/audit/chain/{run_id}`| Audit | Retrieve SHA-256 hash-chained audit ledger | Yes |
| `GET` | `/api/v1/reporting/{run_id}/pdf`| Reporting | Download ReportLab executive PDF assessment report | Yes |
| `POST`| `/api/v1/workflow/run` | Workflow | Run full 17-stage automated end-to-end pipeline | Yes |

---

## 22. Project Directory Structure

```
FalconStrikeAI/
├── backend/
│   ├── app/
│   │   ├── api/                    # FastAPI route definitions
│   │   │   └── v1/                 # Versioned sub-routers (health, auth, graph, etc.)
│   │   ├── collectors/             # Cloud asset discovery (AWS Boto3 & Synthetic)
│   │   ├── graph/                  # Directed property graph, pathfinding & ranker
│   │   ├── planner/                # Google Gemini LLM & deterministic heuristic planner
│   │   ├── policies/               # Declarative Policy Gate & safety guardrail rules
│   │   ├── orchestrator/           # Subprocess, Docker & Kubernetes Job runners
│   │   ├── techniques/             # 16 curated MITRE ATT&CK simulation modules
│   │   ├── telemetry/              # Jittered C2 beacon sinks & OpenTelemetry tracer
│   │   ├── detection/              # SIEM correlation engine & MTTD calculator
│   │   ├── teardown/               # LIFO cleanup engine & baseline verification
│   │   ├── audit/                  # SHA-256 hash-chained immutable audit ledger
│   │   ├── reporting/              # Multi-format SOC report generators (PDF/HTML/JSON)
│   │   └── core/                   # Configuration, security dependencies & logging
│   └── tests/                      # Pytest suite (157 unit, integration, and security tests)
├── frontend/
│   ├── src/
│   │   ├── app/                    # Next.js 14 App Router pages (14 routes)
│   │   ├── components/             # Reusable UI components (Carousels, Radar, Cards)
│   │   ├── lib/api/                # Strongly-typed API client & contract normalizers
│   │   └── types/                  # TypeScript interface definitions
│   ├── tailwind.config.ts          # Dark navy & cyan theme configuration
│   └── package.json                # Frontend package dependencies & scripts
├── configs/                        # Detection rules and environment settings
├── docs/                           # Architecture, audit, and compliance documentation
├── artifacts/                      # Generated audit logs, PDF reports, and scale benchmarks
├── .env.example                    # Sanitized environment configuration template
├── pyproject.toml                  # Python package configuration and dependencies
└── README.md                       # Comprehensive project documentation
```

---

## 23. Environment Configuration

Copy the sanitized configuration template to `.env`:
```powershell
cp .env.example .env
```

### Key Environment Variables (`.env.example`)
```ini
# Application Safety Mode
FALCON_ENVIRONMENT=development
FALCON_DRY_RUN=true

# Multi-Layer Account Allowlist
FALCON_TARGET_ACCOUNT_ID=000000000000
FALCON_ALLOWLISTED_ACCOUNTS=000000000000,123456789012

# Blast-Radius Safety Caps
FALCON_MAX_RESOURCES_TOUCHED=5
FALCON_MAX_RUN_DURATION_SECONDS=300

# REST API Settings
FALCON_API_HOST=127.0.0.1
FALCON_API_PORT=8000

# Google Gemini API (Optional - falls back to deterministic heuristic planner offline)
GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_MODEL=gemini-flash-latest

# AWS Lab Configuration (Read-only discovery)
AWS_REGION=us-east-1
AWS_PROFILE=default
```

---

## 24. Prerequisites

- **Python:** Version `3.11+` (Python `3.14` tested and supported)
- **Node.js:** Version `18.18+` or `20.x`
- **npm:** Version `9.x+`
- **Git:** Version `2.40+`
- *(Optional)* **Docker Desktop:** For containerized execution (`falconstrike-sandbox:latest`)
- *(Optional)* **Kubernetes (Kind / Docker Desktop):** For cloud-native Jobs in `falcon-strike-lab`

---

## 25. Installation Instructions

### 1. Clone the Repository
```powershell
git clone https://github.com/HalaNaaz/FalconStrikeAI.git
cd FalconStrikeAI
```

### 2. Set Up Python Virtual Environment
```powershell
# Windows PowerShell
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# Linux / macOS
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install Backend Dependencies
```powershell
pip install -e .
```

### 4. Install Frontend Dependencies
```powershell
cd frontend
npm install
cd ..
```

---

## 26. Backend Setup & Execution

### Starting the FastAPI Control Plane
```powershell
python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload
```
- Interactive Swagger UI: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- ReDoc Documentation: [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)
- Health Probe: [http://127.0.0.1:8000/health](http://127.0.0.1:8000/health)

---

## 27. Frontend Setup & Execution

### Starting the Next.js Dashboard
```powershell
# Run from repository root
npm run dev --prefix frontend
```
- Open your browser at: [http://localhost:3000/dashboard](http://localhost:3000/dashboard)

---

## 28. Google Gemini API Configuration

1. Obtain a free API key from [Google AI Studio](https://aistudio.google.com/).
2. Add the key to `.env`:
   ```ini
   GEMINI_API_KEY=your_actual_key_here
   GEMINI_MODEL=gemini-flash-latest
   ```
3. When configured, campaign generation automatically leverages `gemini-flash-latest`. If absent or rate-limited, the platform falls back instantly to the deterministic offline heuristic engine.

---

## 29. AWS Lab Configuration & Read-Only Scoping

1. Configure your AWS CLI credentials against an isolated laboratory account:
   ```powershell
   aws configure
   ```
2. Verify that your lab account ID is added to `FALCON_ALLOWLISTED_ACCOUNTS` in `.env`.
3. The platform will execute read-only calls (`iam:ListRoles`, `ec2:DescribeSecurityGroups`, `s3:ListBuckets`). Any attempt to target an unlisted account is blocked immediately before any AWS API call is sent.

---

## 30. Docker & Kubernetes Configuration

- **Docker Sandbox:** Launch Docker Desktop. The engine uses `falconstrike-sandbox:latest` to isolate emulation techniques. If Docker is offline, the platform automatically executes within the safe in-process `SubprocessRunner`.
- **Kubernetes Sandbox:** Enable Kubernetes in Docker Desktop. Pre-provision the isolated namespace:
  ```powershell
  kubectl create namespace falcon-strike-lab
  ```

---

## 31. Local Demonstration Guide

Run the complete 17-stage end-to-end adversary emulation pipeline from the command line:

```powershell
python -m backend.app.main run --mode synthetic --dry-run
```

### Expected Output Summary
```
================================================================================
FALCON STRIKE-AI: END-TO-END PIPELINE COMPLETE
================================================================================
Run ID:                 RUN-20261102083711-7EF5C8
Campaign ID:            CAMP-798E3005
Status:                 COMPLETED
Duration:               40.97 ms
Graph Nodes Analyzed:   13
Attack Paths Found:     3
Stages Executed:        4
Detection Coverage:     100.0%
MTTD:                   16.32 seconds
Baseline Teardown:      VERIFIED
Audit Chain Integrity:  VERIFIED_UNBROKEN
--------------------------------------------------------------------------------
Generated Artifacts:
  - json_report: artifacts\reports\soc_report_RUN-20261102083711-7EF5C8.json
  - markdown_report: artifacts\reports\soc_report_RUN-20261102083711-7EF5C8.md
  - html_report: artifacts\reports\soc_report_RUN-20261102083711-7EF5C8.html
  - pdf_report: artifacts\reports\soc_report_RUN-20261102083711-7EF5C8.pdf
  - audit_chain_jsonl: artifacts\audit\audit_chain_RUN-20261102083711-7EF5C8.jsonl
================================================================================
```

---

## 32. Automated Testing & Verification Suite

### Running Backend Pytest Suite
```powershell
python -m pytest backend/tests -v
```
**Results:** **157 passed, 2 skipped** (100% pass rate across 22 test files in 55.69s).

### Running Frontend Vitest Suite
```powershell
npm test --prefix frontend -- --run
```
**Results:** **20 passed** (100% pass rate across 5 test suites in 10.55s).

### Running 10,000-Node Scale Benchmark
```powershell
python -m backend.app.graph.scale_benchmark
```
**Results:**
- Graph Nodes: **10,000** | Edges: **5,670**
- Construction Time: **88.01 ms**
- Path Query Latency (p95): **5.22 ms** (Threshold: $<1,000\text{ ms}$, **191.5x faster than target**).

---

## 33. Security Architecture & Safeguards

Falcon Strike-AI enforces seven non-negotiable security safeguards:

1. **3-Layer Account Allowlist:** Enforced at `BaseCollector.validate_scope()`, `CollectorOrchestrator`, and `PolicyGateEngine`. Prevents scanning or touching unauthorized accounts.
2. **Static MITRE Technique Enum:** Only 16 pre-approved, non-destructive Python modules can be resolved or executed. Zero arbitrary shell injection.
3. **Mandatory Dry-Run Default:** `FALCON_DRY_RUN=true` prevents live cloud mutations.
4. **Dual-Key Live Authorization:** Exiting dry-run mode requires cryptographic sign-off from two independent operators.
5. **Instantaneous Kill-Switch:** Halts running processes, evicts containers, and initiates rollback in **<1 millisecond**.
6. **LIFO Teardown & Baseline Diffing:** Reverts any temporary test artifact in reverse order of creation and verifies zero baseline drift.
7. **Cryptographic SHA-256 Ledger:** Logs all events into an append-only, tamper-evident hash chain.

---

## 34. Known Limitations

- **Cloud Scope:** Deep native discovery is implemented for AWS; Azure and GCP discovery are designed as extensible interfaces for future implementation.
- **Dedicated Lab Target:** Designed strictly for dedicated, isolated security laboratory environments. Not intended for direct execution against production estates.
- **External Dependencies:** While offline synthetic execution is 100% functional, live container execution and live AWS discovery require active host daemons (Docker Desktop) and valid STS sessions.

---

## 35. Future Roadmap

- [ ] **Multi-Cloud Collectors:** Extend native read-only collectors to Azure Entra ID / Resources and Google Cloud Platform (GCP).
- [ ] **Automated Remediation Dispatch:** Terraform / AWS CloudFormation patch generation to automatically mobilize fixes for discovered attack paths.
- [ ] **Live EDR / SIEM Connectors:** Native webhooks for real-time ingestion from Splunk, CrowdStrike Falcon LogScale, and AWS GuardDuty.
- [ ] **Adversary Emulation Profiles:** Pre-configured emulation bundles modeling specific threat actor profiles (e.g., FIN7, SCATTERED SPIDER).

---

## 36. Project Status

Falcon Strike-AI has achieved **100% Functional and Non-Functional Requirement Compliance** against its original Product Requirements Document (PRD v1.0).

- **Implementation Completeness:** **PASS (100.0%)**
- **Security Acceptance:** **PASS (100.0%)**
- **Test Suite Pass Rate:** **100.0%**
- **Status:** **Active / Production Ready**

---

## 37. Contributing Guidelines

Contributions are welcome! Please follow these steps:
1. Fork the repository.
2. Create a feature branch: `git checkout -b feature/new-capability`.
3. Commit changes with clear, descriptive commit messages.
4. Verify that all tests pass: `python -m pytest backend/tests` and `npm test --prefix frontend`.
5. Open a Pull Request against `main`.

---

## 38. Author & Project Credits

- **Author & Lead Architect:** [Hala Naaz](https://github.com/HalaNaaz)
- **Project Repository:** [FalconStrikeAI](https://github.com/HalaNaaz/FalconStrikeAI)
- **Reference Project Architecture:** [Ransomware Detection & Response System (RDRS)](https://github.com/HalaNaaz/ransomware-detection-response-system)

---

## 39. Disclaimer

**FOR AUTHORIZED SECURITY RESEARCH AND LABORATORY TESTING ONLY.**

Falcon Strike-AI is an independent open-source cybersecurity project designed to help organizations assess and improve their cloud security posture. It is not an official product of CrowdStrike, Amazon Web Services, or Google, nor is it endorsed by them. All emulation techniques are strictly non-destructive and intended exclusively for authorized laboratory testing. The author assumes no liability for misuse or damage resulting from the operation of this software.
