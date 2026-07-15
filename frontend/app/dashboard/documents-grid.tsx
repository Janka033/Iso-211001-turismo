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
import { complianceLevel } from "@/lib/quality";
import { createClient } from "@/lib/supabase/client";

// Un único cliente del navegador para todo el grid (no uno por tarjeta).
const supabase = createClient();

export interface DocState {
  status: DocStatus;
  completeness: number | null;
  // Score del Auditor (0-100): Nivel de Cumplimiento Normativo. null = aún no
  // evaluado por el Auditor (distinto de 0).
  complianceScore: number | null;
  version: number | null;
  storagePath: string | null;
  pendingFields: string[] | null;
}

const EMPTY: DocState = {
  status: "pending",
  completeness: null,
  complianceScore: null,
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
        // El documento cambió: el score del Auditor previo queda obsoleto. Se
        // limpia hasta que se vuelva a evaluar en Calidad (no mostrar un nivel
        // de cumplimiento que ya no corresponde a este contenido).
        complianceScore: null,
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
    if (state.version === null) return;
    setError(null);
    try {
      const {
        data: { session },
      } = await supabase.auth.getSession();
      if (!session) throw new Error("Sesión expirada, vuelve a entrar.");
      const res = await fetch(
        `${apiBase()}/generation/${meta.type}/download?version=${state.version}`,
        { headers: { Authorization: `Bearer ${session.access_token}` } },
      );
      const body = await res.json().catch(() => ({}));
      if (!res.ok || !body.url) {
        throw new Error(body.detail ?? "Descarga no disponible");
      }
      window.open(body.url, "_blank");
    } catch (err) {
      setError(err instanceof Error ? err.message : "La descarga no está disponible.");
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

      {generatedOnce && (
        <div className="mt-4">
          {state.complianceScore !== null ? (
            <ComplianceBar value={state.complianceScore} />
          ) : (
            <p className="text-xs text-slate-400">
              Sin evaluación del Auditor. Evalúa el cumplimiento en{" "}
              <span className="font-medium text-slate-500">Calidad</span>.
            </p>
          )}
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
        {state.version !== null && (
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
    needs_correction: "bg-amber-50 text-amber-700",
  };
  return <span className={`badge ${styles[status]}`}>{STATUS_LABEL[status]}</span>;
}

/**
 * Nivel de Cumplimiento Normativo: refleja el score del Auditor (no la
 * completitud). Colores por umbral de producto (ver complianceLevel):
 * rojo 0-59, amarillo 60-89, verde 90-100.
 */
function ComplianceBar({ value }: { value: number }) {
  const level = complianceLevel(value);
  const pct = Math.min(Math.max(value, 0), 100);
  return (
    <div>
      <div className="mb-1 flex items-center justify-between text-xs">
        <span className="text-slate-500">Nivel de cumplimiento normativo</span>
        <span className={`font-semibold ${level.text}`}>{value}%</span>
      </div>
      <div className="h-2 w-full overflow-hidden rounded-full bg-slate-100">
        <div
          className={`h-full rounded-full ${level.bar} transition-all`}
          style={{ width: `${pct}%` }}
        />
      </div>
      <p className={`mt-1 text-xs font-medium ${level.text}`}>{level.label}</p>
    </div>
  );
}
