import type { Config } from "tailwindcss";

/**
 * Tokens de marca ColAdventure.
 * - brand: azul océano/cielo — confianza + agua/cielo (rafting, parapente, mar).
 * - accent: naranja atardecer — energía/aventura (complementario del azul).
 * Semánticos (success/warning/danger) y neutros se apoyan en slate de Tailwind.
 */
const config: Config = {
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        brand: {
          50: "#ECF5FF",
          100: "#D5E9FF",
          200: "#AED4FF",
          300: "#7BB8FF",
          400: "#4593F5",
          500: "#1E72E6",
          600: "#1359C4",
          700: "#11479B",
          800: "#133D7C",
          900: "#0E2A52",
        },
        accent: {
          50: "#FFF6ED",
          100: "#FFE9D5",
          400: "#FB923C",
          500: "#F97316",
          600: "#EA580C",
        },
      },
      fontFamily: {
        sans: ["var(--font-inter)", "ui-sans-serif", "system-ui", "sans-serif"],
      },
      borderRadius: {
        xl: "0.875rem",
        "2xl": "1.25rem",
        "3xl": "1.75rem",
      },
      boxShadow: {
        card: "0 1px 2px rgba(14, 42, 82, 0.05), 0 8px 24px -12px rgba(14, 42, 82, 0.14)",
        "card-hover":
          "0 2px 4px rgba(14, 42, 82, 0.07), 0 18px 44px -16px rgba(14, 42, 82, 0.24)",
        glow: "0 10px 30px -8px rgba(30, 114, 230, 0.45)",
      },
      backgroundImage: {
        "brand-gradient":
          "linear-gradient(135deg, #0E2A52 0%, #1359C4 45%, #1E72E6 70%, #38BDF8 100%)",
      },
      keyframes: {
        "fade-up": {
          "0%": { opacity: "0", transform: "translateY(8px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
      },
      animation: {
        "fade-up": "fade-up 0.5s ease-out both",
      },
    },
  },
  plugins: [],
};

export default config;
