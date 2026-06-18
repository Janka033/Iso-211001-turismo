"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";

import { apiBase } from "@/lib/api";
import {
  DOCUMENTS,
  DocStatus,
  DocumentMeta,
  DocumentType,
  STATUS_LABEL,
} from "@/lib/documents";
import { createClient } from "@/lib/supabase/client";

// Un único cliente del navegador para todo el grid (no uno por tarjeta).
const supabase = createClient();

export interface DocState {
  status: DocStatus;
  completeness: number | null;
  version: number | null;
  storagePath: string | null;
  pendingFields: string[] | null;
}

const EMPTY: DocState = {
  status: "pending",
  completeness: null,
  version: null,
  storagePath: null,
  pendingFields: null,
};

export function DocumentsGrid({
  initial,
}: {
  initial: Partial<Record<DocumentType, DocState>>;
}) {
  return (
    <div className="grid gap-5 sm:grid-cols-2">
      {DOCUMENTS.map((doc) => (
        <DocumentCard key={doc.type} meta={doc} initial={initial[doc.type] ?? EMPTY} />
      ))}
    </div>
  );
}

function DocumentCard({ meta, initial }: { meta: DocumentMeta; initial: DocState }) {
  const router = useRouter();
  const [state, setState] = useState<DocState>(initial);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function generate() {
    setBusy(true);
    setError(null);
    try {
      const {
        data: { session },
      } = await supabase.auth.getSession();
      if (!session) throw new Error("Sesión expirada, vuelve a entrar.");

      const res = await fetch(`${apiBase()}/generation/${meta.type}`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${session.access_token}`,
        },
        body: JSON.stringify({}),
      });
      const body = await res.json().catch(() => ({}));
      if (!res.ok) throw new Error(body.detail ?? "No se pudo generar el documento");

      setState({
        status: body.status ?? "generated",
        completeness: body.completeness ?? null,
        version: body.version ?? null,
        storagePath: body.storage_path ?? null,
        pendingFields: body.pending_fields ?? [],
      });
      // Refresca el server component (contador "X/4", estado persistido).
      router.refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Error inesperado");
    } finally {
      setBusy(false);
    }
  }

  async function download() {
    if (!state.storagePath) return;
    try {
      const { data, error: e } = await supabase.storage
        .from("documents")
        .createSignedUrl(state.storagePath, 60);
      if (e || !data) throw e ?? new Error("Sin URL");
      window.open(data.signedUrl, "_blank");
    } catch {
      setError("La descarga no está disponible (Storage no configurado).");
    }
  }

  const generatedOnce = state.version !== null || state.status !== "pending";

  return (
    <article className="card flex flex-col p-5 transition-shadow hover:shadow-card-hover">
      <div className="flex items-start justify-between gap-3">
        <div className="flex items-center gap-2">
          <span className="badge bg-slate-100 text-slate-600">{meta.numeral}</span>
          <span className="badge bg-slate-100 text-slate-500 uppercase">
            .{meta.engine}
          </span>
        </div>
        <StatusBadge status={busy ? "generating" : state.status} />
      </div>

      <h3 className="mt-3 text-base font-semibold text-slate-900">{meta.title}</h3>
      <p className="mt-1 flex-1 text-sm text-slate-500">{meta.description}</p>

      {state.completeness !== null && (
        <div className="mt-4">
          <div className="mb-1 flex items-center justify-between text-xs">
            <span className="text-slate-500">Completitud</span>
            <span className="font-medium text-slate-700">{state.completeness}%</span>
          </div>
          <CompletenessBar value={state.completeness} />
        </div>
      )}

      {state.pendingFields && state.pendingFields.length > 0 && (
        <p className="mt-3 rounded-lg bg-accent-50 px-3 py-2 text-xs text-amber-700">
          {state.pendingFields.length} campo(s) marcados como{" "}
          <span className="font-medium">[PENDIENTE]</span> por falta de datos.
        </p>
      )}

      {error && (
        <p className="mt-3 rounded-lg bg-rose-50 px-3 py-2 text-xs text-rose-700">
          {error}
        </p>
      )}

      <div className="mt-5 flex items-center gap-2">
        <button onClick={generate} disabled={busy} className="btn-primary flex-1">
          {busy ? "Generando…" : generatedOnce ? "Regenerar" : "Generar"}
        </button>
        {state.storagePath && (
          <button onClick={download} className="btn-secondary" title="Descargar">
            Descargar
          </button>
        )}
      </div>
      {state.version !== null && (
        <p className="mt-2 text-center text-xs text-slate-400">versión {state.version}</p>
      )}
    </article>
  );
}

function StatusBadge({ status }: { status: DocStatus }) {
  const styles: Record<DocStatus, string> = {
    pending: "bg-slate-100 text-slate-500",
    generating: "bg-sky-50 text-sky-700",
    generated: "bg-brand-50 text-brand-700",
    approved: "bg-emerald-50 text-emerald-700",
    rejected: "bg-rose-50 text-rose-700",
  };
  return <span className={`badge ${styles[status]}`}>{STATUS_LABEL[status]}</span>;
}

function CompletenessBar({ value }: { value: number }) {
  const color =
    value >= 80 ? "bg-brand-500" : value >= 40 ? "bg-accent-500" : "bg-rose-400";
  return (
    <div className="h-2 w-full overflow-hidden rounded-full bg-slate-100">
      <div
        className={`h-full rounded-full ${color} transition-all`}
        style={{ width: `${Math.min(Math.max(value, 0), 100)}%` }}
      />
    </div>
  );
}
