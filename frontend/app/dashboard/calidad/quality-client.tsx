"use client";

import { useMemo, useState } from "react";

import { apiBase } from "@/lib/api";
import { DOCUMENTS, type DocumentMeta } from "@/lib/documents";
import { fieldLabel } from "@/lib/field-labels";
import {
  REMEDIABLE_STATUSES,
  REVIEW_STATUS_LABEL,
  complianceLevel,
  type QualityEvaluation,
  type QualityReview,
  type RemediationResult,
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

/** Estado por el que se puede filtrar: los de revisión + "sin evaluar". */
type StatusFilter = "all" | "unevaluated" | ReviewStatus;

const STATUS_FILTERS: { key: StatusFilter; label: string }[] = [
  { key: "all", label: "Todos" },
  { key: "unevaluated", label: "Sin evaluar" },
  { key: "pending_review", label: REVIEW_STATUS_LABEL.pending_review },
  { key: "approved", label: REVIEW_STATUS_LABEL.approved },
  { key: "needs_correction", label: REVIEW_STATUS_LABEL.needs_correction },
  { key: "rejected", label: REVIEW_STATUS_LABEL.rejected },
];

/** Un tipo de documento con todas sus versiones (la vigente primero). */
interface DocumentGroup {
  type: string;
  versions: ReviewableDocument[];
  latest: ReviewableDocument;
}

/** El estado del grupo es el de su versión vigente: es lo accionable. */
function groupStatus(group: DocumentGroup): StatusFilter {
  return group.latest.review?.review_status ?? "unevaluated";
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
  const [filter, setFilter] = useState<StatusFilter>("all");

  function setReview(docId: string, review: QualityReview) {
    setDocs((xs) => xs.map((d) => (d.id === docId ? { ...d, review } : d)));
  }

  // Una subsanación regenera el documento: la versión nueva entra de primera
  // (su grupo sube y la pestaña vigente pasa a ser ella, sin evaluar).
  function addDocument(doc: ReviewableDocument) {
    setDocs((xs) => [doc, ...xs]);
  }

  // Una tarjeta por tipo de documento; dentro, sus versiones. El orden de los
  // grupos hereda el del server (created_at desc): lo último generado, arriba.
  const groups = useMemo<DocumentGroup[]>(() => {
    const byType = new Map<string, ReviewableDocument[]>();
    for (const d of docs) {
      const xs = byType.get(d.document_type) ?? [];
      xs.push(d);
      byType.set(d.document_type, xs);
    }
    return Array.from(byType.entries()).map(([type, versions]) => {
      const sorted = [...versions].sort((a, b) => b.version - a.version);
      return { type, versions: sorted, latest: sorted[0] };
    });
  }, [docs]);

  const counts = useMemo(() => {
    const c = new Map<StatusFilter, number>([["all", groups.length]]);
    for (const g of groups) {
      const s = groupStatus(g);
      c.set(s, (c.get(s) ?? 0) + 1);
    }
    return c;
  }, [groups]);

  const visible =
    filter === "all" ? groups : groups.filter((g) => groupStatus(g) === filter);

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
      {/* Filtro por estado (de la versión vigente de cada documento) */}
      <div
        className="flex flex-wrap gap-2"
        role="group"
        aria-label="Filtrar documentos por estado"
      >
        {STATUS_FILTERS.map(({ key, label }) => {
          const n = counts.get(key) ?? 0;
          const active = filter === key;
          return (
            <button
              key={key}
              onClick={() => setFilter(key)}
              aria-pressed={active}
              className={`rounded-full px-3 py-1.5 text-xs font-medium transition-colors ${
                active
                  ? "bg-slate-900 text-white"
                  : "bg-white text-slate-600 shadow-sm hover:bg-slate-50"
              }`}
            >
              {label}
              <span
                className={`ml-1.5 ${active ? "text-slate-300" : "text-slate-400"}`}
              >
                {n}
              </span>
            </button>
          );
        })}
      </div>

      {visible.length === 0 ? (
        <div className="card p-8 text-center">
          <p className="text-sm text-slate-500">
            Ningún documento con este estado.
          </p>
          <button
            onClick={() => setFilter("all")}
            className="mt-2 text-sm font-medium text-slate-700 underline underline-offset-2 hover:text-slate-900"
          >
            Ver todos
          </button>
        </div>
      ) : (
        visible.map((group) => (
          <DocumentGroupCard
            key={group.type}
            group={group}
            canDecide={canDecide}
            expandedId={expanded}
            onToggle={(id) => setExpanded(expanded === id ? null : id)}
            onReview={setReview}
            onNewDocument={addDocument}
          />
        ))
      )}
    </div>
  );
}

