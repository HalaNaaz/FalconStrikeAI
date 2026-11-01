export type Severity = "CRITICAL" | "HIGH" | "MEDIUM" | "LOW" | "INFORMATIONAL";

export interface ComponentStatus {
  graph_store: string;
  policy_gate: string;
  audit_logger: string;
  c2_sink: string;
}

export interface HealthResponse {
  status: string;
  version: string;
  timestamp: string;
  environment: string;
  dry_run: boolean;
  target_account_id: string;
  allowlisted_accounts: string[];
  components: ComponentStatus;
}

export interface CollectorStatusResponse {
  available_collectors: string[];
  default_mode: string;
  dry_run: boolean;
  target_account: string;
  allowlisted_accounts: string[];
}

export interface CollectRequest {
  account_id?: string;
  force_synthetic?: boolean;
  synthetic_topology_type?: "flawed" | "clean";
}

export interface CollectResponse {
  collection_id: string;
  account_id: string;
  source_type: string;
  collected_at: string;
  duration_ms: number;
  total_assets: number;
  asset_breakdown: Record<string, number>;
  error_count: number;
}

export interface GraphSummary {
  total_nodes: number;
  total_edges: number;
  node_counts_by_type: Record<string, number>;
  edge_counts_by_type: Record<string, number>;
  total_findings: number;
  findings_by_severity: Record<string, number>;
}

export interface GraphNode {
  id: string;
  label?: string;
  name?: string;
  type: string;
  properties?: Record<string, any>;
  risk_score?: number;
  critical?: boolean;
}

export interface GraphEdge {
  id?: string;
  source: string;
  target: string;
  type: string;
  properties?: Record<string, any>;
}

export interface GraphExport {
  nodes: GraphNode[];
  edges: GraphEdge[];
}

export interface MisconfigurationFinding {
  finding_id: string;
  rule_id: string;
  rule_name: string;
  severity: Severity;
  target_node_id: string;
  description: string;
  remediation: string;
  details?: Record<string, any>;
}

export interface AnalyzeResponse {
  total_findings: number;
  findings_by_severity: Record<string, number>;
  findings: MisconfigurationFinding[];
}

export interface AttackPath {
  path_id: string;
  entry_node_id: string;
  target_node_id: string;
  node_sequence: string[];
  edge_sequence: string[];
  hop_count: number;
  risk_score: number;
  exploitability_score?: number;
  impact_score?: number;
  findings?: MisconfigurationFinding[];
  attck_mappings?: string[];
  narrative?: string;
}

export interface AttackPathDiscoveryResponse {
  total_paths: number;
  search_depth: number;
  paths: AttackPath[];
  execution_time_ms: number;
}

export interface CampaignStage {
  stage_id: string;
  step_number: number;
  tactic: string;
  technique_id: string;
  technique_name: string;
  target_resource: string;
  parameters: Record<string, any>;
  rationale: string;
  expected_observables: string[];
  cleanup_actions: string[];
}

export interface CampaignPlan {
  campaign_id: string;
  attack_path_id: string;
  target_crown_jewel: string;
  objective: string;
  stages: CampaignStage[];
  total_stages: number;
  rationale: string;
  planner_provider: string;
  schema_validated: boolean;
  approved_by_policy: boolean;
  generated_at?: string;
}

export interface CampaignGenerationRequest {
  attack_path_id?: string;
  provider?: string;
  run_id?: string;
}

export interface TechniqueContract {
  technique_id: string;
  name: string;
  tactic: string;
  description: string;
  preconditions: string[];
  execution_action: string;
  emitted_iocs: string[];
  safety_guarantee: string;
  teardown_strategy: string;
  reversible: boolean;
  requires_credentials: boolean;
}

export interface PolicyStatusResponse {
  policy_version: string;
  active_rules: string[];
  allowlisted_accounts: string[];
  dry_run_default: boolean;
  kill_switch_active: boolean;
  blast_radius_limits: {
    max_resources_touched: number;
    max_duration_seconds: number;
    max_campaign_stages: number;
  };
}

export interface PolicyDecision {
  decision_id: string;
  approved: boolean;
  violations?: string[];
  warnings?: string[];
  evaluation_summary?: string;
  rejected_rules?: string[];
  evaluated_at?: string;
}

export interface SimulationEvent {
  event_id: string;
  run_id: string;
  timestamp: string;
  technique_id: string;
  tactic: string;
  action: string;
  target_resource: string;
  success: boolean;
  error_message?: string | null;
  details?: Record<string, any>;
}

export interface CampaignExecutionRecord {
  run_id: string;
  campaign_id: string;
  mode: "DRY_RUN" | "LIVE_SIMULATION";
  status: "PENDING" | "IN_PROGRESS" | "COMPLETED" | "FAILED" | "CANCELLED";
  started_at: string;
  completed_at?: string | null;
  duration_ms?: number;
  stages_completed: number;
  stages_failed: number;
  runner_type: string;
  dry_run: boolean;
  events?: SimulationEvent[];
  teardown_status?: string;
}

