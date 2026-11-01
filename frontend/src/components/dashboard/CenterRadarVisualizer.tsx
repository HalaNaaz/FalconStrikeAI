"use client";

import React from "react";
import { ShieldAlert, ShieldCheck, Zap } from "lucide-react";

interface CenterRadarVisualizerProps {
  totalIssues?: number;
  openCases?: number;
  threatCasesCount?: number;
  postureCasesCount?: number;
  criticalThreats?: number;
  highThreats?: number;
  mediumThreats?: number;
  lowThreats?: number;
  remediationsAvailable?: number;
  automationsAvailable?: number;
}

export function CenterRadarVisualizer({
  totalIssues = 0,
  openCases = 0,
  threatCasesCount = 0,
  postureCasesCount = 0,
  criticalThreats = 0,
  highThreats = 0,
  mediumThreats = 0,
  lowThreats = 0,
  remediationsAvailable = 0,
  automationsAvailable = 0,
}: CenterRadarVisualizerProps) {
  return (
    <div className="relative flex flex-col xl:flex-row items-center justify-between rounded-2xl border border-surface-border bg-gradient-to-r from-surface/90 via-surface-elevated/70 to-surface/90 p-6 shadow-panel overflow-hidden">
      {/* Background ambient radial glow */}
      <div className="absolute left-1/3 top-1/2 -translate-y-1/2 -translate-x-1/2 w-96 h-96 bg-brand-primary/5 rounded-full blur-3xl pointer-events-none" />

      {/* Left: Open Issues Metrics */}
      <div className="flex items-center gap-6 z-10 py-4 xl:py-0">
        <div className="flex flex-col">
          <span className="text-3xl font-extrabold tracking-tight text-text-primary font-mono">
            {totalIssues.toLocaleString()}
          </span>
          <span className="text-[11px] font-semibold tracking-wider text-brand-secondary uppercase">
            Active Findings
          </span>
        </div>

        {/* Center: Radial Radar Graphic */}
        <div className="relative flex h-36 w-36 items-center justify-center">
          {/* Outer ring */}
          <div className="absolute inset-0 rounded-full border border-surface-border animate-pulse-glow" />
          {/* Middle dotted ring */}
          <div className="absolute inset-3 rounded-full border border-dashed border-brand-primary/30" />
          {/* Inner ring */}
          <div className="absolute inset-7 rounded-full border border-brand-primary/50 shadow-cyan-glow" />
          {/* Radar sweep simulation line */}
          <div className="absolute inset-0 rounded-full animate-radar-sweep bg-gradient-to-tr from-transparent via-transparent to-brand-primary/20 pointer-events-none" />

          {/* Dotted Constellation particles */}
          <div className="absolute h-2 w-2 rounded-full bg-brand-primary top-4 left-8 animate-ping opacity-75" />
          <div className="absolute h-1.5 w-1.5 rounded-full bg-status-critical top-10 right-6 shadow-red-glow" />
          <div className="absolute h-2 w-2 rounded-full bg-status-warning bottom-6 left-10" />
          <div className="absolute h-1.5 w-1.5 rounded-full bg-brand-secondary bottom-8 right-10" />

          {/* Center core */}
          <div className="flex h-12 w-12 items-center justify-center rounded-full bg-surface-dark border border-brand-primary text-brand-primary shadow-cyan-glow">
            <ShieldAlert className="h-5 w-5" />
          </div>
        </div>

        {/* Middle count */}
        <div className="flex flex-col">
          <span className="text-3xl font-extrabold tracking-tight text-text-primary font-mono">
            {openCases}
          </span>
          <span className="text-[11px] font-semibold tracking-wider text-text-muted uppercase">
            Attack Paths
          </span>
        </div>
      </div>

      {/* Right: Active Threat Cases & Posture Cases */}
      <div className="flex flex-col gap-4 w-full xl:w-auto z-10 mt-4 xl:mt-0">
        {/* Threat Cases Card */}
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 rounded-xl border border-red-500/20 bg-gradient-to-r from-red-500/10 via-surface to-surface p-4">
          <div className="flex flex-col">
            <div className="flex items-center gap-2">
              <span className="h-2 w-2 rounded-full bg-red-500 animate-pulse" />
              <span className="text-[11px] font-bold uppercase tracking-wider text-red-400">
                Critical Threats
              </span>
            </div>
            <div className="flex items-baseline gap-3 mt-1 font-mono">
              <span className="text-2xl font-bold text-text-primary">{threatCasesCount}</span>
              <span className="text-xs text-red-400">▲ {criticalThreats} Crit</span>
              <span className="text-xs text-amber-400">▲ {highThreats} High</span>
            </div>
          </div>

          {/* Mini Sparkline Simulation */}
          <div className="hidden md:flex h-8 w-28 items-end gap-1 px-2 border-l border-surface-border">
            <div className="w-2 bg-red-400/40 rounded-t h-3" />
            <div className="w-2 bg-red-400/60 rounded-t h-5" />
            <div className="w-2 bg-red-400/30 rounded-t h-2" />
            <div className="w-2 bg-red-400/80 rounded-t h-7" />
            <div className="w-2 bg-red-400 rounded-t h-8" />
            <div className="w-2 bg-red-400/50 rounded-t h-4" />
          </div>

          {/* Action Pills */}
          <div className="flex flex-col gap-1.5 shrink-0">
            <span className="flex items-center gap-1.5 rounded-md bg-emerald-500/10 border border-emerald-500/30 px-2 py-0.5 text-[11px] font-medium text-emerald-400 font-mono">
              <ShieldCheck className="h-3 w-3" /> {remediationsAvailable} Actions Ready
            </span>
            <span className="flex items-center gap-1.5 rounded-md bg-brand-primary/10 border border-brand-primary/30 px-2 py-0.5 text-[11px] font-medium text-brand-primary font-mono">
              <Zap className="h-3 w-3" /> {automationsAvailable} Plans Formulated
            </span>
          </div>
        </div>

        {/* Posture Cases Card */}
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 rounded-xl border border-amber-500/20 bg-gradient-to-r from-amber-500/10 via-surface to-surface p-4">
          <div className="flex flex-col">
            <div className="flex items-center gap-2">
              <span className="h-2 w-2 rounded-full bg-amber-400" />
              <span className="text-[11px] font-bold uppercase tracking-wider text-amber-400">
                Posture Misconfigurations
              </span>
            </div>
            <div className="flex items-baseline gap-3 mt-1 font-mono">
              <span className="text-2xl font-bold text-text-primary">{postureCasesCount}</span>
              <span className="text-xs text-sky-400">▲ {mediumThreats} Med</span>
              <span className="text-xs text-slate-400">▲ {lowThreats} Low</span>
            </div>
          </div>

          {/* Action Pills */}
          <div className="flex flex-col gap-1.5 shrink-0">
            <span className="flex items-center gap-1.5 rounded-md bg-emerald-500/10 border border-emerald-500/30 px-2 py-0.5 text-[11px] font-medium text-emerald-400 font-mono">
              <ShieldCheck className="h-3 w-3" /> Policy Verification Active
            </span>
            <span className="flex items-center gap-1.5 rounded-md bg-brand-primary/10 border border-brand-primary/30 px-2 py-0.5 text-[11px] font-medium text-brand-primary font-mono">
              <Zap className="h-3 w-3" /> Teardown Verified
            </span>
          </div>
        </div>
      </div>
    </div>
  );
}
