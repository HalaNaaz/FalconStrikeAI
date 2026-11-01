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
} from "lucide-react";
import { api } from "@/lib/api/client";
import { HealthResponse } from "@/types/api";

export default function SettingsPage() {
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [testing, setTesting] = useState(false);
  const [pingResult, setPingResult] = useState<string | null>(null);
  const [apiUrl, setApiUrl] = useState(
    process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000"
  );

  const testConnection = async () => {
    try {
      setTesting(true);
      setPingResult(null);
      const res = await api.getHealth();
      setHealth(res);
      setPingResult(`Connected! Backend version ${res.version} is ${res.status}.`);
    } catch (err: any) {
      setPingResult(`Connection failed: ${err.message}`);
    } finally {
      setTesting(false);
    }
  };

  useEffect(() => {
    testConnection();
  }, []);

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

      {/* Section 2: Runtime Environment & Subsystems */}
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

