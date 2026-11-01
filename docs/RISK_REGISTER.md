# Falcon Strike-AI — Project Risk Register

**Document Version:** 1.0.0  
**Date:** 2026-11-01  
**Project:** Falcon Strike-AI  
**Target Deadline:** 2026-11-06  

---

## 1. Risk Matrix Definition

Risks are evaluated using standard Likelihood (1–5) and Impact (1–5) metrics:
- **Severity Score:** `Likelihood × Impact` (1–25)
- **Classification:** Low (1–5), Medium (6–12), High (15–19), Critical (20–25).

---

## 2. Active Risk Register

| Risk ID | Category | Risk Description | Likelihood (1–5) | Impact (1–5) | Severity Score | Mitigation Strategy & Invariants | Owner Decision Required? |
| :--- | :--- | :--- | :---: | :---: | :---: | :--- | :--- |
| **RSK-01** | **Safety** | Accidental live cloud mutation or targeting of non-lab / production AWS accounts. | 2 | 5 | **10 (Med)** | • Dry-run is hardcoded default.<br>• Compiled account allowlist checked at process start.<br>• Mandatory signed JWT authorization token.<br>• Egress allowlisting and least-privilege AWS credentials. | **YES**: Project Owner must confirm approved AWS Lab Account ID. |
| **RSK-02** | **Schedule** | Compressed 5-day timeline causes scope creep across entire ATT&CK matrix or multi-cloud features. | 4 | 5 | **20 (Crit)** | • Scope strictly bounded to AWS-first.<br>• Exactly 12 curated ATT&CK techniques implemented.<br>• Extensibility designed via clean interfaces without writing Azure/GCP code now. | **NO**: Already constrained by engineering plan. |
| **RSK-03** | **Technical** | External LLM API downtime, rate limits, or non-deterministic hallucinations in campaign plans. | 4 | 4 | **16 (High)** | • Pydantic schema validation rejects invalid outputs.<br>• Implement `DeterministicCampaignPlanner` for reproducible offline testing and benchmarking.<br>• Set LLM temperature=0 and fix random seeds. | **NO**: Mitigated by dual-mode planner design. |
| **RSK-04** | **Technical** | Neo4j server or Docker daemon unavailable on host machine during testing or evaluation. | 5 | 3 | **15 (High)** | • Implement zero-dependency `InMemoryGraphStore` (NetworkX) and `SubprocessRunner` alongside Neo4j and Docker implementations.<br>• Ensure 100% of tests run cleanly offline. | **NO**: Mitigated by architectural design. |
| **RSK-05** | **Performance**| Graph attack-path queries fail sub-second p95 latency target on 10,000+ node graphs (NFR-P2). | 3 | 4 | **12 (Med)** | • Index all node labels (`Principal`, `Role`, `Endpoint`).<br>• Implement depth-bounded bidirectional breadth-first search.<br>• Continuous benchmark testing in CI. | **NO**: Verified via Day 2 benchmark script. |
| **RSK-06** | **Security** | Emulation artifacts or benign marker accounts persist in target account after run completion. | 2 | 4 | **8 (Med)** | • `TeardownEngine` records pre-execution baseline.<br>• Pre/post execution hooks track all created objects.<br>• Guaranteed cleanup in `finally` blocks and kill-switch abort handlers. | **NO**: Verified via automated baseline equality test. |
| **RSK-07** | **Operational**| Absence of a live enterprise SIEM (CrowdStrike / Splunk) prevents measuring MTTD and detection coverage. | 5 | 3 | **15 (High)** | • Build high-fidelity `DetectionStub` that matches ground-truth IOCs against Sigma detection rules with realistic delay modeling.<br>• Support both live webhooks and detection stub. | **YES**: Project Owner confirms acceptance of Detection Stub for lab evaluation. |

---

## 3. Explicit Decisions Requiring Project Owner Input

1. **Lab Account Allowlist Specification**: Confirm the designated AWS Lab Account ID (e.g. `123456789012` or test dummy `000000000000`) for the compiled allowlist in `backend/app/core/config.py`.
2. **SIEM / EDR Target**: Confirm that the internal `DetectionStub` (ingesting ground-truth IOCs and evaluating simulated detections with configurable detection delays) satisfies the validation requirement in the absence of a live CrowdStrike Falcon / Splunk instance.
3. **LLM Provider Preference**: Specify preferred default provider for agent planning (`gemini`, `openai`, or deterministic offline mode).

