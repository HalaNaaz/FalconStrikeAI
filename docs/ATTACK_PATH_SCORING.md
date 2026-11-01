# Falcon Strike-AI — Attack Path Discovery & Scoring Model

**Document Version:** 1.0.0  
**Date:** 2026-11-01  
**Project:** Falcon Strike-AI  
**Conformance:** PRD FR-1.6, FR-1.7  

---

## 1. Overview

The Falcon Strike-AI Attack Path Discovery Engine models reachable paths from unauthenticated external footholds to internal crown jewels (administrator roles and sensitive data stores). Path ranking is governed by a **transparent, deterministic, evidence-backed scoring algorithm** that produces reproducible risk ratings without relying on black-box heuristics or hallucinated LLM scores.

---

## 2. Discovery Algorithm

The path traversal algorithm utilizes a depth-bounded Breadth-First Search (BFS) over the directed property graph:
- **Default Maximum Depth:** 6 hops (configurable via API).
- **Cycle Prevention:** Branch-level visited tracking ensures no node is revisited within the same path trajectory.
- **Actionable Edge Filter:** Only privilege-bearing relationships (`EXPOSED_TO_INTERNET`, `RUNS_AS`, `ASSUMES_ROLE`, `CAN_ACCESS`) are traversed.
- **Deduplication:** Paths are uniquely identified by their ordered sequence of node IDs.

---

## 3. Deterministic Scoring Model

Every discovered path receives a score ranging from **0.0 to 100.0**, calculated across four transparent dimensions:

$$\text{Final Score} = \min(100.0, \; S_{\text{entry}} + S_{\text{target}} + S_{\text{hops}} + S_{\text{findings}})$$

### 3.1 Dimension 1: Entry Point Exposure ($S_{\text{entry}}$) — Max 30 Points
- **+30 pts:** Unauthenticated Public Internet (`0.0.0.0/0` ingress).
- **+25 pts:** Direct public resource exposure (e.g., publicly reachable IP).
- **+15 pts:** Authenticated internal access (e.g., compromised internal IAM user).

### 3.2 Dimension 2: Target Asset Criticality ($S_{\text{target}}$) — Max 35 Points
- **+35 pts:** Cloud Administrator Role with full `AdministratorAccess` (`*` on `*`).
- **+30 pts:** Confidential Data Store (S3 bucket with sensitive data markings).
- **+20 pts:** Privileged IAM Role (elevated service role).
- **+15 pts:** Standard S3 bucket.
- **+10 pts:** Standard internal resource.

### 3.3 Dimension 3: Path Hop Efficiency ($S_{\text{hops}}$) — Max 15 Points
Shorter, more direct paths present lower operational friction to an adversary:
- **+15 pts:** $\le 2$ hops (immediate direct exposure).
- **+10 pts:** 3–4 hops (moderate pivot complexity).
- **+5 pts:** $\ge 5$ hops (complex multi-stage lateral chain).

### 3.4 Dimension 4: Corroborated Findings ($S_{\text{findings}}$) — Max 20 Points
Bonus points awarded when active misconfiguration findings reside along the traversed nodes:
- **+10 pts:** Path contains an active `PRIVILEGE_ESCALATION` finding (e.g., role chaining).
- **+5 pts:** Path contains an active `WILDCARD_PERMISSIONS` finding.
- **+5 pts:** Path contains an active `PUBLIC_STORAGE` finding.

---

## 4. Severity Mapping

| Risk Score Range | Severity Classification | SLA / Priority |
| :---: | :---: | :--- |
| **80.0 – 100.0** | **`CRITICAL`** | Immediate emulation and defensive validation required. |
| **60.0 – 79.9** | **`HIGH`** | High priority for automated campaign scheduling. |
| **40.0 – 59.9** | **`MEDIUM`** | Normal operational priority. |
| **0.0 – 39.9** | **`LOW`** | Informational exposure path. |

---

## 5. Traceability & Explainability

Every generated `AttackPath` object includes a human-readable `ranking_explanation` field documenting the step-by-step point contributions, e.g.:
```text
Risk Score 90.0/100 (CRITICAL): +30 pts: Entry point is unauthenticated Public Internet (0.0.0.0/0). +35 pts: Target is Cloud Administrator Role with full administrative control. +10 pts: Moderate chain complexity (3 hops). +10 pts: Corroborated by active Privilege Escalation finding on path. +5 pts: Corroborated by Wildcard Permission finding along path.
```

