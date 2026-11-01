"use client";

import React from "react";
import { Server, UserCheck, Network, Database, Layers, Sparkles } from "lucide-react";

interface CategoryDetail {
  label: string;
  count: number;
  atRisk: number;
  icon: React.ComponentType<{ className?: string }>;
  isRoadmap?: boolean;
}

interface HeroMetricsProps {
  totalAssets?: number;
  assetsAtRiskCount?: number;
  computeCount?: number;
  computeAtRisk?: number;
  identityCount?: number;
  identityAtRisk?: number;
  networkCount?: number;
  networkAtRisk?: number;
  dataCount?: number;
  dataAtRisk?: number;
}

export function HeroMetrics({
  totalAssets = 13,
  assetsAtRiskCount = 5,
  computeCount = 1,
  computeAtRisk = 1,
  identityCount = 7,
  identityAtRisk = 3,
  networkCount = 1,
  networkAtRisk = 1,
  dataCount = 1,
  dataAtRisk = 1,
}: HeroMetricsProps) {
  const categories: CategoryDetail[] = [
    {
      label: "Compute (EC2)",
      count: computeCount,
      atRisk: computeAtRisk,
      icon: Server,
    },
    {
      label: "Identity (IAM)",
      count: identityCount,
      atRisk: identityAtRisk,
      icon: UserCheck,
    },
    {
      label: "Network (SG)",
      count: networkCount,
      atRisk: networkAtRisk,
      icon: Network,
    },
    {
      label: "Storage (S3)",
      count: dataCount,
      atRisk: dataAtRisk,
      icon: Database,
    },
    {
      label: "Containers (K8s)",
      count: 0,
      atRisk: 0,
      icon: Layers,
      isRoadmap: true,
    },
    {
      label: "Multi-Cloud API",
      count: 0,
      atRisk: 0,
      icon: Sparkles,
      isRoadmap: true,
    },
  ];

  return (
    <div className="flex flex-col gap-4">
      {/* Big Counter from real backend graph */}
      <div className="flex flex-col">
        <span className="text-[11px] font-semibold uppercase tracking-wider text-text-muted">
          Active Environment Risk Posture
        </span>
        <div className="flex items-baseline gap-2 mt-1">
          <span className="text-4xl font-extrabold tracking-tight text-text-primary font-mono">
            {assetsAtRiskCount}
          </span>
          <span className="text-xl font-bold text-text-muted font-mono">
            / {totalAssets}
          </span>
        </div>
        <span className="text-xs font-medium text-brand-secondary">
          Cloud Assets Associated with Attack Paths / Findings
        </span>
      </div>

      {/* Grid of Verified Categories */}
      <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
        {categories.map((cat) => {
          const Icon = cat.icon;
          return (
            <div
              key={cat.label}
              className={`flex items-center gap-3 rounded-xl border p-3 transition-all ${
                cat.isRoadmap
                  ? "border-surface-border/50 bg-surface/40 opacity-60"
                  : "border-surface-border bg-surface/80 hover:border-surface-borderHover"
              }`}
            >
              <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-surface-dark border border-surface-border text-brand-secondary">
                <Icon className="h-4 w-4" />
              </div>
              <div className="flex flex-col overflow-hidden">
                <div className="flex items-baseline gap-1.5">
                  <span className="text-xs font-semibold text-text-primary truncate">
                    {cat.label}
                  </span>
                  {!cat.isRoadmap && (
                    <span className="text-[10px] font-mono text-text-muted">
                      ({cat.count})
                    </span>
                  )}
                </div>
                {cat.isRoadmap ? (
                  <span className="text-[9px] font-mono text-text-muted uppercase">
                    Roadmap
                  </span>
                ) : (
                  <span className="text-[10px] text-status-critical font-medium truncate font-mono">
                    {cat.atRisk} at Risk
                  </span>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
