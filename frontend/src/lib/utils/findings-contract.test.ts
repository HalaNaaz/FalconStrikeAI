import { describe, expect, it } from "vitest";
import { normalizeFinding, normalizeAnalyzeResponse } from "../api/client";
import { MisconfigurationFinding } from "@/types/api";

describe("Findings Data Contract & Regression Tests", () => {
  it("normalizes a raw backend finding that lacks target_node_id without throwing", () => {
    // Exact raw backend output from graph_misconfiguration_analyzer
    const rawBackendFinding = {
      finding_id: "FIND-A1B2C3D4",
      resource_id: "i-0abcd1234ef56789a",
      category: "PUBLIC_EXPOSURE",
      severity: "HIGH",
      explanation: "Compute instance 'web-app-prod' is directly exposed to the public internet.",
      evidence: { public_ip: "54.200.10.15", instance_id: "i-0abcd1234ef56789a" },
      remediation: "Place compute workloads inside private subnets.",
      source_provenance: "graph_misconfiguration_analyzer",
    };

    const normalized = normalizeFinding(rawBackendFinding);

    // Verify both naming conventions are populated
    expect(normalized.target_node_id).toBe("i-0abcd1234ef56789a");
    expect(normalized.resource_id).toBe("i-0abcd1234ef56789a");
    expect(normalized.description).toBe(
      "Compute instance 'web-app-prod' is directly exposed to the public internet."
    );
    expect(normalized.explanation).toBe(
      "Compute instance 'web-app-prod' is directly exposed to the public internet."
    );
    expect(normalized.rule_name).toBe("PUBLIC_EXPOSURE");
    expect(normalized.category).toBe("PUBLIC_EXPOSURE");
  });

  it("handles completely empty or incomplete findings safely with fallbacks", () => {
    const emptyFinding = {};
    const normalized = normalizeFinding(emptyFinding);

    expect(normalized.target_node_id).toBe("");
    expect(normalized.resource_id).toBe("");
    expect(normalized.description).toBe("Security exposure detected");
    expect(normalized.rule_name).toBe("WILDCARD_PERMISSIONS");
    expect(normalized.severity).toBe("MEDIUM");
    expect(normalized.evidence).toEqual({});
    expect(normalized.details).toEqual({});
  });

  it("prevents TypeError: Cannot read properties of undefined (reading 'includes') on line 109 scenario", () => {
    // Simulate array containing raw backend finding, null finding, and empty finding
    const rawList = [
      {
        finding_id: "FIND-01",
        resource_id: "i-0abcd1234ef56789a",
        category: "PUBLIC_EXPOSURE",
        severity: "HIGH",
        explanation: "EC2 instance public",
      },
      {
        finding_id: "FIND-02",
        resource_id: "arn:aws:iam::123:role/AdminRole",
        category: "WILDCARD_PERMISSIONS",
        severity: "CRITICAL",
        explanation: "Admin wildcard",
      },
      {
        finding_id: "FIND-03",
        // target_node_id is completely missing
        category: "PUBLIC_STORAGE",
        severity: "MEDIUM",
      },
    ];

    const normalizedResponse = normalizeAnalyzeResponse({
      total_findings: 3,
      findings: rawList,
    });

    expect(normalizedResponse.findings).toHaveLength(3);

    // Reproduce and verify line 109 logic does not throw and computes correctly
    const matchesAssetCategory = (f: MisconfigurationFinding, keywords: string[]): boolean => {
      const target = (f.target_node_id || f.resource_id || "").toLowerCase();
      const cat = (f.category || f.rule_name || "").toLowerCase();
      const desc = (f.description || f.explanation || "").toLowerCase();
      return keywords.some((kw) => target.includes(kw) || cat.includes(kw) || desc.includes(kw));
    };

    const computeAtRisk = normalizedResponse.findings.filter((f) =>
      matchesAssetCategory(f, ["instance", "ec2", "compute"])
    ).length;

    const identityAtRisk = normalizedResponse.findings.filter((f) =>
      matchesAssetCategory(f, ["iam", "role", "user", "policy", "privilege", "wildcard"])
    ).length;

    const dataAtRisk = normalizedResponse.findings.filter((f) =>
      matchesAssetCategory(f, ["s3", "bucket", "storage"])
    ).length;

    expect(computeAtRisk).toBe(1);
    expect(identityAtRisk).toBe(1);
    expect(dataAtRisk).toBe(1);

    // Verify uniqueAssetsAtRisk ignores empty strings
    const uniqueAssetsAtRisk = new Set(
      normalizedResponse.findings
        .map((f) => f.target_node_id || f.resource_id)
        .filter((id): id is string => typeof id === "string" && id.length > 0)
    ).size;

    expect(uniqueAssetsAtRisk).toBe(2);
  });
});

