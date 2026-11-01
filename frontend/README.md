# Falcon Strike-AI — Enterprise Frontend Command Center

**Technology Stack:** Next.js 14 (App Router) + TypeScript + Tailwind CSS + React Flow (`@xyflow/react`) + Recharts + Lucide React  
**Architecture:** Enterprise Dark Navy Command Center inspired by Cloud Security Platforms  

---

## 1. Overview

The **Falcon Strike-AI Frontend** is a dedicated enterprise web dashboard providing deep, real-time observability and interactive control over the Falcon Strike-AI Continuous Threat Exposure Management (CTEM) and autonomous adversary emulation engine.

### Core Sections Implemented:
1. **Overview Dashboard (`/dashboard`)**: Hero metrics ("Total Assets at Risk"), Cloud Provider carousel, Center Constellation Radial visualizer, active threat cases, posture cases, and top attack paths.
2. **AWS Environment Explorer (`/environment`)**: Comprehensive asset inventory with tabs for IAM users, roles, policies, EC2 instances, security groups, S3 buckets, and public exposure, plus single-click read-only lab collection.
3. **Interactive Attack Graph (`/attack-graph`)**: High-performance interactive graph visualizer powered by React Flow with zoom, pan, minimap, custom typed resource nodes, attack path sequence highlighting, and inspector drawer.
4. **Agentic AI Campaign Planner (`/campaign-planner`)**: Visual multi-stage campaign timeline, ATT&CK tactics, schema validation status, planner rationale, and deterministic/AI generation triggers.
5. **Adversary Execution Center (`/execution`)**: Real-time simulation event feed, dry-run default execution, two-key JWT authorization gate, in-progress cancellation, and verified baseline teardown.
6. **Telemetry & Detection Center (`/telemetry`)**: Ground-truth observability tabs (simulation events, synthetic canary IOCs, HTTPS C2 beacons, DNS queries) and detection correlation metrics with explicit `"SYNTHETIC DETECTION RESULTS"` provenance labelling.
7. **SOC Reports (`/reports`)**: Executive summaries, attack path narratives, MITRE ATT&CK coverage heatmaps, prioritized remediation matrices, and multi-format exports (JSON, Markdown, HTML).
8. **Security & Controls (`/security`)**: Policy gate status, compiled account allowlist, blast-radius limits, sub-second emergency kill switch with confirmation modal, and SHA-256 hash-chain audit verification.
9. **Tamper-Evident Audit Ledger (`/audit-logs`)**: Append-only cryptographic ledger viewer with sequence ordering, hash chaining, search/filter, and JSONL export.
10. **Platform Settings (`/settings`)**: API connection testing, target account configuration, runtime environment, and subsystem health status.

---

## 2. Installation & Quick Start

### 2.1 Prerequisites
- Node.js 18+ (Node.js v24.19.0 recommended)
- Python 3.11+ running the backend FastAPI control plane on `http://localhost:8000`

### 2.2 Install Dependencies
```bash
cd frontend
npm install
```

### 2.3 Environment Configuration
Copy `.env.example` to `.env.local`:
```bash
cp .env.example .env.local
```

Default configuration:
```ini
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
NEXT_PUBLIC_APP_ENV=development
```

### 2.4 Running Development Server
```bash
npm run dev
```
Open `http://localhost:3000` in your web browser.

### 2.5 Building for Production
```bash
npm run build
npm run start
```

