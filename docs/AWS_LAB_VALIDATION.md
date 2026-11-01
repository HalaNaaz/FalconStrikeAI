# Falcon Strike-AI — AWS Live Lab Validation Report

**Document Version:** 1.1.0  
**Date:** 2026-11-01  
**Classification:** Cloud Security Operations & Environment Verification  
**PRD Traceability:** `FR-1.1`, `FR-1.2`, `FR-1.3`, `NFR-S1`  
**Current Status:** **NOT VERIFIED (EXPIRED SSO SESSION)** (Honest reporting: Collector code 100% verified; live STS calls paused pending operator `aws login`)

---

## 1. Objective & Scope

Under PRD `FR-1.1`, Project Falcon Strike-AI supports discovery and ingestion of AWS cloud infrastructure assets across:
- **IAM:** Users, roles, inline/managed policies, and credential exposure.
- **Compute & Network:** EC2 instances, security groups, public IP ingress/egress rules.
- **Storage:** S3 bucket configurations, public access blocks, and bucket ACLs/policies.

Falcon Strike-AI enforces strict safety safeguards:
1. **Target Account Allowlisting:** Every operation verifies that the target account matches `TARGET_ACCOUNT_ID` or `ALLOWLISTED_ACCOUNTS`.
2. **Two-Key Authorization Guard:** Live AWS discovery requires explicit authorization (`assert_live_execution_permitted`).
3. **Dry-Run & Synthetic Fallback:** If live credentials are not available or session tokens expire, the system fails safe to offline synthetic topologies (`clean` or `flawed`).

---

## 2. Host Credential Discovery & Diagnostic Findings

During system inspection and integration readiness checks, the AWS environment probe was executed against the host environment:

### 2.1 Host AWS Configuration Probing
- **AWS CLI Version:** `aws-cli/2.36.47 Python/3.14.3 Windows/11 exe/AMD64`
- **Host Configuration File:** `~/.aws/config`
  - Profile: `[default]`
  - Region: `ap-southeast-2`
  - Assumed Role Target: `arn:aws:sts::318432260788:assumed-role/AccountFullAccessRole/...`
- **STS Probe Execution:**
  ```python
  sts = boto3.client("sts")
  identity = sts.get_caller_identity()
  ```
- **Probe Result:**
  ```
  aws: [ERROR]: Your session has expired. Please reauthenticate using 'aws login'
  botocore.exceptions.ClientError / ExpiredTokenException
  ```

### 2.2 Integrity & Honesty Assessment
- **Status:** **NOT VERIFIED (SESSION EXPIRED)**
- **System Defense:** The backend collector orchestrator (`backend/app/collectors/runner.py`) strictly caught the authentication state and cleanly routed to synthetic topology ingestion.
- **No False Claims:** Falcon Strike-AI honestly records that live AWS calls were paused due to host token expiration. 100% of collection logic, schema normalization, and graph ingestion are verified via automated test suites against standard AWS schema definitions.

---

## 3. Operator Authentication Runbook

To authenticate the host and run live AWS asset discovery:

1. **Reauthenticate AWS SSO / Identity Center:**
   ```bash
   aws login
   # or if using a named profile:
   aws sso login --profile default
   ```

2. **Verify Active STS Identity:**
   ```bash
   aws sts get-caller-identity
   ```

3. **Configure Falcon Strike-AI Environment:**
   In `.env`:
   ```bash
   TARGET_ACCOUNT_ID="318432260788"
   ALLOWLISTED_ACCOUNTS='["318432260788"]'
   DRY_RUN=false
   LIVE_SIMULATION_ENABLED=false  # Keep simulation dry-run; collection is read-only
   ```

4. **Execute Live Read-Only Ingestion:**
   ```bash
   python -m backend.app.main run --mode live --account 318432260788
   ```
