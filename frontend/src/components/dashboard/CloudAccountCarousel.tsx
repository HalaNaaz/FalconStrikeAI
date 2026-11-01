"use client";

import React, { useEffect, useState } from "react";
import { Cloud, Shield, Server, Database, AlertCircle } from "lucide-react";
import { cn } from "@/lib/utils/cn";
import { api } from "@/lib/api/client";
import { CollectorStatusResponse, HealthResponse } from "@/types/api";

interface AccountCard {
  title: string;
  subtitle: string;
  badge: string;
  status: "active" | "ready" | "unconfigured" | "disabled";
  isSynthetic?: boolean;
}

export function CloudAccountCarousel() {
  const [collectorStatus, setCollectorStatus] = useState<CollectorStatusResponse | null>(null);
  const [health, setHealth] = useState<HealthResponse | null>(null);

  useEffect(() => {
    Promise.allSettled([api.getCollectorStatus(), api.getHealth()]).then(([colRes, healthRes]) => {
      if (colRes.status === "fulfilled") setCollectorStatus(colRes.value);
      if (healthRes.status === "fulfilled") setHealth(healthRes.value);
    });
  }, []);

  const targetAccount = health?.target_account_id || collectorStatus?.target_account || "000000000000";
  const isSynthetic = targetAccount === "000000000000" || collectorStatus?.default_mode === "synthetic";

  const cards: AccountCard[] = [
    {
      title: "AWS Target Lab",
      subtitle: isSynthetic ? "Synthetic Lab Fixture" : `AWS Account ${targetAccount}`,
      badge: isSynthetic ? "SYNTHETIC_ENV" : "AWS_LIVE",
      status: "active",
      isSynthetic,
    },
    {
      title: "AWS IAM Collector",
      subtitle: "Users, Roles, Policies, Trusts",
      badge: "OPERATIONAL",
      status: "ready",
    },
    {
      title: "AWS EC2 & Network",
      subtitle: "Instances, SGs, Public Endpoints",
      badge: "OPERATIONAL",
      status: "ready",
    },
    {
      title: "AWS S3 Storage",
      subtitle: "Buckets & Public Access Blocks",
      badge: "OPERATIONAL",
      status: "ready",
    },
    {
      title: "Live AWS Boto3 SDK",
      subtitle: "Production Cloud Ingestion",
      badge: "AWS NOT CONFIGURED",
      status: "unconfigured",
    },
    {
      title: "GCP / Azure / K8s",
      subtitle: "Multi-Cloud Roadmap",
      badge: "NOT CONNECTED",
      status: "disabled",
    },
  ];

  return (
    <div className="flex items-center gap-3 overflow-x-auto pb-1 scrollbar-none w-full">
      {cards.map((card) => {
        const isActive = card.status === "active";
        const isReady = card.status === "ready";
        const isUnconfigured = card.status === "unconfigured";
        const isDisabled = card.status === "disabled";

        return (
          <div
            key={card.title}
            className={cn(
              "flex min-w-[210px] shrink-0 items-center justify-between rounded-xl border p-3 transition-all",
              isActive && "border-brand-primary/40 bg-surface-elevated/90 shadow-cyan-glow",
              isReady && "border-surface-border bg-surface/80",
              isUnconfigured && "border-amber-500/30 bg-surface/50 opacity-80",
              isDisabled && "border-surface-border/50 bg-surface/30 opacity-50"
            )}
          >
            <div className="flex items-center gap-2.5">
              <div
                className={cn(
                  "flex h-8 w-8 items-center justify-center rounded-lg border",
                  isActive && "bg-brand-primary/10 border-brand-primary/30 text-brand-primary",
                  isReady && "bg-surface-dark border-surface-border text-emerald-400",
                  isUnconfigured && "bg-amber-500/10 border-amber-500/30 text-amber-400",
                  isDisabled && "bg-surface-dark border-surface-border text-text-muted"
                )}
              >
                {card.title.includes("IAM") ? (
                  <Shield className="h-4 w-4" />
                ) : card.title.includes("EC2") ? (
                  <Server className="h-4 w-4" />
                ) : card.title.includes("S3") ? (
                  <Database className="h-4 w-4" />
                ) : card.title.includes("Live") ? (
                  <AlertCircle className="h-4 w-4" />
                ) : (
                  <Cloud className="h-4 w-4" />
                )}
              </div>
              <div className="flex flex-col">
                <span className="text-xs font-semibold text-text-primary">{card.title}</span>
                <span className="text-[10px] text-text-muted truncate max-w-[120px] font-mono">
                  {card.subtitle}
                </span>
                <span
                  className={cn(
                    "text-[9px] font-mono font-bold mt-0.5",
                    isActive && "text-brand-primary",
                    isReady && "text-emerald-400",
                    isUnconfigured && "text-amber-400",
                    isDisabled && "text-text-muted"
                  )}
                >
                  {card.badge}
                </span>
              </div>
            </div>
          </div>
        );
      })}
    </div>
  );
}
