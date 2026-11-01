"use client";

import React, { useEffect, useState, useMemo, useCallback } from "react";
import {
  ReactFlow,
  Controls,
  Background,
  MiniMap,
  useNodesState,
  useEdgesState,
  MarkerType,
  Node,
  Edge,
} from "@xyflow/react";
import "@xyflow/react/dist/style.css";
import {
  Network,
  GitCommit,
  ShieldAlert,
  Flame,
  ArrowRight,
  RefreshCw,
  Search,
  Filter,
  Layers,
  ChevronRight,
  Info,
} from "lucide-react";
import Link from "next/link";
import { CustomGraphNode } from "@/components/attack-graph/CustomGraphNode";
import { api } from "@/lib/api/client";
import { GraphExport, AttackPath, MisconfigurationFinding } from "@/types/api";
import { getSeverityBadgeClass } from "@/lib/utils/formatters";

const nodeTypes = {
  custom: CustomGraphNode,
};

export default function AttackGraphPage() {
  const [nodes, setNodes, onNodesChange] = useNodesState<Node>([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState<Edge>([]);
  const [loading, setLoading] = useState(true);
  const [attackPaths, setAttackPaths] = useState<AttackPath[]>([]);
  const [selectedPathId, setSelectedPathId] = useState<string | null>(null);
  const [selectedNodeData, setSelectedNodeData] = useState<any | null>(null);
  const [findings, setFindings] = useState<MisconfigurationFinding[]>([]);
  const [search, setSearch] = useState("");

  const loadGraph = useCallback(async () => {
    try {
      setLoading(true);
      const [exportRes, pathsRes, analyzeRes] = await Promise.allSettled([
        api.exportGraph(),
        api.getAttackPaths(),
        api.analyzeGraph(),
      ]);

      let rawNodes: any[] = [];
      let rawEdges: any[] = [];
      let paths: AttackPath[] = [];

      if (exportRes.status === "fulfilled") {
        rawNodes = exportRes.value.nodes || [];
        rawEdges = exportRes.value.edges || [];
      }
      if (pathsRes.status === "fulfilled") {
        paths = pathsRes.value || [];
        setAttackPaths(paths);
        if (paths.length > 0 && !selectedPathId) {
          setSelectedPathId(paths[0].path_id);
        }
      }
      if (analyzeRes.status === "fulfilled") {
        setFindings(analyzeRes.value.findings || []);
      }

      // Convert to React Flow layout
      // Auto-layout in grid or circular hierarchy
      const cols = 4;
      const xSpacing = 280;
      const ySpacing = 160;

      const flowNodes: Node[] = rawNodes.map((n, idx) => {
        const col = idx % cols;
        const row = Math.floor(idx / cols);
        const isTarget = n.type === "S3_BUCKET" || n.label?.includes("Crown") || n.id?.includes("Target");

        return {
          id: n.id,
          type: "custom",
          position: { x: 50 + col * xSpacing, y: 50 + row * ySpacing },
          data: {
            ...n,
            is_crown_jewel: isTarget,
          },
        };
      });

      const flowEdges: Edge[] = rawEdges.map((e, idx) => ({
        id: e.id || `e-${idx}`,
        source: e.source,
        target: e.target,
        label: e.type,
        labelStyle: { fill: "#94A3B8", fontSize: 10, fontFamily: "JetBrains Mono" },
        labelBgStyle: { fill: "#101B2D", fillOpacity: 0.8 },
        animated: false,
        markerEnd: {
          type: MarkerType.ArrowClosed,
          color: "#334764",
        },
        style: { stroke: "#334764", strokeWidth: 1.5 },
      }));

      setNodes(flowNodes);
      setEdges(flowEdges);
    } catch {
      // Fallback
    } finally {
      setLoading(false);
    }
  }, [selectedPathId, setEdges, setNodes]);

  useEffect(() => {
    loadGraph();
  }, [loadGraph]);

  // Highlight path when selectedPathId changes
  useEffect(() => {
    if (!selectedPathId) return;
    const activePath = attackPaths.find((p) => p.path_id === selectedPathId);
    if (!activePath) return;

    const pathNodes = new Set(activePath.node_sequence || []);
    const pathEdges = new Set(activePath.edge_sequence || []);

    setNodes((nds) =>
      nds.map((n) => {
        const inPath = pathNodes.has(n.id);
        return {
          ...n,
          selected: inPath,
          data: {
            ...n.data,
            highlighted: inPath,
          },
        };
      })
    );

    setEdges((eds) =>
      eds.map((e) => {
        const inPath = pathEdges.has(e.id) || (pathNodes.has(e.source) && pathNodes.has(e.target));
        return {
          ...e,
          animated: inPath,
          style: {
            stroke: inPath ? "#22D3EE" : "#334764",
            strokeWidth: inPath ? 3 : 1.5,
          },
          markerEnd: {
            type: MarkerType.ArrowClosed,
            color: inPath ? "#22D3EE" : "#334764",
          },
        };
      })
    );
  }, [selectedPathId, attackPaths, setEdges, setNodes]);

  const onNodeClick = (_: any, node: Node) => {
    setSelectedNodeData(node.data);
  };

  const currentPath = attackPaths.find((p) => p.path_id === selectedPathId) || attackPaths[0];

  return (
    <div className="flex flex-col h-[calc(100vh-100px)] gap-4">
      {/* Top Controls Bar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 bg-surface p-3 rounded-xl border border-surface-border shrink-0">
        <div className="flex items-center gap-3">
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-brand-primary/10 text-brand-primary border border-brand-primary/30">
            <Network className="h-4 w-4" />
          </div>
          <div>
            <h2 className="text-sm font-bold text-text-primary">Interactive Attack Graph</h2>
            <p className="text-[11px] text-text-muted">
              Select an attack path to highlight the traversal chain from exposed entry to crown jewel
            </p>
          </div>
        </div>

        {/* Path Selector */}
        <div className="flex items-center gap-2">
          <span className="text-xs font-mono text-text-muted">Active Path:</span>
          <select
            value={selectedPathId || ""}
            onChange={(e) => setSelectedPathId(e.target.value)}
            className="rounded-lg border border-surface-border bg-surface-dark px-3 py-1.5 text-xs font-mono text-brand-primary focus:border-brand-primary focus:outline-none"
          >
            {attackPaths.map((p) => (
              <option key={p.path_id} value={p.path_id}>
                {p.path_id} (Risk {p.risk_score !== undefined ? p.risk_score.toFixed(1) : "—"}) - {p.hop_count ?? (p.node_sequence ? p.node_sequence.length - 1 : 0)} hops
              </option>
            ))}
          </select>

          <button
            onClick={loadGraph}
            disabled={loading}
            className="flex items-center gap-1 rounded-lg border border-surface-border bg-surface-dark px-2.5 py-1.5 text-xs text-text-secondary hover:text-text-primary"
            title="Reload Graph"
          >
            <RefreshCw className={`h-3.5 w-3.5 ${loading ? "animate-spin" : ""}`} />
          </button>
        </div>
      </div>

      {/* Main Canvas & Detail Sidebar */}
      <div className="flex-1 grid grid-cols-1 lg:grid-cols-12 gap-4 overflow-hidden rounded-xl border border-surface-border bg-surface-dark">
        {/* Canvas Area */}
        <div className="lg:col-span-8 h-full relative">
          <ReactFlow
            nodes={nodes}
            edges={edges}
            onNodesChange={onNodesChange}
            onEdgesChange={onEdgesChange}
            onNodeClick={onNodeClick}
            nodeTypes={nodeTypes}
            fitView
            className="bg-background"
          >
            <Background color="#24344A" gap={24} size={1} />
            <Controls className="fill-text-primary text-text-primary" />
            <MiniMap
              nodeColor={(n) => {
                if (n.data?.is_crown_jewel) return "#EF4444";
                if (n.data?.type === "INTERNET") return "#38BDF8";
                return "#22D3EE";
              }}
              className="!bg-surface-elevated !border !border-surface-border !rounded-lg"
            />
          </ReactFlow>

          {/* Legend Overlay */}
          <div className="absolute bottom-4 left-4 flex items-center gap-3 bg-surface/90 border border-surface-border p-2 rounded-lg text-[10px] font-mono backdrop-blur">
            <span className="flex items-center gap-1 text-sky-400">
              <span className="h-2 w-2 rounded-full bg-sky-400" /> Internet / Entry
            </span>
            <span className="flex items-center gap-1 text-cyan-400">
              <span className="h-2 w-2 rounded-full bg-cyan-400" /> Compute / IAM
            </span>
            <span className="flex items-center gap-1 text-red-400">
              <span className="h-2 w-2 rounded-full bg-red-400 shadow-red-glow" /> Crown Jewel
            </span>
            <span className="flex items-center gap-1 text-brand-primary">
              <span className="h-2 w-4 bg-brand-primary rounded" /> Active Attack Traversal
            </span>
          </div>
        </div>

        {/* Attack Path & Node Inspector Sidebar */}
        <div className="lg:col-span-4 h-full border-l border-surface-border bg-surface p-4 overflow-y-auto flex flex-col gap-4">
          {/* Active Attack Path Card */}
          {currentPath ? (
            <div className="flex flex-col gap-3 rounded-xl border border-brand-primary/30 bg-surface-elevated p-4 shadow-cyan-glow">
              <div className="flex items-center justify-between">
                <span className="text-[10px] font-mono uppercase tracking-wider text-brand-primary font-bold">
                  Targeted Attack Path
                </span>
                <span className="px-2 py-0.5 rounded bg-red-500/20 text-red-400 border border-red-500/40 text-[10px] font-bold font-mono">
                  RISK {currentPath.risk_score !== undefined ? currentPath.risk_score.toFixed(1) : "—"} / 100
                </span>
              </div>

              <div>
                <h3 className="text-xs font-bold text-text-primary font-mono">{currentPath.path_id}</h3>
                <p className="text-[11px] text-text-muted mt-0.5 font-mono">
                  Length: {currentPath.hop_count !== undefined ? currentPath.hop_count : (currentPath.node_sequence ? currentPath.node_sequence.length - 1 : 0)} hops | Entry: {currentPath.entry_node_id}
                </p>
              </div>

              {/* Traversal Step Sequence */}
              <div>
                <span className="text-[10px] font-semibold uppercase text-text-muted">
                  Traversal Sequence:
                </span>
                <div className="mt-2 flex flex-col gap-1.5 font-mono text-[11px]">
                  {currentPath.node_sequence?.map((nodeId, idx) => (
                    <div
                      key={idx}
                      className="flex items-center gap-2 p-1.5 rounded bg-surface-dark border border-surface-border text-text-secondary truncate"
                    >
                      <span className="h-4 w-4 shrink-0 rounded-full bg-brand-primary/20 text-brand-primary flex items-center justify-center text-[9px] font-bold">
                        {idx + 1}
                      </span>
                      <span className="truncate">{nodeId}</span>
                    </div>
                  ))}
                </div>
              </div>

              <Link
                href={`/campaign-planner?path_id=${encodeURIComponent(currentPath.path_id)}`}
                className="mt-2 flex items-center justify-center gap-1.5 rounded-lg bg-brand-primary px-3 py-2 text-xs font-semibold text-sidebar hover:bg-brand-secondary transition-all shadow-cyan-glow"
              >
                Assemble Campaign Plan <ArrowRight className="h-3.5 w-3.5" />
              </Link>
            </div>
          ) : (
            <div className="p-4 rounded-xl border border-surface-border text-xs text-text-muted text-center">
              No attack path selected.
            </div>
          )}

          {/* Node Inspector */}
          {selectedNodeData && (
            <div className="flex flex-col gap-2 rounded-xl border border-surface-border bg-surface-elevated p-4">
              <span className="text-[10px] font-mono uppercase text-brand-secondary font-bold">
                Inspected Node
              </span>
              <h4 className="text-xs font-bold text-text-primary font-mono break-all">
                {selectedNodeData.label || selectedNodeData.id}
              </h4>
              <div className="text-[11px] font-mono text-text-muted">
                Type: {selectedNodeData.type}
              </div>

              {selectedNodeData.properties && (
                <div className="mt-2 p-2 rounded bg-surface-dark border border-surface-border text-[10px] font-mono text-text-secondary max-h-40 overflow-y-auto">
                  <pre>{JSON.stringify(selectedNodeData.properties, null, 2)}</pre>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

