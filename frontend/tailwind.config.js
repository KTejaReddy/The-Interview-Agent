/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  darkMode: "class",
  theme: {
    extend: {
      colors: {
        background: "#080B14",
        surface: {
          50: "#0B0E1A",
          100: "#141823",
          200: "#1C2130",
          300: "#252B3D",
        },
        base: {
          950: "#05050A",
          900: "#080B14",
          850: "#0e1124",
          800: "#12162e",
          700: "#1a1f3d",
          600: "#232a4f",
          500: "#4b5563",
          400: "#9ca3af",
          300: "#d1d5db",
        },
        accent: {
          400: "#818cf8",
          500: "#6366f1",
          600: "#4f46e5",
          purple: "#A07CFE",
          cyan: "#00F0FF",
        },
        mint: {
          400: "#34d399",
          500: "#10b981",
        },
        amber: {
          400: "#fbbf24",
          500: "#F59E0B",
        },
      },
      fontFamily: {
        sans: ["Inter", "ui-sans-serif", "system-ui", "-apple-system", "Segoe UI", "sans-serif"],
        serif: ["Playfair Display", "ui-serif", "Georgia", "Cambria", "Times New Roman", "Times", "serif"],
        mono: ["JetBrains Mono", "ui-monospace", "SFMono-Regular", "monospace"],
      },
      backgroundImage: {
        'premium-gradient': 'linear-gradient(135deg, #4f46e5 0%, #A07CFE 100%)',
        'glass-gradient': 'linear-gradient(180deg, rgba(255, 255, 255, 0.05) 0%, rgba(255, 255, 255, 0.01) 100%)',
      },
      keyframes: {
        "fade-up": {
          "0%": { opacity: "0", transform: "translateY(10px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
        "fade-in": {
          "0%": { opacity: "0" },
          "100%": { opacity: "1" },
        },
        "breathe": {
          "0%, 100%": { transform: "translateY(0)" },
          "50%": { transform: "translateY(-1px)" },
        },
        "blink": {
          "0%, 96%, 98%": { transform: "scaleY(1)" },
          "97%": { transform: "scaleY(0.1)" },
        }
      },
      animation: {
        "fade-up": "fade-up 0.4s cubic-bezier(0.16, 1, 0.3, 1) both",
        "fade-in": "fade-in 0.3s ease-out both",
        "breathe": "breathe 4s ease-in-out infinite",
        "blink": "blink 5s infinite",
      },
    },
  },
  plugins: [],
};
