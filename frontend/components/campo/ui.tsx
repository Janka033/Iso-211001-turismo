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
