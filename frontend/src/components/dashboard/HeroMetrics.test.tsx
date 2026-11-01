import React from "react";
import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { HeroMetrics } from "./HeroMetrics";

describe("HeroMetrics Component", () => {
  it("renders with default metrics successfully", () => {
    render(<HeroMetrics />);
    expect(screen.getByText("Active Environment Risk Posture")).toBeInTheDocument();
    expect(screen.getByText(/\/ 13/)).toBeInTheDocument();
    expect(screen.getByText("Compute (EC2)")).toBeInTheDocument();
    expect(screen.getByText("Identity (IAM)")).toBeInTheDocument();
    expect(screen.getByText("Network (SG)")).toBeInTheDocument();
    expect(screen.getByText("Storage (S3)")).toBeInTheDocument();
  });

  it("renders custom metric counts passed via props", () => {
    render(
      <HeroMetrics
        totalAssets={42}
        assetsAtRiskCount={12}
        computeCount={10}
        computeAtRisk={4}
      />
    );
    expect(screen.getByText(/\/ 42/)).toBeInTheDocument();
    expect(screen.getByText("Compute (EC2)")).toBeInTheDocument();
  });
});
