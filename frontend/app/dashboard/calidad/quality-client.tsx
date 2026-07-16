"use client";

import { useState } from "react";

import { apiBase } from "@/lib/api";
import { DOCUMENTS, type DocumentMeta } from "@/lib/documents";
import { fieldLabel } from "@/lib/field-labels";
import {
  REVIEW_STATUS_LABEL,
  complianceLevel,
  type QualityReview,
  type ReviewDecision,
  type ReviewStatus,
  type ReviewableDocument,
} from "@/lib/quality";
import { createClient } from "@/lib/supabase/client";

// Un único cliente del navegador para toda la vista (no uno por fila).
const supabase = createClient();

const META = new Map<string, DocumentMeta>(DOCUMENTS.map((d) => [d.type, d]));

async function authToken(): Promise<string | null> {
  const {
    data: { session },
  } = await supabase.auth.getSession();
  return session?.access_token ?? null;
}

export function QualityClient({
  documents,
  canDecide,
}: {
  documents: ReviewableDocument[];
  canDecide: boolean;
}) {
  const [docs, setDocs] = useState(documents);
  const [expanded, setExpanded] = useState<string | null>(null);

  function setReview(docId: string, review: QualityReview) {
    setDocs((xs) => xs.map((d) => (d.id === docId ? { ...d, review } : d)));
  }

  if (docs.length === 0) {
    return (
      <div className="card p-8 text-center">
        <p className="text-sm text-slate-500">
          Aún no hay documentos generados. Genera el set núcleo desde el panel
          y vuelve aquí para revisar su calidad.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {docs.map((doc) => (
        <DocumentRow
          key={doc.id}
          doc={doc}
          canDecide={canDecide}
          expanded={expanded === doc.id}
          onToggle={() => setExpanded(expanded === doc.id ? null : doc.id)}
          onReview={(r) => setReview(doc.id, r)}
        />
      ))}
    </div>
  );
}

function DocumentRow({
  doc,
  canDecide,
  expanded,
  onToggle,
  onReview,
}: {
  doc: ReviewableDocument;
  canDecide: boolean;
  expanded: boolean;
  onToggle: () => void;
  onReview: (review: QualityReview) => void;
}) {
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const meta = META.get(doc.document_type);
  const title = meta?.title ?? doc.document_type;
  const review = doc.review;

  async function evaluate() {
    setBusy(true);
    setError(null);
    try {
      const t = await authToken();
      if (!t) throw new Error("Sesión expirada, vuelve a entrar.");
      const res = await fetch(`${apiBase()}/quality/evaluations/${doc.id}`, {
        method: "POST",
        headers: { Authorization: `Bearer ${t}` },
      });
      const body = await res.json().catch(() => ({}));
      if (!res.ok) {
        throw new Error(body.detail ?? "No se pudo evaluar el documento");
      }
      onReview({
        id: body.review_id,
        document_id: body.document_id,
        score: body.score,
        evaluation: body.evaluation,
        review_status: (body.review_status ?? "pending_review") as ReviewStatus,
        review_notes: null,
        reviewed_at: null,
        created_at: body.created_at ?? new Date().toISOString(),
      });
      if (!expanded) onToggle();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Error inesperado");
    } finally {
      setBusy(false);
    }
  }

  return (
    <article className="card overflow-hidden">
      {/* Encabezado de la fila */}
      <div className="flex flex-col gap-3 p-5 sm:flex-row sm:items-center sm:justify-between">
        <div className="min-w-0">
          <div className="flex flex-wrap items-center gap-2">
            {meta && (
              <span className="badge bg-slate-100 text-slate-600">
                {meta.numeral}
              </span>
            )}
            <span className="badge bg-slate-100 text-slate-500">
              v{doc.version}
            </span>
            <ReviewStatusBadge status={review?.review_status ?? null} />
          </div>
          <h3 className="mt-2 truncate text-base font-semibold text-slate-900">
            {title}
          </h3>
          <p className="mt-0.5 text-xs text-slate-400">
            Generado el {formatDate(doc.created_at)}
            {review && ` · evaluado el ${formatDate(review.created_at)}`}
          </p>
        </div>

        <div className="flex shrink-0 items-center gap-3">
          <ComplianceBadge score={review?.score ?? null} />
          <button onClick={evaluate} disabled={busy} className="btn-secondary">
            {busy ? "Evaluando…" : review ? "Reevaluar" : "Evaluar con IA"}
          </button>
          {review && (
            <button
              onClick={onToggle}
              className="btn-secondary"
              aria-expanded={expanded}
            >
              {expanded ? "Ocultar" : "Ver detalle"}
            </button>
          )}
        </div>
      </div>

      {error && (
        <p className="mx-5 mb-4 rounded-lg bg-rose-50 px-3 py-2 text-xs text-rose-700">
          {error}
        </p>
      )}

      {expanded && review && (
        <EvaluationDetail
          review={review}
          canDecide={canDecide}
          onReview={onReview}
        />
      )}
    </article>
  );
}

function EvaluationDetail({
  review,
  canDecide,
  onReview,
}: {
  review: QualityReview;
  canDecide: boolean;
  onReview: (review: QualityReview) => void;
}) {
  const ev = review.evaluation;
  const { completeness, coherence } = ev;
  const missingRequired = completeness.missing_required_fields ?? [];
  const missingOptional = completeness.missing_optional_fields ?? [];

  return (
    <div className="space-y-5 border-t border-slate-100 bg-slate-50/60 p-5">
      {/* a) Completitud */}
      <section>
        <SectionTitle>Completitud</SectionTitle>
        {missingRequired.length === 0 && missingOptional.length === 0 ? (
          <p className="mt-1 text-sm text-slate-600">
            Todos los datos requeridos están completos.
          </p>
        ) : (
          <div className="mt-2 space-y-2">
            {missingRequired.length > 0 && (
              <FieldChips
                label="Datos obligatorios que faltan"
                fields={missingRequired}
                tone="rose"
              />
            )}
            {missingOptional.length > 0 && (
              <FieldChips
                label="Datos opcionales que faltan"
                fields={missingOptional}
                tone="slate"
              />
            )}
          </div>
        )}
        {completeness.comment && (
          <p className="mt-2 text-sm text-slate-500">{completeness.comment}</p>
        )}
      </section>

      {/* b) Coherencia con el numeral */}
      <section>
        <SectionTitle>Coherencia con la norma</SectionTitle>
        {coherence.coherent && coherence.issues.length === 0 ? (
          <p className="mt-1 text-sm text-emerald-700">
            El contenido es coherente con lo que exige el numeral.
          </p>
        ) : (
          <ul className="mt-1 list-disc space-y-1 pl-5 text-sm text-slate-600">
            {coherence.issues.map((issue, i) => (
              <li key={i}>{issue}</li>
            ))}
          </ul>
        )}
      </section>

      {/* c) Alertas según patrones de auditoría */}
      <section>
        <SectionTitle>Alertas activadas ({ev.alerts.length})</SectionTitle>
        {ev.alerts.length === 0 ? (
          <p className="mt-1 text-sm text-slate-600">
            Ningún patrón de rechazo o requisito activado.
          </p>
        ) : (
          <div className="mt-2 space-y-2">
            {ev.alerts.map((alert, i) => (
              <div
                key={i}
                className="rounded-lg border border-amber-100 bg-amber-50 px-3 py-2"
              >
                <p className="text-sm font-medium text-amber-800">
                  {alert.pattern_type && (
                    <span className="mr-1 uppercase text-[10px] tracking-wide">
                      [{alert.pattern_type}]
                    </span>
                  )}
                  {alert.pattern}
                </p>
                {alert.detail && (
                  <p className="mt-0.5 text-xs text-amber-700">{alert.detail}</p>
                )}
              </div>
            ))}
          </div>
        )}
      </section>

      {/* Observaciones */}
      {ev.observations.length > 0 && (
        <section>
          <SectionTitle>Observaciones</SectionTitle>
          <ul className="mt-1 list-disc space-y-1 pl-5 text-sm text-slate-600">
            {ev.observations.map((obs, i) => (
              <li key={i}>{obs}</li>
            ))}
          </ul>
        </section>
      )}

      {/* Correcciones sugeridas */}
      {ev.suggested_corrections.length > 0 && (
        <section>
          <SectionTitle>
            Correcciones sugeridas ({ev.suggested_corrections.length})
          </SectionTitle>
          <div className="mt-2 space-y-2">
            {ev.suggested_corrections.map((c, i) => (
              <div key={i} className="rounded-lg bg-white px-3 py-2 shadow-sm">
                <p className="text-sm text-slate-700">
                  {c.field && (
                    <span
                      title={c.field}
                      className="mr-1.5 rounded-full bg-slate-100 px-2 py-0.5 text-xs font-medium text-slate-600"
                    >
                      {fieldLabel(c.field)}
                    </span>
                  )}
                  {c.issue}
                </p>
                {c.suggestion && (
                  <p className="mt-0.5 text-xs text-slate-500">{c.suggestion}</p>
                )}
              </div>
            ))}
          </div>
        </section>
      )}

      {/* Decisión del revisor */}
      <DecisionPanel review={review} canDecide={canDecide} onReview={onReview} />
    </div>
  );
}

function DecisionPanel({
  review,
  canDecide,
  onReview,
}: {
  review: QualityReview;
  canDecide: boolean;
  onReview: (review: QualityReview) => void;
}) {
  const [notes, setNotes] = useState(review.review_notes ?? "");
  const [deciding, setDeciding] = useState<ReviewDecision | null>(null);
  const [error, setError] = useState<string | null>(null);

  const decided = review.review_status !== "pending_review";

  async function decide(decision: ReviewDecision) {
    setDeciding(decision);
    setError(null);
    try {
      const t = await authToken();
      if (!t) throw new Error("Sesión expirada, vuelve a entrar.");
      const res = await fetch(
        `${apiBase()}/quality/reviews/${review.id}/decision`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${t}`,
          },
          body: JSON.stringify({ decision, notes: notes.trim() || null }),
        },
      );
      const body = await res.json().catch(() => ({}));
      if (!res.ok) {
        throw new Error(body.detail ?? "No se pudo aplicar la decisión");
      }
      onReview({
        ...review,
        review_status: (body.review_status ?? decision) as ReviewStatus,
        review_notes: notes.trim() || null,
        reviewed_at: new Date().toISOString(),
      });
    } catch (err) {
      setError(err instanceof Error ? err.message : "Error inesperado");
    } finally {
      setDeciding(null);
    }
  }

  if (!canDecide) {
    return (
      <section className="rounded-xl bg-white p-4 shadow-sm">
        <SectionTitle>Decisión del revisor</SectionTitle>
        <p className="mt-1 text-sm text-slate-500">
          {decided
            ? `Estado: ${REVIEW_STATUS_LABEL[review.review_status]}.`
            : "Pendiente de revisión."}
          {review.review_notes && ` Notas: ${review.review_notes}`}
        </p>
      </section>
    );
  }

  return (
    <section className="rounded-xl bg-white p-4 shadow-sm">
      <SectionTitle>Decisión del revisor</SectionTitle>
      {decided && (
        <p className="mt-1 text-sm text-slate-500">
          Decisión actual:{" "}
          <span className="font-medium text-slate-700">
            {REVIEW_STATUS_LABEL[review.review_status]}
          </span>
          . Puedes cambiarla si lo necesitas.
        </p>
      )}
      <textarea
        value={notes}
        onChange={(e) => setNotes(e.target.value)}
        placeholder="Notas para la empresa (qué corregir y por qué)…"
        rows={2}
        className="mt-3 w-full rounded-lg border border-slate-200 px-3 py-2 text-sm text-slate-700 placeholder:text-slate-400 focus:border-brand-500 focus:outline-none"
      />
      {error && (
        <p className="mt-2 rounded-lg bg-rose-50 px-3 py-2 text-xs text-rose-700">
          {error}
        </p>
      )}
      <div className="mt-3 flex flex-wrap gap-2">
        <button
          onClick={() => decide("approved")}
          disabled={deciding !== null}
          className="rounded-lg bg-emerald-600 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-emerald-700 disabled:opacity-50"
        >
          {deciding === "approved" ? "Aplicando…" : "Aprobar"}
        </button>
        <button
          onClick={() => decide("needs_correction")}
          disabled={deciding !== null}
          className="rounded-lg bg-amber-500 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-amber-600 disabled:opacity-50"
        >
          {deciding === "needs_correction" ? "Aplicando…" : "Pedir corrección"}
        </button>
        <button
          onClick={() => decide("rejected")}
          disabled={deciding !== null}
          className="rounded-lg bg-rose-600 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-rose-700 disabled:opacity-50"
        >
          {deciding === "rejected" ? "Aplicando…" : "Rechazar"}
        </button>
      </div>
    </section>
  );
}

// ---------------------------------------------------------------------------
// Piezas de presentación
// ---------------------------------------------------------------------------

function SectionTitle({ children }: { children: React.ReactNode }) {
  return (
    <h4 className="text-xs font-semibold uppercase tracking-wide text-slate-400">
      {children}
    </h4>
  );
}

function ComplianceBadge({ score }: { score: number | null }) {
  if (score === null) {
    return <span className="badge bg-slate-100 text-slate-500">Sin evaluar</span>;
  }
  const level = complianceLevel(score);
  return (
    <span
      className={`badge ${level.soft} ${level.text}`}
      title={`Nivel de cumplimiento normativo: ${Math.round(score)} de 100`}
    >
      {level.label}
    </span>
  );
}

function ReviewStatusBadge({ status }: { status: ReviewStatus | null }) {
  if (!status) {
    return null;
  }
  const styles: Record<ReviewStatus, string> = {
    pending_review: "bg-sky-50 text-sky-700",
    approved: "bg-emerald-50 text-emerald-700",
    rejected: "bg-rose-50 text-rose-700",
    needs_correction: "bg-amber-50 text-amber-700",
  };
  return (
    <span className={`badge ${styles[status]}`}>
      {REVIEW_STATUS_LABEL[status]}
    </span>
  );
}

function FieldChips({
  label,
  fields,
  tone,
}: {
  label: string;
  fields: string[];
  tone: "rose" | "slate";
}) {
  const chip =
    tone === "rose"
      ? "bg-rose-50 text-rose-700"
      : "bg-slate-100 text-slate-600";
  return (
    <div>
      <p className="text-xs text-slate-500">{label}:</p>
      <div className="mt-1 flex flex-wrap gap-1.5">
        {fields.map((f) => (
          <span
            key={f}
            title={f}
            className={`rounded-full px-2.5 py-0.5 text-xs ${chip}`}
          >
            {fieldLabel(f)}
          </span>
        ))}
      </div>
    </div>
  );
}

function formatDate(iso: string): string {
  const d = new Date(iso);
  return Number.isNaN(d.getTime())
    ? "—"
    : d.toLocaleDateString("es-CO", { day: "numeric", month: "short", year: "numeric" });
}
