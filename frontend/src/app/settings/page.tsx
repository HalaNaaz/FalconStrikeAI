"use client";

import React, { useEffect, useState } from "react";
import {
  Settings,
  Server,
  ShieldCheck,
  RotateCw,
  CheckCircle2,
  AlertTriangle,
  Lock,
  Globe,
  Database,
  Cpu,
  Box,
  Cloud,
  Sparkles,
  Terminal,
} from "lucide-react";
import { api } from "@/lib/api/client";
import { HealthResponse, IntegrationsStatusResponse } from "@/types/api";

export default function SettingsPage() {
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [integrations, setIntegrations] = useState<IntegrationsStatusResponse | null>(null);
  const [testing, setTesting] = useState(false);
  const [pingResult, setPingResult] = useState<string | null>(null);
  const [apiUrl, setApiUrl] = useState(
    process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000"
  );

  const testConnection = async () => {
    try {
      setTesting(true);
      setPingResult(null);
      const [hRes, intRes] = await Promise.allSettled([
        api.getHealth(),
        api.getIntegrationsStatus(),
      ]);

      if (hRes.status === "fulfilled") {
        setHealth(hRes.value);
        setPingResult(`Connected! Backend version ${hRes.value.version} is ${hRes.value.status}.`);
      } else {
        setPingResult(`Health check failed: ${hRes.reason.message}`);
      }

      if (intRes.status === "fulfilled") {
        setIntegrations(intRes.value);
      }
    } catch (err: any) {
      setPingResult(`Connection failed: ${err.message}`);
    } finally {
      setTesting(false);
    }
  };

  useEffect(() => {
    testConnection();
  }, []);

  const getStatusBadge = (status: string) => {
    switch (status) {
      case "VERIFIED":
        return "bg-emerald-500/10 text-emerald-400 border-emerald-500/30";
      case "CONNECTED":
      case "CONFIGURED":
        return "bg-sky-500/10 text-sky-400 border-sky-500/30";
      case "BLOCKED":
        return "bg-red-500/10 text-red-400 border-red-500/30";
      case "NOT_VERIFIED":
        return "bg-amber-500/10 text-amber-400 border-amber-500/30";
      case "NOT_CONFIGURED":
      default:
        return "bg-slate-500/10 text-slate-400 border-slate-500/30";
    }
  };

  return (
    <div className="flex flex-col gap-6 max-w-4xl">
      {/* Header */}
      <div>
        <h2 className="text-xl font-bold text-text-primary">Platform Settings</h2>
        <p className="text-xs text-text-muted">
          Manage backend connection, inspect runtime configuration, and verify security invariants
        </p>
      </div>

      {pingResult && (
        <div className={`flex items-center gap-2 p-3 rounded-xl border text-xs ${
          health
            ? "border-emerald-500/30 bg-emerald-500/10 text-emerald-400"
            : "border-red-500/30 bg-red-500/10 text-red-400"
        }`}>
          {health ? <CheckCircle2 className="h-4 w-4 shrink-0" /> : <AlertTriangle className="h-4 w-4 shrink-0" />}
          <span className="font-mono">{pingResult}</span>
        </div>
      )}

      {/* Section 1: Backend Connection */}
      <div className="rounded-2xl border border-surface-border bg-surface p-5 shadow-panel">
        <h3 className="text-xs font-bold uppercase tracking-wider text-text-muted pb-3 border-b border-surface-border flex items-center gap-2">
          <Server className="h-4 w-4 text-brand-primary" />
          Backend API Connection
        </h3>

        <div className="mt-4 flex flex-col gap-3 text-xs">
          <div>
            <label className="text-[11px] font-semibold text-text-muted uppercase">Base API URL</label>
            <div className="mt-1 flex items-center gap-2">
              <input
                type="text"
                value={apiUrl}
                onChange={(e) => setApiUrl(e.target.value)}
                readOnly
                className="flex-1 rounded-lg border border-surface-border bg-surface-dark px-3 py-2 text-xs font-mono text-text-primary focus:outline-none"
              />
              <button
                onClick={testConnection}
                disabled={testing}
                className="flex items-center gap-1.5 rounded-lg bg-brand-primary px-3.5 py-2 text-xs font-semibold text-sidebar hover:bg-brand-secondary transition-all disabled:opacity-50"
              >
                <RotateCw className={`h-3.5 w-3.5 ${testing ? "animate-spin" : ""}`} />
                <span>Test Connection</span>
              </button>
            </div>
            <p className="text-[10px] text-text-muted mt-1">
              Configured via <code className="font-mono text-brand-secondary">NEXT_PUBLIC_API_BASE_URL</code>.
            </p>
          </div>
        </div>
      </div>

      {/* Section 2: External Infrastructure & Integration Readiness */}
      {integrations && (
        <div className="rounded-2xl border border-surface-border bg-surface p-5 shadow-panel">
          <h3 className="text-xs font-bold uppercase tracking-wider text-text-muted pb-3 border-b border-surface-border flex items-center gap-2">
            <Box className="h-4 w-4 text-brand-primary" />
            External Infrastructure & Integration Readiness
          </h3>

          <div className="mt-4 grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* Docker Sandbox */}
            <div className="flex flex-col justify-between p-4 rounded-xl border border-surface-border bg-surface-dark gap-3">
              <div>
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <Box className="h-4 w-4 text-brand-primary" />
                    <span className="text-xs font-bold text-text-primary">Docker Sandbox Runner</span>
                  </div>
                  <span className={`text-[10px] font-mono px-2 py-0.5 rounded border ${getStatusBadge(integrations.docker_sandbox.status)}`}>
                    {integrations.docker_sandbox.status}
                  </span>
                </div>
                <p className="text-[11px] text-text-muted mt-2 leading-relaxed">
                  {integrations.docker_sandbox.details}
                </p>
              </div>
              {integrations.docker_sandbox.action_required && (
                <div className="rounded-lg bg-surface p-2 border border-surface-border text-[10px] text-amber-300 flex items-start gap-1.5 font-mono">
                  <Terminal className="h-3 w-3 shrink-0 mt-0.5 text-amber-400" />
                  <span>{integrations.docker_sandbox.action_required}</span>
                </div>
              )}
            </div>

            {/* AWS Cloud Discovery */}
            <div className="flex flex-col justify-between p-4 rounded-xl border border-surface-border bg-surface-dark gap-3">
              <div>
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <Cloud className="h-4 w-4 text-brand-secondary" />
                    <span className="text-xs font-bold text-text-primary">AWS Cloud Discovery</span>
                  </div>
                  <span className={`text-[10px] font-mono px-2 py-0.5 rounded border ${getStatusBadge(integrations.aws_cloud.status)}`}>
                    {integrations.aws_cloud.status}
                  </span>
                </div>
                <p className="text-[11px] text-text-muted mt-2 leading-relaxed">
                  {integrations.aws_cloud.details}
                </p>
              </div>
              {integrations.aws_cloud.action_required && (
                <div className="rounded-lg bg-surface p-2 border border-surface-border text-[10px] text-amber-300 flex items-start gap-1.5 font-mono">
                  <Terminal className="h-3 w-3 shrink-0 mt-0.5 text-amber-400" />
                  <span>Action: <code>{integrations.aws_cloud.action_required}</code></span>
                </div>
              )}
            </div>

            {/* Gemini LLM Planner */}
            <div className="flex flex-col justify-between p-4 rounded-xl border border-surface-border bg-surface-dark gap-3">
              <div>
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <Sparkles className="h-4 w-4 text-purple-400" />
                    <span className="text-xs font-bold text-text-primary">Gemini 2.5 Flash Planner</span>
                  </div>
                  <span className={`text-[10px] font-mono px-2 py-0.5 rounded border ${getStatusBadge(integrations.gemini_planner.status)}`}>
                    {integrations.gemini_planner.status}
                  </span>
                </div>
                <p className="text-[11px] text-text-muted mt-2 leading-relaxed">
                  {integrations.gemini_planner.details}
                </p>
              </div>
              {integrations.gemini_planner.action_required && (
                <div className="rounded-lg bg-surface p-2 border border-surface-border text-[10px] text-text-muted flex items-start gap-1.5 font-mono">
                  <Terminal className="h-3 w-3 shrink-0 mt-0.5 text-brand-primary" />
                  <span>{integrations.gemini_planner.action_required}</span>
                </div>
              )}
            </div>

            {/* Kubernetes Jobs Adapter */}
            <div className="flex flex-col justify-between p-4 rounded-xl border border-surface-border bg-surface-dark gap-3">
              <div>
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <Cpu className="h-4 w-4 text-text-muted" />
                    <span className="text-xs font-bold text-text-primary">Kubernetes Jobs Adapter</span>
                  </div>
                  <span className={`text-[10px] font-mono px-2 py-0.5 rounded border ${getStatusBadge(integrations.kubernetes_runner.status)}`}>
                    {integrations.kubernetes_runner.status}
                  </span>
                </div>
                <p className="text-[11px] text-text-muted mt-2 leading-relaxed">
                  {integrations.kubernetes_runner.details}
                </p>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Section 3: Runtime Environment & Subsystems */}
      {health && (
        <div className="rounded-2xl border border-surface-border bg-surface p-5 shadow-panel">
          <h3 className="text-xs font-bold uppercase tracking-wider text-text-muted pb-3 border-b border-surface-border flex items-center gap-2">
            <Cpu className="h-4 w-4 text-brand-secondary" />
            Active Subsystem Architecture
          </h3>

          <div className="mt-4 grid grid-cols-1 sm:grid-cols-2 gap-4 text-xs font-mono">
            <div className="flex items-center justify-between p-3 rounded-xl border border-surface-border bg-surface-dark">
              <span className="text-text-muted">Deployment Environment:</span>
              <span className="text-text-primary font-bold">{health.environment}</span>
            </div>

            <div className="flex items-center justify-between p-3 rounded-xl border border-surface-border bg-surface-dark">
              <span className="text-text-muted">Dry-Run Default:</span>
              <span className="text-brand-primary font-bold">
                {String(health.dry_run).toUpperCase()} (ENFORCED)
              </span>
            </div>

            <div className="flex items-center justify-between p-3 rounded-xl border border-surface-border bg-surface-dark">
              <span className="text-text-muted">Graph Store Engine:</span>
              <span className="text-emerald-400 font-bold">{health.components.graph_store}</span>
            </div>

            <div className="flex items-center justify-between p-3 rounded-xl border border-surface-border bg-surface-dark">
              <span className="text-text-muted">Safety Policy Gate:</span>
              <span className="text-emerald-400 font-bold">{health.components.policy_gate}</span>
            </div>

            <div className="flex items-center justify-between p-3 rounded-xl border border-surface-border bg-surface-dark">
              <span className="text-text-muted">Audit Logger:</span>
              <span className="text-emerald-400 font-bold">{health.components.audit_logger}</span>
            </div>

            <div className="flex items-center justify-between p-3 rounded-xl border border-surface-border bg-surface-dark">
              <span className="text-text-muted">Benign C2 Sink:</span>
              <span className="text-emerald-400 font-bold">{health.components.c2_sink}</span>
            </div>
          </div>
        </div>
      )}

      {/* Section 3: Product Metadata */}
      <div className="rounded-2xl border border-surface-border bg-surface p-5 shadow-panel">
        <h3 className="text-xs font-bold uppercase tracking-wider text-text-muted pb-3 border-b border-surface-border flex items-center gap-2">
          <Globe className="h-4 w-4 text-text-muted" />
          Product Specification
        </h3>

        <div className="mt-3 flex flex-col gap-2 text-xs font-mono text-text-secondary">
          <div className="flex justify-between py-1 border-b border-surface-border/50">
            <span>Product Identity:</span>
            <span className="text-text-primary font-bold">Falcon Strike-AI (Adversary Emulation & CTEM)</span>
          </div>
          <div className="flex justify-between py-1 border-b border-surface-border/50">
            <span>Frontend Architecture:</span>
            <span className="text-brand-primary font-bold">Next.js 14 (App Router) + TypeScript + Tailwind</span>
          </div>
          <div className="flex justify-between py-1 border-b border-surface-border/50">
            <span>Graph Visualizer:</span>
            <span className="text-emerald-400 font-bold">React Flow (@xyflow/react)</span>
          </div>
          <div className="flex justify-between py-1">
            <span>Submission Deadline:</span>
            <span className="text-amber-400 font-bold">6 November 2026</span>
          </div>
        </div>
      </div>
    </div>
  );
}