function DocumentGroupCard({
  group,
  canDecide,
  expandedId,
  onToggle,
  onReview,
  onNewDocument,
}: {
  group: DocumentGroup;
  canDecide: boolean;
  expandedId: string | null;
  onToggle: (id: string) => void;
  onReview: (docId: string, review: QualityReview) => void;
  onNewDocument: (doc: ReviewableDocument) => void;
}) {
  // Versión seleccionada en las pestañas; null = la vigente.
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const shown =
    group.versions.find((v) => v.id === selectedId) ?? group.latest;

  const meta = META.get(group.type);
  const title = meta?.title ?? group.type;

  return (
    <article className="card overflow-hidden">
      {/* Encabezado del documento (común a todas sus versiones) */}
      <div className="flex flex-wrap items-center gap-2 border-b border-slate-100 px-5 py-4">
        {meta && (
          <span className="badge bg-slate-100 text-slate-600">
            {meta.numeral}
          </span>
        )}
        <h3 className="min-w-0 truncate text-base font-semibold text-slate-900">
          {title}
        </h3>
      </div>

      {/* Pestañas de versión (solo si hay más de una) */}
      {group.versions.length > 1 && (
        <div
          className="flex flex-wrap items-center gap-1.5 px-5 pt-4"
          role="tablist"
          aria-label={`Versiones de ${title}`}
        >
          {group.versions.map((v) => {
            const active = v.id === shown.id;
            return (
              <button
                key={v.id}
                role="tab"
                aria-selected={active}
                onClick={() =>
                  setSelectedId(v.id === group.latest.id ? null : v.id)
                }
                className={`rounded-full px-2.5 py-1 text-xs font-medium transition-colors ${
                  active
                    ? "bg-slate-900 text-white"
                    : "bg-slate-100 text-slate-500 hover:bg-slate-200"
                }`}
              >
                v{v.version}
              </button>
            );
          })}
        </div>
      )}

      <VersionRow
        key={shown.id}
        doc={shown}
        isLatest={shown.id === group.latest.id}
        canDecide={canDecide}
        expanded={expandedId === shown.id}
        onToggle={() => onToggle(shown.id)}
        onReview={(r) => onReview(shown.id, r)}
        onNewDocument={onNewDocument}
      />
    </article>
  );
}

function VersionRow({
  doc,
  isLatest,
  canDecide,
  expanded,
  onToggle,
  onReview,
  onNewDocument,
}: {
  doc: ReviewableDocument;
  isLatest: boolean;
  canDecide: boolean;
  expanded: boolean;
  onToggle: () => void;
  onReview: (review: QualityReview) => void;
  onNewDocument: (doc: ReviewableDocument) => void;
}) {
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

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
    <>
      <div className="flex flex-col gap-3 p-5 sm:flex-row sm:items-center sm:justify-between">
        <div className="min-w-0">
          <div className="flex flex-wrap items-center gap-2">
            <span className="badge bg-slate-100 text-slate-500">
              v{doc.version}
            </span>
            <span
              className={`badge ${
                isLatest
                  ? "bg-sky-50 text-sky-700"
                  : "bg-slate-100 text-slate-400"
              }`}
            >
              {isLatest ? "Vigente" : "Versión anterior"}
            </span>
            <ReviewStatusBadge status={review?.review_status ?? null} />
          </div>
          <p className="mt-2 text-xs text-slate-400">
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
          onNewDocument={onNewDocument}
        />
      )}
    </>
  );
}

function EvaluationDetail({
  review,
  canDecide,
  onReview,
  onNewDocument,
}: {
  review: QualityReview;
  canDecide: boolean;
  onReview: (review: QualityReview) => void;
  onNewDocument: (doc: ReviewableDocument) => void;
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

      {/* Subsanación: responder la corrección y regenerar */}
      {REMEDIABLE_STATUSES.includes(review.review_status) && (
        <RemediationPanel review={review} onNewDocument={onNewDocument} />
      )}
    </div>
  );
}

/**
 * Campos que la empresa puede subsanar: los obligatorios sin dato + los que
 * marcó una corrección puntual. El hint viene de la corrección (issue +
 * sugerencia del evaluador) cuando existe.
 */
function remediationFields(
  ev: QualityEvaluation,
): { key: string; hint: string | null }[] {
  const out: { key: string; hint: string | null }[] = [];
  const byKey = new Map<string, { key: string; hint: string | null }>();

  for (const key of ev.completeness.missing_required_fields ?? []) {
    if (!byKey.has(key)) {
      const item = { key, hint: null };
      byKey.set(key, item);
      out.push(item);
    }
  }
  for (const c of ev.suggested_corrections ?? []) {
    if (!c.field) continue;
    const hint = [c.issue, c.suggestion].filter(Boolean).join(" — ") || null;
    const existing = byKey.get(c.field);
    if (existing) {
      if (!existing.hint) existing.hint = hint;
    } else {
      const item = { key: c.field, hint };
      byKey.set(c.field, item);
      out.push(item);
    }
  }
  return out;
}

