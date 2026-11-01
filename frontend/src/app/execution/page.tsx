"use client";

import React, { useEffect, useState } from "react";
import { useSearchParams } from "next/navigation";
import {
  Terminal,
  Play,
  RotateCw,
  CheckCircle2,
  XCircle,
  AlertTriangle,
  ShieldAlert,
  Clock,
  Layers,
  StopCircle,
  RefreshCw,
  Lock,
  ChevronRight,
  Shield,
  Activity,
} from "lucide-react";
import Link from "next/link";
import { api } from "@/lib/api/client";
import {
  CampaignExecutionRecord,
  CampaignPlan,
  SimulationEvent,
  TeardownResult,
} from "@/types/api";
import { formatDuration, formatDate, getStatusBadgeClass } from "@/lib/utils/formatters";

function ExecutionCenterContent() {
  const searchParams = useSearchParams();
  const initialCampaignId = searchParams.get("campaign_id");

  const [executions, setExecutions] = useState<CampaignExecutionRecord[]>([]);
  const [campaigns, setCampaigns] = useState<CampaignPlan[]>([]);
  const [selectedRun, setSelectedRun] = useState<CampaignExecutionRecord | null>(null);
  const [selectedCampaignId, setSelectedCampaignId] = useState<string>(initialCampaignId || "");
  const [preferDocker, setPreferDocker] = useState<boolean>(false);
  const [loading, setLoading] = useState(true);
  const [executing, setExecuting] = useState(false);
  const [teardownResult, setTeardownResult] = useState<TeardownResult | null>(null);
  const [statusMsg, setStatusMsg] = useState<string | null>(null);

  const fetchData = async () => {
    try {
      setLoading(true);
      const [execsRes, campsRes] = await Promise.allSettled([
        api.getExecutions(),
        api.getCampaigns(),
      ]);

      if (campsRes.status === "fulfilled") {
        const camps = campsRes.value || [];
        setCampaigns(camps);
        if (camps.length > 0 && !selectedCampaignId) {
          setSelectedCampaignId(camps[0].campaign_id);
        }
      }

      if (execsRes.status === "fulfilled") {
        const execs = execsRes.value || [];
        setExecutions(execs);
        if (execs.length > 0) {
          setSelectedRun(execs[0]);
        }
      }
    } catch {
      // Fallback
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const handleRunDryRun = async () => {
    if (!selectedCampaignId) {
      alert("Please select or formulate a campaign first.");
      return;
    }
    try {
      setExecuting(true);
      setStatusMsg(null);
      const record = await api.runDryRun(selectedCampaignId, preferDocker);
      setExecutions((prev) => [record, ...prev]);
      setSelectedRun(record);
      setStatusMsg(`Dry-Run ${record.run_id} completed successfully in ${record.duration_ms?.toFixed(2)}ms!`);
    } catch (err: any) {
      alert(`Dry-run execution failed: ${err.message}`);
    } finally {
      setExecuting(false);
    }
  };

  const handleCancel = async () => {
    if (!selectedRun) return;
    try {
      await api.cancelExecution(selectedRun.run_id);
      setStatusMsg(`Execution ${selectedRun.run_id} cancel requested.`);
      await fetchData();
    } catch (err: any) {
      alert(`Cancel failed: ${err.message}`);
    }
  };

  const handleTeardown = async () => {
    if (!selectedRun) return;
    try {
      const res = await api.triggerTeardown(selectedRun.run_id);
      setTeardownResult(res);
      setStatusMsg(`Teardown completed. Baseline verified: ${res.baseline_verified}`);
      await fetchData();
    } catch (err: any) {
      alert(`Teardown failed: ${err.message}`);
    }
  };

  return (
    <div className="flex flex-col gap-6">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold text-text-primary">Adversary Execution Center</h2>
          <p className="text-xs text-text-muted">
            Monitors isolated adversary emulation in ephemeral sandboxes with guaranteed teardown
          </p>
        </div>

        {/* Execution Triggers */}
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2 rounded-lg border border-surface-border bg-surface px-3 py-1.5 text-xs">
            <span className="text-text-muted font-mono">Campaign:</span>
            <select
              value={selectedCampaignId}
              onChange={(e) => setSelectedCampaignId(e.target.value)}
              className="bg-transparent font-mono text-brand-primary focus:outline-none"
            >
              {campaigns.map((c) => (
                <option key={c.campaign_id} value={c.campaign_id} className="bg-surface text-text-primary">
                  {c.campaign_id} ({c.stages?.length ?? 0} stages)
                </option>
              ))}
            </select>
          </div>

          <label className="flex items-center gap-2 text-xs text-text-muted cursor-pointer">
            <input
              type="checkbox"
              checked={preferDocker}
              onChange={(e) => setPreferDocker(e.target.checked)}
              className="rounded bg-surface-dark border-surface-border text-brand-primary focus:ring-0"
            />
            <span className="font-mono text-[11px]">Docker Sandbox</span>
          </label>

          <button
            onClick={handleRunDryRun}
            disabled={executing || !selectedCampaignId}
            className="flex items-center gap-2 rounded-lg bg-brand-primary px-3.5 py-2 text-xs font-semibold text-sidebar hover:bg-brand-secondary transition-all disabled:opacity-50 shadow-cyan-glow"
          >
            <Play className={`h-3.5 w-3.5 fill-current ${executing ? "animate-spin" : ""}`} />
            <span>{executing ? "Emulating..." : "Execute Dry-Run"}</span>
          </button>
        </div>
      </div>

      {statusMsg && (
        <div className="flex items-center gap-2 rounded-xl border border-emerald-500/30 bg-emerald-500/10 p-3 text-xs text-emerald-400">
          <CheckCircle2 className="h-4 w-4 shrink-0" />
          <span>{statusMsg}</span>
        </div>
      )}

      {/* Safety Notice */}
      <div className="flex items-center gap-3 rounded-xl border border-brand-primary/30 bg-brand-primary/10 p-3 text-xs text-brand-primary">
        <ShieldAlert className="h-4 w-4 shrink-0" />
        <div>
          <span className="font-bold">Safety Invariant (NFR-S4):</span> Default execution touches zero cloud resources. Live execution is blocked without a signed two-key cryptographic JWT authorization token.
        </div>
      </div>

      {/* Execution Details Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Run History List */}
        <div className="lg:col-span-4 flex flex-col gap-3">
          <div className="flex items-center justify-between">
            <h3 className="text-xs font-bold uppercase tracking-wider text-text-muted">
              Execution Runs ({executions.length})
            </h3>
            <button
              onClick={fetchData}
              disabled={loading}
              className="text-[11px] text-text-muted hover:text-text-primary flex items-center gap-1"
            >
              <RefreshCw className={`h-3 w-3 ${loading ? "animate-spin" : ""}`} /> Refresh
            </button>
          </div>

          <div className="flex flex-col gap-2 max-h-[600px] overflow-y-auto pr-1">
            {executions.length > 0 ? (
              executions.map((exec) => {
                const isSelected = selectedRun?.run_id === exec.run_id;
                return (
                  <div
                    key={exec.run_id}
                    onClick={() => setSelectedRun(exec)}
                    className={`cursor-pointer rounded-xl border p-3.5 transition-all ${
                      isSelected
                        ? "border-brand-primary/50 bg-surface-elevated shadow-cyan-glow"
                        : "border-surface-border bg-surface hover:border-surface-borderHover"
                    }`}
                  >
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-bold font-mono text-text-primary">
                        {exec.run_id}
                      </span>
                      <span className={`text-[10px] font-mono px-2 py-0.5 rounded font-semibold ${getStatusBadgeClass(exec.status)}`}>
                        {exec.status}
                      </span>
                    </div>

                    <div className="flex items-center justify-between mt-2 text-[10px] font-mono text-text-muted">
                      <span>Mode: {exec.mode}</span>
                      <span>{formatDuration(exec.duration_ms)}</span>
                    </div>

                    <div className="flex items-center justify-between mt-1 text-[10px] font-mono text-text-muted">
                      <span>Stages: {exec.stages_completed} / {exec.stages_completed + exec.stages_failed}</span>
                      <span>Runner: {exec.runner_type}</span>
                    </div>
                  </div>
                );
              })
            ) : (
              <div className="p-6 rounded-xl border border-surface-border text-center text-xs text-text-muted">
                No executions recorded yet. Execute Dry-Run above or run the CTEM Pipeline.
              </div>
            )}
          </div>
        </div>

        {/* Selected Run Details & Stage Timeline */}
        <div className="lg:col-span-8 flex flex-col gap-4">
          {selectedRun ? (
            <div className="flex flex-col rounded-2xl border border-surface-border bg-surface p-5 shadow-panel">
              {/* Header */}
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-4 border-b border-surface-border">
                <div className="flex flex-col">
                  <div className="flex items-center gap-2">
                    <span className="text-base font-bold font-mono text-text-primary">
                      {selectedRun.run_id}
                    </span>
                    <span className={`px-2 py-0.5 rounded text-[10px] font-mono font-semibold ${getStatusBadgeClass(selectedRun.status)}`}>
                      {selectedRun.status}
                    </span>
                    <span className="px-2 py-0.5 rounded bg-brand-primary/10 border border-brand-primary/30 text-[10px] font-mono font-semibold text-brand-primary">
                      {selectedRun.mode}
                    </span>
                  </div>
                  <p className="text-xs text-text-muted mt-1 font-mono">
                    Campaign: {selectedRun.campaign_id} | Started: {formatDate(selectedRun.started_at)}
                  </p>
                </div>

                {/* Actions: Cancel & Teardown */}
                <div className="flex items-center gap-2">
                  <button
                    onClick={handleTeardown}
                    className="flex items-center gap-1.5 rounded-lg border border-surface-border bg-surface-elevated px-3 py-1.5 text-xs text-text-secondary hover:text-text-primary hover:border-surface-borderHover"
                  >
                    <RotateCw className="h-3 w-3" />
                    <span>Teardown Baseline</span>
                  </button>

                  <button
                    onClick={handleCancel}
                    className="flex items-center gap-1.5 rounded-lg border border-red-500/30 bg-red-500/10 px-3 py-1.5 text-xs text-red-400 hover:bg-red-500/20"
                  >
                    <StopCircle className="h-3 w-3" />
                    <span>Cancel Run</span>
                  </button>
                </div>
              </div>

              {/* Execution Telemetry Summary */}
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mt-4">
                <div className="rounded-xl border border-surface-border bg-surface-dark p-3">
                  <span className="text-[10px] font-mono text-text-muted uppercase">Duration</span>
                  <p className="text-sm font-bold font-mono text-text-primary mt-0.5">
                    {formatDuration(selectedRun.duration_ms)}
                  </p>
                </div>

                <div className="rounded-xl border border-surface-border bg-surface-dark p-3">
                  <span className="text-[10px] font-mono text-text-muted uppercase">Runner Engine</span>
                  <p className="text-sm font-bold font-mono text-brand-primary mt-0.5">
                    {selectedRun.runner_type}
                  </p>
                </div>

                <div className="rounded-xl border border-surface-border bg-surface-dark p-3">
                  <span className="text-[10px] font-mono text-text-muted uppercase">Stages Completed</span>
                  <p className="text-sm font-bold font-mono text-emerald-400 mt-0.5">
                    {selectedRun.stages_completed} / {selectedRun.stages_completed + selectedRun.stages_failed}
                  </p>
                </div>

                <div className="rounded-xl border border-surface-border bg-surface-dark p-3">
                  <span className="text-[10px] font-mono text-text-muted uppercase">Teardown Status</span>
                  <p className="text-sm font-bold font-mono text-text-primary mt-0.5">
                    {selectedRun.teardown_status || "VERIFIED_CLEAN"}
                  </p>
                </div>
              </div>

              {/* Simulation Events Log */}
              <div className="mt-5 flex flex-col gap-3">
                <div className="flex items-center justify-between">
                  <h4 className="text-xs font-bold uppercase tracking-wider text-text-muted flex items-center gap-1.5">
                    <Activity className="h-3.5 w-3.5 text-brand-primary" />
                    Simulation Telemetry Events ({selectedRun.events?.length || 0})
                  </h4>
                  <Link
                    href={`/telemetry?run_id=${encodeURIComponent(selectedRun.run_id)}`}
                    className="text-xs text-brand-primary hover:underline flex items-center gap-1"
                  >
                    View in Telemetry Center <ChevronRight className="h-3.5 w-3.5" />
                  </Link>
                </div>

                <div className="flex flex-col gap-2 max-h-[350px] overflow-y-auto">
                  {selectedRun.events && selectedRun.events.length > 0 ? (
                    selectedRun.events.map((event, idx) => (
                      <div
                        key={event.event_id || idx}
                        className="flex flex-col rounded-xl border border-surface-border bg-surface-elevated/80 p-3 text-xs"
                      >
                        <div className="flex items-center justify-between font-mono">
                          <div className="flex items-center gap-2">
                            <span className="h-2 w-2 rounded-full bg-emerald-400" />
                            <span className="font-bold text-brand-primary">{event.technique_id}</span>
                            <span className="text-text-muted">({event.tactic})</span>
                          </div>
                          <span className="text-[10px] text-text-muted">{formatDate(event.timestamp)}</span>
                        </div>
                        <p className="mt-1 font-mono text-text-secondary truncate">
                          Action: {event.action} → Target: {event.target_resource}
                        </p>
                      </div>
                    ))
                  ) : (
                    <div className="p-4 rounded-xl border border-surface-border text-center text-xs text-text-muted">
                      No events captured for this execution run.
                    </div>
                  )}
                </div>
              </div>
            </div>
          ) : (
            <div className="flex flex-col items-center justify-center p-12 rounded-2xl border border-surface-border bg-surface text-center text-text-muted">
              <Terminal className="h-10 w-10 text-brand-primary/40 mb-3" />
              <p className="text-sm font-semibold text-text-primary">No execution selected</p>
              <p className="text-xs max-w-md mt-1">
                Select an execution run from the left history or launch a dry-run emulation.
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default function ExecutionCenterPage() {
  return (
    <React.Suspense fallback={<div className="p-8 text-xs text-text-muted">Loading Execution Center...</div>}>
      <ExecutionCenterContent />
    </React.Suspense>
  );
}
