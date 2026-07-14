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
        /**
         * Sistema DESIGN.md (paleta azul) — hoy SOLO lo usa la landing.
         * Escalas canónicas Tailwind: marca=blue, naranja=orange, cielo=sky.
         * brand/accent (verde/amarillo) siguen vivos para el resto de la app
         * hasta la migración por vista (ver DESIGN.md → Migración pendiente).
         */
        marca: {
          50: "#EFF6FF",
          100: "#DBEAFE",
          200: "#BFDBFE",
          300: "#93C5FD",
          400: "#60A5FA",
          500: "#3B82F6",
          600: "#2563EB",
          700: "#1D4ED8",
          800: "#1E40AF",
          900: "#1E3A8A",
          950: "#172554",
        },
        naranja: {
          100: "#FFEDD5",
          300: "#FDBA74",
          400: "#FB923C",
          500: "#F97316",
          600: "#EA580C",
        },
        cielo: {
          100: "#E0F2FE",
          500: "#0EA5E9",
          600: "#0284C7",
          700: "#0369A1",
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
        /* Sistema DESIGN.md (landing): sombras teñidas de marca, no negras. */
        "card-marca":
          "0 1px 2px rgba(23, 37, 84, 0.05), 0 8px 24px -12px rgba(23, 37, 84, 0.16)",
        "card-marca-hover":
          "0 2px 4px rgba(23, 37, 84, 0.07), 0 18px 44px -16px rgba(23, 37, 84, 0.28)",
        "glow-naranja": "0 10px 30px -8px rgba(249, 115, 22, 0.45)",
      },
      backgroundImage: {
        "brand-gradient":
          "linear-gradient(135deg, #071B15 0%, #10523D 45%, #1E8663 75%, #3FA37D 100%)",
        /* Sistema DESIGN.md (landing): profundidad radial sutil, no lineal 45°. */
        "marca-gradient":
          "radial-gradient(120% 140% at 15% 0%, #1D4ED8 0%, #172554 55%, #172554 100%)",
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
        /* Sello: aterriza con decel, sin asentamiento (DESIGN.md: nada de
           bounce/elastic — ni en la curva ni horneado en los keyframes). */
        "stamp-in": {
          "0%": { opacity: "0", transform: "scale(1.35) rotate(-8deg)" },
          "100%": { opacity: "1", transform: "scale(1) rotate(-3deg)" },
        },
        caret: {
          "0%, 45%": { opacity: "1" },
          "50%, 100%": { opacity: "0" },
        },
        /* Entrada de sección al hacer scroll (landing). Solo transform/opacity. */
        reveal: {
          "0%": { opacity: "0", transform: "translateY(16px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
      },
      animation: {
        "fade-up": "fade-up 0.5s ease-out both",
        "doc-line": "doc-line 0.45s ease-out both",
        "stamp-in": "stamp-in 0.5s cubic-bezier(0.32, 0.72, 0, 1) both",
        caret: "caret 1.1s steps(1) infinite",
        reveal: "reveal 0.7s cubic-bezier(0.32, 0.72, 0, 1) both",
      },
    },
  },
  plugins: [],
};

export default config;
