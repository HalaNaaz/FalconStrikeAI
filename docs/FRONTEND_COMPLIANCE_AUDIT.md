# Falcon Strike-AI — Frontend Compliance & Interface Audit

**Document Version:** 2.0.0  
**Audit Date:** 1 November 2026  
**Auditor:** Principal Software Architect & Senior Frontend QA Specialist  
**Application Stack:** Next.js 14.2.24 (App Router), React 18, TypeScript 5.7, Tailwind CSS v3.4, React Flow (`@xyflow/react`), Recharts, Lucide Icons

---

## 1. Executive Summary

The frontend application for **Falcon Strike-AI** is an enterprise-grade cybersecurity command center engineered to provide continuous visibility into cloud identity exposure, multi-hop attack paths, autonomous campaign planning, real-time execution monitoring, and SOC reporting.

Following the recent **CSS Restoration and Data Authenticity Audit**, all 14 routes compile cleanly into static prerendered pages (`npm run build` exit code 0, zero TypeScript errors). Every metric displayed on the dashboard has been mapped to real FastAPI backend endpoints, with explicit badges for synthetic environment data (`000000000000`) and roadmap integrations.

This audit evaluates each view against PRD requirements, verifying UI components, API client bindings, interactive workflows, and remaining frontend testing gaps.

---

## 2. Section-by-Section Frontend Audit

### 2.1 Overview Dashboard (`/dashboard`)
- **Implemented Components:**
  - `CloudAccountCarousel`: Displays operational status of AWS IAM, Network, and S3 collectors, with roadmap labels for GCP/Azure/K8s.
  - `HeroMetrics`: Dynamic tally of compute, identity, storage, and network assets, highlighting unique assets at risk.
  - `CenterRadarVisualizer`: Palo Alto Networks-style dark circular radar showing open issues, open cases, threat cases, and posture cases.
  - `KPICards`: 6 high-level KPI cards (Total Assets, Attack Paths, Campaigns, Detection Coverage %, MTTD, Teardown Status).
  - `ThreatCards`: Top active threats and posture cases with severity badges.
- **Backend API Endpoints Called:**
  - `GET /api/v1/health` (Collector & system health)
  - `GET /api/v1/graph/stats` (Total nodes, node distribution by type)
  - `GET /api/v1/attack-paths/` (Calculated paths, risk score >= 80.0)
  - `GET /api/v1/planner/campaigns` (Stored campaign count)
  - `GET /api/v1/collectors/findings` (Active findings by severity)
  - `GET /api/v1/detection/correlation/report` (Real detection coverage % and MTTD)
- **User Interactions & State Handling:**
  - Refresh button triggers live re-fetch across all summary endpoints.
  - Empty state displays `Pending Run` and `—` for detection metrics before first run.
- **Compliance Status:** **VERIFIED (100% Data Grounding)**

---

### 2.2 AWS Environment View (`/environment`)
- **Implemented Components:**
  - Collector status indicators (IAM, EC2 Network, S3).
  - Topology mode toggle (`Synthetic Lab` vs `Live AWS SDK`).
  - Scan execution panel with environment selector.
  - Ingested asset inventory table with filtering by type (`IAM_ROLE`, `EC2_INSTANCE`, `S3_BUCKET`, `SECURITY_GROUP`).
- **Backend API Endpoints Called:**
  - `GET /api/v1/collectors/status`
  - `POST /api/v1/collectors/collect`
  - `GET /api/v1/graph/nodes`
  - `GET /api/v1/collectors/findings`
- **User Interactions & State Handling:**
  - User can trigger a scan (`synthetic` or `live`).
  - Live mode prompts for AWS credential confirmation; rejects unallowlisted accounts.
- **Compliance Status:** **VERIFIED**

---

### 2.3 Attack Graph Visualization (`/attack-graph`)
- **Implemented Components:**
  - React Flow (`@xyflow/react`) node-edge canvas with pan, zoom, mini-map, and controls.
  - `CustomGraphNode`: Color-coded nodes (Red for Crown Jewel Admin Role, Cyan for Internet Entry, Amber for Vulnerable EC2, Green for S3).
  - Attack path selector sidebar listing discovered paths ranked by risk score (0-100).
  - Node inspector drawer displaying metadata, permissions, and attached misconfigurations.
- **Backend API Endpoints Called:**
  - `GET /api/v1/graph/export` (Canvas nodes and edges)
  - `GET /api/v1/attack-paths/` (Discovered attack paths)
  - `POST /api/v1/attack-paths/discover` (Trigger discovery algorithm)
- **User Interactions & State Handling:**
  - Selecting a path in the sidebar highlights the exact sequence of edges in cyan glow.
  - Clicking any node opens the detail inspector panel.
- **Compliance Status:** **VERIFIED (Interactive WebGL/Canvas Graph)**

---

### 2.4 AI Campaign Planner (`/campaign-planner`)
- **Implemented Components:**
  - Campaign creation wizard selecting target attack path.
  - LLM planner parameters: Provider (`Google Gemini` vs `Deterministic Fallback`), Seed, Rationale.
  - ATT&CK tactical stage viewer (Initial Access -> Discovery -> Privesc -> Exfiltration).
  - Technique cards displaying ATT&CK ID, name, non-destructive contract, and expected IOCs.
  - Plan validation badge confirming schema conformance and technique allowlist check.
