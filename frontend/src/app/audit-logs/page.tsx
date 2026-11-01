"use client";

import React, { useEffect, useState } from "react";
import { useSearchParams } from "next/navigation";
import {
  History,
  FileCheck2,
  Search,
  Filter,
  RefreshCw,
  Download,
  ShieldCheck,
  ShieldAlert,
  AlertTriangle,
  Lock,
} from "lucide-react";
import { api } from "@/lib/api/client";
import { AuditRecord, AuditChainVerificationResult, CampaignExecutionRecord } from "@/types/api";
import { formatDate, truncateHash } from "@/lib/utils/formatters";

function AuditLogsContent() {
  const searchParams = useSearchParams();
  const initialRunId = searchParams.get("run_id");

  const [executions, setExecutions] = useState<CampaignExecutionRecord[]>([]);
  const [selectedRunId, setSelectedRunId] = useState<string>(initialRunId || "");
  const [records, setRecords] = useState<AuditRecord[]>([]);
  const [verification, setVerification] = useState<AuditChainVerificationResult | null>(null);
  const [loading, setLoading] = useState(true);
  const [verifying, setVerifying] = useState(false);
  const [search, setSearch] = useState("");
  const [selectedRecord, setSelectedRecord] = useState<AuditRecord | null>(null);

  const fetchExecutions = async () => {
    try {
      const execs = await api.getExecutions();
      setExecutions(execs);
      if (execs.length > 0 && !selectedRunId) {
        setSelectedRunId(execs[0].run_id);
      }
    } catch {
      // Fallback
    }
  };

  const fetchAuditChain = async (runId: string) => {
    if (!runId) return;
    try {
      setLoading(true);
      const chain = await api.getAuditChain(runId);
      setRecords(chain);
      if (chain.length > 0) {
        setSelectedRecord(chain[0]);
      }
      // Also verify
      const verRes = await api.verifyAuditChain(runId);
      setVerification(verRes);
    } catch {
      setRecords([]);
      setVerification(null);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchExecutions();
  }, []);

  useEffect(() => {
    if (selectedRunId) {
      fetchAuditChain(selectedRunId);
    }
  }, [selectedRunId]);

  const handleVerify = async () => {
    if (!selectedRunId) return;
    try {
      setVerifying(true);
      const res = await api.verifyAuditChain(selectedRunId);
      setVerification(res);
    } catch (err: any) {
      alert(`Verification failed: ${err.message}`);
    } finally {
      setVerifying(false);
    }
  };

  const handleExportJsonl = () => {
    if (!selectedRunId) return;
    const url = `${process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000"}/api/v1/audit/export/${encodeURIComponent(selectedRunId)}`;
    window.open(url, "_blank");
  };

  const filteredRecords = records.filter((r) => {
    if (!search) return true;
    const q = search.toLowerCase();
    return (
      r.action.toLowerCase().includes(q) ||
      r.actor.toLowerCase().includes(q) ||
      r.record_hash.toLowerCase().includes(q) ||
      r.event_type.toLowerCase().includes(q)
    );
  });

  return (
    <div className="flex flex-col gap-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold text-text-primary">Tamper-Evident Audit Ledger</h2>
          <p className="text-xs text-text-muted">
            Append-only cryptographic SHA-256 hash-chained log linking every simulated adversary action from genesis
          </p>
        </div>

        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2 rounded-lg border border-surface-border bg-surface px-3 py-1.5 text-xs">
            <span className="text-text-muted font-mono">Run ID:</span>
            <select
              value={selectedRunId}
              onChange={(e) => setSelectedRunId(e.target.value)}
              className="bg-transparent font-mono text-brand-primary focus:outline-none"
            >
              {executions.map((x) => (
                <option key={x.run_id} value={x.run_id} className="bg-surface text-text-primary">
                  {x.run_id}
                </option>
              ))}
            </select>
          </div>

          <button
            onClick={handleVerify}
            disabled={verifying || !selectedRunId}
            className="flex items-center gap-1.5 rounded-lg border border-brand-primary/30 bg-brand-primary/10 px-3 py-2 text-xs font-semibold text-brand-primary hover:bg-brand-primary/20 transition-all font-mono shadow-cyan-glow"
          >
            <ShieldCheck className={`h-3.5 w-3.5 ${verifying ? "animate-spin" : ""}`} />
            <span>{verifying ? "Verifying..." : "Verify Cryptographic Chain"}</span>
          </button>

          <button
            onClick={handleExportJsonl}
            disabled={!selectedRunId || records.length === 0}
            className="flex items-center gap-1.5 rounded-lg border border-surface-border bg-surface px-3 py-2 text-xs text-text-secondary hover:text-text-primary hover:bg-surface-elevated font-mono"
            title="Download JSONL"
          >
            <Download className="h-3.5 w-3.5" />
            <span className="hidden sm:inline">Export JSONL</span>
          </button>
        </div>
      </div>

      {/* Verification Status Banner */}
      {verification && (
        <div className={`flex items-center justify-between p-4 rounded-xl border ${
          verification.is_valid
            ? "border-emerald-500/30 bg-emerald-500/10 text-emerald-400"
            : "border-red-500/30 bg-red-500/10 text-red-400"
        }`}>
          <div className="flex items-center gap-3">
            {verification.is_valid ? (
              <ShieldCheck className="h-5 w-5 shrink-0" />
            ) : (
              <AlertTriangle className="h-5 w-5 shrink-0" />
            )}
            <div>
              <span className="font-bold font-mono uppercase text-xs">
                {verification.is_valid ? "CRYPTOGRAPHIC INTEGRITY VERIFIED (UNBROKEN CHAIN)" : "TAMPERING DETECTED"}
              </span>
              <p className="text-xs text-text-secondary mt-0.5">
                {verification.total_records} records verified from genesis hash: <span className="font-mono">{truncateHash(verification.genesis_hash, 16)}</span>
              </p>
            </div>
          </div>
          <span className="font-mono text-xs px-2.5 py-1 rounded bg-surface-dark border border-surface-border text-text-primary">
            NFR-A2 COMPLIANT
          </span>
        </div>
      )}

      {/* Search Bar */}
      <div className="flex items-center justify-between gap-4">
        <div className="relative w-full sm:w-96">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-text-muted" />
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search action, actor, or hash..."
            className="w-full rounded-lg border border-surface-border bg-surface pl-9 pr-3 py-2 text-xs text-text-primary placeholder:text-text-muted focus:border-brand-primary focus:outline-none font-mono"
          />
        </div>
        <span className="text-xs font-mono text-text-muted">
          Showing: {filteredRecords.length} of {records.length} records
        </span>
      </div>

      {/* Audit Table & Record Detail */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        <div className={selectedRecord ? "lg:col-span-7" : "lg:col-span-12"}>
          <div className="overflow-hidden rounded-xl border border-surface-border bg-surface shadow-panel">
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs font-mono">
                <thead className="bg-surface-elevated border-b border-surface-border text-[11px] font-semibold uppercase text-text-muted">
                  <tr>
                    <th className="px-4 py-3">Seq</th>
                    <th className="px-4 py-3">Timestamp</th>
                    <th className="px-4 py-3">Action</th>
                    <th className="px-4 py-3">Actor</th>
                    <th className="px-4 py-3">Record SHA-256</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-surface-border text-[11px]">
                  {filteredRecords.length > 0 ? (
                    filteredRecords.map((rec) => {
                      const isSelected = selectedRecord?.record_id === rec.record_id;
                      return (
                        <tr
                          key={rec.record_id || rec.sequence_id}
                          onClick={() => setSelectedRecord(rec)}
                          className={`cursor-pointer transition-colors ${
                            isSelected
                              ? "bg-brand-primary/10 border-l-2 border-l-brand-primary"
                              : "hover:bg-surface-elevated/60"
                          }`}
                        >
                          <td className="px-4 py-3 font-bold text-brand-primary">{rec.sequence_id}</td>
                          <td className="px-4 py-3 text-text-muted">{formatDate(rec.timestamp)}</td>
                          <td className="px-4 py-3 text-text-primary font-bold">{rec.action}</td>
                          <td className="px-4 py-3 text-text-secondary">{rec.actor}</td>
                          <td className="px-4 py-3 text-text-muted">{truncateHash(rec.record_hash, 16)}</td>
                        </tr>
                      );
                    })
                  ) : (
                    <tr>
                      <td colSpan={5} className="p-8 text-center text-text-muted">
                        No audit records found matching query.
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>
        </div>

        {/* Record Detail Drawer */}
        {selectedRecord && (
          <div className="lg:col-span-5 flex flex-col rounded-xl border border-surface-border bg-surface p-5 shadow-panel font-mono text-xs">
            <div className="flex items-center justify-between pb-3 border-b border-surface-border">
              <div>
                <span className="text-[10px] uppercase text-brand-primary font-bold">Audit Block #{selectedRecord.sequence_id}</span>
                <h3 className="text-sm font-bold text-text-primary">{selectedRecord.action}</h3>
              </div>
              <button
                onClick={() => setSelectedRecord(null)}
                className="text-text-muted hover:text-text-primary text-xs"
              >
                ✕ Close
              </button>
            </div>

            <div className="mt-4 flex flex-col gap-3">
              <div>
                <span className="text-[10px] text-text-muted uppercase">Record ID</span>
                <p className="text-text-primary text-[11px] bg-surface-dark p-1.5 rounded border border-surface-border break-all">
                  {selectedRecord.record_id}
                </p>
              </div>

              <div>
                <span className="text-[10px] text-text-muted uppercase">Actor & Event Type</span>
                <p className="text-text-secondary text-[11px]">
                  {selectedRecord.actor} ({selectedRecord.event_type})
                </p>
              </div>

              <div>
                <span className="text-[10px] text-text-muted uppercase">Previous Hash Link</span>
                <p className="text-sky-400 text-[10px] bg-surface-dark p-1.5 rounded border border-surface-border break-all">
                  {selectedRecord.previous_hash}
                </p>
              </div>

              <div>
                <span className="text-[10px] text-text-muted uppercase">Current Record Hash</span>
                <p className="text-emerald-400 text-[10px] bg-surface-dark p-1.5 rounded border border-surface-border break-all">
                  {selectedRecord.record_hash}
                </p>
              </div>

              <div>
                <span className="text-[10px] text-text-muted uppercase">Scrubbed Payload Details</span>
                <div className="mt-1 p-2 rounded bg-surface-dark border border-surface-border text-[10px] text-text-secondary max-h-48 overflow-y-auto">
                  <pre>{JSON.stringify(selectedRecord.details, null, 2)}</pre>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default function AuditLogsPage() {
  return (
    <React.Suspense fallback={<div className="p-8 text-xs text-text-muted">Loading Audit Logs...</div>}>
      <AuditLogsContent />
    </React.Suspense>
  );
}
