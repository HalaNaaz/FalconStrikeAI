"use client";

import React from "react";
import { AlertCircle, ShieldAlert, ArrowRight, CheckCircle2, ChevronRight } from "lucide-react";
import Link from "next/link";
import { MisconfigurationFinding, AttackPath } from "@/types/api";
import { getSeverityBadgeClass } from "@/lib/utils/formatters";

interface ThreatCardsProps {
  findings?: MisconfigurationFinding[];
  attackPaths?: AttackPath[];
}

export function ThreatCards({ findings = [], attackPaths = [] }: ThreatCardsProps) {
  const topPaths = attackPaths.slice(0, 3);
  const topFindings = findings.slice(0, 4);

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
      {/* Top Active Threats Card */}
      <div className="flex flex-col rounded-2xl border border-surface-border bg-surface/90 p-5 shadow-panel">
        <div className="flex items-center justify-between pb-3 border-b border-surface-border">
          <div className="flex items-center gap-2">
            <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-red-500/10 text-red-400 border border-red-500/30">
              <ShieldAlert className="h-4 w-4" />
            </div>
            <div className="flex flex-col">
              <h3 className="text-xs font-bold uppercase tracking-wider text-text-primary">
                Top Active Threats to Address
              </h3>
              <p className="text-[11px] text-text-muted">
                Remediate the most pressing attack paths to reduce exposure
              </p>
            </div>
          </div>
          <Link
            href="/attack-graph"
            className="text-[11px] font-semibold text-brand-primary hover:underline flex items-center gap-1"
          >
            View Graph <ChevronRight className="h-3.5 w-3.5" />
          </Link>
        </div>

        <div className="mt-3 flex flex-col gap-2.5">
          {topPaths.length > 0 ? (
            topPaths.map((path, idx) => (
              <div
                key={path.path_id || idx}
                className="flex items-center justify-between rounded-xl border border-surface-border bg-surface-elevated/70 p-3 hover:border-brand-primary/40 transition-all"
              >
                <div className="flex flex-col gap-1 overflow-hidden pr-3">
                  <div className="flex items-center gap-2">
                    <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-red-500/20 text-red-400 font-semibold border border-red-500/40">
                      RISK {path.risk_score !== undefined ? path.risk_score.toFixed(1) : "—"}
                    </span>
                    <span className="text-xs font-semibold text-text-primary font-mono truncate">
                      {path.path_id}
                    </span>
                    <span className="text-[10px] font-mono text-text-muted">
                      ({path.hop_count !== undefined ? path.hop_count : (path.node_sequence ? path.node_sequence.length - 1 : 0)} hops)
                    </span>
                  </div>
                  <p className="text-[11px] text-text-secondary truncate font-mono">
                    {path.entry_node_id} → {path.target_node_id}
                  </p>
                </div>

                <Link
                  href={`/campaign-planner?path_id=${encodeURIComponent(path.path_id)}`}
                  className="shrink-0 flex items-center gap-1 text-[11px] font-medium text-brand-primary hover:text-brand-secondary bg-brand-primary/10 border border-brand-primary/30 px-2.5 py-1.5 rounded-lg"
                >
                  Plan Emulation <ArrowRight className="h-3 w-3" />
                </Link>
              </div>
            ))
          ) : (
            <div className="flex flex-col items-center justify-center p-6 text-center text-text-muted">
              <CheckCircle2 className="h-8 w-8 text-emerald-400/60 mb-2" />
              <p className="text-xs">No active attack paths identified in current baseline.</p>
            </div>
          )}
        </div>
      </div>

      {/* Top Posture Cases Card */}
      <div className="flex flex-col rounded-2xl border border-surface-border bg-surface/90 p-5 shadow-panel">
        <div className="flex items-center justify-between pb-3 border-b border-surface-border">
          <div className="flex items-center gap-2">
            <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-amber-500/10 text-amber-400 border border-amber-500/30">
              <AlertCircle className="h-4 w-4" />
            </div>
            <div className="flex flex-col">
              <h3 className="text-xs font-bold uppercase tracking-wider text-text-primary">
                Top Posture Cases to Address
              </h3>
              <p className="text-[11px] text-text-muted">
                Remediate misconfigurations to harden cloud identity perimeter
              </p>
            </div>
          </div>
          <Link
            href="/environment"
            className="text-[11px] font-semibold text-brand-primary hover:underline flex items-center gap-1"
          >
            All Findings <ChevronRight className="h-3.5 w-3.5" />
          </Link>
        </div>

        <div className="mt-3 flex flex-col gap-2.5">
          {topFindings.length > 0 ? (
            topFindings.map((finding) => (
              <div
                key={finding.finding_id}
                className="flex items-center justify-between rounded-xl border border-surface-border bg-surface-elevated/70 p-3 hover:border-amber-500/40 transition-all"
              >
                <div className="flex flex-col gap-1 overflow-hidden pr-3">
                  <div className="flex items-center gap-2">
                    <span className={`text-[10px] font-mono px-1.5 py-0.5 rounded font-semibold ${getSeverityBadgeClass(finding.severity)}`}>
                      {finding.severity}
                    </span>
                    <span className="text-xs font-semibold text-text-primary truncate">
                      {finding.rule_name}
                    </span>
                  </div>
                  <p className="text-[11px] text-text-secondary truncate">
                    {finding.description}
                  </p>
                </div>

                <div className="shrink-0 flex items-center gap-1 text-[11px] font-medium text-emerald-400 bg-emerald-500/10 border border-emerald-500/30 px-2.5 py-1.5 rounded-lg">
                  Remediation Ready
                </div>
              </div>
            ))
          ) : (
            <div className="flex flex-col items-center justify-center p-6 text-center text-text-muted">
              <CheckCircle2 className="h-8 w-8 text-emerald-400/60 mb-2" />
              <p className="text-xs">No posture misconfigurations detected in active graph.</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

