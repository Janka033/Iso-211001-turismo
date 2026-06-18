import type { Config } from "tailwindcss";

/**
 * Tokens de marca ColAdventure.
 * - brand: verde-teal "pino" — confianza + naturaleza/aventura.
 * - accent: ámbar "atardecer" — energía/acento.
 * Semánticos (success/warning/danger) y neutros se apoyan en slate de Tailwind.
 */
const config: Config = {
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        brand: {
          50: "#EAF7F2",
          100: "#CDEBE0",
          200: "#9FD8C4",
          300: "#6BC1A2",
          400: "#38A37E",
          500: "#138A66",
          600: "#0E6E52",
          700: "#0B5742",
          800: "#094636",
          900: "#07382C",
        },
        accent: {
          50: "#FFF7ED",
          400: "#FBBF24",
          500: "#F59E0B",
          600: "#D97706",
        },
      },
      fontFamily: {
        sans: ["var(--font-inter)", "ui-sans-serif", "system-ui", "sans-serif"],
      },
      borderRadius: {
        xl: "0.875rem",
        "2xl": "1.25rem",
      },
      boxShadow: {
        card: "0 1px 2px rgba(7, 56, 44, 0.04), 0 8px 24px -12px rgba(7, 56, 44, 0.12)",
        "card-hover":
          "0 2px 4px rgba(7, 56, 44, 0.06), 0 16px 40px -16px rgba(7, 56, 44, 0.20)",
      },
      backgroundImage: {
        "brand-gradient": "linear-gradient(135deg, #0B5742 0%, #138A66 60%, #38A37E 100%)",
      },
    },
  },
  plugins: [],
};

export default config;
