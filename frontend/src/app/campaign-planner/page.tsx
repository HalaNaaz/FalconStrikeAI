"use client";

import React, { useEffect, useState } from "react";
import { useSearchParams } from "next/navigation";
import {
  Cpu,
  Shield,
  Layers,
  ArrowRight,
  CheckCircle2,
  AlertTriangle,
  RotateCw,
  Play,
  Terminal,
  Zap,
  Lock,
  ListOrdered,
  FileCheck,
} from "lucide-react";
import Link from "next/link";
import { api } from "@/lib/api/client";
import { CampaignPlan, AttackPath, CampaignStage } from "@/types/api";

function CampaignPlannerContent() {
  const searchParams = useSearchParams();
  const initialPathId = searchParams.get("path_id");

  const [campaigns, setCampaigns] = useState<CampaignPlan[]>([]);
  const [attackPaths, setAttackPaths] = useState<AttackPath[]>([]);
  const [selectedCampaign, setSelectedCampaign] = useState<CampaignPlan | null>(null);
  const [selectedPathId, setSelectedPathId] = useState<string>(initialPathId || "");
  const [selectedProvider, setSelectedProvider] = useState<string>("deterministic");
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const fetchData = async () => {
    try {
      setLoading(true);
      setErrorMsg(null);
      const [campsRes, pathsRes] = await Promise.allSettled([
        api.getCampaigns(),
        api.getAttackPaths(),
      ]);

      let paths: AttackPath[] = [];
      if (pathsRes.status === "fulfilled") {
        paths = pathsRes.value || [];
        setAttackPaths(paths);
        if (paths.length > 0 && !selectedPathId) {
          setSelectedPathId(paths[0].path_id);
        }
      }

      if (campsRes.status === "fulfilled") {
        const camps = campsRes.value || [];
        setCampaigns(camps);
        if (camps.length > 0) {
          setSelectedCampaign(camps[0]);
        }
      }
    } catch (err: any) {
      setErrorMsg(err.message || "Failed to load campaign plans");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const handleGenerate = async () => {
    try {
      setGenerating(true);
      setErrorMsg(null);
      const newPlan = await api.generateCampaign({
        attack_path_id: selectedPathId || undefined,
        provider: selectedProvider,
      });
      setCampaigns((prev) => [newPlan, ...prev]);
      setSelectedCampaign(newPlan);
    } catch (err: any) {
      setErrorMsg(`Campaign generation failed: ${err.message}`);
    } finally {
      setGenerating(false);
    }
  };

  return (
    <div className="flex flex-col gap-6">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold text-text-primary">Agentic AI Campaign Planner</h2>
          <p className="text-xs text-text-muted">
            Assembles bounded, multi-stage adversary campaigns from approved MITRE ATT&CK techniques
          </p>
        </div>

        {/* Generator Controls */}
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2 rounded-lg border border-surface-border bg-surface px-3 py-1.5 text-xs">
            <span className="text-text-muted font-mono">Provider:</span>
            <select
              value={selectedProvider}
              onChange={(e) => setSelectedProvider(e.target.value)}
              className="bg-transparent font-mono text-brand-primary focus:outline-none"
            >
              <option value="deterministic" className="bg-surface text-text-primary">
                Deterministic Engine (Offline Safe)
              </option>
              <option value="gemini" className="bg-surface text-text-primary">
                Gemini Pro (Google GenAI)
              </option>
              <option value="openai" className="bg-surface text-text-primary">
                GPT-4o (OpenAI API)
              </option>
            </select>
          </div>

          <button
            onClick={handleGenerate}
            disabled={generating}
            className="flex items-center gap-2 rounded-lg bg-brand-primary px-3.5 py-2 text-xs font-semibold text-sidebar hover:bg-brand-secondary transition-all disabled:opacity-50 shadow-cyan-glow"
          >
            <Play className={`h-3.5 w-3.5 fill-current ${generating ? "animate-spin" : ""}`} />
            <span>{generating ? "Planning Campaign..." : "Generate Campaign"}</span>
          </button>
        </div>
      </div>

      {errorMsg && (
        <div className="flex items-center gap-2 rounded-xl border border-red-500/30 bg-red-500/10 p-3 text-xs text-red-400">
          <AlertTriangle className="h-4 w-4 shrink-0" />
          <span>{errorMsg}</span>
        </div>
      )}

      {/* Safety Invariant Notice */}
      <div className="flex items-center gap-3 rounded-xl border border-brand-primary/20 bg-brand-primary/5 p-3.5 text-xs text-text-secondary">
        <Lock className="h-4 w-4 text-brand-primary shrink-0" />
        <div>
          <span className="font-semibold text-brand-primary">AI Containment Axiom:</span> The AI planner emits strictly typed JSON schema models validated against Pydantic definitions. The planner has <strong className="text-text-primary">zero shell access</strong> and selects only approved technique contracts.
        </div>
      </div>

      {/* Campaign Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Campaign History List */}
        <div className="lg:col-span-4 flex flex-col gap-3">
          <h3 className="text-xs font-bold uppercase tracking-wider text-text-muted">
            Formulated Campaigns ({campaigns.length})
          </h3>

          <div className="flex flex-col gap-2 max-h-[600px] overflow-y-auto pr-1">
            {campaigns.length > 0 ? (
              campaigns.map((camp) => {
                const isSelected = selectedCampaign?.campaign_id === camp.campaign_id;
                return (
                  <div
                    key={camp.campaign_id}
                    onClick={() => setSelectedCampaign(camp)}
                    className={`cursor-pointer rounded-xl border p-3.5 transition-all ${
                      isSelected
                        ? "border-brand-primary/50 bg-surface-elevated shadow-cyan-glow"
                        : "border-surface-border bg-surface hover:border-surface-borderHover"
                    }`}
                  >
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-bold font-mono text-brand-primary">
                        {camp.campaign_id}
                      </span>
                      <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-surface-dark border border-surface-border text-text-muted">
                        {camp.stages?.length ?? 0} Stages
                      </span>
                    </div>
                    <p className="text-xs font-semibold text-text-primary mt-1 line-clamp-1">
                      {camp.objective || "Adversary Emulation Campaign"}
                    </p>
                    <div className="flex items-center justify-between mt-2 text-[10px] font-mono text-text-muted">
                      <span>Provider: {camp.planner_provider}</span>
                      <span className="text-emerald-400">Validated ✓</span>
                    </div>
                  </div>
                );
              })
            ) : (
              <div className="p-6 rounded-xl border border-surface-border text-center text-xs text-text-muted">
                No campaigns generated yet. Click Generate Campaign above.
              </div>
            )}
          </div>
        </div>

        {/* Selected Campaign Detailed Timeline */}
        <div className="lg:col-span-8 flex flex-col gap-4">
          {selectedCampaign ? (
            <div className="flex flex-col rounded-2xl border border-surface-border bg-surface p-5 shadow-panel">
              {/* Campaign Header */}
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-4 border-b border-surface-border">
                <div className="flex flex-col">
                  <div className="flex items-center gap-2">
                    <span className="text-base font-bold font-mono text-text-primary">
                      {selectedCampaign.campaign_id}
                    </span>
                    <span className="px-2 py-0.5 rounded bg-brand-primary/10 border border-brand-primary/30 text-[10px] font-mono font-semibold text-brand-primary">
                      {selectedCampaign.planner_provider.toUpperCase()}
                    </span>
                    <span className="px-2 py-0.5 rounded bg-emerald-500/10 border border-emerald-500/30 text-[10px] font-mono font-semibold text-emerald-400">
                      SCHEMA_VALIDATED
                    </span>
                  </div>
                  <p className="text-xs text-text-secondary mt-1">
                    {selectedCampaign.objective}
                  </p>
                </div>

                <Link
                  href={`/execution?campaign_id=${encodeURIComponent(selectedCampaign.campaign_id)}`}
                  className="shrink-0 flex items-center gap-1.5 rounded-lg bg-brand-primary px-3.5 py-2 text-xs font-semibold text-sidebar hover:bg-brand-secondary transition-all shadow-cyan-glow"
                >
                  <Terminal className="h-3.5 w-3.5" />
                  <span>Deploy to Execution Center</span>
                </Link>
              </div>

              {/* Rationale Section */}
              <div className="mt-4 p-3 rounded-xl border border-surface-border bg-surface-elevated/70">
                <span className="text-[10px] font-mono uppercase text-brand-secondary font-bold">
                  Planner Rationale & Target Jewel
                </span>
                <p className="text-xs text-text-secondary mt-1">
                  {selectedCampaign.rationale}
                </p>
                <div className="flex items-center gap-2 mt-2 text-[11px] font-mono text-text-muted">
                  <span>Crown Jewel:</span>
                  <span className="text-red-400 font-bold break-all">
                    {selectedCampaign.target_crown_jewel}
                  </span>
                </div>
              </div>

              {/* Multi-Stage Visual Timeline */}
              <div className="mt-5 flex flex-col gap-3">
                <h4 className="text-xs font-bold uppercase tracking-wider text-text-muted flex items-center gap-1.5">
                  <ListOrdered className="h-3.5 w-3.5 text-brand-primary" />
                  Ordered Campaign Stages ({selectedCampaign.stages?.length || 0})
                </h4>

                <div className="flex flex-col gap-3 relative before:absolute before:left-3.5 before:top-4 before:bottom-4 before:w-0.5 before:bg-surface-border">
                  {selectedCampaign.stages?.map((stage, idx) => (
                    <div
                      key={stage.stage_id || idx}
                      className="relative flex items-start gap-3 pl-8 group"
                    >
                      {/* Timeline Dot */}
                      <div className="absolute left-1.5 top-3 flex h-4 w-4 -translate-x-1/2 items-center justify-center rounded-full bg-surface-dark border-2 border-brand-primary text-[9px] font-bold text-brand-primary shadow-cyan-glow">
                        {idx + 1}
                      </div>

                      {/* Stage Card */}
                      <div className="flex flex-1 flex-col rounded-xl border border-surface-border bg-surface-elevated/90 p-3.5 hover:border-brand-primary/40 transition-all">
                        <div className="flex flex-wrap items-center justify-between gap-2">
                          <div className="flex items-center gap-2">
                            <span className="px-2 py-0.5 rounded bg-surface-dark border border-brand-primary/30 text-brand-primary font-mono text-[10px] font-bold">
                              {stage.technique_id}
                            </span>
                            <span className="text-xs font-bold text-text-primary">
                              {stage.technique_name}
                            </span>
                          </div>
                          <span className="px-2 py-0.5 rounded bg-surface-dark border border-surface-border text-text-muted font-mono text-[10px]">
                            {stage.tactic}
                          </span>
                        </div>

                        <p className="mt-1.5 text-xs text-text-secondary">
                          {stage.rationale}
                        </p>

                        <div className="mt-2 flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-t border-surface-border/50 pt-2 text-[10px] font-mono text-text-muted">
                          <span className="truncate max-w-sm">
                            Target: {stage.target_resource}
                          </span>
                          <span className="text-brand-secondary">
                            Observables: {stage.expected_observables?.join(", ") || "API Telemetry"}
                          </span>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          ) : (
            <div className="flex flex-col items-center justify-center p-12 rounded-2xl border border-surface-border bg-surface text-center text-text-muted">
              <Cpu className="h-10 w-10 text-brand-primary/40 mb-3" />
              <p className="text-sm font-semibold text-text-primary">No campaign selected</p>
              <p className="text-xs max-w-md mt-1">
                Select an existing campaign from the left list or generate a new one from the active attack path.
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default function CampaignPlannerPage() {
  return (
    <React.Suspense fallback={<div className="p-8 text-xs text-text-muted">Loading Campaign Planner...</div>}>
      <CampaignPlannerContent />
    </React.Suspense>
  );
}
