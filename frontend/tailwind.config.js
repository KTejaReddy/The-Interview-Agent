/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  darkMode: "class",
  theme: {
    extend: {
      colors: {
        background: "#070a12",
        // Ink — the base surface system (deep navy-black)
        ink: {
          950: "#04060b",
          900: "#070a12",
          850: "#0a0e18",
          800: "#0e1420",
          700: "#151c2a",
          600: "#1d2536",
          500: "#273149",
        },
        // Warm ivory — editorial typography accents
        ivory: {
          50:  "#fbf9f4",
          100: "#f5f2ea",
          200: "#eae4d6",
          300: "#dcd3bf",
          400: "#c4b99f",
        },
        surface: {
          50:  "#0a0e18",
          100: "#0e1420",
          200: "#151c2a",
          300: "#1d2536",
          400: "#273149",
          800: "#101624",
        },
        base: {
          950: "#04060b",
          900: "#0b0f1a",
          800: "#101624",
          700: "#1a2233",
          600: "#2a3547",
          500: "#475569",
          400: "#64748b",
          300: "#94a3b8",
          200: "#cbd5e1",
        },
        // Primary accent — electric violet (identity color)
        accent: {
          300: "#b3a6ff",
          400: "#9d8cff",
          500: "#7c5cff",
          600: "#6a4bf0",
          700: "#5a3de0",
          purple: "#a78bfa",
          cyan: "#22d3ee",
        },
        // Extended palette for candidate identities (kept in sync with the
        // inline palette system used by the candidate cards)
        cyan:    { 300:"#67e8f9", 400:"#22d3ee", 500:"#06b6d4", 600:"#0891b2" },
        teal:    { 300:"#5eead4", 400:"#2dd4bf", 500:"#14b8a6", 600:"#0d9488" },
        emerald: { 300:"#6ee7b7", 400:"#34d399", 500:"#10b981", 600:"#059669" },
        mint:    { 400:"#34d399",  500:"#10b981" },
        lime:    { 300:"#bef264", 400:"#a3e635", 500:"#84cc16" },
        amber:   { 300:"#fcd34d", 400:"#fbbf24", 500:"#f59e0b", 600:"#d97706" },
        orange:  { 400:"#fb923c", 500:"#f97316", 600:"#ea580c" },
        coral:   { 400:"#fb7185", 500:"#f43f5e", 600:"#e11d48" },
        rose:    { 300:"#fda4af", 400:"#fb7185", 500:"#f43f5e" },
        pink:    { 300:"#f9a8d4", 400:"#f472b6", 500:"#ec4899" },
        violet:  { 300:"#c4b5fd", 400:"#a78bfa", 500:"#8b5cf6", 600:"#7c3aed" },
        indigo:  { 300:"#a5b4fc", 400:"#818cf8", 500:"#6366f1", 600:"#4f46e5" },
        sky:     { 300:"#7dd3fc", 400:"#38bdf8", 500:"#0ea5e9" },
        gold:    { 400:"#fde68a", 500:"#fcd34d", 600:"#fbbf24" },
        magenta: { 400:"#e879f9", 500:"#d946ef", 600:"#c026d3" },
      },
      fontFamily: {
        sans:  ["Inter", "ui-sans-serif", "system-ui", "-apple-system", "Segoe UI", "sans-serif"],
        serif: ["Playfair Display", "ui-serif", "Georgia", "Cambria", "Times New Roman", "serif"],
        mono:  ["ui-monospace", "SFMono-Regular", "Menlo", "Consolas", "monospace"],
      },
      backgroundImage: {
        "premium-gradient": "linear-gradient(135deg, #7c5cff 0%, #6366f1 45%, #22d3ee 100%)",
        "glass-gradient":   "linear-gradient(180deg, rgba(255,255,255,0.08) 0%, rgba(255,255,255,0.02) 100%)",
        "card-gradient":    "linear-gradient(160deg, rgba(14, 20, 32, 0.9) 0%, rgba(8, 11, 20, 0.95) 100%)",
        "ivory-text":       "linear-gradient(135deg, #f5f2ea 0%, #eae4d6 55%, #c4b99f 100%)",
      },
      boxShadow: {
        'glow-accent': '0 0 25px -5px rgba(124, 92, 255, 0.45), 0 0 10px -2px rgba(124, 92, 255, 0.2)',
        'glow-magenta': '0 0 25px -5px rgba(217, 70, 239, 0.4), 0 0 10px -2px rgba(217, 70, 239, 0.2)',
        'glow-cyan': '0 0 25px -5px rgba(34, 211, 238, 0.4), 0 0 10px -2px rgba(34, 211, 238, 0.2)',
        'level-1': '0 1px 2px rgba(0,0,0,0.3), 0 2px 8px -2px rgba(0,0,0,0.35)',
        'level-2': '0 4px 16px -4px rgba(0,0,0,0.45), 0 12px 32px -12px rgba(0,0,0,0.5)',
        'level-3': '0 16px 40px -12px rgba(0,0,0,0.6), 0 32px 64px -20px rgba(0,0,0,0.65)',
      },
      keyframes: {
        "fade-up": {
          "0%":   { opacity: "0", transform: "translateY(14px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
        "fade-in": {
          "0%":   { opacity: "0" },
          "100%": { opacity: "1" },
        },
        "slide-in-right": {
          "0%":   { opacity: "0", transform: "translateX(40px)" },
          "100%": { opacity: "1", transform: "translateX(0)" },
        },
        "scale-in": {
          "0%":   { opacity: "0", transform: "scale(0.94)" },
          "100%": { opacity: "1", transform: "scale(1)" },
        },
        "breathe": {
          "0%, 100%": { transform: "translateY(0px)" },
          "50%":      { transform: "translateY(-3px)" },
        },
        "float": {
          "0%, 100%": { transform: "translateY(0px) rotate(0deg)" },
          "33%":      { transform: "translateY(-4px) rotate(0.5deg)" },
          "66%":      { transform: "translateY(-2px) rotate(-0.5deg)" },
        },
        "progress-fill": {
          "0%":   { width: "0%" },
          "100%": { width: "var(--progress-width)" },
        },
        "orb-drift": {
          "0%, 100%": { transform: "translate(0, 0) scale(1)" },
          "33%":      { transform: "translate(30px, -20px) scale(1.05)" },
          "66%":      { transform: "translate(-20px, 15px) scale(0.98)" },
        },
        "node-pulse": {
          "0%, 100%": { opacity: "1", transform: "scale(1)" },
          "50%":      { opacity: "0.6", transform: "scale(1.2)" },
        },
        "indicator-slide": {
          "0%":   { transform: "scaleX(0)", opacity: "0" },
          "100%": { transform: "scaleX(1)", opacity: "1" },
        },
        "pulse-dot": {
          "0%, 100%": { opacity: "0.25", transform: "scale(0.85)" },
          "50%":      { opacity: "1",    transform: "scale(1)" },
        },
        "shimmer": {
          "0%":   { backgroundPosition: "-600px 0" },
          "100%": { backgroundPosition: "600px 0" },
        },
        "aurora": {
          "0%, 100%": { transform: "translate(0,0) scale(1) rotate(0deg)", opacity: "0.5" },
          "33%":      { transform: "translate(4%, -6%) scale(1.08) rotate(3deg)", opacity: "0.7" },
          "66%":      { transform: "translate(-4%, 5%) scale(0.96) rotate(-3deg)", opacity: "0.55" },
        },
        "spin-slow": {
          "0%":   { transform: "rotate(0deg)" },
          "100%": { transform: "rotate(360deg)" },
        },
      },
      animation: {
        "fade-up":         "fade-up 0.5s cubic-bezier(0.22, 1, 0.36, 1) both",
        "fade-in":         "fade-in 0.4s ease-out both",
        "slide-in-right":  "slide-in-right 0.4s cubic-bezier(0.22, 1, 0.36, 1) both",
        "scale-in":        "scale-in 0.4s cubic-bezier(0.22, 1, 0.36, 1) both",
        "breathe":         "breathe 5s ease-in-out infinite",
        "float":           "float 7s ease-in-out infinite",
        "orb-drift":       "orb-drift 20s ease-in-out infinite",
        "node-pulse":      "node-pulse 2s ease-in-out infinite",
        "indicator-slide": "indicator-slide 0.3s ease-out both",
        "pulse-dot":       "pulse-dot 1.2s ease-in-out infinite",
        "shimmer":         "shimmer 1.6s linear infinite",
        "aurora":          "aurora 26s ease-in-out infinite",
        "spin-slow":       "spin-slow 14s linear infinite",
      },
    },
  },
  plugins: [],
};
