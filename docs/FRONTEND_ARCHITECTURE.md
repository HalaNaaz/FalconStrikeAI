# Falcon Strike-AI — Frontend Architecture & Design Specification

**Document Version:** 1.0.0  
**Date:** 2026-11-01  
**Project:** Falcon Strike-AI Enterprise Web Dashboard  
**Classification:** Enterprise Security Command Center  

---

## 1. Design Philosophy & Visual Identity

The Falcon Strike-AI frontend is designed as a commercial-grade **Cloud Security Command Center** and **Autonomous Adversary Emulation Platform**. Drawing direct visual inspiration from modern enterprise security suites (e.g. Palo Alto Prisma Cloud, CrowdStrike Falcon, Wiz), the interface emphasizes:
- **Dark Navy Palette**: High contrast, minimal visual noise, and prolonged readability for SOC operations centers.
- **Data-Rich Ergonomics**: Dense yet clean visual hierarchy prioritizing actionable metrics (assets at risk, critical findings, attack paths, MTTD).
- **Interactive Visualizations**: Dynamic React Flow graph canvas representing cloud identity and resource nodes with real-time path highlight traversals.
- **Safety Transparency**: Non-negotiable safety boundaries (dry-run default, compiled account allowlist, two-key cryptographic token gate, emergency kill switch) surfaced directly in the top navigation and security controls.

---

## 2. Design Tokens & Color System

| Token | Hex Value | Semantic Usage |
| :--- | :--- | :--- |
| `background` | `#080F1D` | Root application background |
| `sidebar` | `#060C18` | Left vertical navigation rail |
| `surface` | `#101B2D` | Primary card and panel surface |
| `surface-elevated`| `#152238` | Interactive cards and table headers |
| `surface-dark` | `#0C1424` | Nested code blocks, parameter values, and tags |
| `surface-border` | `#24344A` | Subtle dividers and card outlines |
| `brand-primary` | `#22D3EE` | Cyan-400 primary accent, glowing indicators, active nav |
| `brand-secondary`| `#38BDF8` | Sky-400 secondary accent, sub-labels, information pills |
| `status-success` | `#22C55E` | Emerald-500: Valid audit chains, healthy connections, detected techniques |
| `status-warning` | `#F59E0B` | Amber-500: Partial detections, warnings, posture cases |
| `status-critical` | `#EF4444` | Red-500: High-risk attack paths, critical findings, kill-switch |
| `text-primary` | `#E5EDF7` | Primary text and headers |
| `text-secondary` | `#94A3B8` | Body text, descriptions, secondary values |
| `text-muted` | `#64748B` | Footers, timestamps, placeholders |

---

## 3. Component Architecture & Directory Structure

```
frontend/
├── src/
│   ├── app/                    # Next.js App Router Pages
│   │   ├── layout.tsx          # Global Shell wrapper with persistent dark theme
│   │   ├── page.tsx            # Root redirect to /dashboard
│   │   ├── globals.css         # Tailwind & custom radar animations
│   │   ├── dashboard/          # Section 1: Security Command Center
│   │   ├── environment/        # Section 2: AWS Asset & Exposure Explorer
│   │   ├── attack-graph/       # Section 3: Interactive Attack Graph Visualizer
│   │   ├── campaign-planner/   # Section 4: AI Campaign Planner
│   │   ├── execution/          # Section 5: Adversary Execution Center
│   │   ├── telemetry/          # Section 6: Telemetry & Detection Center
│   │   ├── reports/            # Section 7: SOC Assessment Reports
│   │   ├── security/           # Section 8: Security & Emergency Controls
│   │   ├── audit-logs/         # System: Tamper-Evident Audit Ledger
│   │   └── settings/           # System: Platform Settings & API Config
│   ├── components/
│   │   ├── layout/             # Persistent Shell, Sidebar, TopNavbar
│   │   ├── dashboard/          # Carousel, Center Radar, HeroMetrics, ThreatCards
│   │   ├── attack-graph/       # Custom React Flow nodes with typed styles
│   │   ├── campaigns/          # Campaign stage timeline
│   │   └── execution/          # Execution controls
│   ├── lib/
│   │   ├── api/                # Centralized typed API client
│   │   └── utils/              # Formatting, styling helpers, and class mergers
│   └── types/                  # Typed interfaces mirroring FastAPI Pydantic schemas
├── package.json
├── tsconfig.json
├── tailwind.config.ts
└── next.config.mjs
```

---

## 4. State Management & API Flow

1. **Centralized Client (`frontend/src/lib/api/client.ts`)**:
   - Single point of communication with the FastAPI backend over `NEXT_PUBLIC_API_BASE_URL`.
   - Incorporates request timeouts via `AbortController`.
   - Strict typing using TypeScript models mirroring FastAPI Pydantic schemas.
   - Graceful offline fallback: if the backend server is unreachable, displays clear error notices without crashing.
2. **Honest Provenance Labelling**:
   - The UI never synthesizes imaginary SIEM connections. If detections come from the synthetic detection stub, they are explicitly tagged `SYNTHETIC DETECTION RESULTS`.
   - The UI never fabricates a verified audit status without invoking the cryptographic verifier.

