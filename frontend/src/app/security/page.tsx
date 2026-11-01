"use client";

import React, { useEffect, useState } from "react";
import {
  ShieldAlert,
  ShieldCheck,
  Lock,
  StopCircle,
  AlertTriangle,
  RotateCw,
  Key,
  Layers,
  FileCheck2,
  CheckCircle2,
  RefreshCw,
} from "lucide-react";
import { api } from "@/lib/api/client";
import { PolicyStatusResponse, KillSwitchStatus, AuditChainVerificationResult, CampaignExecutionRecord } from "@/types/api";

export default function SecurityControlsPage() {
  const [policyStatus, setPolicyStatus] = useState<PolicyStatusResponse | null>(null);
  const [killSwitch, setKillSwitch] = useState<KillSwitchStatus | null>(null);
  const [executions, setExecutions] = useState<CampaignExecutionRecord[]>([]);
  const [selectedRunId, setSelectedRunId] = useState<string>("");
  const [auditResult, setAuditResult] = useState<AuditChainVerificationResult | null>(null);

  const [loading, setLoading] = useState(true);
  const [triggeringKill, setTriggeringKill] = useState(false);
  const [killReason, setKillReason] = useState("Operator emergency stop during security review");
  const [showKillModal, setShowKillModal] = useState(false);
  const [actionMsg, setActionMsg] = useState<string | null>(null);

  const fetchData = async () => {
    try {
      setLoading(true);
      const [polRes, ksRes, execsRes] = await Promise.allSettled([
        api.getPolicyStatus(),
        api.getKillSwitchStatus(),
        api.getExecutions(),
      ]);

      if (polRes.status === "fulfilled") setPolicyStatus(polRes.value);
      if (ksRes.status === "fulfilled") setKillSwitch(ksRes.value);
      if (execsRes.status === "fulfilled") {
        const execs = execsRes.value || [];
        setExecutions(execs);
        if (execs.length > 0 && !selectedRunId) {
          setSelectedRunId(execs[0].run_id);
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

  const handleVerifyAudit = async () => {
    if (!selectedRunId) return;
    try {
      const res = await api.verifyAuditChain(selectedRunId);
      setAuditResult(res);
      setActionMsg(`Audit Chain verification completed for ${selectedRunId}: Valid = ${res.is_valid}`);
    } catch (err: any) {
      alert(`Audit verification failed: ${err.message}`);
    }
  };

  const handleTriggerKillSwitch = async () => {
    try {
      setTriggeringKill(true);
      const res = await api.triggerKillSwitch(killReason, "security-operator", selectedRunId || undefined);
      setShowKillModal(false);
      setActionMsg(`EMERGENCY KILL SWITCH ENGAGED! Latency: ${res.latency_ms.toFixed(3)}ms. Execution halted.`);
      await fetchData();
    } catch (err: any) {
      alert(`Kill switch trigger error: ${err.message}`);
    } finally {
      setTriggeringKill(false);
    }
  };

  return (
    <div className="flex flex-col gap-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold text-text-primary">Security Posture & Safety Controls</h2>
          <p className="text-xs text-text-muted">
            Inspect hardcoded safety invariants, cryptographic authorization gates, blast-radius boundaries, and emergency kill switches
          </p>
        </div>

        <button
          onClick={fetchData}
          disabled={loading}
          className="flex items-center gap-1.5 rounded-lg border border-surface-border bg-surface px-3 py-2 text-xs text-text-secondary hover:text-text-primary hover:bg-surface-elevated transition-colors"
        >
          <RefreshCw className={`h-3.5 w-3.5 ${loading ? "animate-spin" : ""}`} />
          <span>Refresh Controls</span>
        </button>
      </div>

      {actionMsg && (
        <div className="flex items-center gap-2 rounded-xl border border-emerald-500/30 bg-emerald-500/10 p-3 text-xs text-emerald-400">
          <CheckCircle2 className="h-4 w-4 shrink-0" />
          <span>{actionMsg}</span>
        </div>
      )}

      {/* Safety Controls Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Panel 1: Policy Gate & Rules */}
        <div className="flex flex-col rounded-2xl border border-surface-border bg-surface p-5 shadow-panel">
          <div className="flex items-center justify-between pb-3 border-b border-surface-border">
            <div className="flex items-center gap-2">
              <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-emerald-500/10 text-emerald-400 border border-emerald-500/30">
                <ShieldCheck className="h-4 w-4" />
              </div>
              <h3 className="text-xs font-bold uppercase tracking-wider text-text-primary">
                Safety Policy Gate Engine
              </h3>
            </div>
            <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-emerald-500/20 text-emerald-400 border border-emerald-500/40 font-bold">
              ENFORCED (v{policyStatus?.policy_version || "1.0.0"})
            </span>
          </div>

          <div className="mt-4 flex flex-col gap-3 text-xs">
            <div>
              <span className="text-[11px] font-semibold text-text-muted uppercase">Active Policy Rules</span>
              <div className="mt-1 flex flex-col gap-1.5 font-mono text-[11px]">
                {policyStatus?.active_rules.map((rule, idx) => (
                  <div key={idx} className="flex items-center gap-2 p-2 rounded bg-surface-dark border border-surface-border text-text-secondary">
                    <span className="h-1.5 w-1.5 rounded-full bg-emerald-400" />
                    <span>{rule}</span>
                  </div>
                ))}
              </div>
            </div>

            <div className="grid grid-cols-3 gap-2 mt-2 pt-3 border-t border-surface-border">
              <div className="p-2 rounded bg-surface-dark border border-surface-border">
                <span className="text-[9px] font-mono text-text-muted uppercase">Max Resources</span>
                <p className="text-sm font-bold font-mono text-brand-primary">
                  {policyStatus?.blast_radius_limits?.max_resources_touched || 5}
                </p>
              </div>

              <div className="p-2 rounded bg-surface-dark border border-surface-border">
                <span className="text-[9px] font-mono text-text-muted uppercase">Max Duration</span>
                <p className="text-sm font-bold font-mono text-brand-primary">
                  {policyStatus?.blast_radius_limits?.max_duration_seconds || 600}s
                </p>
              </div>

              <div className="p-2 rounded bg-surface-dark border border-surface-border">
                <span className="text-[9px] font-mono text-text-muted uppercase">Max Stages</span>
                <p className="text-sm font-bold font-mono text-brand-primary">
                  {policyStatus?.blast_radius_limits?.max_campaign_stages || 10}
                </p>
              </div>
            </div>
          </div>
        </div>

        {/* Panel 2: Emergency Kill Switch */}
        <div className="flex flex-col rounded-2xl border border-red-500/30 bg-surface p-5 shadow-panel">
          <div className="flex items-center justify-between pb-3 border-b border-surface-border">
            <div className="flex items-center gap-2">
              <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-red-500/10 text-red-400 border border-red-500/30">
                <StopCircle className="h-4 w-4" />
              </div>
              <h3 className="text-xs font-bold uppercase tracking-wider text-red-400">
                Central Emergency Kill Switch (NFR-S3)
              </h3>
            </div>
            <span className={`text-[10px] font-mono px-2 py-0.5 rounded font-bold ${
              killSwitch?.is_active
                ? "bg-red-500/20 text-red-400 border border-red-500/40 animate-pulse"
                : "bg-surface-dark text-text-muted border border-surface-border"
            }`}>
              {killSwitch?.is_active ? "ENGAGED" : "ARMED & READY"}
            </span>
          </div>

          <div className="mt-4 flex flex-col gap-4 text-xs">
            <p className="text-text-secondary leading-relaxed">
              The emergency kill switch terminates in-flight execution within <strong className="text-text-primary">&lt; 1.0 millisecond</strong> and initiates verified baseline rollback.
            </p>

            <div className="p-3 rounded-xl border border-red-500/20 bg-red-500/10">
              <span className="text-[10px] font-mono uppercase text-red-400 font-bold">
                Emergency Procedure
              </span>
              <p className="text-[11px] text-text-secondary mt-1">
                Triggering the kill switch signals all active runner threads to immediately abort and execute the teardown engine.
              </p>
            </div>

            <div className="mt-auto pt-2">
              <button
                onClick={() => setShowKillModal(true)}
                className="w-full flex items-center justify-center gap-2 rounded-xl bg-red-500 px-4 py-2.5 text-xs font-bold text-white hover:bg-red-600 transition-all shadow-red-glow"
              >
                <StopCircle className="h-4 w-4 fill-current" />
                <span>ENGAGE EMERGENCY KILL SWITCH</span>
              </button>
            </div>
          </div>
        </div>

        {/* Panel 3: Account Allowlist & Cryptographic Auth */}
        <div className="flex flex-col rounded-2xl border border-surface-border bg-surface p-5 shadow-panel">
          <div className="flex items-center justify-between pb-3 border-b border-surface-border">
            <div className="flex items-center gap-2">
              <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-brand-primary/10 text-brand-primary border border-brand-primary/30">
                <Lock className="h-4 w-4" />
              </div>
              <h3 className="text-xs font-bold uppercase tracking-wider text-text-primary">
                Environment Boundaries & Allowlist
              </h3>
            </div>
            <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-brand-primary/20 text-brand-primary border border-brand-primary/40 font-bold">
              NFR-S1 / NFR-S2
            </span>
          </div>

          <div className="mt-4 flex flex-col gap-3 text-xs">
            <div>
              <span className="text-[11px] font-semibold text-text-muted uppercase">Compiled Account Allowlist</span>
              <div className="mt-1 flex flex-wrap gap-2 font-mono text-[11px]">
                {policyStatus?.allowlisted_accounts.map((acc, idx) => (
                  <span key={idx} className="px-2 py-1 rounded bg-surface-dark border border-surface-border text-cyan-400 font-bold">
                    {acc}
                  </span>
                ))}
              </div>
              <p className="text-[10px] text-text-muted mt-1">
                Refuses execution against any non-allowlisted AWS account ID.
              </p>
            </div>

            <div className="mt-2 pt-3 border-t border-surface-border">
              <span className="text-[11px] font-semibold text-text-muted uppercase">Two-Key Authorization Protocol</span>
              <p className="text-[11px] text-text-secondary mt-1">
                To exit dry-run mode, a signed HMAC-SHA256 JWT authorization token signed by two distinct authorized leads is required. Unsigned requests default strictly to dry-run.
              </p>
            </div>
          </div>
        </div>

        {/* Panel 4: Cryptographic Audit Verification */}
        <div className="flex flex-col rounded-2xl border border-surface-border bg-surface p-5 shadow-panel">
          <div className="flex items-center justify-between pb-3 border-b border-surface-border">
            <div className="flex items-center gap-2">
              <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-sky-500/10 text-sky-400 border border-sky-500/30">
                <FileCheck2 className="h-4 w-4" />
              </div>
              <h3 className="text-xs font-bold uppercase tracking-wider text-text-primary">
                Audit Hash Chain Verification
              </h3>
            </div>
            <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-emerald-500/20 text-emerald-400 border border-emerald-500/40 font-bold">
              NFR-A2
            </span>
          </div>

          <div className="mt-4 flex flex-col gap-3 text-xs">
            <div className="flex items-center gap-2">
              <span className="text-text-muted font-mono">Verify Run:</span>
              <select
                value={selectedRunId}
                onChange={(e) => setSelectedRunId(e.target.value)}
                className="rounded border border-surface-border bg-surface-dark px-2.5 py-1 text-xs font-mono text-brand-primary focus:outline-none"
              >
                {executions.map((x) => (
                  <option key={x.run_id} value={x.run_id}>
                    {x.run_id}
                  </option>
                ))}
              </select>

              <button
                onClick={handleVerifyAudit}
                className="ml-auto rounded-lg bg-brand-primary/10 border border-brand-primary/30 px-3 py-1.5 text-xs font-semibold text-brand-primary hover:bg-brand-primary/20 transition-all font-mono shadow-cyan-glow"
              >
                Verify Hash Chain
              </button>
            </div>

            {auditResult && (
              <div className="mt-2 flex flex-col gap-2 p-3 rounded-xl border border-surface-border bg-surface-dark font-mono text-[11px]">
                <div className="flex items-center justify-between">
                  <span className="text-text-muted">Chain Status:</span>
                  <span className={auditResult.is_valid ? "text-emerald-400 font-bold" : "text-red-400 font-bold"}>
                    {auditResult.is_valid ? "CRYPTOGRAPHICALLY VALID" : "INVALID"}
                  </span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-text-muted">Records Verified:</span>
                  <span className="text-text-primary">{auditResult.total_records}</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-text-muted">Genesis Hash:</span>
                  <span className="text-text-secondary truncate max-w-xs">{auditResult.genesis_hash}</span>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Confirmation Modal for Kill Switch */}
      {showKillModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm p-4">
          <div className="flex flex-col gap-4 rounded-2xl border border-red-500/50 bg-surface p-6 shadow-2xl max-w-md w-full">
            <div className="flex items-center gap-3 text-red-400">
              <AlertTriangle className="h-6 w-6 shrink-0" />
              <h3 className="text-base font-bold text-text-primary">Confirm Emergency Kill Switch</h3>
            </div>

            <p className="text-xs text-text-secondary leading-relaxed">
              Are you sure you want to trigger the Central Emergency Kill Switch? This will halt any active adversary emulation immediately and initiate baseline teardown.
            </p>

            <div>
              <label className="text-[11px] font-semibold text-text-muted uppercase">Operational Rationale:</label>
              <input
                type="text"
                value={killReason}
                onChange={(e) => setKillReason(e.target.value)}
                className="mt-1 w-full rounded-lg border border-surface-border bg-surface-dark px-3 py-2 text-xs text-text-primary focus:border-red-400 focus:outline-none"
              />
            </div>

            <div className="flex items-center justify-end gap-2 pt-2">
              <button
                onClick={() => setShowKillModal(false)}
                className="rounded-lg border border-surface-border px-3 py-1.5 text-xs text-text-secondary hover:text-text-primary"
              >
                Cancel
              </button>
              <button
                onClick={handleTriggerKillSwitch}
                disabled={triggeringKill}
                className="rounded-lg bg-red-500 px-4 py-1.5 text-xs font-bold text-white hover:bg-red-600 transition-all shadow-red-glow"
              >
                {triggeringKill ? "Engaging..." : "Confirm & Engage"}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

