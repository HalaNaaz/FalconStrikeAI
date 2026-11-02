"use client";

import React, { useEffect, useState } from "react";
import {
  Layers,
  ShieldAlert,
  GitCommit,
  PlayCircle,
  Activity,
  Clock,
  RefreshCw,
  AlertTriangle,
} from "lucide-react";
import { CloudAccountCarousel } from "@/components/dashboard/CloudAccountCarousel";
import { CenterRadarVisualizer } from "@/components/dashboard/CenterRadarVisualizer";
import { HeroMetrics } from "@/components/dashboard/HeroMetrics";
import { ThreatCards } from "@/components/dashboard/ThreatCards";
import { api } from "@/lib/api/client";
import {
  GraphSummary,
  AttackPath,
  MisconfigurationFinding,
  CampaignExecutionRecord,
  DetectionCorrelationReport,
  CampaignPlan,
} from "@/types/api";
import { formatPercent } from "@/lib/utils/formatters";

export default function DashboardPage() {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [graphSummary, setGraphSummary] = useState<GraphSummary | null>(null);
  const [attackPaths, setAttackPaths] = useState<AttackPath[]>([]);
  const [findings, setFindings] = useState<MisconfigurationFinding[]>([]);
  const [executions, setExecutions] = useState<CampaignExecutionRecord[]>([]);
  const [campaigns, setCampaigns] = useState<CampaignPlan[]>([]);
  const [latestCorrelation, setLatestCorrelation] = useState<DetectionCorrelationReport | null>(null);

  const loadData = async () => {
    try {
      setLoading(true);
      setError(null);
      const [summaryRes, pathsRes, analyzeRes, execsRes, campsRes] = await Promise.allSettled([
        api.getGraphSummary(),
        api.getAttackPaths(),
        api.analyzeGraph(),
        api.getExecutions(),
        api.getCampaigns(),
      ]);

      if (summaryRes.status === "fulfilled") setGraphSummary(summaryRes.value);
      if (pathsRes.status === "fulfilled") setAttackPaths(pathsRes.value);
      if (analyzeRes.status === "fulfilled") setFindings(analyzeRes.value.findings);
      if (campsRes.status === "fulfilled") setCampaigns(campsRes.value);

      if (execsRes.status === "fulfilled") {
        const execs = execsRes.value || [];
        setExecutions(execs);
        if (execs.length > 0) {
          try {
            const corr = await api.getCorrelationReport(execs[0].run_id);
            setLatestCorrelation(corr);
          } catch {
            setLatestCorrelation(null);
          }
        }
      }
    } catch (err: any) {
      setError(err.message || "Failed to load dashboard data");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  // Rigorous backend-derived metrics
  const totalAssets = graphSummary ? graphSummary.total_nodes : 0;
  const criticalFindings = findings.filter((f) => f.severity === "CRITICAL").length;
  const highFindings = findings.filter((f) => f.severity === "HIGH").length;
  const mediumFindings = findings.filter((f) => f.severity === "MEDIUM").length;
  const lowFindings = findings.filter(
    (f) => f.severity === "LOW" || f.severity === "INFORMATIONAL"
  ).length;

  const totalPaths = attackPaths.length;
  const executedCount = executions.length;
  const uniqueAssetsAtRisk = new Set(
    findings
      .map((f) => f.target_node_id || f.resource_id)
      .filter((id): id is string => typeof id === "string" && id.length > 0)
  ).size;

  // Real detection coverage and MTTD
  const coverageDisplay = latestCorrelation
    ? formatPercent(latestCorrelation.coverage_percentage)
    : executedCount > 0
    ? "Correlate in Telemetry"
    : "Pending Run";

  const mttdDisplay = latestCorrelation?.mean_time_to_detect_seconds !== null &&
    latestCorrelation?.mean_time_to_detect_seconds !== undefined
    ? `${latestCorrelation.mean_time_to_detect_seconds.toFixed(2)}s`
    : executedCount > 0
    ? "Pending"
    : "—";

  // Category counts from graphSummary and normalized findings
  const matchesAssetCategory = (f: MisconfigurationFinding, keywords: string[]): boolean => {
    const target = (f.target_node_id || f.resource_id || "").toLowerCase();
    const cat = (f.category || f.rule_name || "").toLowerCase();
    const desc = (f.description || f.explanation || "").toLowerCase();
    return keywords.some((kw) => target.includes(kw) || cat.includes(kw) || desc.includes(kw));
  };

  const computeCount = graphSummary?.node_counts_by_type?.["EC2_INSTANCE"] ?? 0;
  const computeAtRisk = findings.filter((f) =>
    matchesAssetCategory(f, ["instance", "ec2", "compute"])
  ).length;

  const identityCount =
    (graphSummary?.node_counts_by_type?.["IAM_USER"] ?? 0) +
    (graphSummary?.node_counts_by_type?.["IAM_ROLE"] ?? 0) +
    (graphSummary?.node_counts_by_type?.["IAM_POLICY"] ?? 0);
  const identityAtRisk = findings.filter((f) =>
    matchesAssetCategory(f, ["iam", "role", "user", "policy", "privilege", "wildcard"])
  ).length;

  const networkCount = graphSummary?.node_counts_by_type?.["SECURITY_GROUP"] ?? 0;
  const networkAtRisk = findings.filter((f) =>
    matchesAssetCategory(f, ["sg", "security-group", "network", "ingress", "port"])
  ).length;

  const dataCount = graphSummary?.node_counts_by_type?.["S3_BUCKET"] ?? 0;
  const dataAtRisk = findings.filter((f) =>
    matchesAssetCategory(f, ["s3", "bucket", "storage"])
  ).length;

  return (
    <div className="flex flex-col gap-6">
      {/* Top Carousel */}
      <div className="flex items-center justify-between">
        <CloudAccountCarousel />
        <button
          onClick={loadData}
          disabled={loading}
          className="ml-3 shrink-0 flex items-center gap-1.5 rounded-lg border border-surface-border bg-surface px-3 py-2 text-xs font-medium text-text-secondary hover:text-text-primary hover:bg-surface-elevated transition-colors"
          title="Refresh Dashboard Data"
        >
          <RefreshCw className={`h-3.5 w-3.5 ${loading ? "animate-spin" : ""}`} />
          <span className="hidden sm:inline">Refresh</span>
        </button>
      </div>

      {error && (
        <div className="flex items-center gap-2 rounded-xl border border-amber-500/30 bg-amber-500/10 p-3 text-xs text-amber-400">
          <AlertTriangle className="h-4 w-4 shrink-0" />
          <span>Notice: Could not sync live telemetry from backend. Please ensure the backend is running.</span>
        </div>
      )}

      {/* KPI Metric Cards — Grounded in live backend state */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3">
        <div className="flex flex-col rounded-xl border border-surface-border bg-surface p-3.5">
          <div className="flex items-center justify-between text-text-muted">
            <span className="text-[11px] font-semibold uppercase tracking-wider">Total AWS Assets</span>
            <Layers className="h-3.5 w-3.5 text-cyan-400" />
          </div>
          <span className="text-xl font-bold text-text-primary font-mono mt-1">
            {totalAssets}
          </span>
          <span className="text-[10px] text-text-muted">Graph Nodes</span>
        </div>

        <div className="flex flex-col rounded-xl border border-surface-border bg-surface p-3.5">
          <div className="flex items-center justify-between text-text-muted">
            <span className="text-[11px] font-semibold uppercase tracking-wider">Critical Gaps</span>
            <ShieldAlert className="h-3.5 w-3.5 text-red-400" />
          </div>
          <span className="text-xl font-bold text-red-400 font-mono mt-1">
            {criticalFindings}
          </span>
          <span className="text-[10px] text-text-muted">Severe Exploits</span>
        </div>

        <div className="flex flex-col rounded-xl border border-surface-border bg-surface p-3.5">
          <div className="flex items-center justify-between text-text-muted">
            <span className="text-[11px] font-semibold uppercase tracking-wider">Attack Paths</span>
            <GitCommit className="h-3.5 w-3.5 text-amber-400" />
          </div>
          <span className="text-xl font-bold text-amber-400 font-mono mt-1">
            {totalPaths}
          </span>
          <span className="text-[10px] text-text-muted">Ranked Traversals</span>
        </div>

        <div className="flex flex-col rounded-xl border border-surface-border bg-surface p-3.5">
          <div className="flex items-center justify-between text-text-muted">
            <span className="text-[11px] font-semibold uppercase tracking-wider">Campaigns Run</span>
            <PlayCircle className="h-3.5 w-3.5 text-brand-primary" />
          </div>
          <span className="text-xl font-bold text-text-primary font-mono mt-1">
            {executedCount}
          </span>
          <span className="text-[10px] text-text-muted">Completed Runs</span>
        </div>

        <div className="flex flex-col rounded-xl border border-surface-border bg-surface p-3.5">
          <div className="flex items-center justify-between text-text-muted">
            <span className="text-[11px] font-semibold uppercase tracking-wider">Detection Coverage</span>
            <Activity className="h-3.5 w-3.5 text-emerald-400" />
          </div>
          <span className="text-xl font-bold text-emerald-400 font-mono mt-1">
            {coverageDisplay}
          </span>
          <span className="text-[10px] text-text-muted">Defensive Posture</span>
        </div>

        <div className="flex flex-col rounded-xl border border-surface-border bg-surface p-3.5">
          <div className="flex items-center justify-between text-text-muted">
            <span className="text-[11px] font-semibold uppercase tracking-wider">Observed MTTD</span>
            <Clock className="h-3.5 w-3.5 text-sky-400" />
          </div>
          <span className="text-xl font-bold text-sky-400 font-mono mt-1">
            {mttdDisplay}
          </span>
          <span className="text-[10px] text-text-muted">Mean Detection Time</span>
        </div>
      </div>

      {/* Hero Category Breakdown + Center Constellation Radar */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
        <div className="lg:col-span-5 flex flex-col justify-center">
          <HeroMetrics
            totalAssets={totalAssets}
            assetsAtRiskCount={uniqueAssetsAtRisk}
            computeCount={computeCount}
            computeAtRisk={computeAtRisk}
            identityCount={identityCount}
            identityAtRisk={identityAtRisk}
            networkCount={networkCount}
            networkAtRisk={networkAtRisk}
            dataCount={dataCount}
            dataAtRisk={dataAtRisk}
          />
        </div>

        <div className="lg:col-span-7">
          <CenterRadarVisualizer
            totalIssues={findings.length}
            openCases={attackPaths.length}
            threatCasesCount={criticalFindings + highFindings}
            postureCasesCount={mediumFindings + lowFindings}
            criticalThreats={criticalFindings}
            highThreats={highFindings}
            mediumThreats={mediumFindings}
            lowThreats={lowFindings}
            remediationsAvailable={findings.filter((f) => f.remediation).length}
            automationsAvailable={campaigns.length}
          />
        </div>
      </div>

      {/* Bottom Threats & Posture Cards */}
      <ThreatCards findings={findings} attackPaths={attackPaths} />
    </div>
  );
}
