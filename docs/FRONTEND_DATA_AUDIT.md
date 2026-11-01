# Falcon Strike-AI — Frontend Integration & Data Authenticity Audit Report

**Document Version:** 1.0.0  
**Date:** 2026-11-01  
**Project:** Falcon Strike-AI Enterprise Web Dashboard  
**Auditor:** Senior Full-Stack Engineer & Cybersecurity QA Specialist  
**Audit Scope:** Data Authenticity, Metric Grounding, Provenance, Environment Identification, and API Hardening  

---

## 1. Executive Summary of Audit Findings

An exhaustive, metric-by-metric audit of the **Falcon Strike-AI** frontend dashboard was performed to ensure that the interface strictly reflects the reality of the existing FastAPI backend without fabricated metrics, simulated multi-cloud production claims, or ungrounded statistics.

### Key Audit Outcomes:
1. **Misleading Multi-Cloud Indicators Removed**:
   - The original visual prototype included cards for GCP Accounts, Azure Accounts, Kubernetes Fleet, and Snowflake Warehouses copied from a generic multi-cloud reference screenshot.
   - **Remediation**: Replaced with actual AWS-first collector subsystems (`AWS Target Lab`, `AWS IAM Collector`, `AWS EC2 & Network Collector`, `AWS S3 Storage Collector`, and `Live AWS Boto3 SDK (Unconfigured)`). Non-implemented providers are explicitly flagged as `NOT CONNECTED / ROADMAP`.
2. **Hardcoded Metrics Eliminated**:
   - The Overview dashboard previously contained placeholder fallback values (e.g. `100.0%` Detection Coverage and `16.3s` MTTD before any run had been correlated, and static `3,925 / 50.8k` asset risk numbers).
   - **Remediation**: All metrics are now calculated dynamically from live backend responses (`GET /api/v1/graph/summary`, `GET /api/v1/attack-paths`, `POST /api/v1/graph/analyze`, and `GET /api/v1/detection/reports/{run_id}`). When a metric has not yet been computed, the UI displays `Pending Run` or `—` rather than fabricated values.
3. **Environment & Account State Disambiguation**:
   - The top navigation bar previously displayed target account `000000000000` without context.
   - **Remediation**: Hardened to explicitly distinguish between:
     - `Synthetic Environment (000000000000)`: Safe offline lab fixture.
     - `AWS Connected ({account_id})`: Production AWS environment with valid credentials.
     - `AWS Connection Error`: Unreachable backend or cloud connection failure.
4. **Backend Connection Integrity**:
   - The top navigation actively polls `GET /health` and only displays `Connected` when the FastAPI backend returns `HTTP 200` with `status: "healthy"`. If the server is unreachable, it shows `Disconnected` in high-contrast red.
5. **Dry-Run Enforcement**:
   - All execution triggers default strictly to `dry_run=true`. Live execution controls in the UI require signed cryptographic authorization tokens and enforce backend policy gate validation.

---

## 2. Overview Dashboard Metric-to-API Mapping & Authenticity Table