function RemediationPanel({
  review,
  onNewDocument,
}: {
  review: QualityReview;
  onNewDocument: (doc: ReviewableDocument) => void;
}) {
  const fields = remediationFields(review.evaluation);
  const [values, setValues] = useState<Record<string, string>>({});
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [done, setDone] = useState<string | null>(null);

  const answers = Object.entries(values)
    .map(([k, v]) => [k, v.trim()] as const)
    .filter(([, v]) => v.length > 0);

  async function submit() {
    setBusy(true);
    setError(null);
    try {
      const t = await authToken();
      if (!t) throw new Error("Sesión expirada, vuelve a entrar.");
      const res = await fetch(
        `${apiBase()}/quality/reviews/${review.id}/remediation`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${t}`,
          },
          body: JSON.stringify({ answers: Object.fromEntries(answers) }),
        },
      );
      const body: RemediationResult & { detail?: string } = await res
        .json()
        .catch(() => ({}) as RemediationResult & { detail?: string });
      if (!res.ok) {
        throw new Error(
          typeof body.detail === "string"
            ? body.detail
            : "No se pudo guardar la subsanación",
        );
      }
      if (body.document) {
        onNewDocument({
          id: body.document.document_id,
          document_type: body.document.document_type,
          version: body.document.version,
          created_at: new Date().toISOString(),
          review: null,
        });
        setDone(
          `Se generó la versión v${body.document.version} con tus datos. ` +
            "Evalúala para verificar que la corrección quedó resuelta.",
        );
      } else {
        setDone("Datos guardados. Regenera el documento para aplicarlos.");
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Error inesperado");
    } finally {
      setBusy(false);
    }
  }

  if (done) {
    return (
      <section className="rounded-xl border border-emerald-100 bg-emerald-50 p-4">
        <SectionTitle>Subsanación enviada</SectionTitle>
        <p className="mt-1 text-sm text-emerald-800">{done}</p>
      </section>
    );
  }

  if (fields.length === 0) {
    return (
      <section className="rounded-xl bg-white p-4 shadow-sm">
        <SectionTitle>Subsanar</SectionTitle>
        <p className="mt-1 text-sm text-slate-500">
          La evaluación no marcó campos puntuales para corregir. Ajusta tus
          datos desde el onboarding o el inventario y regenera el documento
          desde el panel.
        </p>
      </section>
    );
  }

  return (
    <section className="rounded-xl bg-white p-4 shadow-sm">
      <SectionTitle>Subsanar y regenerar</SectionTitle>
      <p className="mt-1 text-sm text-slate-500">
        Completa los datos marcados; al guardar se genera una versión nueva
        del documento con esta información. Lo que dejes vacío no se toca.
      </p>

      <div className="mt-3 space-y-3">
        {fields.map((f) => (
          <div key={f.key}>
            <label
              htmlFor={`remediation-${review.id}-${f.key}`}
              className="text-sm font-medium text-slate-700"
              title={f.key}
            >
              {fieldLabel(f.key)}
            </label>
            {f.hint && <p className="mt-0.5 text-xs text-slate-500">{f.hint}</p>}
            <textarea
              id={`remediation-${review.id}-${f.key}`}
              value={values[f.key] ?? ""}
              onChange={(e) =>
                setValues((xs) => ({ ...xs, [f.key]: e.target.value }))
              }
              rows={2}
              className="mt-1 w-full rounded-lg border border-slate-200 px-3 py-2 text-sm text-slate-700 placeholder:text-slate-400 focus:border-marca-500 focus:outline-none"
            />
          </div>
        ))}
      </div>

      {error && (
        <p className="mt-2 rounded-lg bg-rose-50 px-3 py-2 text-xs text-rose-700">
          {error}
        </p>
      )}

      <button
        onClick={submit}
        disabled={busy || answers.length === 0}
        className="mt-3 rounded-lg bg-slate-900 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-slate-800 disabled:opacity-50"
      >
        {busy
          ? "Guardando y regenerando… (puede tardar un minuto)"
          : "Guardar y regenerar documento"}
      </button>
    </section>
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
        className="mt-3 w-full rounded-lg border border-slate-200 px-3 py-2 text-sm text-slate-700 placeholder:text-slate-400 focus:border-marca-500 focus:outline-none"
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
