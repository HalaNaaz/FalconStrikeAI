# Falcon Strike-AI — Permanent CSS Regression Root Cause Analysis & Prevention

**Document Version:** 1.0.0  
**Date:** 1 November 2026  
**Classification:** Frontend Architecture & Quality Assurance  
**PRD Traceability:** `FR-5.1`, `FR-5.2`, `NFR-Q1`  

---

## 1. Executive Summary

During testing and deployment, the Falcon Strike-AI dashboard experienced intermittent and recurring CSS failures where the frontend reverted to unstyled browser default HTML (white background, Times New Roman typography, blue/purple hyperlinks, missing sidebar, unstyled cards).

A deep forensic investigation across the build pipeline, runtime server processes, and CSS asset delivery mechanisms isolated the exact compound root cause. A permanent architectural fix has been implemented and validated by automated styling smoke tests.

---

## 2. Root Cause Analysis

The regression was caused by three interacting defects:

### 2.1 Competing PostCSS Configurations (`postcss.config.js` vs `postcss.config.mjs`)
- **Finding:** The `frontend/` directory contained both `postcss.config.js` (CommonJS `module.exports`) and `postcss.config.mjs` (ES Module `export default`).
- **Impact:** Next.js 14 and PostCSS loaders encountered non-deterministic resolution between the two configuration formats. Under certain rebuild triggers, PostCSS failed to invoke the Tailwind plugin, resulting in `@tailwind base; @tailwind components; @tailwind utilities;` being passed uncompiled or skipped.

### 2.2 Zombie Next.js Server Holding Port 3000
- **Finding:** A background Node.js process (PID 27872) from 5:39 PM remained active on the host machine, bound to TCP port 3000. It was trapped in an infinite error loop:
  ```html
  missing required error components, refreshing...
  <script>
    async function check() {
      const res = await fetch(location.href).catch(() => ({}))
      if (res.status === 200) location.reload()
      else setTimeout(check, 1000)
    }
  </script>
  ```
- **Impact:** When developers or operators started `npm run dev`, Next.js detected that port 3000 was occupied and automatically fell back to port 3001 (`⚠ Port 3000 is in use, trying 3001 instead`). Any browser session pointing to `http://localhost:3000` continued to receive the broken, unstyled error response from the zombie process.

### 2.3 Fragile Font Loading Without Native System Fallbacks
- **Finding:** In `frontend/src/app/globals.css`, `body` specified `font-family: var(--font-inter);` without fallback fonts. In `frontend/src/app/layout.tsx`, `Inter` and `JetBrains_Mono` did not configure fallback font families.
- **Impact:** If `next/font/google` failed to download woff2 fonts from Google CDN (e.g. offline environments, firewalled proxies, or initial cold boot), the CSS variable `--font-inter` remained unpopulated, causing the browser to fall back directly to the OS default serif font (**Times New Roman**). Furthermore, absence of baseline CSS resets caused links to render in default browser purple/blue styling.

---

## 3. Permanent Fix Implemented

| Remediation Step | File Changed | Description |
| :--- | :--- | :--- |
| **1. Remove Conflicting PostCSS Config** | `frontend/postcss.config.js` | Removed duplicate CommonJS configuration, retaining the authoritative `frontend/postcss.config.mjs`. |
| **2. Robust Font & Baseline Fallbacks** | `frontend/src/app/globals.css` | Added `font-family: var(--font-inter), 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;` to `body`. Added baseline resets for `a`, `button`, `input` ensuring dark theme inheritance even before utility classes mount. |
| **3. Font Metric Fallbacks in Layout** | `frontend/src/app/layout.tsx` | Added `fallback: ["system-ui", "-apple-system", ...]` to `Inter` and monospace fallbacks to `JetBrains_Mono`. |
| **4. Process Termination** | Host Environment | Force-terminated zombie process 27872, restoring port 3000 to clean, unblocked availability. |
| **5. Automated Styling Smoke Tests** | `frontend/src/lib/utils/styling-smoke.test.ts` | 5 automated Vitest smoke tests verifying single PostCSS config, Tailwind directives, dark theme variables, font fallbacks, and production CSS asset generation. |

---

## 4. Verification & Smoke Test Evidence

Automated Vitest smoke tests (`frontend/src/lib/utils/styling-smoke.test.ts`) executed:
```
 ✓ src/lib/utils/styling-smoke.test.ts (5 tests) 6ms
   ✓ maintains exactly one authoritative PostCSS configuration
   ✓ contains required Tailwind directives and dark theme custom properties in globals.css
   ✓ configures font fallbacks in layout.tsx to prevent Times New Roman flash
   ✓ verifies tailwind.config.ts covers all source files and defines the theme colors
   ✓ verifies production build outputs valid non-empty CSS assets

 Test Files  4 passed (4)
      Tests  17 passed (17)
```

Production build verification:
- **Build Status:** Exit code 0
- **Static Pages Generated:** 14/14
- **CSS Bundles Produced:** `d9a948f68cc327d9.css` (34.5 KB), `322e14d06135256b.css` (15.7 KB)
- **HTML Links:** All routes include `<link rel="stylesheet" href="/_next/static/css/...">`

