import type { Config } from "tailwindcss";

/**
 * Tokens de marca ColAdventure — "El expediente de la selva".
 * - brand: verdes de selva y río (ancla oscura selva-negro → esmeralda de río).
 *   El verde es el territorio real del turismo de aventura colombiano.
 * - accent: amarillo señal — el amarillo de cascos, kayaks y señalización de
 *   seguridad. SIEMPRE con texto oscuro (brand-950); nunca texto blanco.
 * - papel/tinta: el mundo documento (fondos claros de la landing).
 * - flag: coral de [PENDIENTE] — solo funcional, nunca decorativo.
 */
const config: Config = {
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        brand: {
          50: "#EDF7F1",
          100: "#D7EDDF",
          200: "#AEDCC4",
          300: "#79C4A2",
          400: "#3FA37D",
          500: "#1E8663",
          600: "#136B4F",
          700: "#10523D",
          800: "#0D3E30",
          900: "#0B2A21",
          950: "#071B15",
        },
        accent: {
          50: "#FFF8E4",
          100: "#FFEDBD",
          200: "#FFDF8A",
          300: "#FFD05C",
          400: "#FFC53D",
          500: "#F5B31C",
          600: "#D89A0D",
          700: "#A97508",
        },
        papel: "#FBF9F4",
        tinta: "#16211B",
        flag: {
          100: "#FCE4DB",
          500: "#E4572E",
          600: "#C74624",
        },
      },
      fontFamily: {
        sans: ["var(--font-sans)", "ui-sans-serif", "system-ui", "sans-serif"],
        display: ["var(--font-display)", "ui-sans-serif", "system-ui", "sans-serif"],
        mono: ["var(--font-mono)", "ui-monospace", "SFMono-Regular", "monospace"],
      },
      borderRadius: {
        xl: "0.875rem",
        "2xl": "1.25rem",
        "3xl": "1.75rem",
      },
      boxShadow: {
        card: "0 1px 2px rgba(7, 27, 21, 0.05), 0 8px 24px -12px rgba(7, 27, 21, 0.16)",
        "card-hover":
          "0 2px 4px rgba(7, 27, 21, 0.07), 0 18px 44px -16px rgba(7, 27, 21, 0.28)",
        glow: "0 10px 30px -8px rgba(245, 179, 28, 0.45)",
      },
      backgroundImage: {
        "brand-gradient":
          "linear-gradient(135deg, #071B15 0%, #10523D 45%, #1E8663 75%, #3FA37D 100%)",
      },
      keyframes: {
        "fade-up": {
          "0%": { opacity: "0", transform: "translateY(8px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
        "doc-line": {
          "0%": { opacity: "0", transform: "translateY(6px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
        "stamp-in": {
          "0%": { opacity: "0", transform: "scale(1.35) rotate(-8deg)" },
          "60%": { opacity: "1", transform: "scale(0.96) rotate(-3deg)" },
          "100%": { opacity: "1", transform: "scale(1) rotate(-3deg)" },
        },
        caret: {
          "0%, 45%": { opacity: "1" },
          "50%, 100%": { opacity: "0" },
        },
      },
      animation: {
        "fade-up": "fade-up 0.5s ease-out both",
        "doc-line": "doc-line 0.45s ease-out both",
        "stamp-in": "stamp-in 0.5s cubic-bezier(0.2, 1.2, 0.3, 1) both",
        caret: "caret 1.1s steps(1) infinite",
      },
    },
  },
  plugins: [],
};

export default config;
