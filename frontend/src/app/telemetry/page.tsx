"use client";

import React, { useEffect, useState } from "react";
import { useSearchParams } from "next/navigation";
import {
  Activity,
  Radio,
  FileCode,
  Globe,
  ShieldCheck,
  ShieldAlert,
  Search,
  Filter,
  RefreshCw,
  Clock,
  Layers,
  AlertTriangle,
  Play,
  RotateCw,
} from "lucide-react";
import { api } from "@/lib/api/client";
import {
  SimulationEvent,
  SyntheticIOC,
  C2BeaconEvent,
  DNSSignallingEvent,
  DetectionCorrelationReport,
  CampaignExecutionRecord,
} from "@/types/api";
import { formatDate, formatDuration, formatPercent, getSeverityBadgeClass, getStatusBadgeClass } from "@/lib/utils/formatters";

type TelemetryTab = "events" | "iocs" | "c2_beacons" | "dns_queries" | "detection_results";

function TelemetryDetectionContent() {
  const searchParams = useSearchParams();
  const initialRunId = searchParams.get("run_id");

  const [activeTab, setActiveTab] = useState<TelemetryTab>("events");
  const [executions, setExecutions] = useState<CampaignExecutionRecord[]>([]);
  const [selectedRunId, setSelectedRunId] = useState<string>(initialRunId || "");
  const [loading, setLoading] = useState(true);
  const [correlating, setCorrelating] = useState(false);
  const [profile, setProfile] = useState<string>("FULL_COVERAGE");

  // Data states
  const [events, setEvents] = useState<SimulationEvent[]>([]);
  const [iocs, setIocs] = useState<SyntheticIOC[]>([]);
  const [c2Beacons, setC2Beacons] = useState<C2BeaconEvent[]>([]);
  const [dnsQueries, setDnsQueries] = useState<DNSSignallingEvent[]>([]);
  const [correlationReport, setCorrelationReport] = useState<DetectionCorrelationReport | null>(null);

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

  const fetchTelemetry = async (runId: string) => {
    if (!runId) return;
    try {
      setLoading(true);
      const [eventsRes, iocsRes, beaconsRes, dnsRes, corrRes] = await Promise.allSettled([
        api.getSimulationEvents(runId),
        api.getSyntheticIOCs(runId),
        api.getC2Beacons(runId),
        api.getDNSQueries(runId),
        api.getCorrelationReport(runId),
      ]);

      if (eventsRes.status === "fulfilled") setEvents(eventsRes.value);
      if (iocsRes.status === "fulfilled") setIocs(iocsRes.value);
      if (beaconsRes.status === "fulfilled") setC2Beacons(beaconsRes.value);
      if (dnsRes.status === "fulfilled") setDnsQueries(dnsRes.value);
      if (corrRes.status === "fulfilled") setCorrelationReport(corrRes.value);
      else setCorrelationReport(null);
    } catch {
      // Fallback
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchExecutions();
  }, []);

  useEffect(() => {
    if (selectedRunId) {
      fetchTelemetry(selectedRunId);
    }
  }, [selectedRunId]);

  const handleCorrelate = async () => {
    if (!selectedRunId) return;
    try {
      setCorrelating(true);
      const report = await api.correlateDetections(selectedRunId, profile);
      setCorrelationReport(report);
      setActiveTab("detection_results");
    } catch (err: any) {
      alert(`Correlation failed: ${err.message}`);
    } finally {
      setCorrelating(false);
    }
  };

  return (
    <div className="flex flex-col gap-6">
      {/* Top Header & Run Selector */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold text-text-primary">Telemetry & Detection Center</h2>
          <p className="text-xs text-text-muted">
            Ground-truth observability: simulation events, canary IOCs, benign C2 signalling, and detection metrics
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
                  {x.run_id} ({x.status})
                </option>
              ))}
            </select>
          </div>

          <button
            onClick={() => fetchTelemetry(selectedRunId)}
            disabled={loading}
            className="flex items-center gap-1 rounded-lg border border-surface-border bg-surface px-2.5 py-2 text-xs text-text-secondary hover:text-text-primary"
            title="Refresh Telemetry"
          >
            <RefreshCw className={`h-3.5 w-3.5 ${loading ? "animate-spin" : ""}`} />
          </button>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex items-center gap-1 border-b border-surface-border overflow-x-auto pb-px">
        {[
          { id: "events", label: `Simulation Events (${events.length})`, icon: Activity },
          { id: "iocs", label: `Synthetic IOCs (${iocs.length})`, icon: FileCode },
          { id: "c2_beacons", label: `HTTPS C2 Beacons (${c2Beacons.length})`, icon: Radio },
          { id: "dns_queries", label: `DNS Signalling (${dnsQueries.length})`, icon: Globe },
          { id: "detection_results", label: "Detection Correlation & MTTD", icon: ShieldCheck },
        ].map((tab) => {
          const Icon = tab.icon;
          const active = activeTab === tab.id;
          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id as TelemetryTab)}
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

      {/* Tab 1: Simulation Events */}
      {activeTab === "events" && (
        <div className="overflow-hidden rounded-xl border border-surface-border bg-surface shadow-panel">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-surface-elevated border-b border-surface-border text-[11px] font-semibold uppercase tracking-wider text-text-muted">
                <tr>
                  <th className="px-4 py-3">Timestamp</th>
                  <th className="px-4 py-3">Technique ID</th>
                  <th className="px-4 py-3">Tactic</th>
                  <th className="px-4 py-3">Emulated Action</th>
                  <th className="px-4 py-3">Target Resource</th>
                  <th className="px-4 py-3">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-surface-border font-mono text-[11px]">
                {events.length > 0 ? (
                  events.map((e, idx) => (
                    <tr key={e.event_id || idx} className="hover:bg-surface-elevated/50">
                      <td className="px-4 py-3 text-text-muted">{formatDate(e.timestamp)}</td>
                      <td className="px-4 py-3 text-brand-primary font-bold">{e.technique_id}</td>
                      <td className="px-4 py-3 text-text-secondary">{e.tactic}</td>
                      <td className="px-4 py-3 text-text-primary">{e.action}</td>
                      <td className="px-4 py-3 text-text-muted truncate max-w-xs">{e.target_resource}</td>
                      <td className="px-4 py-3">
                        {e.success ? (
                          <span className="text-emerald-400 font-semibold">SUCCESS</span>
                        ) : (
                          <span className="text-red-400 font-semibold">FAILED</span>
                        )}
                      </td>
                    </tr>
                  ))
                ) : (
                  <tr>
                    <td colSpan={6} className="p-8 text-center text-text-muted">
                      No simulation telemetry recorded for run {selectedRunId}.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Tab 2: Synthetic IOCs */}
      {activeTab === "iocs" && (
        <div className="overflow-hidden rounded-xl border border-surface-border bg-surface shadow-panel">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-surface-elevated border-b border-surface-border text-[11px] font-semibold uppercase tracking-wider text-text-muted">
                <tr>
                  <th className="px-4 py-3">IOC Type</th>
                  <th className="px-4 py-3">Indicator Value</th>
                  <th className="px-4 py-3">SHA-256 Digest</th>
                  <th className="px-4 py-3">Technique</th>
                  <th className="px-4 py-3">Generated At</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-surface-border font-mono text-[11px]">
                {iocs.length > 0 ? (
                  iocs.map((ioc, idx) => (
                    <tr key={ioc.ioc_id || idx} className="hover:bg-surface-elevated/50">
                      <td className="px-4 py-3">
                        <span className="px-2 py-0.5 rounded bg-surface-dark border border-brand-primary/30 text-brand-primary font-semibold text-[10px]">
                          {ioc.ioc_type}
                        </span>
                      </td>
                      <td className="px-4 py-3 text-text-primary break-all max-w-xs">{ioc.value}</td>
                      <td className="px-4 py-3 text-text-muted">{ioc.sha256_hash ? `${ioc.sha256_hash.slice(0, 16)}...` : "—"}</td>
                      <td className="px-4 py-3 text-brand-secondary font-bold">{ioc.technique_id}</td>
                      <td className="px-4 py-3 text-text-muted">{formatDate(ioc.generated_at)}</td>
                    </tr>
                  ))
                ) : (
                  <tr>
                    <td colSpan={5} className="p-8 text-center text-text-muted">
                      No synthetic IOCs recorded for run {selectedRunId}.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Tab 3: C2 Beacons */}
      {activeTab === "c2_beacons" && (
        <div className="overflow-hidden rounded-xl border border-surface-border bg-surface shadow-panel">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-surface-elevated border-b border-surface-border text-[11px] font-semibold uppercase tracking-wider text-text-muted">
                <tr>
                  <th className="px-4 py-3">Timestamp</th>
                  <th className="px-4 py-3">Destination URI</th>
                  <th className="px-4 py-3">Interval</th>
                  <th className="px-4 py-3">Applied Jitter</th>
                  <th className="px-4 py-3">Payload Token</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-surface-border font-mono text-[11px]">
                {c2Beacons.length > 0 ? (
                  c2Beacons.map((b, idx) => (
                    <tr key={b.beacon_id || idx} className="hover:bg-surface-elevated/50">
                      <td className="px-4 py-3 text-text-muted">{formatDate(b.timestamp)}</td>
                      <td className="px-4 py-3 text-text-primary font-bold">{b.destination_uri}</td>
                      <td className="px-4 py-3 text-text-secondary">{b.interval_seconds}s</td>
                      <td className="px-4 py-3 text-brand-secondary">{b.jitter_applied}%</td>
                      <td className="px-4 py-3 text-emerald-400 font-semibold">{b.payload_token}</td>
                    </tr>
                  ))
                ) : (
                  <tr>
                    <td colSpan={5} className="p-8 text-center text-text-muted">
                      No C2 beacons recorded for run {selectedRunId}.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Tab 4: DNS Queries */}
      {activeTab === "dns_queries" && (
        <div className="overflow-hidden rounded-xl border border-surface-border bg-surface shadow-panel">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-surface-elevated border-b border-surface-border text-[11px] font-semibold uppercase tracking-wider text-text-muted">
                <tr>
                  <th className="px-4 py-3">Timestamp</th>
                  <th className="px-4 py-3">Queried Domain</th>
                  <th className="px-4 py-3">Record Type</th>
                  <th className="px-4 py-3">Signal Marker</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-surface-border font-mono text-[11px]">
                {dnsQueries.length > 0 ? (
                  dnsQueries.map((q, idx) => (
                    <tr key={q.query_id || idx} className="hover:bg-surface-elevated/50">
                      <td className="px-4 py-3 text-text-muted">{formatDate(q.timestamp)}</td>
                      <td className="px-4 py-3 text-text-primary font-bold">{q.queried_domain}</td>
                      <td className="px-4 py-3 text-sky-400">{q.record_type}</td>
                      <td className="px-4 py-3 text-emerald-400">{q.signal_marker}</td>
                    </tr>
                  ))
                ) : (
                  <tr>
                    <td colSpan={4} className="p-8 text-center text-text-muted">
                      No DNS covert queries recorded for run {selectedRunId}.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Tab 5: Detection Correlation & MTTD */}
      {activeTab === "detection_results" && (
        <div className="flex flex-col gap-6">
          {/* Honest Provenance Banner */}
          <div className="flex items-center justify-between rounded-xl border border-amber-500/30 bg-amber-500/10 p-4">
            <div className="flex items-center gap-3">
              <AlertTriangle className="h-5 w-5 text-amber-400 shrink-0" />
              <div>
                <span className="font-bold text-amber-400 uppercase text-xs tracking-wider">
                  SYNTHETIC DETECTION RESULTS (Detection Stub Active)
                </span>
                <p className="text-xs text-text-secondary mt-0.5">
                  These telemetry correlation metrics originate from the deterministic offline detection stub. Live SIEM/EDR integrations (CrowdStrike Falcon, Splunk, Sentinel) require explicit production API credentials.
                </p>
              </div>
            </div>

            {/* Re-correlate controls */}
            <div className="flex items-center gap-2 shrink-0">
              <select
                value={profile}
                onChange={(e) => setProfile(e.target.value)}
                className="rounded-lg border border-surface-border bg-surface px-2.5 py-1.5 text-xs font-mono text-text-primary focus:outline-none"
              >
                <option value="FULL_COVERAGE">Profile: FULL_COVERAGE (100%)</option>
                <option value="PARTIAL_COVERAGE">Profile: PARTIAL_COVERAGE (70%)</option>
                <option value="HIGH_MISS_RATE">Profile: HIGH_MISS_RATE (30%)</option>
              </select>

              <button
                onClick={handleCorrelate}
                disabled={correlating}
                className="flex items-center gap-1.5 rounded-lg bg-brand-primary px-3 py-1.5 text-xs font-semibold text-sidebar hover:bg-brand-secondary transition-all disabled:opacity-50"
              >
                <Play className={`h-3 w-3 fill-current ${correlating ? "animate-spin" : ""}`} />
                <span>{correlating ? "Correlating..." : "Re-Correlate"}</span>
              </button>
            </div>
          </div>

          {/* Metric Cards */}
          {correlationReport && (
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="rounded-xl border border-surface-border bg-surface p-4">
                <span className="text-[11px] font-semibold uppercase text-text-muted">Detection Coverage</span>
                <p className="text-2xl font-bold font-mono text-emerald-400 mt-1">
                  {formatPercent(correlationReport.coverage_percentage)}
                </p>
                <span className="text-[10px] text-text-muted">
                  {correlationReport.detected_count} of {correlationReport.total_techniques} Techniques Detected
                </span>
              </div>

              <div className="rounded-xl border border-surface-border bg-surface p-4">
                <span className="text-[11px] font-semibold uppercase text-text-muted">Mean Time to Detect (MTTD)</span>
                <p className="text-2xl font-bold font-mono text-sky-400 mt-1">
                  {correlationReport.mean_time_to_detect_seconds !== null && correlationReport.mean_time_to_detect_seconds !== undefined
                    ? `${correlationReport.mean_time_to_detect_seconds.toFixed(2)}s`
                    : "—"}
                </p>
                <span className="text-[10px] text-text-muted">Average Defensive Latency</span>
              </div>

              <div className="rounded-xl border border-surface-border bg-surface p-4">
                <span className="text-[11px] font-semibold uppercase text-text-muted">Missed Detections</span>
                <p className="text-2xl font-bold font-mono text-red-400 mt-1">
                  {correlationReport.missed_count}
                </p>
                <span className="text-[10px] text-text-muted">Techniques Evaded Defense</span>
              </div>

              <div className="rounded-xl border border-surface-border bg-surface p-4">
                <span className="text-[11px] font-semibold uppercase text-text-muted">Partially Detected</span>
                <p className="text-2xl font-bold font-mono text-amber-400 mt-1">
                  {correlationReport.partially_detected_count}
                </p>
                <span className="text-[10px] text-text-muted">Partial IOC Footprints</span>
              </div>
            </div>
          )}

          {/* Correlated Techniques Table */}
          {correlationReport ? (
            <div className="overflow-hidden rounded-xl border border-surface-border bg-surface shadow-panel">
              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs">
                  <thead className="bg-surface-elevated border-b border-surface-border text-[11px] font-semibold uppercase tracking-wider text-text-muted">
                    <tr>
                      <th className="px-4 py-3">Technique ID</th>
                      <th className="px-4 py-3">Status</th>
                      <th className="px-4 py-3">Detection Latency</th>
                      <th className="px-4 py-3">IOC Coverage Ratio</th>
                      <th className="px-4 py-3">Alert Matches</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-surface-border font-mono text-[11px]">
                    {correlationReport.technique_results.map((tr) => (
                      <tr key={tr.technique_id} className="hover:bg-surface-elevated/50">
                        <td className="px-4 py-3 text-brand-primary font-bold">{tr.technique_id}</td>
                        <td className="px-4 py-3">
                          <span className={`px-2 py-0.5 rounded font-semibold ${getStatusBadgeClass(tr.status)}`}>
                            {tr.status}
                          </span>
                        </td>
                        <td className="px-4 py-3 text-sky-400">
                          {tr.detection_latency_seconds ? `${tr.detection_latency_seconds.toFixed(2)}s` : "—"}
                        </td>
                        <td className="px-4 py-3 text-text-primary">
                          {(tr.ioc_coverage_ratio * 100).toFixed(0)}%
                        </td>
                        <td className="px-4 py-3 text-text-muted">
                          {tr.matched_events?.length || 0} alerts matched
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          ) : (
            <div className="p-8 rounded-xl border border-surface-border text-center text-xs text-text-muted">
              No correlation report generated yet. Click Re-Correlate above.
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export default function TelemetryDetectionPage() {
  return (
    <React.Suspense fallback={<div className="p-8 text-xs text-text-muted">Loading Telemetry & Detection...</div>}>
      <TelemetryDetectionContent />
    </React.Suspense>
  );
}
