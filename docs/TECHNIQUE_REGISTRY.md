# Falcon Strike-AI — MITRE ATT&CK Technique Registry

**Document Version:** 1.0.0  
**Date:** 2026-11-01  
**Project:** Falcon Strike-AI  
**Conformance:** PRD Section 6.3, Appendix A (FR-2.2, FR-3.1, FR-3.2, FR-3.5)  

---

## 1. Overview & Safety Mandate

The Technique Registry is the centralized allowlist and contract enforcement point for all adversary emulation behaviors in Falcon Strike-AI. The engine is **emulation-only**: it reproduces the observable signals (API calls, log patterns, network metadata) required to validate defensive detections, without executing live exploits, malware, destructive code, or harvesting real credentials.

---

## 2. Curated 15 ATT&CK Techniques Catalog

| Technique ID | Technique Name | Tactic | What the Engine Emulates (Non-Destructive) | Expected Telemetry |
| :--- | :--- | :--- | :--- | :--- |
| **`T1078`** | Valid Accounts | Initial Access | Authenticated API access from unusual principal/source in-lab; anomalous AssumeRole. | CloudTrail: `sts:AssumeRole` |
| **`T1526`** | Cloud Service Discovery | Discovery | Bursts of read-only describe/list calls; observable as service enumeration. | CloudTrail: `ec2:DescribeInstances` |
| **`T1087`** | Account Discovery | Discovery | Read-only inventory of IAM users and roles. | CloudTrail: `iam:ListUsers`, `iam:ListRoles` |
| **`T1580`** | Cloud Infrastructure Discovery | Discovery | Read-only inventory of security groups and VPC network elements. | CloudTrail: `ec2:DescribeSecurityGroups` |
| **`T1098`** | Account Manipulation | Privilege Escalation | Traversal of an assume-role trust edge to a higher-privilege lab role (role chaining). | CloudTrail: `sts:AssumeRole` chaining event |
| **`T1136`** | Create Account | Persistence | Creation of a tagged, benign, auto-expiring lab principal; fully reversed at teardown. | CloudTrail: `iam:CreateUser` |
| **`T1053`** | Scheduled Task/Job | Persistence | Creation of a benign scheduled job in-lab; observable as scheduler creation; removed at teardown. | CloudTrail: `events:PutRule` |
| **`T1552`** | Unsecured Credentials | Credential Access | Discovery of a planted, clearly-marked benign marker secret file. | CloudTrail: `s3:GetObject` |
| **`T1555`** | Credentials from Password Stores | Credential Access | Read pattern against a lab secret store using synthetic test marker keys only. | CloudTrail: `secretsmanager:GetSecretValue` |
| **`T1550`** | Use Alternate Authentication Material | Defense Evasion | Token-reuse pattern in-lab; observable as alternate auth usage. | CloudTrail: `AssumeRoleWithWebIdentity` |
| **`T1071`** | Application Layer Protocol | Command and Control | Jittered HTTPS beacons carrying inert marker tokens to local lab sink for detection validation. | VPC Flow Logs: outbound 443 with jitter |
| **`T1071.004`** | Application Layer Protocol: DNS | Command and Control | DNS-based signalling patterns with inert marker tokens terminating at local lab sink. | Route53 Resolver query logs |
| **`T1572`** | Protocol Tunneling | Command and Control | Tunneling traffic shape simulation over standard ports terminating at local sink. | VPC Flow Logs: persistent connection shape |
| **`T1568`** | Dynamic Resolution | Command and Control | Dynamic-resolution traffic shapes mimicking Fast Flux / DGA against local lab zone. | High-frequency DNS lookup bursts |
| **`T1090.004`** | Proxy: Domain Fronting | Command and Control | Domain-fronting-style HTTP Host header mismatch traffic shape terminating at lab sink. | Web proxy / TLS SNI mismatch logs |
| **`T1537`** | Transfer Data to Cloud Account | Exfiltration | Copy of an inert benign marker string to a lab-owned, allowlisted destination; reversible. | CloudTrail: `s3:CopyObject` |

---

## 3. Mandatory Contract Structure

Every registered technique module must implement `TechniqueContract`:
1. **Preconditions**: Verified before scheduling.
2. **Safety Constraints**: Guaranteed behavioral bounds.
3. **Expected Benign IOCs**: Deterministic indicators (e.g. `user_agent: FalconStrike-Emulation-Agent/1.0`, marker strings) recorded as ground truth for detection correlation.
4. **Teardown Instructions**: If a technique touches state (e.g. `T1136`, `T1053`, `T1537`), explicit reversal steps must be declared and registered in the teardown stack.

