import {
  HealthResponse,
  CollectorStatusResponse,
  CollectRequest,
  CollectResponse,
  GraphSummary,
  GraphExport,
  AnalyzeResponse,
  AttackPath,
  AttackPathDiscoveryResponse,
  CampaignPlan,
  CampaignGenerationRequest,
  TechniqueContract,
  PolicyStatusResponse,
  PolicyDecision,
  CampaignExecutionRecord,
  SimulationEvent,
  TeardownResult,
  SyntheticIOC,
  C2BeaconEvent,
  DNSSignallingEvent,
  KillSwitchStatus,
  KillSwitchRecord,
  DetectionCorrelationReport,
  AuditRecord,
  AuditChainVerificationResult,
  SOCReportData,
  WorkflowExecutionResult,
} from "@/types/api";

const BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";

async function getAuthToken(): Promise<string | null> {
  if (typeof window === "undefined") return null;
  let token = sessionStorage.getItem("falcon_auth_token");
  if (!token) {
    try {
      const res = await fetch(`${BASE_URL}/api/v1/auth/token`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          operator_id: "operator-console",
          role: "admin",
          target_account_id: "000000000000",
          valid_duration_seconds: 86400,
        }),
      });
      if (res.ok) {
        const data = await res.json();
        token = data.access_token;
        if (token) {
          sessionStorage.setItem("falcon_auth_token", token);
        }
      }
    } catch {
      // Backend may be offline during initial client boot
    }
  }
  return token;
}

export class ApiError extends Error {
  status: number;
  data: any;

  constructor(message: string, status: number, data?: any) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.data = data;
  }
}

async function request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  const url = `${BASE_URL}${endpoint}`;
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), 15000);

  const token = await getAuthToken();
  const authHeaders: Record<string, string> = token ? { Authorization: `Bearer ${token}` } : {};

  try {
    const res = await fetch(url, {
      ...options,
      signal: controller.signal,
      headers: {
        "Content-Type": "application/json",
        Accept: "application/json",
        ...authHeaders,
        ...(options.headers || {}),
      },
    });

    clearTimeout(timeoutId);

    if (!res.ok) {
      let errorBody: any = null;
      try {
        errorBody = await res.json();
      } catch {
        errorBody = await res.text();
      }
      const message =
        typeof errorBody === "object" && errorBody?.detail
          ? String(errorBody.detail)
          : `Request failed with status ${res.status}`;
      throw new ApiError(message, res.status, errorBody);
    }

    return (await res.json()) as T;
  } catch (err: any) {
    clearTimeout(timeoutId);
    if (err.name === "AbortError") {
      throw new ApiError("Request timed out after 15 seconds", 408);
    }
    if (err instanceof ApiError) {
      throw err;
    }
    throw new ApiError(err.message || "Failed to communicate with backend", 0, err);
  }
}

