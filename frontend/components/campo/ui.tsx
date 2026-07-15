"use client";

import Link from "next/link";

import { Logo } from "@/components/logo";

/** Cabecera móvil azul con opción de volver. */
export function CampoHeader({
  title,
  subtitle,
  backHref,
}: {
  title?: string;
  subtitle?: string;
  backHref?: string;
}) {
  return (
    <header className="bg-marca-gradient px-5 pb-6 pt-5 text-white">
      <div className="mx-auto flex w-full max-w-md items-center justify-between">
        <Logo variant="marcaOnDark" />
        {backHref && (
          <Link
            href={backHref}
            className="text-sm font-medium text-marca-200 hover:text-white"
          >
            ← Volver
          </Link>
        )}
      </div>
      {(subtitle || title) && (
        <div className="mx-auto mt-4 w-full max-w-md">
          {subtitle && (
            <p className="font-mono text-[11px] font-semibold uppercase tracking-[0.22em] text-marca-300">
              {subtitle}
            </p>
          )}
          {title && (
            <h1 className="mt-1 font-display text-2xl font-extrabold leading-tight">
              {title}
            </h1>
          )}
        </div>
      )}
    </header>
  );
}

export function CampoMain({ children }: { children: React.ReactNode }) {
  return <div className="mx-auto w-full max-w-md px-5 py-6">{children}</div>;
}

export function ErrorNote({ children }: { children: React.ReactNode }) {
  if (!children) return null;
  return (
    <p className="mb-4 rounded-lg bg-flag-100 px-3 py-2 text-sm text-flag-600">
      {children}
    </p>
  );
}

export function OkNote({ children }: { children: React.ReactNode }) {
  return (
    <p className="mb-4 rounded-lg bg-cielo-100 px-3 py-2 text-sm text-cielo-700">
      {children}
    </p>
  );
}

const STATUS_STYLES: Record<string, string> = {
  programada: "bg-marca-100 text-marca-800",
  en_curso: "bg-naranja-100 text-naranja-600",
  finalizada: "bg-cielo-100 text-cielo-700",
  cancelada: "bg-slate-200 text-slate-600",
};

export function StatusBadge({ status }: { status: string }) {
  const label = status.replace("_", " ");
  return (
    <span
      className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium capitalize ${
        STATUS_STYLES[status] ?? "bg-slate-200 text-slate-600"
      }`}
    >
      {label}
    </span>
  );
}

/**
 * Iconografía de operación en terreno. Trazo fino sobre `currentColor` (mismo
 * lenguaje que el sidebar): sin emojis, para una lectura sobria y profesional.
 */
type IconProps = { className?: string };
const SVG = (props: IconProps & { children: React.ReactNode }) => (
  <svg
    viewBox="0 0 20 20"
    fill="none"
    stroke="currentColor"
    strokeWidth="1.6"
    strokeLinecap="round"
    strokeLinejoin="round"
    className={props.className ?? "h-5 w-5"}
    aria-hidden="true"
  >
    {props.children}
  </svg>
);

export const IconWrench = (p: IconProps) => (
  <SVG {...p}>
    <path d="M13.6 6.4a3.2 3.2 0 0 1-4.1 4.1l-4.2 4.2a1.5 1.5 0 0 1-2.1-2.1l4.2-4.2a3.2 3.2 0 0 1 4.1-4.1l-2 2 1.9 1.9 2.2-1.8Z" />
  </SVG>
);
export const IconCompass = (p: IconProps) => (
  <SVG {...p}>
    <circle cx="10" cy="10" r="7.5" />
    <path d="m13 7-2 4-4 2 2-4 4-2Z" />
  </SVG>
);
export const IconCheckCircle = (p: IconProps) => (
  <SVG {...p}>
    <circle cx="10" cy="10" r="7.5" />
    <path d="m6.6 10.3 2.2 2.2 4.6-4.8" />
  </SVG>
);
export const IconCheck = (p: IconProps) => (
  <SVG {...p}>
    <path d="m4.5 10.5 3.2 3.2 7.8-7.8" />
  </SVG>
);
export const IconPin = (p: IconProps) => (
  <SVG {...p}>
    <path d="M10 2.6c-2.8 0-4.8 2-4.8 4.7 0 3.3 4.8 9.4 4.8 9.4s4.8-6.1 4.8-9.4c0-2.7-2-4.7-4.8-4.7Z" />
    <circle cx="10" cy="7.3" r="1.8" />
  </SVG>
);
export const IconFlag = (p: IconProps) => (
  <SVG {...p}>
    <path d="M5 3v14" />
    <path d="M5 3.6h9.2l-2.1 3 2.1 3H5" />
  </SVG>
);
export const IconAlertTriangle = (p: IconProps) => (
  <SVG {...p}>
    <path d="M10 3.2 17.6 16.4H2.4L10 3.2Z" />
    <path d="M10 8.4v3.4" />
    <path d="M10 14.1h.01" />
  </SVG>
);
