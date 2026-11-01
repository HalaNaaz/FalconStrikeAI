# Falcon Strike-AI — Native PDF Report Export Guide

**Document Version:** 1.0.0  
**Date:** 2026-11-01  
**Classification:** Product Capabilities & SOC Reporting  
**PRD Traceability:** `FR-5.2`, `FR-5.3`  

---

## 1. Overview

Under PRD `FR-5.3`, Falcon Strike-AI provides multi-format export capabilities for executive and SOC engineering consumers. While Markdown, HTML, and JSON representations are available for programmatic ingestion, executive leadership and compliance auditors require formal, self-contained, publication-ready PDF documents.

Falcon Strike-AI includes a native two-pass PDF generator implemented with **ReportLab**:
- **Module:** `backend/app/reporting/pdf_generator.py`
- **Exporters:** `backend/app/reporting/exporters.py`
- **API Endpoints:**
  - `GET /api/v1/reporting/{run_id}/export?format=pdf`
  - `GET /api/v1/reporting/{run_id}/pdf`

---

## 2. PDF Document Structure & Design

The generated PDF report contains an enterprise layout matching modern cybersecurity audit standards:

1. **Header & Footer Canvas (`NumberedCanvas`):**
   - Two-pass canvas calculates exact total page numbers ("Page X of Y").
   - Running header with platform banner, classification ("RESTRICTED — INTERNAL SOC ASSESSMENT"), and report ID.
   - Running footer with cryptographic integrity disclaimer and generation timestamp.

2. **Executive Summary Banner:**
   - Run ID, Target AWS Account, Execution Mode (`DRY_RUN` / `LIVE_SIMULATION`).
   - Provenance badges: Data Provenance, Runner Provenance, Detection Provenance.

3. **Key Performance Indicators (KPI Cards):**
   - **Detection Coverage:** Percentage with color-coded severity (Green >= 80%, Amber >= 50%, Red < 50%).
   - **Techniques Emulated:** Total executed, detected, partially detected, and missed.
   - **Mean Time to Detect (MTTD):** Average detection latency in seconds.
   - **Teardown & Audit:** Cryptographic hash chain status and post-run environment fingerprint match.

4. **Attack Path Discovery Chain:**
   - Multi-hop traversal table with Source Node, Vector / Relationship (`ASSUME_ROLE`, `INGRESS_ALLOW`, `READ_BUCKET`), and Target Crown Jewel.

5. **MITRE ATT&CK Emulation Scorecard:**
   - Technique ID (`T1078`, `T1526`, `T1098`, `T1071.004`), Technique Name, ATT&CK Tactic, Detection Outcome (`DETECTED`, `PARTIALLY_DETECTED`, `MISSED`), and Detection Latency.

6. **Prioritized Remediation Actions:**
   - Ranked actionable guidance (Critical, High, Medium) with specific cloud IAM policies, security group restrictions, or S3 bucket policy fixes.

7. **Teardown & Cryptographic Audit Verification:**
   - Verifies SHA-256 tamper-evident hash chain integrity and confirmation that all emulated artifacts were reverted.

---

## 3. How to Generate and Download

### Via REST API:
```bash
# Obtain Bearer token
TOKEN=$(curl -s -X POST http://localhost:8000/api/v1/auth/token \
  -H "Content-Type: application/json" \
  -d '{"operator_id": "auditor", "role": "admin", "target_account_id": "000000000000"}' \
  | jq -r .access_token)

# Download PDF report
curl -X GET "http://localhost:8000/api/v1/reporting/RUN-20261101-001/pdf" \
  -H "Authorization: Bearer $TOKEN" \
  --output soc_report.pdf
```

### Via Python CLI / Script:
```python
from backend.app.reporting.exporters import ReportExporter

# Generate report object
pdf_bytes = ReportExporter.export_pdf(report, file_path="artifacts/reports/soc_report.pdf")
```
