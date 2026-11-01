# Falcon Strike-AI — Frontend-to-Backend API Integration Mapping

**Document Version:** 1.0.0  
**Date:** 2026-11-01  
**Project:** Falcon Strike-AI Enterprise Web Dashboard  

---

## 1. Overview

This document provides the complete, authoritative mapping between every frontend page/component in `frontend/src/` and the live FastAPI backend endpoints defined in `backend/app/api/v1/`.

All API requests are routed through the centralized, strongly typed client: `frontend/src/lib/api/client.ts`.

---

## 2. API Endpoint Mapping Matrix

| Page / Route | Component | Backend Endpoint | HTTP Method | Request Body / Query | Backend Response Schema |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Top Navigation** | `TopNavbar.tsx` | `/health` | `GET` | — | `HealthResponse` |
| **Top Navigation** | `TopNavbar.tsx` | `/api/v1/workflow/run` | `POST` | `PipelineRunRequest` | `WorkflowExecutionResult` |
| **Overview** (`/dashboard`) | `DashboardPage` | `/api/v1/graph/summary` | `GET` | — | `GraphSummary` |
| **Overview** (`/dashboard`) | `DashboardPage` | `/api/v1/attack-paths` | `GET` | — | `List[AttackPath]` |
| **Overview** (`/dashboard`) | `DashboardPage` | `/api/v1/graph/analyze` | `POST` | — | `AnalyzeResponse` |
| **Overview** (`/dashboard`) | `DashboardPage` | `/api/v1/executions` | `GET` | — | `List[CampaignExecutionRecord]` |
| **AWS Environment** (`/environment`) | `EnvironmentExplorerPage` | `/api/v1/graph/export` | `GET` | — | `GraphExport` |
| **AWS Environment** (`/environment`) | `EnvironmentExplorerPage` | `/api/v1/graph/analyze` | `POST` | — | `AnalyzeResponse` |
| **AWS Environment** (`/environment`) | `EnvironmentExplorerPage` | `/api/v1/environment/collect` | `POST` | `CollectRequest` | `CollectResponse` |
| **Attack Graph** (`/attack-graph`) | `AttackGraphPage` | `/api/v1/graph/export` | `GET` | — | `GraphExport` |
| **Attack Graph** (`/attack-graph`) | `AttackGraphPage` | `/api/v1/attack-paths` | `GET` | — | `List[AttackPath]` |
| **Attack Graph** (`/attack-graph`) | `AttackGraphPage` | `/api/v1/graph/analyze` | `POST` | — | `AnalyzeResponse` |
| **Campaign Planner** (`/campaign-planner`) | `CampaignPlannerPage` | `/api/v1/planner/campaigns` | `GET` | — | `List[CampaignPlan]` |
| **Campaign Planner** (`/campaign-planner`) | `CampaignPlannerPage` | `/api/v1/attack-paths` | `GET` | — | `List[AttackPath]` |
| **Campaign Planner** (`/campaign-planner`) | `CampaignPlannerPage` | `/api/v1/planner/generate` | `POST` | `CampaignGenerationRequest` | `CampaignPlan` |
| **Execution Center** (`/execution`) | `ExecutionCenterPage` | `/api/v1/executions` | `GET` | — | `List[CampaignExecutionRecord]` |
| **Execution Center** (`/execution`) | `ExecutionCenterPage` | `/api/v1/planner/campaigns` | `GET` | — | `List[CampaignPlan]` |
| **Execution Center** (`/execution`) | `ExecutionCenterPage` | `/api/v1/executions/dry-run` | `POST` | `DryRunExecutionRequest` | `CampaignExecutionRecord` |
| **Execution Center** (`/execution`) | `ExecutionCenterPage` | `/api/v1/executions/{run_id}/cancel` | `POST` | — | `{"run_id", "status"}` |
| **Execution Center** (`/execution`) | `ExecutionCenterPage` | `/api/v1/executions/{run_id}/teardown` | `POST` | — | `TeardownResult` |
| **Telemetry & Detection** (`/telemetry`) | `TelemetryDetectionPage` | `/api/v1/telemetry/events` | `GET` | `?run_id=...` | `List[SimulationEvent]` |
| **Telemetry & Detection** (`/telemetry`) | `TelemetryDetectionPage` | `/api/v1/telemetry/iocs` | `GET` | `?run_id=...` | `List[SyntheticIOC]` |
| **Telemetry & Detection** (`/telemetry`) | `TelemetryDetectionPage` | `/api/v1/telemetry/c2-beacons` | `GET` | `?run_id=...` | `List[C2BeaconEvent]` |
| **Telemetry & Detection** (`/telemetry`) | `TelemetryDetectionPage` | `/api/v1/telemetry/dns-queries` | `GET` | `?run_id=...` | `List[DNSSignallingEvent]` |
| **Telemetry & Detection** (`/telemetry`) | `TelemetryDetectionPage` | `/api/v1/detection/correlate` | `POST` | `DetectionCorrelateRequest` | `DetectionCorrelationReport` |
| **Telemetry & Detection** (`/telemetry`) | `TelemetryDetectionPage` | `/api/v1/detection/reports/{run_id}` | `GET` | — | `DetectionCorrelationReport` |
| **SOC Reports** (`/reports`) | `SOCReportsPage` | `/api/v1/reporting/{run_id}` | `GET` | — | `SOCReportData` |
| **SOC Reports** (`/reports`) | `SOCReportsPage` | `/api/v1/reporting/generate` | `POST` | `GenerateReportRequest` | `SOCReportData` |
| **SOC Reports** (`/reports`) | `SOCReportsPage` | `/api/v1/reporting/{run_id}/export` | `GET` | `?format=json\|markdown\|html` | Raw Document Stream |
| **Security & Controls** (`/security`) | `SecurityControlsPage` | `/api/v1/policies/status` | `GET` | — | `PolicyStatusResponse` |
| **Security & Controls** (`/security`) | `SecurityControlsPage` | `/api/v1/system/kill-switch` | `GET` | — | `KillSwitchStatus` |
| **Security & Controls** (`/security`) | `SecurityControlsPage` | `/api/v1/system/kill-switch` | `POST` | `KillSwitchTriggerRequest` | `KillSwitchRecord` |
| **Security & Controls** (`/security`) | `SecurityControlsPage` | `/api/v1/audit/verify/{run_id}` | `POST` | — | `AuditChainVerificationResult` |
| **Audit Logs** (`/audit-logs`) | `AuditLogsPage` | `/api/v1/audit/chain/{run_id}` | `GET` | — | `List[AuditRecord]` |
| **Audit Logs** (`/audit-logs`) | `AuditLogsPage` | `/api/v1/audit/verify/{run_id}` | `POST` | — | `AuditChainVerificationResult` |
| **Audit Logs** (`/audit-logs`) | `AuditLogsPage` | `/api/v1/audit/export/{run_id}` | `GET` | — | `{"run_id", "jsonl_content"}` |
| **Settings** (`/settings`) | `SettingsPage` | `/health` | `GET` | — | `HealthResponse` |

---

## 3. Strict Safety & Contract Guarantees

1. **No Contract Invention**: The frontend only calls endpoints that explicitly exist in `backend/app/api/v1/`.
2. **Default Dry-Run**: All execution buttons invoke `/api/v1/executions/dry-run` or `/api/v1/workflow/run` with `dry_run=true`.
3. **No Credential Leakage**: JWT tokens, secret keys, and passwords are never exposed in input fields or local browser storage.

