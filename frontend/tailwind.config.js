/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  darkMode: "class",
  theme: {
    extend: {
      colors: {
        background: "#FAF9F6",
        surface: {
          50: "#FFFFFF",
          100: "#F7F5F0",
          200: "#F0ECE1",
          300: "#E6DFD3",
        },
        base: {
          950: "#0D0D0D",
          900: "#1A1A1A",
          850: "#262626",
          800: "#333333",
          700: "#4D4D4D",
          600: "#666666",
        },
        accent: {
          400: "#3B82F6", // Cobalt lighter
          500: "#2563EB", // Cobalt Blue
          600: "#1D4ED8", // Cobalt darker
          coral: "#F26457", // Warm Coral
          purple: "#8B5CF6", // Lavender
        },
        mint: {
          400: "#4ADE80",
          500: "#22C55E",
        },
        amber: {
          400: "#FBBF24",
          500: "#F59E0B",
        },
      },
      fontFamily: {
        sans: ["Inter", "ui-sans-serif", "system-ui", "-apple-system", "sans-serif"],
        serif: ["'Playfair Display'", "ui-serif", "Georgia", "Cambria", "Times New Roman", "Times", "serif"],
        mono: ["JetBrains Mono", "ui-monospace", "monospace"],
      },
      backgroundImage: {
        'paper-texture': "url(\"data:image/svg+xml,%3Csvg width='100' height='100' viewBox='0 0 100 100' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='noise'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.8' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100' height='100' filter='url(%23noise)' opacity='0.04'/%3E%3C/svg%3E\")",
      },
      keyframes: {
        "fade-up": {
          "0%": { opacity: "0", transform: "translateY(15px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
        "fade-in": {
          "0%": { opacity: "0" },
          "100%": { opacity: "1" },
        },
        "breathe": {
          "0%, 100%": { transform: "scale(1)" },
          "50%": { transform: "scale(1.02) translateY(-2px)" },
        },
        "blink": {
          "0%, 96%, 98%": { transform: "scaleY(1)" },
          "97%": { transform: "scaleY(0.1)" },
        },
        "look-around": {
          "0%, 100%": { transform: "translateX(0)" },
          "25%": { transform: "translateX(-2px)" },
          "75%": { transform: "translateX(2px)" },
        }
      },
      animation: {
        "fade-up": "fade-up 0.6s cubic-bezier(0.16, 1, 0.3, 1) both",
        "fade-in": "fade-in 0.4s ease-out both",
        "breathe": "breathe 4s ease-in-out infinite",
        "blink": "blink 5s infinite",
        "look-around": "look-around 8s ease-in-out infinite",
      },
    },
  },
  plugins: [],
};
