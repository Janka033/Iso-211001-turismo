import { Logo } from "@/components/logo";
import { DocStatus, DocumentType, DOCUMENTS } from "@/lib/documents";
import { createClient } from "@/lib/supabase/server";

import { DocumentsGrid, type DocState } from "./documents-grid";

// Server Component protegido por middleware. Las consultas pasan por RLS con el
// JWT del usuario: solo devuelven filas de su tenant.
export default async function DashboardPage() {
  const supabase = createClient();

  const {
    data: { user },
  } = await supabase.auth.getUser();

  const [profileRes, companyRes, statusesRes, docsRes, reviewsRes] = await Promise.all([
    supabase.from("user_profiles").select("tenant_id, role").single(),
    supabase.from("companies").select("name").limit(1).maybeSingle(),
    supabase
      .from("document_status")
      .select("document_type, status, completeness, updated_at"),
    supabase
      .from("documents")
      .select("id, document_type, version, storage_path, created_at")
      .order("created_at", { ascending: false }),
    // Score del Auditor por documento (última evaluación). Es el Nivel de
    // Cumplimiento Normativo que ve el panel, NO la completitud.
    supabase
      .from("quality_reviews")
      .select("document_id, score, created_at")
      .order("created_at", { ascending: false }),
  ]);

  const profile = profileRes.data;
  const company = companyRes.data;
  const statuses = statusesRes.data;
  const docs = docsRes.data;
  const reviews = reviewsRes.data;

  // Un error de consulta NO puede pasar en silencio: pintaría "Pendiente" y 0%
  // sobre documentos que sí existen. Se loguea y se avisa en la UI.
  const queryErrors = [profileRes, companyRes, statusesRes, docsRes, reviewsRes]
    .map((r) => r.error)
    .filter((e): e is NonNullable<typeof e> => Boolean(e));
  if (queryErrors.length > 0) {
    console.error(
      "[dashboard] error cargando datos del tenant:",
      queryErrors.map((e) => e.message),
    );
  }

  // Score del Auditor (última evaluación) por tipo de documento. Los reviews
  // vienen ordenados desc por created_at; se resuelve document_id → tipo y se
  // conserva el primero (más reciente) por tipo.
  const docTypeById = new Map<string, DocumentType>();
  for (const d of docs ?? []) {
    docTypeById.set(d.id as string, d.document_type as DocumentType);
  }
  const complianceByType = new Map<DocumentType, number>();
  for (const r of reviews ?? []) {
    const type = docTypeById.get(r.document_id as string);
    if (type && !complianceByType.has(type)) {
      complianceByType.set(type, r.score as number);
    }
  }

  // Estado inicial por tipo de documento (último estado + último documento).
  const initial: Partial<Record<DocumentType, DocState>> = {};
  for (const s of statuses ?? []) {
    initial[s.document_type as DocumentType] = {
      status: s.status as DocStatus,
      completeness: s.completeness ?? null,
      complianceScore: complianceByType.get(s.document_type as DocumentType) ?? null,
      version: null,
      storagePath: null,
      pendingFields: null,
    };
  }
  for (const d of docs ?? []) {
    const type = d.document_type as DocumentType;
    const entry = (initial[type] ??= {
      status: "generated",
      completeness: null,
      complianceScore: complianceByType.get(type) ?? null,
      version: null,
      storagePath: null,
      pendingFields: null,
    });
    if (entry.version === null) {
      entry.version = d.version;
      entry.storagePath = d.storage_path;
    }
  }

  const total = DOCUMENTS.length;
  const generated = Object.values(initial).filter(
    (s) => s && s.status !== "pending",
  ).length;
  const pct = total ? Math.round((generated / total) * 100) : 0;
  const companyName = company?.name ?? "Tu empresa";

  return (
    <div className="flex min-h-screen flex-col">
      {/* Topbar */}
      <header className="sticky top-0 z-10 border-b border-slate-100 bg-white/80 backdrop-blur">
        <div className="flex h-16 items-center justify-between px-4 sm:px-6">
          <div className="md:hidden">
            <Logo />
          </div>
          <p className="hidden text-sm text-slate-400 md:block">
            Panel de cumplimiento
          </p>
          <div className="flex items-center gap-3">
            <div className="text-right">
              <p className="text-sm font-medium text-slate-700">{companyName}</p>
              <p className="text-xs text-slate-400">{user?.email}</p>
            </div>
            <span className="flex h-9 w-9 items-center justify-center rounded-full bg-brand-gradient text-sm font-semibold text-white">
              {companyName.charAt(0).toUpperCase()}
            </span>
          </div>
        </div>
      </header>

      <main className="mx-auto w-full max-w-5xl flex-1 px-4 py-8 sm:px-6">
        <h1 className="font-display text-2xl font-extrabold tracking-tight text-tinta">
          Documentos de cumplimiento
        </h1>
        <p className="mt-1 text-sm text-slate-500">
          Set núcleo NTC-ISO 21101. Genera cada documento; lo que falte de tu
          empresa aparecerá como{" "}
          <span className="font-medium text-slate-700">[PENDIENTE]</span>.
        </p>

        {queryErrors.length > 0 && (
          <div className="mt-4 rounded-xl border border-rose-100 bg-rose-50 px-4 py-3 text-sm text-rose-700">
            No pudimos cargar parte de la información de tu empresa; lo que ves
            puede estar incompleto. Recarga la página y, si persiste, contacta
            soporte.
          </div>
        )}

        {/* Alerta de RNT (acción real, sin inventar fechas) */}
        <div className="mt-6 flex flex-col gap-3 rounded-2xl border border-accent-100 bg-accent-50 p-4 sm:flex-row sm:items-center sm:justify-between">
          <div className="flex items-start gap-3">
            <span className="mt-0.5 flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-accent-500/15 text-accent-600">
              <svg viewBox="0 0 20 20" className="h-5 w-5" fill="none">
                <path d="M10 7v4m0 3h.01M10 2.5 18 16H2L10 2.5Z" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" />
              </svg>
            </span>
            <div>
              <p className="text-sm font-semibold text-slate-900">
                Mantén tu RNT al día
              </p>
              <p className="text-sm text-slate-600">
                Configura la fecha de tu Registro Nacional de Turismo y te
                avisaremos antes de que venza.
              </p>
            </div>
          </div>
          <a href="#config" className="btn-secondary shrink-0">
            Configurar fecha
          </a>
        </div>

        {/* Progreso global */}
        <div className="mt-6 grid gap-4 sm:grid-cols-3">
          <div className="card p-6 sm:col-span-2">
            <div className="flex items-center justify-between">
              <p className="text-sm font-medium text-slate-700">
                Progreso de implementación
              </p>
              <span className="badge bg-brand-50 text-brand-700">
                {generated} / {total} documentos
              </span>
            </div>
            <div className="mt-4 flex items-end gap-4">
              <span className="text-4xl font-semibold text-slate-900">{pct}%</span>
              <div className="mb-2 flex-1">
                <div className="h-2.5 w-full overflow-hidden rounded-full bg-slate-100">
                  <div
                    className="h-full rounded-full bg-brand-600 transition-all"
                    style={{ width: `${pct}%` }}
                  />
                </div>
              </div>
            </div>
          </div>
          <div className="card flex flex-col justify-center p-6">
            <p className="text-sm text-slate-500">Fase actual</p>
            <p className="mt-1 text-lg font-semibold text-slate-900">
              Documentación
            </p>
            <p className="mt-1 text-xs text-slate-400">
              Genera el set núcleo para avanzar a operación.
            </p>
          </div>
        </div>

        {/* Documentos */}
        <div id="documentos" className="mt-10 scroll-mt-20">
          <DocumentsGrid initial={initial} />
        </div>

        <p className="mt-10 text-center text-xs text-slate-400">
          Tenant {profile?.tenant_id ?? "—"} · rol {profile?.role ?? "—"}
        </p>
      </main>
    </div>
  );
}
