"use client";

import Link from "next/link";
import { useEffect, useRef, useState } from "react";

/**
 * Piezas de UI del sistema DESIGN.md (paleta azul) — SOLO para la landing.
 * El resto de la app sigue en el sistema verde (globals.css) hasta su
 * migración; por eso estas variantes viven aquí y no en globals.
 */

/** Curva estándar del sistema: decel suave, sin rebote (DESIGN.md → Movimiento). */
const EASE = "ease-[cubic-bezier(0.32,0.72,0,1)]";

export function LandingCta({
  href,
  children,
  variant = "naranja",
  size = "md",
}: {
  href: string;
  children: React.ReactNode;
  variant?: "naranja" | "outline";
  size?: "md" | "lg";
}) {
  const base = `group inline-flex items-center justify-center gap-2.5 rounded-full font-semibold
    transition-[background-color,transform] duration-150 ${EASE} active:scale-[0.98]
    focus:outline-none focus-visible:ring-2 focus-visible:ring-naranja-400`;
  const sizes = size === "lg" ? "px-6 py-3 text-base" : "px-5 py-2.5 text-sm";
  const styles =
    variant === "naranja"
      ? "bg-naranja-500 text-marca-950 shadow-glow-naranja hover:bg-naranja-400"
      : "border border-white/25 text-white hover:bg-white/10";
  const iconBg =
    variant === "naranja" ? "bg-marca-950/10" : "bg-white/10";

  return (
    <Link href={href} className={`${base} ${sizes} ${styles}`}>
      {children}
      <span
        className={`flex h-6 w-6 items-center justify-center rounded-full ${iconBg}
          transition-transform duration-200 ${EASE} group-hover:translate-x-0.5`}
        aria-hidden="true"
      >
        <svg viewBox="0 0 16 16" className="h-3.5 w-3.5" fill="none">
          <path
            d="M3 8h9.5M9 4.5 12.5 8 9 11.5"
            stroke="currentColor"
            strokeWidth="1.4"
            strokeLinecap="round"
            strokeLinejoin="round"
          />
        </svg>
      </span>
    </Link>
  );
}

/** Chip de numeral de la norma en el sistema azul (equivale a .numeral-chip). */
export function NumeralChip({ children }: { children: React.ReactNode }) {
  return (
    <span className="inline-flex items-center rounded-md bg-marca-950/90 px-2 py-0.5 font-mono text-[11px] font-semibold tracking-wide text-naranja-400">
      {children}
    </span>
  );
}

/** Eyebrow mono del sistema azul (equivale a .eyebrow). */
export function Eyebrow({ children }: { children: React.ReactNode }) {
  return (
    <p className="font-mono text-[11px] font-semibold uppercase tracking-[0.22em] text-marca-600">
      {children}
    </p>
  );
}

/**
 * Entrada al hacer scroll: fade-up suave con IntersectionObserver.
 * Con prefers-reduced-motion se muestra el estado final, sin animación.
 * Solo transform/opacity (GPU-safe).
 */
export function Reveal({
  children,
  className = "",
  delay = 0,
}: {
  children: React.ReactNode;
  className?: string;
  delay?: number;
}) {
  const ref = useRef<HTMLDivElement>(null);
  const [shown, setShown] = useState(false);

  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) {
      setShown(true);
      return;
    }
    const io = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          setShown(true);
          io.disconnect();
        }
      },
      { rootMargin: "0px 0px -10% 0px", threshold: 0.15 },
    );
    io.observe(el);
    return () => io.disconnect();
  }, []);

  return (
    <div
      ref={ref}
      className={`${shown ? "animate-reveal" : "opacity-0"} ${className}`}
      style={delay ? { animationDelay: `${delay}ms` } : undefined}
    >
      {children}
    </div>
  );
}
