import { describe, expect, it } from "vitest";
import {
  formatDate,
  formatDuration,
  formatLatency,
  formatPercent,
  getSeverityBadgeClass,
  getStatusBadgeClass,
  truncateHash,
} from "./formatters";

describe("Frontend Formatters", () => {
  it("formats dates gracefully with fallback on null/empty", () => {
    expect(formatDate(null)).toBe("—");
    expect(formatDate("")).toBe("—");
    expect(formatDate("invalid-date-string")).toBe("invalid-date-string");
    const valid = formatDate("2026-11-01T12:00:00Z");
    expect(valid).toContain("2026");
  });

  it("formats durations in ms and seconds", () => {
    expect(formatDuration(null)).toBe("—");
    expect(formatDuration(250)).toBe("250.0ms");
    expect(formatDuration(1500)).toBe("1.50s");
    expect(formatDuration(65000)).toBe("1m 5.0s");
  });

  it("formats latencies in seconds", () => {
    expect(formatLatency(null)).toBe("—");
    expect(formatLatency(12.345)).toBe("12.35s");
  });

  it("formats percentages with 1 decimal", () => {
    expect(formatPercent(null)).toBe("0.0%");
    expect(formatPercent(87.654)).toBe("87.7%");
  });

  it("truncates hashes with ellipsis", () => {
    expect(truncateHash(null)).toBe("—");
    expect(truncateHash("short")).toBe("short");
    expect(truncateHash("a1b2c3d4e5f6g7h8", 8)).toBe("a1b2c3d4...");
  });

  it("returns appropriate badge classes for severity", () => {
    expect(getSeverityBadgeClass("CRITICAL")).toContain("text-red-400");
    expect(getSeverityBadgeClass("HIGH")).toContain("text-amber-400");
    expect(getSeverityBadgeClass("MEDIUM")).toContain("text-sky-400");
    expect(getSeverityBadgeClass("LOW")).toContain("text-slate-400");
    expect(getSeverityBadgeClass("INFORMATIONAL")).toContain("text-cyan-400");
  });

  it("returns appropriate badge classes for execution/detection status", () => {
    expect(getStatusBadgeClass("COMPLETED")).toContain("text-emerald-400");
    expect(getStatusBadgeClass("DETECTED")).toContain("text-emerald-400");
    expect(getStatusBadgeClass("FAILED")).toContain("text-red-400");
    expect(getStatusBadgeClass("MISSED")).toContain("text-red-400");
    expect(getStatusBadgeClass("PENDING")).toContain("text-amber-400");
  });
});

