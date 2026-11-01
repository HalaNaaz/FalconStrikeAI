# Falcon Strike-AI — Property Graph Schema Specification

**Document Version:** 1.0.0  
**Date:** 2026-11-01  
**Project:** Falcon Strike-AI  
**Conformance:** PRD FR-1.4, FR-1.5  

---

## 1. Schema Overview

The Falcon Strike-AI property graph normalizes disparate AWS cloud infrastructure and identity states into an interconnected, directed property graph. The schema models principals, compute workloads, security boundaries, storage assets, and trust relationships to enable sub-second attack-path discovery.

---

## 2. Node Types (`NodeType`)

| Node Label | ID Format | Key Properties | Description |
| :--- | :--- | :--- | :--- |
| **`ACCOUNT`** | `account:{account_id}` | `name`, `source` | Represents the top-level AWS account boundary. |
| **`PUBLIC_ENDPOINT`** | `endpoint:public-internet` | `description` | Virtual anchor node representing unauthenticated external Internet access (`0.0.0.0/0`). |
| **`IAM_USER`** | `arn:aws:iam::{account}:user/{name}` | `user_id`, `name` | IAM user principal. |
| **`IAM_ROLE`** | `arn:aws:iam::{account}:role/{name}` | `role_id`, `name`, `is_instance_profile_role`, `trusted_principals` | IAM role that can be assumed by trusted entities. |
| **`POLICY`** | `arn:aws:iam::{account}:policy/{name}` | `is_admin`, `is_inline`, `statements_count` | IAM managed or inline policy document. |
| **`EC2_INSTANCE`** | `ec2:{instance_id}` | `instance_type`, `public_ip`, `is_public`, `associated_iam_role` | Virtual compute workload. |
| **`INSTANCE_PROFILE`** | `arn:aws:iam::{account}:instance-profile/{name}`| `name` | Compute-to-identity binding container. |
| **`SECURITY_GROUP`** | `sg:{group_id}` | `name`, `vpc_id`, `allows_internet_ingress` | Virtual firewall governing network traffic. |
| **`S3_BUCKET`** | `arn:aws:s3:::{bucket_name}` | `name`, `is_public`, `public_access_block_enabled`, `criticality` | Object storage asset. |

---

## 3. Relationship Types (`RelationshipType`)

| Relationship Type | Source Node | Target Node | Actionable in Attack Path? | Semantics |
| :--- | :--- | :--- | :---: | :--- |
| **`EXPOSED_TO_INTERNET`**| `PUBLIC_ENDPOINT` | `EC2_INSTANCE` / `S3_BUCKET` | **YES** | Target is accessible from the public internet without prior authentication. |
| **`RUNS_AS`** | `EC2_INSTANCE` | `IAM_ROLE` | **YES** | Workload possesses credentials associated with the instance profile role. |
| **`ASSUMES_ROLE`** | `IAM_USER` / `IAM_ROLE` | `IAM_ROLE` | **YES** | Principal can assume target role via `sts:AssumeRole` trust or policy. |
| **`CAN_ACCESS`** | `IAM_ROLE` | `S3_BUCKET` | **YES** | Role permissions grant read/write access to storage bucket objects. |
| **`TRUSTS`** | `IAM_ROLE` | `IAM_ROLE` / `IAM_USER` | NO | Inverse representation of role trust policies. |
| **`HAS_POLICY`** | `IAM_ROLE` / `IAM_USER` | `POLICY` | NO | Policy attachment linking principal to permissions. |
| **`ATTACHED_TO`** | `EC2_INSTANCE` | `SECURITY_GROUP` | NO | Security group assignment to network interface. |
| **`CONTAINS`** | `ACCOUNT` | *All Assets* | NO | Organizational containment hierarchy. |

---

## 4. Misconfiguration Enrichment Rules

The `MisconfigurationAnalyzer` evaluates nodes and edges to detect non-destructive exposure patterns:

1. **Wildcard Permissions (`CRITICAL`):** Detected when a `POLICY` node contains `Action: "*"` and `Resource: "*"`.
2. **Public Exposure (`HIGH`):** Detected when an `EC2_INSTANCE` has an incoming `EXPOSED_TO_INTERNET` edge.
3. **Public Storage (`HIGH`):** Detected when an `S3_BUCKET` has `is_public: true` or public bucket policy.
4. **Privilege Escalation (`CRITICAL`):** Detected when a role has an outgoing `ASSUMES_ROLE` edge to another role that holds administrator privileges.
5. **Risky Trust (`CRITICAL`):** Detected when an `IAM_ROLE` trusts wildcard principal (`*`).

