/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  darkMode: "class",
  theme: {
    extend: {
      colors: {
        background: "#07090f",
        surface: {
          50:  "#0a0d16",
          100: "#10141f",
          200: "#161c2a",
          300: "#1d2435",
          400: "#252d42",
        },
        base: {
          950: "#04050a",
          900: "#07090f",
          800: "#0e1120",
          700: "#161b30",
          600: "#1f2844",
          500: "#374151",
          400: "#6b7280",
          300: "#9ca3af",
          200: "#d1d5db",
        },
        // Primary accent — indigo/violet
        accent: {
          400: "#818cf8",
          500: "#6366f1",
          600: "#4f46e5",
          700: "#4338ca",
          purple: "#a78bfa",
          cyan: "#22d3ee",
        },
        // Extended palette for candidate identities
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
        mono:  ["JetBrains Mono", "ui-monospace", "SFMono-Regular", "monospace"],
      },
      backgroundImage: {
        "premium-gradient": "linear-gradient(135deg, #4f46e5 0%, #a78bfa 100%)",
        "glass-gradient":   "linear-gradient(180deg, rgba(255,255,255,0.05) 0%, rgba(255,255,255,0.01) 100%)",
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
      },
    },
  },
  plugins: [],
};
