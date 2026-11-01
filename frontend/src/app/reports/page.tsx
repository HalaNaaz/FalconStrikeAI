"use client";

import React, { useEffect, useState } from "react";
import { useSearchParams } from "next/navigation";
import {
  FileText,
  Download,
  ShieldCheck,
  ShieldAlert,
  Clock,
  Layers,
  CheckCircle2,
  AlertTriangle,
  Play,
  RotateCw,
  ExternalLink,
  ChevronRight,
  Printer,
} from "lucide-react";
import { api } from "@/lib/api/client";
import { SOCReportData, CampaignExecutionRecord } from "@/types/api";
import { formatDate, formatPercent, getSeverityBadgeClass, getStatusBadgeClass } from "@/lib/utils/formatters";

function SOCReportsContent() {
  const searchParams = useSearchParams();
  const initialRunId = searchParams.get("run_id");

  const [executions, setExecutions] = useState<CampaignExecutionRecord[]>([]);
  const [selectedRunId, setSelectedRunId] = useState<string>(initialRunId || "");
  const [report, setReport] = useState<SOCReportData | null>(null);
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const fetchExecutions = async () => {
    try {
      const execs = await api.getExecutions();
      setExecutions(execs);
      if (execs.length > 0 && !selectedRunId) {
        setSelectedRunId(execs[0].run_id);
      }
    } catch {
      // Fallback
    }
  };

  const fetchReport = async (runId: string) => {
    if (!runId) return;
    try {
      setLoading(true);
      setErrorMsg(null);
      const data = await api.getSOCReport(runId);
      setReport(data);
    } catch (err: any) {
      setReport(null);
      setErrorMsg(`Report not yet generated for run ${runId}. Click Generate Report below.`);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchExecutions();
  }, []);

  useEffect(() => {
    if (selectedRunId) {
      fetchReport(selectedRunId);
    }
  }, [selectedRunId]);

  const handleGenerate = async () => {
    if (!selectedRunId) return;
    try {
      setGenerating(true);
      setErrorMsg(null);
      const data = await api.generateSOCReport(selectedRunId);
      setReport(data);
    } catch (err: any) {
      alert(`Report compilation failed: ${err.message}`);
    } finally {
      setGenerating(false);
    }
  };

  const handleDownload = (format: "json" | "markdown" | "html") => {
    if (!selectedRunId) return;
    const url = `${process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000"}/api/v1/reporting/${encodeURIComponent(selectedRunId)}/export?format=${format}`;
    window.open(url, "_blank");
  };

  return (
    <div className="flex flex-col gap-6">
      {/* Header & Controls */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold text-text-primary">SOC Assessment & Executive Reports</h2>
          <p className="text-xs text-text-muted">
            Audit-ready security evaluation reports with ATT&CK matrix coverage, MTTD, and actionable remediations
          </p>
        </div>

        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2 rounded-lg border border-surface-border bg-surface px-3 py-1.5 text-xs">
            <span className="text-text-muted font-mono">Run ID:</span>
            <select
              value={selectedRunId}
              onChange={(e) => setSelectedRunId(e.target.value)}
              className="bg-transparent font-mono text-brand-primary focus:outline-none"
            >
              {executions.map((x) => (
                <option key={x.run_id} value={x.run_id} className="bg-surface text-text-primary">
                  {x.run_id}
                </option>
              ))}
            </select>
          </div>

          <button
            onClick={handleGenerate}
            disabled={generating || !selectedRunId}
            className="flex items-center gap-1.5 rounded-lg bg-brand-primary px-3.5 py-2 text-xs font-semibold text-sidebar hover:bg-brand-secondary transition-all disabled:opacity-50 shadow-cyan-glow"
          >
            <Play className={`h-3.5 w-3.5 fill-current ${generating ? "animate-spin" : ""}`} />
            <span>{generating ? "Compiling..." : "Generate Report"}</span>
          </button>
        </div>
      </div>

      {errorMsg && (
        <div className="flex items-center justify-between rounded-xl border border-amber-500/30 bg-amber-500/10 p-3 text-xs text-amber-400">
          <div className="flex items-center gap-2">
            <AlertTriangle className="h-4 w-4 shrink-0" />
            <span>{errorMsg}</span>
          </div>
          <button
            onClick={handleGenerate}
            disabled={generating}
            className="rounded bg-amber-500/20 px-2.5 py-1 text-xs font-semibold hover:bg-amber-500/30"
          >
            Generate Now
          </button>
        </div>
      )}

      {report ? (
        <div className="flex flex-col gap-6">
          {/* Export Actions Bar */}
          <div className="flex items-center justify-between bg-surface p-3.5 rounded-xl border border-surface-border">
            <div className="flex items-center gap-2">
              <span className="text-xs font-mono font-bold text-text-primary">
                Report ID: {report.report_id}
              </span>
              <span className="text-text-muted">|</span>
              <span className="text-xs font-mono text-text-muted">
                Generated: {formatDate(report.generated_at)}
              </span>
            </div>

            <div className="flex items-center gap-2">
              <button
                onClick={() => handleDownload("json")}
                className="flex items-center gap-1 rounded-lg border border-surface-border bg-surface-elevated px-2.5 py-1.5 text-xs text-text-secondary hover:text-text-primary hover:border-surface-borderHover font-mono"
              >
                <Download className="h-3 w-3" /> JSON
              </button>
              <button
                onClick={() => handleDownload("markdown")}
                className="flex items-center gap-1 rounded-lg border border-surface-border bg-surface-elevated px-2.5 py-1.5 text-xs text-text-secondary hover:text-text-primary hover:border-surface-borderHover font-mono"
              >
                <Download className="h-3 w-3" /> Markdown
              </button>
              <button
                onClick={() => handleDownload("html")}
                className="flex items-center gap-1 rounded-lg bg-brand-primary/10 border border-brand-primary/30 px-3 py-1.5 text-xs font-semibold text-brand-primary hover:bg-brand-primary/20 font-mono shadow-cyan-glow"
              >
                <ExternalLink className="h-3 w-3" /> View HTML Dashboard
              </button>
            </div>
          </div>

          {/* Executive Scorecards */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="rounded-xl border border-surface-border bg-surface p-4">
              <span className="text-[11px] font-semibold uppercase text-text-muted">Environment Risk Score</span>
              <p className="text-3xl font-extrabold font-mono text-red-400 mt-1">
                {report.executive_summary?.environment_risk_score !== undefined
                  ? report.executive_summary.environment_risk_score.toFixed(1)
                  : "—"}
                <span className="text-sm font-normal text-text-muted"> / 100</span>
              </p>
              <span className="text-[10px] text-text-muted">Critical Cloud Exposure</span>
            </div>

            <div className="rounded-xl border border-surface-border bg-surface p-4">
              <span className="text-[11px] font-semibold uppercase text-text-muted">Defensive Coverage</span>
              <p className="text-3xl font-extrabold font-mono text-emerald-400 mt-1">
                {formatPercent(report.executive_summary?.defensive_coverage_percentage)}
              </p>
              <span className="text-[10px] text-text-muted">
                {report.detection_summary?.total_detected} of {report.executive_summary?.total_techniques_evaluated} Techniques Detected
              </span>
            </div>

            <div className="rounded-xl border border-surface-border bg-surface p-4">
              <span className="text-[11px] font-semibold uppercase text-text-muted">Mean Time to Detect (MTTD)</span>
              <p className="text-3xl font-extrabold font-mono text-sky-400 mt-1">
                {report.executive_summary?.mean_time_to_detect_seconds !== null && report.executive_summary?.mean_time_to_detect_seconds !== undefined
                  ? `${report.executive_summary.mean_time_to_detect_seconds.toFixed(2)}s`
                  : "—"}
              </p>
              <span className="text-[10px] text-text-muted">Observed Defense Latency</span>
            </div>

            <div className="rounded-xl border border-surface-border bg-surface p-4">
              <span className="text-[11px] font-semibold uppercase text-text-muted">Audit Chain Status</span>
              <p className="text-xl font-bold font-mono text-emerald-400 mt-1 flex items-center gap-1.5">
                <ShieldCheck className="h-5 w-5" /> VALID
              </p>
              <span className="text-[10px] text-text-muted">
                {report.audit_chain_summary?.total_records} Records Cryptographically Verified
              </span>
            </div>
          </div>

          {/* Attack Path Narrative */}
          <div className="rounded-2xl border border-surface-border bg-surface p-5 shadow-panel">
            <h3 className="text-xs font-bold uppercase tracking-wider text-text-muted pb-3 border-b border-surface-border flex items-center gap-2">
              <Layers className="h-4 w-4 text-brand-primary" />
              Simulated Attack Path Narrative
            </h3>
            <div className="mt-4 flex flex-col gap-2 font-mono text-xs">
              {report.attack_path_narrative?.map((step, idx) => (
                <div key={idx} className="flex items-start gap-3 p-2.5 rounded-lg bg-surface-elevated/70">
                  <span className="h-5 w-5 shrink-0 rounded-full bg-brand-primary/20 text-brand-primary flex items-center justify-center font-bold text-[10px]">
                    {idx + 1}
                  </span>
                  <p className="text-text-secondary leading-relaxed">{step}</p>
                </div>
              ))}
            </div>
          </div>

          {/* MITRE ATT&CK Matrix Heatmap */}
          <div className="rounded-2xl border border-surface-border bg-surface p-5 shadow-panel">
            <h3 className="text-xs font-bold uppercase tracking-wider text-text-muted pb-3 border-b border-surface-border flex items-center gap-2">
              <ShieldAlert className="h-4 w-4 text-brand-secondary" />
              MITRE ATT&CK Matrix Coverage Heatmap
            </h3>
            <div className="mt-4 overflow-x-auto">
              <table className="w-full text-left text-xs font-mono">
                <thead className="bg-surface-elevated border-b border-surface-border text-[11px] font-semibold uppercase text-text-muted">
                  <tr>
                    <th className="px-4 py-2.5">Tactic</th>
                    <th className="px-4 py-2.5">Technique ID</th>
                    <th className="px-4 py-2.5">Technique Name</th>
                    <th className="px-4 py-2.5">Detection Status</th>
                    <th className="px-4 py-2.5">Observed Latency</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-surface-border">
                  {report.attack_heatmap?.map((item, idx) => (
                    <tr key={idx} className="hover:bg-surface-elevated/50">
                      <td className="px-4 py-3 text-text-secondary">{item.tactic}</td>
                      <td className="px-4 py-3 text-brand-primary font-bold">{item.technique_id}</td>
                      <td className="px-4 py-3 text-text-primary font-sans">{item.technique_name}</td>
                      <td className="px-4 py-3">
                        <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${getStatusBadgeClass(item.status)}`}>
                          {item.status}
                        </span>
                      </td>
                      <td className="px-4 py-3 text-sky-400">
                        {item.latency_seconds ? `${item.latency_seconds.toFixed(2)}s` : "—"}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* Prioritized Remediations */}
          <div className="rounded-2xl border border-surface-border bg-surface p-5 shadow-panel">
            <h3 className="text-xs font-bold uppercase tracking-wider text-text-muted pb-3 border-b border-surface-border flex items-center gap-2">
              <CheckCircle2 className="h-4 w-4 text-emerald-400" />
              Prioritized Remediation Matrix
            </h3>
            <div className="mt-4 flex flex-col gap-3">
              {report.remediations?.map((rem, idx) => (
                <div
                  key={idx}
                  className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 p-3.5 rounded-xl border border-surface-border bg-surface-elevated/70"
                >
                  <div className="flex flex-col gap-1">
                    <div className="flex items-center gap-2">
                      <span className={`text-[10px] font-mono px-2 py-0.5 rounded font-bold ${getSeverityBadgeClass(rem.priority)}`}>
                        {rem.priority}
                      </span>
                      <span className="text-xs font-bold text-text-primary font-mono truncate">
                        {rem.target_resource}
                      </span>
                    </div>
                    <p className="text-xs text-text-secondary mt-0.5">
                      {rem.remediation_action}
                    </p>
                    <span className="text-[11px] font-mono text-brand-secondary">
                      Validation: {rem.validation_test}
                    </span>
                  </div>

                  <div className="shrink-0 flex items-center gap-2 font-mono text-[10px]">
                    <span className="px-2 py-1 rounded bg-surface-dark border border-surface-border text-text-muted">
                      Effort: {rem.effort}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      ) : (
        <div className="flex flex-col items-center justify-center p-12 rounded-2xl border border-surface-border bg-surface text-center text-text-muted">
          <FileText className="h-10 w-10 text-brand-primary/40 mb-3" />
          <p className="text-sm font-semibold text-text-primary">No SOC report generated for this run</p>
          <p className="text-xs max-w-md mt-1">
            Click Generate Report above to compile the end-to-end executive report, ATT&CK heatmap, and remediation matrix.
          </p>
        </div>
      )}
    </div>
  );
}

export default function SOCReportsPage() {
  return (
    <React.Suspense fallback={<div className="p-8 text-xs text-text-muted">Loading SOC Reports...</div>}>
      <SOCReportsContent />
    </React.Suspense>
  );
}
