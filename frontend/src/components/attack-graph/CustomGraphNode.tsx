"use client";

import React, { memo } from "react";
import { Handle, Position, NodeProps } from "@xyflow/react";
import {
  Server,
  UserCheck,
  Shield,
  FileCode,
  Database,
  Lock,
  Globe,
  Flame,
} from "lucide-react";
import { cn } from "@/lib/utils/cn";

function getNodeIcon(type?: string) {
  switch (type?.toUpperCase()) {
    case "INTERNET":
    case "ENDPOINT":
      return Globe;
    case "EC2_INSTANCE":
      return Server;
    case "IAM_USER":
      return UserCheck;
    case "IAM_ROLE":
      return Shield;
    case "IAM_POLICY":
      return FileCode;
    case "S3_BUCKET":
      return Database;
    case "SECURITY_GROUP":
      return Lock;
    default:
      return Shield;
  }
}

function getNodeColor(type?: string, isCrownJewel?: boolean) {
  if (isCrownJewel) {
    return {
      border: "border-red-500 shadow-red-glow",
      bg: "bg-red-500/15",
      badge: "bg-red-500/30 text-red-300",
      iconColor: "text-red-400",
    };
  }
  switch (type?.toUpperCase()) {
    case "INTERNET":
    case "ENDPOINT":
      return {
        border: "border-sky-400/80 shadow-cyan-glow",
        bg: "bg-sky-500/10",
        badge: "bg-sky-500/20 text-sky-300",
        iconColor: "text-sky-400",
      };
    case "EC2_INSTANCE":
      return {
        border: "border-cyan-400/80",
        bg: "bg-cyan-500/10",
        badge: "bg-cyan-500/20 text-cyan-300",
        iconColor: "text-cyan-400",
      };
    case "IAM_USER":
      return {
        border: "border-emerald-400/80",
        bg: "bg-emerald-500/10",
        badge: "bg-emerald-500/20 text-emerald-300",
        iconColor: "text-emerald-400",
      };
    case "IAM_ROLE":
      return {
        border: "border-purple-400/80",
        bg: "bg-purple-500/10",
        badge: "bg-purple-500/20 text-purple-300",
        iconColor: "text-purple-400",
      };
    case "S3_BUCKET":
      return {
        border: "border-amber-400/80",
        bg: "bg-amber-500/10",
        badge: "bg-amber-500/20 text-amber-300",
        iconColor: "text-amber-400",
      };
    default:
      return {
        border: "border-surface-border",
        bg: "bg-surface-elevated",
        badge: "bg-surface-dark text-text-muted",
        iconColor: "text-text-muted",
      };
  }
}

export const CustomGraphNode = memo(({ data, selected }: NodeProps) => {
  const nodeType = String(data.type || "ASSET");
  const isCrownJewel = Boolean(data.is_crown_jewel || data.critical);
  const Icon = getNodeIcon(nodeType);
  const colors = getNodeColor(nodeType, isCrownJewel);

  return (
    <div
      className={cn(
        "group relative flex min-w-[180px] max-w-[240px] flex-col rounded-xl border bg-surface-elevated p-3 shadow-panel transition-all",
        colors.border,
        selected && "ring-2 ring-brand-primary scale-105"
      )}
    >
      <Handle type="target" position={Position.Top} className="!bg-surface-border !w-2 !h-2" />

      {/* Header with Type Badge & Crown Jewel Indicator */}
      <div className="flex items-center justify-between gap-1 pb-1.5 border-b border-surface-border/50">
        <div className="flex items-center gap-1.5 overflow-hidden">
          <div className={cn("flex h-6 w-6 shrink-0 items-center justify-center rounded-md", colors.bg, colors.iconColor)}>
            <Icon className="h-3.5 w-3.5" />
          </div>
          <span className={cn("text-[9px] font-mono font-semibold px-1.5 py-0.2 rounded truncate", colors.badge)}>
            {nodeType}
          </span>
        </div>

        {isCrownJewel && (
          <span className="flex items-center gap-1 text-[9px] font-mono text-red-400 bg-red-500/20 border border-red-500/40 px-1.5 py-0.2 rounded font-bold animate-pulse">
            <Flame className="h-2.5 w-2.5" /> JEWEL
          </span>
        )}
      </div>

      {/* Node Title / ARN */}
      <div className="mt-2 flex flex-col">
        <span className="text-xs font-bold text-text-primary truncate">
          {String(data.label || data.name || data.id)}
        </span>
        <span className="text-[9px] font-mono text-text-muted truncate">
          {String(data.id)}
        </span>
      </div>

      <Handle type="source" position={Position.Bottom} className="!bg-brand-primary !w-2 !h-2" />
    </div>
  );
});

CustomGraphNode.displayName = "CustomGraphNode";

