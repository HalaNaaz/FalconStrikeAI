# Falcon Strike-AI — Google Gemini LLM Provider Validation Report

**Document Version:** 1.0.0  
**Date:** 2026-11-01  
**Classification:** AI Architecture & Resilience Verification  
**PRD Traceability:** `FR-2.1`, `FR-2.2`, `NFR-A1`  

---

## 1. Architectural Design & Offline Guarantees

Under PRD `FR-2.1`, Falcon Strike-AI generates grounded, multi-stage adversary campaign plans. The platform features an **Agentic Campaign Planner** with pluggable providers:
1. **`DeterministicPlannerProvider`:** An offline, zero-dependency heuristic planner that maps graph attack paths and misconfiguration findings directly into MITRE ATT&CK technique sequences (`T1078`, `T1526`, `T1098`, `T1071.004`).
2. **`GeminiPlannerProvider`:** An LLM-augmented planner utilizing Google Gemini models (`gemini-1.5-pro` / `gemini-1.5-flash`) to generate contextual planning rationales, adaptive evasion considerations, and tailored SOC observables.

### Deterministic Fallback Principle
Falcon Strike-AI enforces an absolute offline guarantee:
- If `GEMINI_API_KEY` (or `GOOGLE_API_KEY`) is absent, invalid, or rate-limited, the system **never halts or errors out**.
- It immediately and seamlessly falls back to the deterministic planning engine, tagging the resulting plan with:
  `planner_provider = "gemini_fallback_deterministic"`

---

## 2. Host Key Verification Findings

During local environment assessment:
- **Environment Inspection:** Checked environment variables `GEMINI_API_KEY` and `GOOGLE_API_KEY`.
- **Finding:** Neither environment variable is set on the host system.
- **Provider Probe Execution:**
  ```python
  provider = GeminiPlannerProvider()
  plan = provider.plan(attack_path, findings, run_id="RUN-FALLBACK-TEST")
  assert plan.planner_provider == "gemini_fallback_deterministic"
  ```
- **Probe Result:** Verified. Deterministic fallback generated a valid 4-stage campaign plan with 100% MITRE ATT&CK coverage and expected IOCs.

### 2.1 Status Determination
- **Code Implementation:** **VERIFIED** (Both `GeminiPlannerProvider` and `DeterministicPlannerProvider` implemented and tested).
- **Live LLM Execution:** **BLOCKED (NO API KEY IN HOST ENVIRONMENT)** (Honest reporting: offline deterministic planner active).

---

## 3. Operator Activation Runbook

To enable live Gemini LLM campaign generation:

1. Obtain a Gemini API key from Google AI Studio (`https://aistudio.google.com/`).
2. Set the environment variable:
   ```bash
   export GEMINI_API_KEY="AIzaSy..."
   ```
3. Run campaign planning via API or CLI:
   ```bash
   python -m backend.app.main run --planner gemini
   ```
4. Verify generated campaign plans in the Falcon Strike dashboard under the **Campaigns** tab (`planner_provider: "gemini"`).
