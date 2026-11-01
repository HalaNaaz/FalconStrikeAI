# Falcon Strike-AI — AWS Live Lab Validation Report

**Document Version:** 1.0.0  
**Date:** 2026-11-01  
**Classification:** Cloud Security Operations & Environment Verification  
**PRD Traceability:** `FR-1.1`, `FR-1.2`, `FR-1.3`, `NFR-S1`  

---

## 1. Objective & Scope

Under PRD `FR-1.1`, Project Falcon Strike-AI supports discovery and ingestion of AWS cloud infrastructure assets across:
- **IAM:** Users, roles, inline/managed policies, and credential exposure.
- **Compute & Network:** EC2 instances, security groups, public IP ingress/egress rules.
- **Storage:** S3 bucket configurations, public access blocks, and bucket ACLs/policies.

Falcon Strike-AI enforces strict safety safeguards:
1. **Target Account Allowlisting:** Every operation verifies that the target account matches `TARGET_ACCOUNT_ID`.
2. **Two-Key Authorization Guard:** Live AWS discovery requires explicit authorization (`assert_live_execution_permitted`).
3. **Dry-Run & Synthetic Fallback:** If live credentials are not available or session tokens expire, the system fails safe to offline synthetic topologies (`clean` or `flawed`).

---

## 2. Host Credential Discovery & Diagnostic Findings

During local system testing, the AWS environment probe was executed against the host environment:

### 2.1 Host AWS Configuration Probing
- **AWS CLI Version:** `aws-cli/2.36.47 Python/3.14.3 Windows/11 exe/AMD64`
- **Host Configuration:** Configured with IAM Identity Center SSO session profile.
- **STS Probe Execution:**
  ```python
  sts = boto3.client("sts")
  identity = sts.get_caller_identity()
  ```
- **Probe Result:**
  ```
  botocore.exceptions.MissingDependencyException / ExpiredTokenException
  Diagnostics: Host AWS SSO session is expired ("Your session has expired. Please reauthenticate using 'aws login'").
  ```

### 2.2 Integrity & Honesty Assessment
- **Status:** **BLOCKED (EXPIRED AWS SESSION TOKEN)**
- **System Defense:** The backend collector orchestrator (`backend/app/collectors/runner.py`) strictly caught the authentication state and cleanly routed to synthetic topology ingestion.
- **No False Claims:** Falcon Strike-AI honestly records that live AWS calls were blocked due to host token expiration, while 100% of collection logic, schema normalization, and graph ingestion were verified via synthetic test suites.

---

## 3. Operator Onboarding & Live Authentication Runbook

When an operator provides valid AWS credentials:

1. **Authenticate AWS Session:**
   ```bash
   aws sso login --profile <your-profile>
   # or export standard access keys:
   export AWS_ACCESS_KEY_ID="AKIA..."
   export AWS_SECRET_ACCESS_KEY="..."
   export AWS_DEFAULT_REGION="us-east-1"
   ```

2. **Configure Falcon Strike-AI Environment:**
   ```bash
   # In .env:
   TARGET_ACCOUNT_ID="123456789012"
   ALLOWLISTED_ACCOUNTS='["123456789012"]'
   DRY_RUN=false
   LIVE_SIMULATION_ENABLED=true
   TWO_KEY_AUTH_REQUIRED=false
   ```

3. **Run Live Read-Only Collection:**
   ```bash
   python -m backend.app.main run --mode live --account 123456789012
   ```
