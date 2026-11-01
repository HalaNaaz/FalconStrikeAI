export function formatDate(isoString?: string | null): string {
  if (!isoString) return "—";
  try {
    const d = new Date(isoString);
    if (isNaN(d.getTime())) return isoString;
    return d.toLocaleString("en-US", {
      month: "short",
      day: "numeric",
      year: "numeric",
      hour: "2-digit",
      minute: "2-digit",
      second: "2-digit",
      hour12: false,
    });
  } catch {
    return isoString;
  }
}

export function formatDuration(ms?: number | null): string {
  if (ms === undefined || ms === null) return "—";
  if (ms < 1000) return `${ms.toFixed(1)}ms`;
  const sec = ms / 1000;
  if (sec < 60) return `${sec.toFixed(2)}s`;
  const min = Math.floor(sec / 60);
  const remSec = (sec % 60).toFixed(1);
  return `${min}m ${remSec}s`;
}

export function formatLatency(sec?: number | null): string {
  if (sec === undefined || sec === null) return "—";
  return `${sec.toFixed(2)}s`;
}

export function formatPercent(ratio?: number | null): string {
  if (ratio === undefined || ratio === null) return "0.0%";
  return `${ratio.toFixed(1)}%`;
}

export function truncateHash(hash?: string | null, len = 12): string {
  if (!hash) return "—";
  if (hash.length <= len) return hash;
  return `${hash.slice(0, len)}...`;
}

export function getSeverityBadgeClass(severity: string): string {
  switch (severity?.toUpperCase()) {
    case "CRITICAL":
      return "bg-red-500/10 text-red-400 border border-red-500/30";
    case "HIGH":
      return "bg-amber-500/10 text-amber-400 border border-amber-500/30";
    case "MEDIUM":
      return "bg-sky-500/10 text-sky-400 border border-sky-500/30";
    case "LOW":
      return "bg-slate-500/10 text-slate-400 border border-slate-500/30";
    case "INFORMATIONAL":
    default:
      return "bg-cyan-500/10 text-cyan-400 border border-cyan-500/30";
  }
}

export function getStatusBadgeClass(status: string): string {
  switch (status?.toUpperCase()) {
    case "COMPLETED":
    case "DETECTED":
    case "HEALTHY":
    case "VALID":
      return "bg-emerald-500/10 text-emerald-400 border border-emerald-500/30";
    case "IN_PROGRESS":
    case "PENDING":
    case "PARTIALLY_DETECTED":
      return "bg-amber-500/10 text-amber-400 border border-amber-500/30";
    case "FAILED":
    case "MISSED":
    case "CANCELLED":
    case "INVALID":
      return "bg-red-500/10 text-red-400 border border-red-500/30";
    default:
      return "bg-slate-500/10 text-slate-400 border border-slate-500/30";
  }
}