| Metric Label | UI Location | Origin / Source | Backend API Endpoint | Calculation Logic | Provenance & Authenticity |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Total AWS Assets** | Overview KPI Card | Backend API | `GET /api/v1/graph/summary` | `graphSummary.total_nodes` | **AUTHENTIC**: Grounded in normalized property graph node count (13 nodes in synthetic baseline). |
| **Critical Gaps** | Overview KPI Card | Backend API | `POST /api/v1/graph/analyze` | `findings.filter(f => f.severity === 'CRITICAL').length` | **AUTHENTIC**: Count of severe misconfigurations discovered by graph engine. |
| **Attack Paths** | Overview KPI Card | Backend API | `GET /api/v1/attack-paths` | `attackPaths.length` | **AUTHENTIC**: Number of discoverable paths from entry nodes to crown jewels. |
| **Campaigns Run** | Overview KPI Card | Backend API | `GET /api/v1/executions` | `executions.length` | **AUTHENTIC**: Historic campaign execution records stored in app state. |
| **Detection Coverage** | Overview KPI Card | Backend API | `GET /api/v1/detection/reports/{run_id}` | `correlationReport.coverage_percentage` | **AUTHENTIC**: Dynamically fetched from latest correlation report; displays `Pending Run` if unexecuted. |
| **Observed MTTD** | Overview KPI Card | Backend API | `GET /api/v1/detection/reports/{run_id}` | `correlationReport.mean_time_to_detect_seconds` | **AUTHENTIC**: Calculated arithmetic mean of alert detection latencies; displays `—` if zero detections. |
| **Assets at Risk Counter** | Hero Counter | Calculated | `POST /api/v1/graph/analyze` | `new Set(findings.map(f => f.target_node_id)).size` | **AUTHENTIC**: Unique assets tied to one or more active security findings. |
| **Compute (EC2)** | Category Breakdown | Backend API | `GET /api/v1/graph/summary` | `node_counts_by_type["EC2_INSTANCE"]` | **AUTHENTIC**: Filtered to real AWS EC2 instances. |
| **Identity (IAM)** | Category Breakdown | Backend API | `GET /api/v1/graph/summary` | `IAM_USER + IAM_ROLE + IAM_POLICY` counts | **AUTHENTIC**: Aggregated IAM principals, roles, and managed policies. |
| **Network (SG)** | Category Breakdown | Backend API | `GET /api/v1/graph/summary` | `node_counts_by_type["SECURITY_GROUP"]` | **AUTHENTIC**: AWS Security Groups and network endpoints. |
| **Storage (S3)** | Category Breakdown | Backend API | `GET /api/v1/graph/summary` | `node_counts_by_type["S3_BUCKET"]` | **AUTHENTIC**: S3 Buckets in environment. |
| **Active Findings** | Radar Visualizer | Backend API | `POST /api/v1/graph/analyze` | `findings.length` | **AUTHENTIC**: Total misconfiguration finding objects. |
| **Attack Paths** | Radar Visualizer | Backend API | `GET /api/v1/attack-paths` | `attackPaths.length` | **AUTHENTIC**: Traversal sequences identified by `AttackPathFinder`. |
| **Actions Ready** | Radar Visualizer | Calculated | `POST /api/v1/graph/analyze` | `findings.filter(f => f.remediation).length` | **AUTHENTIC**: Specific remediation actions available in findings. |
| **Plans Formulated** | Radar Visualizer | Backend API | `GET /api/v1/planner/campaigns` | `campaigns.length` | **AUTHENTIC**: Campaigns formulated by planner engine. |

---

## 3. Detailed Audit of the Eight Main Sections

### Section 1: Overview Dashboard (`/dashboard`)
- **API Integration**: Connects to `/api/v1/graph/summary`, `/api/v1/attack-paths`, `/api/v1/graph/analyze`, `/api/v1/executions`, and `/api/v1/detection/reports/{run_id}`.
- **States Verified**: Loading spinner, error notice when backend offline, and clean populated cards.
- **Authenticity Audit**: Zero hardcoded metric values; fake multi-cloud providers removed.

### Section 2: AWS Environment Explorer (`/environment`)
- **API Integration**: Connects to `GET /api/v1/graph/export`, `POST /api/v1/graph/analyze`, and `POST /api/v1/environment/collect`.
- **States Verified**: Tab filtering by resource type, real-time ARN search, and asset inspection drawer.
- **Authenticity Audit**: Assets rendered are 100% derived from the actual nodes returned by `app_state.graph_store.to_dict()`.

### Section 3: Interactive Attack Graph (`/attack-graph`)
- **API Integration**: Connects to `GET /api/v1/graph/export` and `GET /api/v1/attack-paths`.
- **States Verified**: Path selector updates highlighted edges in cyan; node inspection displays properties from backend.
- **Authenticity Audit**: All nodes and edges correspond strictly to the graph export. Zero synthetic edges or phantom relationships.

