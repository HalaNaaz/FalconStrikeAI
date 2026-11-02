# Falcon Strike-AI — AWS Live Lab Validation Report

**Document Version:** 2.0.0  
**Date:** 2026-11-01  
**Classification:** Cloud Security Operations & Environment Verification  
**PRD Traceability:** `FR-1.1`, `FR-1.2`, `FR-1.3`, `NFR-S1`, `NFR-S4`  
**Current Status:** **LIVE VERIFIED (AUTHENTICATED READ-ONLY INVENTORY ACTIVE)**

---

## 1. Objective & Scope

Under PRD `FR-1.1`, Project Falcon Strike-AI supports discovery and ingestion of AWS cloud infrastructure assets across:
- **IAM:** Users, roles, inline/managed policies, and credential exposure.
- **Compute & Network:** EC2 instances, security groups, public IP ingress/egress rules.
- **Storage:** S3 bucket configurations, public access blocks, and bucket ACLs/policies.

Falcon Strike-AI enforces strict safety safeguards:
1. **Target Account Allowlisting:** Every operation verifies that the target account matches `TARGET_ACCOUNT_ID` or `ALLOWLISTED_ACCOUNTS`.
2. **Two-Key Authorization Guard:** Live AWS discovery requires explicit authorization (`assert_live_execution_permitted`).
3. **Dry-Run & Synthetic Fallback:** If live credentials are not available, the system fails safe to offline synthetic topologies (`clean` or `flawed`).
4. **Zero Mutation Guarantee:** Collectors use strictly read-only AWS APIs (`List*`, `Describe*`, `Get*`). No AWS resources are ever created, modified, or deleted.

---

## 2. Authentication & Allowlist Verification

### 2.1 STS Identity Verification
- **Target Account:** `318432260788`
- **Active Profile:** `default`
- **Configured Region:** `ap-southeast-2`
- **Assumed Role:** `arn:aws:sts::318432260788:assumed-role/AccountFullAccessRole/...`
- **STS Validation Result:** Confirmed valid live session via `sts.get_caller_identity()`. Zero tokens or credentials exposed.

### 2.2 Allowlist Enforcement Verification
Before executing live collection, allowlist verification was tested:
```python
# Initial verification: account not yet in default allowlist
settings.is_account_allowlisted("318432260788") -> False

# Verification of security invariant:
settings.assert_account_allowlisted("318432260788")
# Result: RAISED AccountNotAllowlistedError (Security invariant verified)
```
- **Allowlist Integrity:** Confirmed that no account IDs are added automatically or dynamically. The system strictly rejects unapproved target accounts.

---

## 3. Read-Only Collector Test Evidence

All three collectors were executed against account `318432260788` in region `ap-southeast-2`:

| Collector | Service | Required API Permissions | Execution Status | Live Assets Discovered | Errors Encountered |
| :--- | :--- | :--- | :---: | :--- | :---: |
| **`AWSIAMCollector`** | IAM | `iam:ListUsers`<br>`iam:ListRoles`<br>`iam:ListPolicies`<br>`iam:Get*Policy` | **PASS** | **12 IAM Roles**<br>(e.g. `AccountFullAccessRole`, `AWSServiceRoleForOrganizations`, etc.) | **0** |
| **`AWSNetworkCollector`** | EC2 | `ec2:DescribeInstances`<br>`ec2:DescribeSecurityGroups` | **PASS** | **1 Security Group**<br>(`sg-0a6f7e0285f302ed5` / `default`)<br>0 EC2 instances | **0** |
| **`AWSS3Collector`** | S3 | `s3:ListBuckets`<br>`s3:GetBucketLocation`<br>`s3:GetBucketPolicy` | **PASS** | **0 S3 Buckets** | **0** |

### 3.1 Observed Resource Inventory Details
- **Discovered IAM Roles (12 total):**
  - `AccountFullAccessRole` (active session role)
  - `AWSManagedAccountManagementAccessRole`
  - `AWSManagedAdvancedFeaturesActivationRole`
  - `AWSServiceRoleForAwsUserNotifications`
  - `AWSServiceRoleForBudgetsSpendLimitMember`
  - `AWSServiceRoleForComputeOptimizer`
  - `AWSServiceRoleForCostOptimizationHub`
  - `AWSServiceRoleForIAMRoleManager`
  - `AWSServiceRoleForOrganizations`
  - `AWSServiceRoleForResourceExplorer`
  - `AWSServiceRoleForSupport`
  - `AWSServiceRoleForTrustedAdvisor`
- **Discovered Security Groups (1 total in `ap-southeast-2`):**
  - Group ID: `sg-0a6f7e0285f302ed5` (Name: `default`)
- **Discovered EC2 Instances:** 0 instances active in `ap-southeast-2`.
- **Discovered S3 Buckets:** 0 buckets active in account.

---

## 4. Safety & Operational Assessment

1. **Non-Destructive Assurance:** Zero `Create*`, `Update*`, `Put*`, or `Delete*` API calls were made.
2. **Credential Protection:** Session tokens and authentication materials remained strictly isolated in the host credential cache.
3. **No Campaign Execution:** No attack paths were traversed and zero adversary emulation techniques were triggered against the live account.
4. **Conclusion:** Falcon Strike-AI's AWS read-only ingestion pipeline is fully operational, safely contained, and validated against a real AWS account.