export const api = {
  // System Health
  getHealth: () => request<HealthResponse>("/health"),

  // Collectors
  getCollectorStatus: () => request<CollectorStatusResponse>("/api/v1/collectors/status"),
  collectEnvironment: (req: CollectRequest = {}) =>
    request<CollectResponse>("/api/v1/environment/collect", {
      method: "POST",
      body: JSON.stringify(req),
    }),

  // Property Graph
  getGraphSummary: () => request<GraphSummary>("/api/v1/graph/summary"),
  exportGraph: () => request<GraphExport>("/api/v1/graph/export"),
  analyzeGraph: () => request<AnalyzeResponse>("/api/v1/graph/analyze", { method: "POST" }),

  // Attack Paths
  getAttackPaths: () => request<AttackPath[]>("/api/v1/attack-paths"),
  discoverAttackPaths: (maxDepth = 6) =>
    request<AttackPathDiscoveryResponse>("/api/v1/attack-paths/discover", {
      method: "POST",
      body: JSON.stringify({ max_depth: maxDepth }),
    }),

  // Planner
  getCampaigns: () => request<CampaignPlan[]>("/api/v1/planner/campaigns"),
  getCampaign: (id: string) => request<CampaignPlan>(`/api/v1/planner/campaigns/${id}`),
  generateCampaign: (req: CampaignGenerationRequest = {}) =>
    request<CampaignPlan>("/api/v1/planner/generate", {
      method: "POST",
      body: JSON.stringify(req),
    }),

  // Techniques
  getTechniques: () => request<TechniqueContract[]>("/api/v1/techniques"),
  getTechnique: (id: string) => request<TechniqueContract>(`/api/v1/techniques/${id}`),

  // Policies
  getPolicyStatus: () => request<PolicyStatusResponse>("/api/v1/policies/status"),
  evaluatePolicy: (campaignId: string) =>
    request<PolicyDecision>("/api/v1/policies/evaluate", {
      method: "POST",
      body: JSON.stringify({ campaign_id: campaignId }),
    }),

  // Executions
  getExecutions: () => request<CampaignExecutionRecord[]>("/api/v1/executions"),
  getExecution: (runId: string) => request<CampaignExecutionRecord>(`/api/v1/executions/${runId}`),
  runDryRun: (campaignId: string, preferDocker = false) =>
    request<CampaignExecutionRecord>("/api/v1/executions/dry-run", {
      method: "POST",
      body: JSON.stringify({ campaign_id: campaignId, prefer_docker: preferDocker }),
    }),
  runLiveSimulation: (campaignId: string, operatorToken?: string, secondaryToken?: string) =>
    request<CampaignExecutionRecord>("/api/v1/executions/live", {
      method: "POST",
      body: JSON.stringify({
        campaign_id: campaignId,
        operator_token: operatorToken,
        secondary_approver_token: secondaryToken,
      }),
    }),
  cancelExecution: (runId: string) =>
    request<{ run_id: string; status: string }>(`/api/v1/executions/${runId}/cancel`, {
      method: "POST",
    }),
  triggerTeardown: (runId: string) =>
    request<TeardownResult>(`/api/v1/executions/${runId}/teardown`, {
      method: "POST",
    }),

  // Telemetry & IOCs
  getSimulationEvents: (runId: string) =>
    request<SimulationEvent[]>(`/api/v1/telemetry/events?run_id=${encodeURIComponent(runId)}`),
  getSyntheticIOCs: (runId: string) =>
    request<SyntheticIOC[]>(`/api/v1/telemetry/iocs?run_id=${encodeURIComponent(runId)}`),
  getC2Beacons: (runId?: string) =>
    request<C2BeaconEvent[]>(
      runId ? `/api/v1/telemetry/c2-beacons?run_id=${encodeURIComponent(runId)}` : "/api/v1/telemetry/c2-beacons"
    ),
  getDNSQueries: (runId?: string) =>
    request<DNSSignallingEvent[]>(
      runId ? `/api/v1/telemetry/dns-queries?run_id=${encodeURIComponent(runId)}` : "/api/v1/telemetry/dns-queries"
    ),

  // System & Emergency Kill Switch
  getKillSwitchStatus: () => request<KillSwitchStatus>("/api/v1/system/kill-switch"),
  triggerKillSwitch: (reason: string, operatorId = "security-admin", runId?: string) =>
    request<KillSwitchRecord>("/api/v1/system/kill-switch", {
      method: "POST",
      body: JSON.stringify({ reason, operator_id: operatorId, run_id: runId }),
    }),
  resetKillSwitch: (authorizedToken: string, operatorId = "security-admin") =>
    request<{ status: string; message: string; operator_id: string }>("/api/v1/system/kill-switch/reset", {
      method: "POST",
      body: JSON.stringify({ authorized_token: authorizedToken, operator_id: operatorId }),
    }),

  // Detection Correlation
  correlateDetections: (runId: string, profile = "FULL_COVERAGE") =>
    request<DetectionCorrelationReport>("/api/v1/detection/correlate", {
      method: "POST",
      body: JSON.stringify({ run_id: runId, detection_profile: profile }),
    }),
  getCorrelationReport: (runId: string) =>
    request<DetectionCorrelationReport>(`/api/v1/detection/reports/${encodeURIComponent(runId)}`),

  // Audit Integrity
  getAuditChain: (runId: string) => request<AuditRecord[]>(`/api/v1/audit/chain/${encodeURIComponent(runId)}`),
  verifyAuditChain: (runId: string) =>
    request<AuditChainVerificationResult>(`/api/v1/audit/verify/${encodeURIComponent(runId)}`, {
      method: "POST",
    }),

  // SOC Reporting
  generateSOCReport: (runId: string, profile = "FULL_COVERAGE") =>
    request<SOCReportData>("/api/v1/reporting/generate", {
      method: "POST",
      body: JSON.stringify({ run_id: runId, detection_profile: profile }),
    }),
  getSOCReport: (runId: string) => request<SOCReportData>(`/api/v1/reporting/${encodeURIComponent(runId)}`),

  // End-to-End Workflow
  runWorkflow: (mode = "synthetic", dryRun = true) =>
    request<WorkflowExecutionResult>("/api/v1/workflow/run", {
      method: "POST",
      body: JSON.stringify({ mode, dry_run: dryRun }),
    }),

  // Authentication & Session
  login: async (operatorId: string, role = "operator", targetAccountId = "000000000000") => {
    const res = await request<{ access_token: string }>("/api/v1/auth/token", {
      method: "POST",
      body: JSON.stringify({
        operator_id: operatorId,
        role,
        target_account_id: targetAccountId,
      }),
    });
    if (res.access_token && typeof window !== "undefined") {
      sessionStorage.setItem("falcon_auth_token", res.access_token);
    }
    return res;
  },
  logout: () => {
    if (typeof window !== "undefined") {
      sessionStorage.removeItem("falcon_auth_token");
    }
  },
  getMe: () => request<{ operator_id: string; role: string; target_account: string }>("/api/v1/auth/me"),
};


