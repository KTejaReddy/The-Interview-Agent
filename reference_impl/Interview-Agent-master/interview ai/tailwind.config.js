/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        bg: {
          primary: "#08080F",
          secondary: "#0F0F1A",
          card: "#14142B",
          elevated: "#1C1C3A",
        },
        brand: {
          violet: "#7C3AED",
          "violet-light": "#9D6FEF",
          "violet-dark": "#5B21B6",
          cyan: "#06B6D4",
          "cyan-light": "#22D3EE",
          emerald: "#10B981",
          amber: "#F59E0B",
          rose: "#F43F5E",
        },
        ink: {
          primary: "#F1F5F9",
          secondary: "#94A3B8",
          muted: "#475569",
        },
      },
      fontFamily: {
        sans: ["Inter", "-apple-system", "BlinkMacSystemFont", "sans-serif"],
        display: ["'Space Grotesk'", "Inter", "-apple-system", "sans-serif"],
        mono: ["'JetBrains Mono'", "ui-monospace", "SFMono-Regular", "monospace"],
      },
      boxShadow: {
        violet: "0 0 40px rgba(124, 58, 237, 0.25)",
        card: "0 8px 32px rgba(0, 0, 0, 0.4)",
        glow: "0 0 20px rgba(124, 58, 237, 0.4)",
      },
      animation: {
        "fade-slide-up": "fadeSlideUp 0.35s ease forwards",
      },
      keyframes: {
        fadeSlideUp: {
          from: { opacity: 0, transform: "translateY(16px)" },
          to: { opacity: 1, transform: "translateY(0)" },
        },
      },
    },
  },
  plugins: [],
};
