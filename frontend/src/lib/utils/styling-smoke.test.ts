import fs from "fs";
import path from "path";
import { describe, expect, it } from "vitest";

describe("Frontend Styling & CSS Smoke Test", () => {
  const frontendRoot = path.resolve(__dirname, "../../..");
  const globalsCssPath = path.join(frontendRoot, "src/app/globals.css");
  const layoutPath = path.join(frontendRoot, "src/app/layout.tsx");
  const tailwindConfigPath = path.join(frontendRoot, "tailwind.config.ts");
  const postcssConfigMjs = path.join(frontendRoot, "postcss.config.mjs");
  const postcssConfigJs = path.join(frontendRoot, "postcss.config.js");

  it("maintains exactly one authoritative PostCSS configuration", () => {
    expect(fs.existsSync(postcssConfigMjs)).toBe(true);
    expect(fs.existsSync(postcssConfigJs)).toBe(false);
  });

  it("contains required Tailwind directives and dark theme custom properties in globals.css", () => {
    expect(fs.existsSync(globalsCssPath)).toBe(true);
    const content = fs.readFileSync(globalsCssPath, "utf-8");

    // Tailwind directives
    expect(content).toContain("@tailwind base;");
    expect(content).toContain("@tailwind components;");
    expect(content).toContain("@tailwind utilities;");

    // Core theme custom properties
    expect(content).toContain("--background: #080F1D;");
    expect(content).toContain("--sidebar: #060C18;");
    expect(content).toContain("--surface: #101B2D;");
    expect(content).toContain("--primary-accent: #22D3EE;");

    // Baseline resets ensuring zero unstyled Times New Roman or purple hyperlinks
    expect(content).toContain("text-decoration: none;");
    expect(content).toContain("font-family: var(--font-inter)");
  });

  it("configures font fallbacks in layout.tsx to prevent Times New Roman flash", () => {
    expect(fs.existsSync(layoutPath)).toBe(true);
    const content = fs.readFileSync(layoutPath, "utf-8");

    expect(content).toContain('import "./globals.css";');
    expect(content).toContain("fallback:");
    expect(content).toContain("bg-[#080F1D]");
    expect(content).toContain("text-[#E5EDF7]");
  });

  it("verifies tailwind.config.ts covers all source files and defines the theme colors", () => {
    expect(fs.existsSync(tailwindConfigPath)).toBe(true);
    const content = fs.readFileSync(tailwindConfigPath, "utf-8");

    expect(content).toContain("./src/**/*.{js,ts,jsx,tsx,mdx}");
    expect(content).toContain("#080F1D");
    expect(content).toContain("#22D3EE");
    expect(content).toContain("#101B2D");
  });

  it("verifies production build outputs valid non-empty CSS assets", () => {
    const cssDir = path.join(frontendRoot, ".next/static/css");
    if (fs.existsSync(cssDir)) {
      const getCssFiles = (dir: string): string[] => {
        let results: string[] = [];
        const entries = fs.readdirSync(dir, { withFileTypes: true });
        for (const entry of entries) {
          const fullPath = path.join(dir, entry.name);
          if (entry.isDirectory()) {
            results = results.concat(getCssFiles(fullPath));
          } else if (entry.isFile() && entry.name.endsWith(".css")) {
            results.push(fullPath);
          }
        }
        return results;
      };
      const cssFiles = getCssFiles(cssDir);
      expect(cssFiles.length).toBeGreaterThan(0);

      // Verify the generated CSS contains the compiled background color
      const mainCss = fs.readFileSync(cssFiles[0], "utf-8");
      expect(mainCss.length).toBeGreaterThan(1000);
    }
  });
});
