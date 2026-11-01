"use client";

import React, { useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  LayoutDashboard,
  Cloud,
  Network,
  Cpu,
  Terminal,
  Activity,
  FileText,
  ShieldAlert,
  History,
  Settings,
  ChevronLeft,
  ChevronRight,
  Shield,
  Zap,
} from "lucide-react";
import { cn } from "@/lib/utils/cn";

interface NavItem {
  name: string;
  href: string;
  icon: React.ComponentType<{ className?: string }>;
  badge?: string;
}

const WORKSPACE_NAV: NavItem[] = [
  { name: "Overview", href: "/dashboard", icon: LayoutDashboard },
  { name: "AWS Environment", href: "/environment", icon: Cloud },
  { name: "Attack Graph", href: "/attack-graph", icon: Network },
  { name: "AI Campaign Planner", href: "/campaign-planner", icon: Cpu },
  { name: "Execution Center", href: "/execution", icon: Terminal },
  { name: "Telemetry & Detection", href: "/telemetry", icon: Activity },
  { name: "SOC Reports", href: "/reports", icon: FileText },
];

const SYSTEM_NAV: NavItem[] = [
  { name: "Security & Controls", href: "/security", icon: ShieldAlert },
  { name: "Audit Logs", href: "/audit-logs", icon: History },
  { name: "Settings", href: "/settings", icon: Settings },
];

export function Sidebar() {
  const pathname = usePathname();
  const [collapsed, setCollapsed] = useState(false);

  return (
    <aside
      className={cn(
        "flex flex-col border-r border-surface-border bg-sidebar transition-all duration-300 z-30 select-none",
        collapsed ? "w-16" : "w-64"
      )}
    >
      {/* Brand Header */}
      <div className="flex h-16 items-center justify-between px-4 border-b border-surface-border">
        {!collapsed && (
          <Link href="/dashboard" className="flex items-center gap-2.5 overflow-hidden">
            <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-brand-primary/10 border border-brand-primary/30 text-brand-primary shadow-cyan-glow">
              <Zap className="h-5 w-5" />
            </div>
            <div className="flex flex-col">
              <span className="text-sm font-bold tracking-wider text-text-primary uppercase flex items-center gap-1.5">
                Falcon Strike
                <span className="text-[10px] px-1.5 py-0.2 rounded bg-brand-primary/20 text-brand-primary font-mono border border-brand-primary/40">
                  AI
                </span>
              </span>
              <span className="text-[10px] font-mono text-text-muted tracking-tight">
                CTEM & Adversary Emulation
              </span>
            </div>
          </Link>
        )}

        {collapsed && (
          <Link href="/dashboard" className="mx-auto flex h-9 w-9 items-center justify-center rounded-lg bg-brand-primary/10 border border-brand-primary/30 text-brand-primary">
            <Zap className="h-5 w-5" />
          </Link>
        )}

        <button
          onClick={() => setCollapsed(!collapsed)}
          className={cn(
            "flex h-7 w-7 items-center justify-center rounded-md border border-surface-border bg-surface text-text-muted hover:text-text-primary hover:bg-surface-elevated transition-colors",
            collapsed && "hidden"
          )}
          title={collapsed ? "Expand sidebar" : "Collapse sidebar"}
        >
          <ChevronLeft className="h-4 w-4" />
        </button>
      </div>

      {/* Navigation Links */}
      <div className="flex-1 overflow-y-auto px-2 py-4 space-y-6">
        {/* Workspace Section */}
        <div>
          {!collapsed && (
            <p className="px-3 pb-2 text-[10px] font-semibold uppercase tracking-wider text-text-muted">
              Workspace
            </p>
          )}
          <nav className="space-y-1">
            {WORKSPACE_NAV.map((item) => {
              const active = pathname === item.href || (item.href !== "/dashboard" && pathname.startsWith(item.href));
              const Icon = item.icon;
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  title={collapsed ? item.name : undefined}
                  className={cn(
                    "group relative flex items-center gap-3 rounded-lg px-3 py-2 text-xs font-medium transition-all",
                    active
                      ? "bg-brand-primary/15 text-brand-primary font-semibold border border-brand-primary/30 shadow-sm"
                      : "text-text-secondary hover:bg-surface hover:text-text-primary"
                  )}
                >
                  <Icon className={cn("h-4 w-4 shrink-0 transition-colors", active ? "text-brand-primary" : "text-text-muted group-hover:text-text-primary")} />
                  {!collapsed && <span className="truncate">{item.name}</span>}
                  {active && (
                    <div className="absolute right-2 h-1.5 w-1.5 rounded-full bg-brand-primary shadow-cyan-glow" />
                  )}
                </Link>
              );
            })}
          </nav>
        </div>

        {/* System Section */}
        <div>
          {!collapsed && (
            <p className="px-3 pb-2 text-[10px] font-semibold uppercase tracking-wider text-text-muted">
              System
            </p>
          )}
          <nav className="space-y-1">
            {SYSTEM_NAV.map((item) => {
              const active = pathname === item.href || pathname.startsWith(item.href);
              const Icon = item.icon;
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  title={collapsed ? item.name : undefined}
                  className={cn(
                    "group relative flex items-center gap-3 rounded-lg px-3 py-2 text-xs font-medium transition-all",
                    active
                      ? "bg-brand-primary/15 text-brand-primary font-semibold border border-brand-primary/30 shadow-sm"
                      : "text-text-secondary hover:bg-surface hover:text-text-primary"
                  )}
                >
                  <Icon className={cn("h-4 w-4 shrink-0 transition-colors", active ? "text-brand-primary" : "text-text-muted group-hover:text-text-primary")} />
                  {!collapsed && <span className="truncate">{item.name}</span>}
                  {active && (
                    <div className="absolute right-2 h-1.5 w-1.5 rounded-full bg-brand-primary shadow-cyan-glow" />
                  )}
                </Link>
              );
            })}
          </nav>
        </div>
      </div>

      {/* Footer / Toggle & Status */}
      <div className="border-t border-surface-border p-3">
        {collapsed ? (
          <button
            onClick={() => setCollapsed(false)}
            className="flex w-full items-center justify-center rounded-lg p-2 text-text-muted hover:bg-surface hover:text-text-primary transition-colors"
            title="Expand sidebar"
          >
            <ChevronRight className="h-4 w-4" />
          </button>
        ) : (
          <div className="flex items-center justify-between rounded-lg bg-surface/50 p-2.5 border border-surface-border">
            <div className="flex items-center gap-2">
              <Shield className="h-4 w-4 text-emerald-400" />
              <div className="flex flex-col">
                <span className="text-[11px] font-medium text-text-primary">Policy Guard</span>
                <span className="text-[9px] font-mono text-emerald-400">ENFORCED</span>
              </div>
            </div>
            <span className="text-[9px] font-mono text-text-muted">v0.1.0</span>
          </div>
        )}
      </div>
    </aside>
  );
}

