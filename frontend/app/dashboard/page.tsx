import { Logo } from "@/components/logo";
import { DocStatus, DocumentType } from "@/lib/documents";
import { createClient } from "@/lib/supabase/server";

import { DocumentsGrid, type DocState } from "./documents-grid";
import { LogoutButton } from "./logout-button";

// Server Component protegido por middleware. Las consultas pasan por RLS con el
// JWT del usuario: solo devuelven filas de su tenant.
export default async function DashboardPage() {
  const supabase = createClient();

  const {
    data: { user },
  } = await supabase.auth.getUser();

  const [{ data: profile }, { data: company }, { data: statuses }, { data: docs }] =
    await Promise.all([
      supabase.from("user_profiles").select("tenant_id, role").single(),
      supabase.from("companies").select("name").limit(1).maybeSingle(),
      supabase
        .from("document_status")
        .select("document_type, status, completeness, updated_at"),
      supabase
        .from("documents")
        .select("document_type, version, storage_path, created_at")
        .order("created_at", { ascending: false }),
    ]);

  // Estado inicial por tipo de documento (último estado + último documento).
  const initial: Partial<Record<DocumentType, DocState>> = {};
  for (const s of statuses ?? []) {
    initial[s.document_type as DocumentType] = {
      status: s.status as DocStatus,
      completeness: s.completeness ?? null,
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
      version: null,
      storagePath: null,
      pendingFields: null,
    });
    // docs viene ordenado desc; el primero por tipo es el más reciente.
    if (entry.version === null) {
      entry.version = d.version;
      entry.storagePath = d.storage_path;
    }
  }

  const generated = Object.values(initial).filter(
    (s) => s && s.status !== "pending",
  ).length;

  return (
    <div className="min-h-screen">
      <header className="border-b border-slate-200 bg-white">
        <div className="mx-auto flex max-w-5xl items-center justify-between px-6 py-4">
          <Logo />
          <div className="flex items-center gap-4">
            <div className="hidden text-right sm:block">
              <p className="text-sm font-medium text-slate-700">{company?.name}</p>
              <p className="text-xs text-slate-400">{user?.email}</p>
            </div>
            <LogoutButton />
          </div>
        </div>
      </header>

      <main className="mx-auto max-w-5xl px-6 py-10">
        <div className="flex flex-col gap-2 sm:flex-row sm:items-end sm:justify-between">
          <div>
            <h1 className="text-2xl font-semibold text-slate-900">
              Documentos de cumplimiento
            </h1>
            <p className="mt-1 text-sm text-slate-500">
              Set núcleo NTC-ISO 21101. Genera cada documento; lo que falte de tu
              empresa aparecerá como{" "}
              <span className="font-medium text-slate-700">[PENDIENTE]</span>.
            </p>
          </div>
          <span className="badge bg-brand-50 text-brand-700">
            {generated} / 4 iniciados
          </span>
        </div>

        <div className="mt-8">
          <DocumentsGrid initial={initial} />
        </div>

        <p className="mt-10 text-center text-xs text-slate-400">
          Tenant {profile?.tenant_id ?? "—"} · rol {profile?.role ?? "—"}
        </p>
      </main>
    </div>
  );
}
