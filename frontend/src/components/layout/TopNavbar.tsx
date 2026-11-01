"use client";

import React, { useEffect, useState } from "react";
import { usePathname } from "next/navigation";
import {
  ShieldAlert,
  Play,
  RotateCw,
  Server,
  AlertTriangle,
  CheckCircle2,
  Lock,
  Cloud,
} from "lucide-react";
import { api } from "@/lib/api/client";
import { HealthResponse } from "@/types/api";

const ROUTE_TITLES: Record<string, string> = {
  "/dashboard": "Security Command Center",
  "/environment": "AWS Environment Explorer",
  "/attack-graph": "Interactive Attack Graph Visualizer",
  "/campaign-planner": "Agentic AI Campaign Planner",
  "/execution": "Adversary Execution Center",
  "/telemetry": "Telemetry & Detection Center",
  "/reports": "SOC Assessment & Executive Reports",
  "/security": "Security Posture & Safety Controls",
  "/audit-logs": "Tamper-Evident Audit Ledger",
  "/settings": "Platform Settings",
};

export function TopNavbar() {
  const pathname = usePathname();
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [loadingHealth, setLoadingHealth] = useState(true);
  const [runningWorkflow, setRunningWorkflow] = useState(false);
  const [workflowSuccessMsg, setWorkflowSuccessMsg] = useState<string | null>(null);

  const currentTitle = ROUTE_TITLES[pathname] || "Command Center";

  const fetchHealth = async () => {
    try {
      setLoadingHealth(true);
      const data = await api.getHealth();
      setHealth(data);
    } catch {
      setHealth(null);
    } finally {
      setLoadingHealth(false);
    }
  };

  useEffect(() => {
    fetchHealth();
    const interval = setInterval(fetchHealth, 30000);
    return () => clearInterval(interval);
  }, []);

  const handleQuickRun = async () => {
    try {
      setRunningWorkflow(true);
      setWorkflowSuccessMsg(null);
      const res = await api.runWorkflow("synthetic", true);
      setWorkflowSuccessMsg(`Pipeline ${res.run_id} completed successfully!`);
      setTimeout(() => setWorkflowSuccessMsg(null), 6000);
    } catch (err: any) {
      alert(`Workflow execution failed: ${err.message}`);
    } finally {
      setRunningWorkflow(false);
    }
  };

  const isSyntheticAccount =
    health?.target_account_id === "000000000000" || health?.environment === "development";

  return (
    <header className="flex h-16 w-full items-center justify-between border-b border-surface-border bg-sidebar/95 px-6 backdrop-blur z-20">
      {/* Left: Title & Breadcrumbs */}
      <div className="flex items-center gap-3">
        <h1 className="text-base font-semibold text-text-primary flex items-center gap-2">
          {currentTitle}
        </h1>
        <span className="text-surface-border">/</span>
        <span className="text-xs font-mono text-text-muted">FALCON-AI-OPS</span>
      </div>

      {/* Right: Status Badges & CTAs */}
      <div className="flex items-center gap-3">
        {/* Workflow completion banner if active */}
        {workflowSuccessMsg && (
          <span className="text-xs text-emerald-400 bg-emerald-500/10 border border-emerald-500/30 px-2.5 py-1 rounded-md animate-fade-in flex items-center gap-1.5 font-mono">
            <CheckCircle2 className="h-3.5 w-3.5" />
            {workflowSuccessMsg}
          </span>
        )}

        {/* Backend Connectivity Status */}
        <div className="flex items-center gap-1.5 rounded-md border border-surface-border bg-surface px-2.5 py-1 text-xs">
          <Server className="h-3.5 w-3.5 text-text-muted" />
          <span className="text-text-muted">Backend:</span>
          {loadingHealth ? (
            <span className="flex items-center gap-1 text-[11px] font-mono text-amber-400">
              <RotateCw className="h-3 w-3 animate-spin" /> Checking Connection
            </span>
          ) : health ? (
            <span className="flex items-center gap-1 text-[11px] font-mono font-medium text-emerald-400">
              <span className="h-2 w-2 rounded-full bg-emerald-400 shadow-sm animate-pulse" />
              Connected
            </span>
          ) : (
            <span className="flex items-center gap-1 text-[11px] font-mono font-medium text-red-400">
              <span className="h-2 w-2 rounded-full bg-red-400" />
              Disconnected
            </span>
          )}
        </div>

        {/* Environment State Badge */}
        {loadingHealth ? (
          <div className="hidden sm:flex items-center gap-1.5 rounded-md border border-surface-border bg-surface px-2.5 py-1 text-xs font-mono text-text-muted">
            <Cloud className="h-3 w-3" />
            <span>Checking Env...</span>
          </div>
        ) : health ? (
          isSyntheticAccount ? (
            <div
              className="hidden sm:flex items-center gap-1.5 rounded-md border border-amber-500/30 bg-amber-500/10 px-2.5 py-1 text-xs font-mono text-amber-400"
              title="Synthetic AWS environment fixture for safe offline CTEM"
            >
              <AlertTriangle className="h-3 w-3" />
              <span>Synthetic Environment (000000000000)</span>
            </div>
          ) : (
            <div className="hidden sm:flex items-center gap-1.5 rounded-md border border-brand-primary/30 bg-brand-primary/10 px-2.5 py-1 text-xs font-mono text-brand-primary">
              <Lock className="h-3 w-3" />
              <span>AWS Connected ({health.target_account_id})</span>
            </div>
          )
        ) : (
          <div className="hidden sm:flex items-center gap-1.5 rounded-md border border-red-500/30 bg-red-500/10 px-2.5 py-1 text-xs font-mono text-red-400">
            <AlertTriangle className="h-3 w-3" />
            <span>AWS Connection Error</span>
          </div>
        )}

        {/* Safety Invariant: Dry-Run Mandatory Badge */}
        <div
          className="flex items-center gap-1.5 rounded-md border border-brand-primary/40 bg-brand-primary/10 px-2.5 py-1 text-xs font-mono text-brand-primary font-semibold shadow-cyan-glow"
          title="Default safety boundary: all mutations run in simulation only"
        >
          <ShieldAlert className="h-3.5 w-3.5" />
          <span>DRY-RUN ENFORCED</span>
        </div>

        {/* Quick Trigger Button */}
        <button
          onClick={handleQuickRun}
          disabled={runningWorkflow}
          className="flex items-center gap-1.5 rounded-lg bg-brand-primary px-3 py-1.5 text-xs font-semibold text-sidebar hover:bg-brand-secondary transition-all disabled:opacity-50 disabled:cursor-not-allowed shadow-cyan-glow"
          title="Run 17-Stage End-to-End Adversary Emulation Workflow"
        >
          {runningWorkflow ? (
            <>
              <RotateCw className="h-3.5 w-3.5 animate-spin" />
              <span>Executing...</span>
            </>
          ) : (
            <>
              <Play className="h-3.5 w-3.5 fill-current" />
              <span>Run CTEM Pipeline</span>
            </>
          )}
        </button>
      </div>
    </header>
  );
}