- **Backend API Endpoints Called:**
  - `GET /api/v1/attack-paths/`
  - `POST /api/v1/planner/generate`
  - `GET /api/v1/planner/campaigns`
  - `GET /api/v1/techniques/`
- **User Interactions & State Handling:**
  - Generates campaign from top attack path in one click.
  - Form validation prevents submission if attack paths have not been computed.
- **Compliance Status:** **VERIFIED**

---

### 2.5 Execution Center (`/execution`)
- **Implemented Components:**
  - Execution mode banner: Persistent amber `DRY-RUN ENFORCED` badge.
  - Live execution toggle locked behind two-key operator token fields (`Token 1: Red Team`, `Token 2: SecOps`).
  - Runner selection toggle (`Docker Container Runner` vs `In-Memory Simulator`).
  - Stage-by-stage execution progress stepper with live status chips (`PENDING`, `RUNNING`, `SUCCESS`, `ROLLED_BACK`).
  - Emergency Kill-Switch button with confirmation dialog.
- **Backend API Endpoints Called:**
  - `POST /api/v1/executions/start`
  - `GET /api/v1/executions/status/{run_id}`
  - `POST /api/v1/executions/cancel/{run_id}`
  - `POST /api/v1/system/kill-switch/trigger`
- **User Interactions & State Handling:**
  - Pressing Kill Switch immediately halts run, disables action triggers, and changes navbar badge to red `EMERGENCY HALT`.
- **Compliance Status:** **VERIFIED (Strict Safety Invariant)**

---

### 2.6 Telemetry & Detection View (`/telemetry`)
- **Implemented Components:**
  - C2 Beacon monitor displaying callback timestamps, interval jitter %, destination URLs, and HTTP response codes.
  - DNS Signalling log showing queried domains, query types (A/TXT), and lab sink IP resolution.
  - Ground-Truth IOC artifact viewer listing emitted indicators with copy-to-clipboard.
  - Detection correlation scorecard matching IOCs against simulated SIEM detections.
- **Backend API Endpoints Called:**
  - `GET /api/v1/telemetry/beacons/{run_id}`
  - `GET /api/v1/telemetry/dns/{run_id}`
  - `GET /api/v1/telemetry/iocs/{run_id}`
  - `POST /api/v1/detection/correlate`
- **User Interactions & State Handling:**
  - Supports live polling during active simulation runs.
- **Compliance Status:** **VERIFIED**

---

### 2.7 SOC Reports View (`/reports`)
- **Implemented Components:**
  - Executive summary card with campaign timeline, target account, and risk posture.
  - ATT&CK Matrix Coverage Heatmap (color-coded: Green = Detected, Amber = Partial, Red = Missed).
  - Mean Time to Detect (MTTD) stopwatch metric card.
  - Prioritized remediation plan with affected asset links and step-by-step guidance.
  - Export action buttons for JSON, Markdown, and HTML report downloads.
- **Backend API Endpoints Called:**
  - `POST /api/v1/reporting/generate`
  - `GET /api/v1/reporting/{run_id}`
  - `GET /api/v1/reporting/{run_id}/export?format={json|markdown|html}`
- **User Interactions & State Handling:**
  - One-click export downloads generated reports directly to client filesystem.
- **Compliance Status:** **VERIFIED**

---

### 2.8 Security & Controls View (`/security`)
- **Implemented Components:**
  - Target Account Allowlist card displaying compiled account IDs (`000000000000`).
  - Two-Key Token Generator utility for operators (for testing authorized live runs).
  - Emergency Kill-Switch control station with real-time status and authorized reset input.
  - Blast-radius policy caps display (Max 5 resources, 60s timeout, `FalconStrike=True` tagging).
  - Immutable Audit Log link.
- **Backend API Endpoints Called:**
  - `GET /api/v1/policies/status`
  - `POST /api/v1/policies/evaluate`
  - `GET /api/v1/system/kill-switch/status`
  - `POST /api/v1/system/kill-switch/reset`
- **User Interactions & State Handling:**
  - Resetting kill switch requires valid authorization token.
- **Compliance Status:** **VERIFIED**

---

### 2.9 System Views: Audit Logs & Settings
- **Audit Logs (`/audit-logs`):** Displays cryptographic SHA-256 hash-chained JSONL records. Features a "Verify Ledger Integrity" button calling `POST /api/v1/audit/verify/{run_id}`, rendering green `VALID CHAIN` or red `TAMPER DETECTED` banner.
- **Settings (`/settings`):** Configures API base URL (`http://localhost:8000`), default planner provider, telemetry polling frequency, and theme preferences.

---

## 3. Identified Frontend Gaps & Limitations

1. **Automated Frontend Test Suite (Testing Gap):**  
   `package.json` contains no Jest, Vitest, or Playwright test runner. Frontend verification relies on TypeScript compilation (`tsc --noEmit`), Next.js static build checks (`next build`), and runtime browser verification. Adding Vitest unit tests for UI formatters and React components is recommended.
2. **Native PDF Export Button:**  
   The SOC report export supports JSON, Markdown, and HTML. The PDF option triggers the browser's `window.print()` dialog rather than downloading a pre-rendered PDF document from the backend.
3. **Graph Layout Auto-Optimization:**  
   In very dense topologies (> 100 nodes), React Flow relies on pre-calculated coordinate offsets. Integrating a WebAssembly-based Dagre or Force-Directed layout engine would improve visual aesthetics for massive graphs.

