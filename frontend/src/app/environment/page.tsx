"use client";

import React, { useEffect, useState } from "react";
import {
  Cloud,
  Layers,
  Search,
  Filter,
  RefreshCw,
  Shield,
  Server,
  UserCheck,
  FileCode,
  Database,
  Lock,
  ExternalLink,
  AlertTriangle,
  CheckCircle2,
  Play,
} from "lucide-react";
import { api } from "@/lib/api/client";
import { GraphExport, GraphNode, MisconfigurationFinding } from "@/types/api";
import { getSeverityBadgeClass } from "@/lib/utils/formatters";

type TabType =
  | "all"
  | "IAM_USER"
  | "IAM_ROLE"
  | "IAM_POLICY"
  | "EC2_INSTANCE"
  | "SECURITY_GROUP"
  | "S3_BUCKET"
  | "EXPOSURE";

export default function EnvironmentExplorerPage() {
  const [activeTab, setActiveTab] = useState<TabType>("all");
  const [search, setSearch] = useState("");
  const [loading, setLoading] = useState(true);
  const [collecting, setCollecting] = useState(false);
  const [graphData, setGraphData] = useState<GraphExport | null>(null);
  const [findings, setFindings] = useState<MisconfigurationFinding[]>([]);
  const [selectedNode, setSelectedNode] = useState<GraphNode | null>(null);
  const [collectMsg, setCollectMsg] = useState<string | null>(null);

  const fetchData = async () => {
    try {
      setLoading(true);
      const [exportRes, analyzeRes] = await Promise.allSettled([
        api.exportGraph(),
        api.analyzeGraph(),
      ]);

      if (exportRes.status === "fulfilled") setGraphData(exportRes.value);
      if (analyzeRes.status === "fulfilled") setFindings(analyzeRes.value.findings);
    } catch {
      // Fallback
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const handleCollect = async () => {
    try {
      setCollecting(true);
      setCollectMsg(null);
      const res = await api.collectEnvironment({
        account_id: "000000000000",
        force_synthetic: true,
        synthetic_topology_type: "flawed",
      });
      setCollectMsg(`Collection successful! Ingested ${res.total_assets} cloud assets.`);
      await fetchData();
      setTimeout(() => setCollectMsg(null), 5000);
    } catch (err: any) {
      alert(`Collection error: ${err.message}`);
    } finally {
      setCollecting(false);
    }
  };

  const nodes = graphData?.nodes || [];

  const filteredNodes = nodes.filter((node) => {
    // Tab filter
    if (activeTab === "EXPOSURE") {
      const isPublic =
        node.properties?.is_public ||
        node.properties?.public_ip ||
        node.type === "INTERNET" ||
        node.type === "ENDPOINT";
      if (!isPublic) return false;
    } else if (activeTab !== "all" && node.type !== activeTab) {
      return false;
    }

    // Search query filter
    if (!search) return true;
    const q = search.toLowerCase();
    const idMatch = node.id.toLowerCase().includes(q);
    const labelMatch = node.label?.toLowerCase().includes(q);
    const typeMatch = node.type.toLowerCase().includes(q);
    return idMatch || labelMatch || typeMatch;
  });

  return (
    <div className="flex flex-col gap-6">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold text-text-primary">AWS Environment Explorer</h2>
          <p className="text-xs text-text-muted">
            Inspect discovered IAM principals, compute instances, security groups, and object stores
          </p>
        </div>

        <div className="flex items-center gap-3">
          {collectMsg && (
            <span className="text-xs text-emerald-400 bg-emerald-500/10 border border-emerald-500/30 px-3 py-1.5 rounded-lg flex items-center gap-1.5 font-mono">
              <CheckCircle2 className="h-3.5 w-3.5" />
              {collectMsg}
            </span>
          )}

          <button
            onClick={handleCollect}
            disabled={collecting}
            className="flex items-center gap-2 rounded-lg bg-brand-primary px-3.5 py-2 text-xs font-semibold text-sidebar hover:bg-brand-secondary transition-all disabled:opacity-50 shadow-cyan-glow"
          >
            <Play className={`h-3.5 w-3.5 fill-current ${collecting ? "animate-spin" : ""}`} />
            <span>{collecting ? "Collecting..." : "Collect Environment"}</span>
          </button>
        </div>
      </div>

      {/* Tabs Row */}
      <div className="flex items-center gap-1 border-b border-surface-border overflow-x-auto pb-px">
        {[
          { id: "all", label: "All Assets", icon: Layers },
          { id: "IAM_USER", label: "IAM Users", icon: UserCheck },
          { id: "IAM_ROLE", label: "IAM Roles", icon: Shield },
          { id: "IAM_POLICY", label: "IAM Policies", icon: FileCode },
          { id: "EC2_INSTANCE", label: "EC2 Instances", icon: Server },
          { id: "SECURITY_GROUP", label: "Security Groups", icon: Lock },
          { id: "S3_BUCKET", label: "S3 Buckets", icon: Database },
          { id: "EXPOSURE", label: "Public Exposure", icon: AlertTriangle },
        ].map((tab) => {
          const Icon = tab.icon;
          const active = activeTab === tab.id;
          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id as TabType)}
              className={`flex items-center gap-2 px-3.5 py-2.5 text-xs font-medium border-b-2 transition-all whitespace-nowrap ${
                active
                  ? "border-brand-primary text-brand-primary font-semibold bg-surface/40"
                  : "border-transparent text-text-muted hover:text-text-primary hover:border-surface-border"
              }`}
            >
              <Icon className="h-3.5 w-3.5" />
              <span>{tab.label}</span>
            </button>
          );
        })}
      </div>

      {/* Search Bar & Stats */}
      <div className="flex flex-col sm:flex-row items-center justify-between gap-3">
        <div className="relative w-full sm:w-96">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-text-muted" />
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search by ARN, ID, or resource name..."
            className="w-full rounded-lg border border-surface-border bg-surface pl-9 pr-3 py-2 text-xs text-text-primary placeholder:text-text-muted focus:border-brand-primary focus:outline-none"
          />
        </div>

        <div className="flex items-center gap-2 text-xs font-mono text-text-muted">
          <span>Showing: {filteredNodes.length} of {nodes.length} assets</span>
        </div>
      </div>

      {/* Asset Table & Details Slide-Over */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        <div className={selectedNode ? "lg:col-span-7" : "lg:col-span-12"}>
          <div className="overflow-hidden rounded-xl border border-surface-border bg-surface shadow-panel">
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead className="bg-surface-elevated border-b border-surface-border text-[11px] font-semibold uppercase tracking-wider text-text-muted">
                  <tr>
                    <th className="px-4 py-3">Resource Identifier</th>
                    <th className="px-4 py-3">Type</th>
                    <th className="px-4 py-3">Exposure</th>
                    <th className="px-4 py-3">Risk Level</th>
                    <th className="px-4 py-3 text-right">Action</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-surface-border">
                  {filteredNodes.length > 0 ? (
                    filteredNodes.map((node) => {
                      const isSelected = selectedNode?.id === node.id;
                      const hasCriticalFinding = findings.some(
                        (f) => f.target_node_id === node.id && f.severity === "CRITICAL"
                      );
                      const isPublic =
                        node.properties?.is_public ||
                        node.properties?.public_ip ||
                        node.type === "INTERNET" ||
                        node.type === "ENDPOINT";

                      return (
                        <tr
                          key={node.id}
                          onClick={() => setSelectedNode(node)}
                          className={`cursor-pointer transition-colors ${
                            isSelected
                              ? "bg-brand-primary/10 border-l-2 border-l-brand-primary"
                              : "hover:bg-surface-elevated/60"
                          }`}
                        >
                          <td className="px-4 py-3 font-mono font-medium text-text-primary">
                            <div className="flex flex-col">
                              <span className="truncate max-w-xs">{node.label || node.id}</span>
                              <span className="text-[10px] text-text-muted truncate max-w-xs">
                                {node.id}
                              </span>
                            </div>
                          </td>
                          <td className="px-4 py-3 font-mono text-text-secondary">
                            <span className="px-2 py-0.5 rounded bg-surface-dark border border-surface-border text-[10px]">
                              {node.type}
                            </span>
                          </td>
                          <td className="px-4 py-3">
                            {isPublic ? (
                              <span className="px-2 py-0.5 rounded bg-red-500/10 border border-red-500/30 text-red-400 font-mono text-[10px]">
                                PUBLIC_EXPOSED
                              </span>
                            ) : (
                              <span className="px-2 py-0.5 rounded bg-surface-dark border border-surface-border text-text-muted font-mono text-[10px]">
                                INTERNAL_ONLY
                              </span>
                            )}
                          </td>
                          <td className="px-4 py-3">
                            {hasCriticalFinding ? (
                              <span className="px-2 py-0.5 rounded bg-red-500/10 text-red-400 border border-red-500/30 text-[10px] font-semibold">
                                HIGH RISK
                              </span>
                            ) : (
                              <span className="px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/30 text-[10px]">
                                NORMAL
                              </span>
                            )}
                          </td>
                          <td className="px-4 py-3 text-right">
                            <button
                              onClick={(e) => {
                                e.stopPropagation();
                                setSelectedNode(node);
                              }}
                              className="text-xs text-brand-primary hover:underline font-medium"
                            >
                              Inspect
                            </button>
                          </td>
                        </tr>
                      );
                    })
                  ) : (
                    <tr>
                      <td colSpan={5} className="p-8 text-center text-text-muted">
                        No assets found matching current filter.
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>
        </div>

        {/* Node Detail Slide-Over */}
        {selectedNode && (
          <div className="lg:col-span-5 flex flex-col rounded-xl border border-surface-border bg-surface p-5 shadow-panel">
            <div className="flex items-center justify-between pb-3 border-b border-surface-border">
              <div className="flex flex-col">
                <span className="text-[10px] font-mono text-brand-primary uppercase">
                  Asset Details
                </span>
                <h3 className="text-sm font-bold text-text-primary font-mono truncate max-w-sm">
                  {selectedNode.label || selectedNode.id}
                </h3>
              </div>
              <button
                onClick={() => setSelectedNode(null)}
                className="text-text-muted hover:text-text-primary text-xs"
              >
                ✕ Close
              </button>
            </div>

            <div className="mt-4 flex flex-col gap-4 overflow-y-auto max-h-[500px]">
              <div>
                <span className="text-[11px] font-semibold text-text-muted uppercase">Resource ID</span>
                <p className="mt-0.5 text-xs font-mono text-text-primary bg-surface-dark p-2 rounded border border-surface-border break-all">
                  {selectedNode.id}
                </p>
              </div>

              <div>
                <span className="text-[11px] font-semibold text-text-muted uppercase">Resource Type</span>
                <p className="mt-0.5 text-xs font-mono text-text-primary">
                  {selectedNode.type}
                </p>
              </div>

              {selectedNode.properties && (
                <div>
                  <span className="text-[11px] font-semibold text-text-muted uppercase">Properties</span>
                  <div className="mt-1 rounded border border-surface-border bg-surface-dark p-2 font-mono text-[11px] text-text-secondary overflow-x-auto">
                    <pre>{JSON.stringify(selectedNode.properties, null, 2)}</pre>
                  </div>
                </div>
              )}

              {/* Associated Findings */}
              <div>
                <span className="text-[11px] font-semibold text-text-muted uppercase">
                  Detected Misconfigurations
                </span>
                <div className="mt-2 flex flex-col gap-2">
                  {findings
                    .filter((f) => f.target_node_id === selectedNode.id)
                    .map((finding) => (
                      <div
                        key={finding.finding_id}
                        className="rounded-lg border border-red-500/20 bg-red-500/10 p-2.5 text-xs"
                      >
                        <div className="flex items-center justify-between">
                          <span className="font-semibold text-red-400">{finding.rule_name}</span>
                          <span className={`text-[10px] px-1.5 py-0.2 rounded font-semibold ${getSeverityBadgeClass(finding.severity)}`}>
                            {finding.severity}
                          </span>
                        </div>
                        <p className="mt-1 text-[11px] text-text-secondary">
                          {finding.description}
                        </p>
                        <p className="mt-1 text-[11px] text-brand-primary">
                          Remediation: {finding.remediation}
                        </p>
                      </div>
                    ))}
                  {!findings.some((f) => f.target_node_id === selectedNode.id) && (
                    <p className="text-xs text-text-muted">No security findings associated with this asset.</p>
                  )}
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

