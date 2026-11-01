import type { Config } from "tailwindcss";

const config: Config = {
  darkMode: "class",
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        background: "#080F1D",
        sidebar: "#060C18",
        surface: {
          DEFAULT: "#101B2D",
          elevated: "#152238",
          dark: "#0C1424",
          border: "#24344A",
          borderHover: "#334764",
        },
        brand: {
          primary: "#22D3EE",
          secondary: "#38BDF8",
          glow: "rgba(34, 211, 238, 0.15)",
        },
        status: {
          success: "#22C55E",
          warning: "#F59E0B",
          critical: "#EF4444",
          info: "#38BDF8",
          neutral: "#94A3B8",
        },
        text: {
          primary: "#E5EDF7",
          secondary: "#94A3B8",
          muted: "#64748B",
        },
      },
      fontFamily: {
        sans: ["var(--font-inter)", "Inter", "-apple-system", "BlinkMacSystemFont", "Segoe UI", "Roboto", "sans-serif"],
        mono: ["var(--font-mono)", "JetBrains Mono", "Menlo", "Monaco", "Consolas", "Courier New", "monospace"],
      },
      boxShadow: {
        "cyan-glow": "0 0 20px -3px rgba(34, 211, 238, 0.25)",
        "red-glow": "0 0 20px -3px rgba(239, 68, 68, 0.25)",
        "panel": "0 4px 20px -2px rgba(0, 0, 0, 0.4)",
      },
      keyframes: {
        pulseGlow: {
          "0%, 100%": { opacity: "1", transform: "scale(1)" },
          "50%": { opacity: "0.7", transform: "scale(1.05)" },
        },
        radarSweep: {
          "0%": { transform: "rotate(0deg)" },
          "100%": { transform: "rotate(360deg)" },
        },
      },
      animation: {
        "pulse-glow": "pulseGlow 3s ease-in-out infinite",
        "radar-sweep": "radarSweep 8s linear infinite",
      },
    },
  },
  plugins: [],
};

export default config;