### Section 4: AI Campaign Planner (`/campaign-planner`)
- **API Integration**: Connects to `GET /api/v1/planner/campaigns` and `POST /api/v1/planner/generate`.
- **States Verified**: Ordered stage timeline, expected observables, provider selector (`deterministic`, `gemini`, `openai`).
- **Authenticity Audit**: Campaigns are generated via the backend `CampaignPlanner.plan_campaign()`. Displays explicit notice: "AI planner outputs structured JSON data, not executable shell commands."

### Section 5: Adversary Execution Center (`/execution`)
- **API Integration**: Connects to `GET /api/v1/executions`, `POST /api/v1/executions/dry-run`, `POST /api/v1/executions/{run_id}/cancel`, and `POST /api/v1/executions/{run_id}/teardown`.
- **States Verified**: Status badges, duration formatting, simulation events stream.
- **Authenticity Audit**: Dry-run mode is strictly enforced. Live simulation cannot be triggered without valid authorization tokens.

### Section 6: Telemetry & Detection Center (`/telemetry`)
- **API Integration**: Connects to `GET /api/v1/telemetry/events`, `iocs`, `c2-beacons`, `dns-queries`, and `POST /api/v1/detection/correlate`.
- **States Verified**: Tabbed data streams for canary tokens, C2 intervals, DNS signalling, and correlation scorecards.
- **Authenticity Audit**: Prominent amber alert banner: **`"SYNTHETIC DETECTION RESULTS (Detection Stub Active)"`**. Never claims live CrowdStrike, Splunk, or Sentinel connectivity when unconfigured.

### Section 7: SOC Reports (`/reports`)
- **API Integration**: Connects to `GET /api/v1/reporting/{run_id}`, `POST /api/v1/reporting/generate`, and `GET /api/v1/reporting/{run_id}/export`.
- **States Verified**: Executive summary, attack path narrative, ATT&CK heatmap, prioritized remediation table, and file downloads.
- **Authenticity Audit**: Every report is tied to a verified `run_id`. Zero fabricated evidence.

### Section 8: Security & Controls (`/security`)
- **API Integration**: Connects to `GET /api/v1/policies/status`, `GET /api/v1/system/kill-switch`, `POST /api/v1/system/kill-switch`, and `POST /api/v1/audit/verify/{run_id}`.
- **States Verified**: Policy rule listing, blast radius limits (max 5 resources, 600s), kill switch confirmation modal, and cryptographic hash-chain verification.
- **Authenticity Audit**: Kill switch executes sub-second halt; audit verifier tests all SHA-256 records back to genesis.

---

## 4. Remediation Changelog

1. **`CloudAccountCarousel.tsx`**: Replaced static GCP/Azure/K8s/Snowflake accounts with real AWS Target Lab (`000000000000`), IAM Collector, EC2 Collector, S3 Collector, and marked unconfigured live AWS as `AWS NOT CONFIGURED`.
2. **`HeroMetrics.tsx`**: Removed static `3,925 / 50.8k` text and non-existent asset categories (Code, API, AI). Replaced with live calculated counts: Compute (EC2), Identity (IAM), Network (SG), and Storage (S3).
3. **`CenterRadarVisualizer.tsx`**: Removed static fallback numbers (`2990`, `200`, `120`) and hardcoded action pills ("19 Actions", "14 Automation"). Replaced with live finding counts and formulated campaign counts.
4. **`DashboardPage`**: Removed static `100.0%` coverage and `16.3s` MTTD fallbacks. Replaced with dynamic lookups from `api.getCorrelationReport()`.
5. **`TopNavbar.tsx`**: Upgraded environment indicator to distinguish `Synthetic Environment (000000000000)`, `AWS Connected`, and `AWS Connection Error`.
6. **`ThreatCards.tsx` & `AttackGraphPage`**: Removed fallback literals (`|| "85.0"`, `|| 4 hops`) in favor of exact property reads.

