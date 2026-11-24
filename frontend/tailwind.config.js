/** @type {import('tailwindcss').Config} */
// RetainIQ Enterprise Design System Tokens
// Unslopped using methodology from unslop by Damir Sokolovsky (@heydamir), CC BY 4.0
export default {
  darkMode: "class",
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // Ink & Slate Neutral Ramp
        midnight: {
          DEFAULT: "var(--color-midnight)",
          50: "var(--color-midnight-50)",
          100: "var(--color-midnight-100)",
          900: "var(--color-midnight-900)",
        },
        navy: {
          DEFAULT: "#1E293B",
          light: "#334155",
          dark: "#0F172A",
        },
        // Operational Precision Accent (Cobalt in Light, Vibrant Blue in Dark)
        electric: {
          DEFAULT: "var(--color-electric)",
          light: "var(--color-electric-light)",
          dark: "var(--color-electric-dark)",
          subtle: "var(--color-electric-subtle)",
        },
        // Muted Technical Cyan (Telemetry & Status Dots)
        cyan: {
          DEFAULT: "#0284C7",
          light: "#38BDF8",
          dark: "#0369A1",
        },
        // Functional Surfaces & Backgrounds
        bg: {
          DEFAULT: "var(--color-bg)",
          alt: "var(--color-bg-alt)",
          subtle: "var(--color-bg-subtle)",
        },
        surface: {
          DEFAULT: "var(--color-surface)",
          muted: "var(--color-surface-muted)",
          card: "var(--color-surface-card)",
          raised: "var(--color-surface-raised)",
          hover: "var(--color-surface-hover)",
        },
        // Text Roles
        text: {
          primary: "var(--color-text-primary)",
          secondary: "var(--color-text-secondary)",
          muted: "var(--color-text-muted)",
          inverse: "var(--color-text-inverse)",
        },
        // Borders & Hairlines
        border: {
          DEFAULT: "var(--color-border)",
          light: "var(--color-border-light)",
          dark: "var(--color-border-dark)",
          hairline: "var(--color-border-hairline)",
        },
        // Semantic Risk & Account Status
        success: {
          DEFAULT: "var(--color-success)",
          light: "var(--color-success-light)",
          dark: "var(--color-success-dark)",
          border: "var(--color-success-border)",
        },
        warning: {
          DEFAULT: "var(--color-warning)",
          light: "var(--color-warning-light)",
          dark: "var(--color-warning-dark)",
          border: "var(--color-warning-border)",
        },
        danger: {
          DEFAULT: "var(--color-danger)",
          light: "var(--color-danger-light)",
          dark: "var(--color-danger-dark)",
          border: "var(--color-danger-border)",
        },
        info: {
          DEFAULT: "var(--color-info)",
          light: "var(--color-info-light)",
          dark: "var(--color-info-dark)",
          border: "var(--color-info-border)",
        },
      },
      fontFamily: {
        heading: ["Sora", "Plus Jakarta Sans", "sans-serif"],
        body: ["Inter", "-apple-system", "BlinkMacSystemFont", "sans-serif"],
        sans: ["Inter", "-apple-system", "BlinkMacSystemFont", "sans-serif"],
        mono: ["JetBrains Mono", "Fira Code", "monospace"],
      },
      fontSize: {
        "display-2xl": ["3.75rem", { lineHeight: "1.1", letterSpacing: "-0.025em" }],
        "display-xl": ["3rem", { lineHeight: "1.12", letterSpacing: "-0.02em" }],
        "display-lg": ["2.25rem", { lineHeight: "1.15", letterSpacing: "-0.015em" }],
        "display-md": ["1.875rem", { lineHeight: "1.2", letterSpacing: "-0.01em" }],
        "display-sm": ["1.5rem", { lineHeight: "1.25", letterSpacing: "-0.005em" }],
      },
      boxShadow: {
        subtle: "0 1px 2px 0 rgba(15, 23, 42, 0.04)",
        card: "0 1px 3px 0 rgba(15, 23, 42, 0.05), 0 1px 2px -1px rgba(15, 23, 42, 0.04)",
        elevated: "0 8px 24px -4px rgba(15, 23, 42, 0.08)",
      },
      borderRadius: {
        "2xl": "1rem", // 16px - Dialogs, panels
        xl: "0.75rem", // 12px - Cards, table wrappers
        lg: "0.5rem", // 8px - Inputs, buttons, rows
        md: "0.375rem", // 6px - Badges, chips
        sm: "0.25rem", // 4px - Keycaps, tags
      },
      transitionTimingFunction: {
        smooth: "cubic-bezier(0.22, 1, 0.36, 1)",
      },
    },
  },
  plugins: [],
};
