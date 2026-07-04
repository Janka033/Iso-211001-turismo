import type { DocumentType } from "@/lib/documents";
import type { QualityReview, ReviewableDocument } from "@/lib/quality";
import { createClient } from "@/lib/supabase/server";

import { QualityClient } from "./quality-client";

// Server Component protegido por middleware. Las consultas pasan por RLS con
// el JWT del usuario: solo documentos y evaluaciones de su tenant. Sin datos
// de ejemplo — se listan los documentos realmente generados.
export default async function CalidadPage() {
  const supabase = createClient();

  const [profileRes, docsRes, reviewsRes] = await Promise.all([
    supabase.from("user_profiles").select("role").single(),
    supabase
      .from("documents")
      .select("id, document_type, version, created_at")
      .order("created_at", { ascending: false }),
    supabase
      .from("quality_reviews")
      .select(
        "id, document_id, score, evaluation, review_status, review_notes, reviewed_at, created_at",
      )
      .order("created_at", { ascending: false }),
  ]);

  // Un error de consulta NO puede pasar en silencio (mismo criterio que el
  // panel): se loguea y se avisa en la UI.
  const queryErrors = [profileRes, docsRes, reviewsRes]
    .map((r) => r.error)
    .filter((e): e is NonNullable<typeof e> => Boolean(e));
  if (queryErrors.length > 0) {
    console.error(
      "[calidad] error cargando datos del tenant:",
      queryErrors.map((e) => e.message),
    );
  }

  // Última evaluación por documento (vienen ordenadas desc por created_at).
  const latestByDoc = new Map<string, QualityReview>();
  for (const r of (reviewsRes.data ?? []) as QualityReview[]) {
    if (!latestByDoc.has(r.document_id)) latestByDoc.set(r.document_id, r);
  }

  const documents: ReviewableDocument[] = (docsRes.data ?? []).map((d) => ({
    id: d.id,
    document_type: d.document_type as DocumentType,
    version: d.version,
    created_at: d.created_at,
    review: latestByDoc.get(d.id) ?? null,
  }));

  // La decisión (aprobar/rechazar/corrección) es del rol revisor; el backend
  // y RLS lo exigen igual — esto solo controla qué acciones se pintan.
  const role = profileRes.data?.role ?? "empresa";
  const canDecide = role === "admin" || role === "superadmin";

  return (
    <div className="flex min-h-screen flex-col">
      <header className="sticky top-0 z-10 border-b border-slate-100 bg-white/80 backdrop-blur">
        <div className="flex h-16 items-center px-4 sm:px-6">
          <p className="text-sm text-slate-400">Revisión de calidad</p>
        </div>
      </header>

      <main className="mx-auto w-full max-w-5xl flex-1 px-4 py-8 sm:px-6">
        <h1 className="text-2xl font-semibold tracking-tight text-slate-900">
          Revisión de calidad
        </h1>
        <p className="mt-1 max-w-2xl text-sm text-slate-500">
          Cada documento generado se evalúa con IA contra la checklist, los
          patrones reales de auditoría y la norma (completitud, coherencia y
          alertas). La decisión final —aprobar, rechazar o pedir corrección—
          es del revisor.
        </p>

        {queryErrors.length > 0 && (
          <div className="mt-4 rounded-xl border border-rose-100 bg-rose-50 px-4 py-3 text-sm text-rose-700">
            No pudimos cargar parte de la información; lo que ves puede estar
            incompleto. Recarga la página y, si persiste, contacta soporte.
          </div>
        )}

        <div className="mt-8">
          <QualityClient documents={documents} canDecide={canDecide} />
        </div>
      </main>
    </div>
  );
}