export interface TeardownResult {
  teardown_id?: string;
  run_id: string;
  status: string;
  actions_reverted?: number;
  discrepancies?: string[];
  baseline_verified?: boolean;
  completed_at?: string;
  duration_ms?: number;
}

export interface SyntheticIOC {
  ioc_id: string;
  run_id: string;
  technique_id: string;
  ioc_type: string;
  value: string;
  sha256_hash: string;
  generated_at: string;
}

export interface C2BeaconEvent {
  beacon_id: string;
  run_id: string;
  timestamp: string;
  destination_uri: string;
  interval_seconds: number;
  jitter_applied: number;
  payload_token: string;
}

export interface DNSSignallingEvent {
  query_id: string;
  run_id: string;
  timestamp: string;
  queried_domain: string;
  record_type: string;
  signal_marker: string;
}

export interface SecurityDetectionEvent {
  event_id: string;
  detection_source: string;
  timestamp: string;
  rule_name: string;
  severity: Severity;
  technique_id?: string;
  matched_indicators: string[];
  raw_alert?: Record<string, any>;
}

export interface CorrelatedTechniqueResult {
  technique_id: string;
  status: "DETECTED" | "PARTIALLY_DETECTED" | "MISSED";
  first_emulated_at?: string | null;
  first_detected_at?: string | null;
  detection_latency_seconds?: number | null;
  matched_events: SecurityDetectionEvent[];
  ioc_coverage_ratio: number;
}

export interface DetectionCorrelationReport {
  run_id: string;
  campaign_id: string;
  total_techniques: number;
  detected_count: number;
  partially_detected_count: number;
  missed_count: number;
  coverage_percentage: number;
  mean_time_to_detect_seconds?: number | null;
  technique_results: CorrelatedTechniqueResult[];
  unmatched_detections?: SecurityDetectionEvent[];
  generated_at?: string;
}

export interface AuditRecord {
  sequence_id: number;
  record_id: string;
  run_id: string;
  timestamp: string;
  event_type: string;
  action: string;
  actor: string;
  details: Record<string, any>;
  previous_hash: string;
  record_hash: string;
}

export interface AuditChainVerificationResult {
  is_valid: boolean;
  total_records: number;
  genesis_hash?: string;
  latest_hash?: string;
  discrepancies: string[];
}

export interface RemediationItem {
  priority: "CRITICAL" | "HIGH" | "MEDIUM" | "LOW";
  misconfiguration_id: string;
  target_resource: string;
  remediation_action: string;
  effort: "LOW" | "MEDIUM" | "HIGH";
  validation_test: string;
}

export interface SOCReportData {
  report_id: string;
  run_id: string;
  generated_at: string;
  executive_summary: {
    environment_risk_score: number;
    defensive_coverage_percentage: number;
    mean_time_to_detect_seconds?: number | null;
    total_critical_path_length: number;
    total_techniques_evaluated: number;
  };
  threat_profile: {
    target_account: string;
    entry_point: string;
    crown_jewel: string;
    risk_score: number;
  };
  attack_path_narrative: string[];
  attack_heatmap: Array<{
    tactic: string;
    technique_id: string;
    technique_name: string;
    status: string;
    latency_seconds?: number | null;
  }>;
  detection_summary: {
    total_detected: number;
    total_partially_detected: number;
    total_missed: number;
    coverage_percentage: number;
  };
  remediations: RemediationItem[];
  audit_chain_summary: {
    total_records: number;
    is_valid: boolean;
    genesis_hash?: string;
    latest_hash?: string;
  };
  provenance: Record<string, string>;
}

export interface KillSwitchRecord {
  action: string;
  triggered_at: string;
  triggered_by: string;
  reason: string;
  run_id?: string | null;
  latency_ms: number;
  success: boolean;
}

export interface KillSwitchStatus {
  is_active: boolean;
  triggered_at?: string | null;
  triggered_by?: string | null;
  reason?: string | null;
  recent_records?: KillSwitchRecord[];
}

export interface WorkflowExecutionResult {
  run_id: string;
  campaign_id: string;
  status: string;
  duration_ms: number;
  stages_executed: number;
  detection_coverage: number;
  mttd_seconds?: number | null;
  baseline_teardown_verified: boolean;
  audit_chain_verified: boolean;
  report_paths?: Record<string, string>;
}

export interface IntegrationComponentStatus {
  name: string;
  status: "IMPLEMENTED" | "CONFIGURED" | "CONNECTED" | "VERIFIED" | "BLOCKED" | "NOT_CONFIGURED" | "NOT_VERIFIED";
  connected: boolean;
  verified: boolean;
  details: string;
  action_required?: string | null;
  metadata?: Record<string, any>;
}

export interface IntegrationsStatusResponse {
  docker_sandbox: IntegrationComponentStatus;
  aws_cloud: IntegrationComponentStatus;
  gemini_planner: IntegrationComponentStatus;
  kubernetes_runner: IntegrationComponentStatus;
}

